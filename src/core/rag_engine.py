from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Optional, Dict, Any, Tuple, Iterator
from src.core.vector_store import BaseVectorStore
from src.core.llm import BaseLLM
from src.core.embeddings import BaseEmbeddings
from src.core.hybrid_retriever import HybridRetriever
from src.core.reranker import MultiPathRetriever, RerankerFactory, QueryRewriter
from src.config.settings import get_settings
import time
import hashlib
from functools import lru_cache

settings = get_settings()


class RAGEngine:
    def __init__(
        self,
        vector_store: BaseVectorStore,
        llm: BaseLLM,
        embedding_service: Optional[BaseEmbeddings] = None,
        system_prompt: Optional[str] = None,
        db_manager=None,
        use_hybrid_search: bool = True,
        use_rerank: bool = False,
        use_query_rewrite: bool = False,
        num_paths: int = 3,
        enable_caching: bool = True,
        cache_size: int = 128
    ):
        self.vector_store = vector_store
        self.llm = llm
        self.embedding_service = embedding_service
        self.db_manager = db_manager
        self.use_hybrid_search = use_hybrid_search
        self.use_rerank = use_rerank
        self.use_query_rewrite = use_query_rewrite
        self.num_paths = num_paths
        self.enable_caching = enable_caching
        
        self.system_prompt = system_prompt or (
            "你是一个专业的企业知识库助手。请根据提供的上下文信息回答用户的问题。"
            "如果上下文中没有相关信息，请明确告知用户。"
            "请保持回答简洁、准确、专业。"
        )
        
        self.default_prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "上下文信息：\n{context}\n\n问题：{question}")
        ])
        
        # Query expansion prompt for generating related terms
        self.query_expansion_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个查询扩展助手。请根据原始查询生成相关的关键词和同义词，用逗号分隔。只返回关键词，不要其他内容。"),
            ("human", "查询: {query}")
        ])
        
        self.hybrid_retriever = None
        self.multi_path_retriever = None
        
        # Initialize caches with LRU strategy
        from collections import OrderedDict
        if enable_caching:
            self._query_cache = OrderedDict()
            self._cache_max_size = cache_size
            self._embedding_cache = {}
        
        if use_hybrid_search:
            self.hybrid_retriever = HybridRetriever(
                bm25_weight=0.3,
                vector_weight=0.7
            )
        
        if use_rerank:
            try:
                reranker = RerankerFactory.create(
                    reranker_type="bge",
                    model_name="BAAI/bge-reranker-v2-m3"
                )
                query_rewriter = QueryRewriter(llm=llm) if use_query_rewrite else None
                
                self.multi_path_retriever = MultiPathRetriever(
                    hybrid_retriever=self.hybrid_retriever,
                    reranker=reranker,
                    query_rewriter=query_rewriter,
                    num_paths=num_paths
                )
            except Exception as e:
                print(f"初始化重排序模型失败: {e}")
                self.use_rerank = False
    
    def _get_cache_key(self, query: str, top_k: int, score_threshold: float, filters: Optional[Dict[str, Any]]) -> str:
        """Generate a cache key for the query"""
        cache_input = f"{query}_{top_k}_{score_threshold}_{str(filters)}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_embedding_cache_key(self, text: str) -> str:
        """Generate a cache key for embeddings"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str):
        """Retrieve cached result if available"""
        if not self.enable_caching:
            return None
        return self._query_cache.get(cache_key)
    
    def _cache_result(self, cache_key: str, result):
        """Cache the result with LRU eviction"""
        if not self.enable_caching:
            return
        # Add to cache
        self._query_cache[cache_key] = result
        # Evict oldest entry if cache exceeds max size
        if len(self._query_cache) > self._cache_max_size:
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        # Generate cache key
        cache_key = self._get_cache_key(query, top_k, score_threshold, filters)
        
        # Try to get cached result
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        start_time = time.time()
        
        if self.use_rerank and self.multi_path_retriever:
            result = self._retrieve_with_rerank(query, top_k, score_threshold, filters, start_time)
        elif self.use_hybrid_search and self.hybrid_retriever:
            result = self._retrieve_hybrid(query, top_k, score_threshold, filters, start_time)
        else:
            result = self._retrieve_vector(query, top_k, score_threshold, filters, start_time)
        
        # Cache the result
        self._cache_result(cache_key, result)
        
        return result
    
    def expand_query(self, query: str) -> str:
        """Expand the query with related terms to improve retrieval"""
        try:
            # Create a simple expanded query by asking the LLM for related terms
            messages = [
                SystemMessage(content="你是一个查询扩展助手。请根据原始查询生成相关的关键词和同义词，用逗号分隔。只返回关键词，不要其他内容。"),
                HumanMessage(content=f"查询: {query}")
            ]
            
            expanded_terms = self.llm.generate(messages, **{"temperature": 0.3, "max_tokens": 100})
            
            # Combine original query with expanded terms
            expanded_query = f"{query} {expanded_terms}".strip()
            return expanded_query
        except Exception as e:
            # If expansion fails, return original query
            print(f"Query expansion failed: {e}")
            return query
    
    def _retrieve_vector(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]],
        start_time: float
    ) -> Tuple[List[Tuple[Document, float]], float]:
        """纯向量检索"""
        # Use expanded query for better retrieval
        expanded_query = self.expand_query(query)
        
        results = self.vector_store.similarity_search_with_score(
            query=expanded_query,
            k=top_k,
            filter=filters
        )
        
        filtered_results = [
            (doc, max(0, min(1.0, 1 - score))) for doc, score in results
            if max(0, min(1.0, 1 - score)) >= score_threshold
        ]
        
        retrieval_time = time.time() - start_time
        return filtered_results, retrieval_time
    
    def _retrieve_hybrid(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]],
        start_time: float
    ) -> Tuple[List[Tuple[Document, float]], float]:
        """混合检索"""
        # Use expanded query for better retrieval
        expanded_query = self.expand_query(query)
        
        vector_results = self.vector_store.similarity_search_with_score(
            query=expanded_query,
            k=top_k * 2,
            filter=filters
        )
        
        if not vector_results:
            retrieval_time = time.time() - start_time
            return [], retrieval_time
        
        documents = [doc.page_content for doc, _ in vector_results]
        
        if not self.hybrid_retriever._bm25_initialized:
            self.hybrid_retriever.initialize_bm25(documents)
        
        vector_results_dict = [
            {
                'index': idx,
                'score': max(0, min(1.0, 1 - score)),
                'content': doc.page_content,
                'document': doc
            }
            for idx, (doc, score) in enumerate(vector_results)
        ]
        
        hybrid_results = self.hybrid_retriever.hybrid_search(
            expanded_query,
            vector_results_dict,
            top_k=top_k
        )
        
        # 创建索引到原始文档的映射
        index_to_document = {item['index']: (item['document'], item['score']) for item in vector_results_dict}
        
        filtered_results = [
            (index_to_document[result['index']][0], max(0, min(1.0, result['score'])))  # (document, normalized_score)
            for result in hybrid_results
            if result['index'] in index_to_document and max(0, min(1.0, result['score'])) >= score_threshold
        ]
        
        retrieval_time = time.time() - start_time
        return filtered_results, retrieval_time
    
    def _retrieve_with_rerank(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]],
        start_time: float
    ) -> Tuple[List[Tuple[Document, float]], float]:
        """带重排序的检索"""
        # Use expanded query for better retrieval
        expanded_query = self.expand_query(query)
        
        vector_results = self.vector_store.similarity_search_with_score(
            query=expanded_query,
            k=top_k * 3,
            filter=filters
        )
        
        if not vector_results:
            retrieval_time = time.time() - start_time
            return [], retrieval_time
        
        documents = [doc.page_content for doc, _ in vector_results]
        
        if not self.hybrid_retriever._bm25_initialized:
            self.hybrid_retriever.initialize_bm25(documents)
        
        vector_results_dict = [
            {
                'index': idx,
                'score': max(0, min(1.0, 1 - score)),
                'content': doc.page_content,
                'document': doc
            }
            for idx, (doc, score) in enumerate(vector_results)
        ]
        
        reranked_results = self.multi_path_retriever.retrieve(
            expanded_query,
            vector_results_dict,
            top_k=top_k
        )
        
        filtered_results = [
            (result['document'], max(0, min(1.0, result.get('rerank_score', result['score']))))
            for result in reranked_results
            if max(0, min(1.0, result.get('rerank_score', result['score']))) >= score_threshold
        ]
        
        retrieval_time = time.time() - start_time
        return filtered_results, retrieval_time

    def format_context(self, documents: List[Tuple[Document, float]]) -> str:
        context_parts = []
        for idx, (doc, score) in enumerate(documents, 1):
            file_name = doc.metadata.get("file_name", "未知文件")
            source = doc.metadata.get("source", "未知来源")
            context_parts.append(
                f"[文档片段 {idx}] (相似度: {score:.4f}, 文件: {file_name})\n{doc.page_content}"
            )
        return "\n\n".join(context_parts)

    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        messages = [
            SystemMessage(content=self.system_prompt)
        ]
        
        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(SystemMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=f"上下文信息：\n{context}\n\n问题：{question}"))
        
        return self.llm.generate(messages, **kwargs)

    def query(
        self,
        question: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        adaptive_threshold: bool = True,  # New parameter for adaptive threshold
        **llm_kwargs
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # Try with original threshold first
        documents, retrieval_time = self.retrieve(
            query=question,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
        
        # If no results and adaptive threshold is enabled, try with lower threshold
        if not documents and adaptive_threshold and score_threshold > 0:
            # Retry with a lower threshold
            documents, retrieval_time = self.retrieve(
                query=question,
                top_k=top_k,
                score_threshold=score_threshold * 0.5,  # Reduce threshold by half
                filters=filters
            )
        
        if not documents:
            return {
                "question": question,
                "answer": "抱歉，我在知识库中没有找到相关信息来回答您的问题。",
                "sources": [],
                "retrieval_time": retrieval_time,
                "generation_time": 0.0,
                "total_time": time.time() - start_time,
                "has_context": False  # Indicate no context was found
            }
        
        context = self.format_context(documents)
        
        gen_start_time = time.time()
        answer = self.generate_answer(question, context, conversation_history, **llm_kwargs)
        generation_time = time.time() - gen_start_time
        
        sources = []
        for doc, score in documents:
            metadata = dict(doc.metadata)
            
            if self.db_manager:
                try:
                    session = self.db_manager.get_session()
                    from src.models.database import Document as DBDocument
                    db_doc = session.query(DBDocument).filter(DBDocument.file_path == metadata.get("source", "")).first()
                    if db_doc:
                        metadata["file_name"] = db_doc.file_name
                    session.close()
                except Exception as e:
                    pass
            
            sources.append({
                "content": doc.page_content,
                "score": max(0, min(1.0, score)),  # score已经是相似度分数，不需要再转换
                "metadata": metadata
            })
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "total_time": time.time() - start_time,
            "has_context": True  # Indicate context was found
        }

    def stream_query(
        self,
        question: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        adaptive_threshold: bool = True,  # New parameter for adaptive threshold
        **llm_kwargs
    ) -> Iterator[Dict[str, Any]]:
        start_time = time.time()
        
        # Try with original threshold first
        documents, retrieval_time = self.retrieve(
            query=question,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
        
        # If no results and adaptive threshold is enabled, try with lower threshold
        if not documents and adaptive_threshold and score_threshold > 0:
            # Retry with a lower threshold
            documents, retrieval_time = self.retrieve(
                query=question,
                top_k=top_k,
                score_threshold=score_threshold * 0.5,  # Reduce threshold by half
                filters=filters
            )
        
        if not documents:
            yield {
                "question": question,
                "answer": "抱歉，我在知识库中没有找到相关信息来回答您的问题。",
                "sources": [],
                "retrieval_time": retrieval_time,
                "generation_time": 0.0,
                "total_time": time.time() - start_time,
                "done": True,
                "has_context": False  # Indicate no context was found
            }
            return
        
        context = self.format_context(documents)
        
        sources = [
            {
                "content": doc.page_content,
                "score": max(0, min(1.0, score)),  # score已经是相似度分数，不需要再转换
                "metadata": doc.metadata
            }
            for doc, score in documents
        ]
        
        messages = [
            SystemMessage(content=self.system_prompt)
        ]
        
        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(SystemMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=f"上下文信息：\n{context}\n\n问题：{question}"))
        
        gen_start_time = time.time()
        full_answer = ""
        
        for chunk in self.llm.stream(messages, **llm_kwargs):
            full_answer += chunk
            yield {
                "question": question,
                "answer": full_answer,
                "sources": sources,
                "retrieval_time": retrieval_time,
                "generation_time": time.time() - gen_start_time,
                "total_time": time.time() - start_time,
                "done": False,
                "has_context": True  # Indicate context was found
            }
        
        yield {
            "question": question,
            "answer": full_answer,
            "sources": sources,
            "retrieval_time": retrieval_time,
            "generation_time": time.time() - gen_start_time,
            "total_time": time.time() - start_time,
            "done": True,
            "has_context": True  # Indicate context was found
        }

    def search_only(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        documents, retrieval_time = self.retrieve(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
        
        results = [
            {
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            }
            for doc, score in documents
        ]
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "retrieval_time": time.time() - start_time
        }

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
        self.default_prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "上下文信息：\n{context}\n\n问题：{question}")
        ])

    def get_stats(self) -> Dict[str, Any]:
        return {
            "vector_store_count": self.vector_store.count(),
            "llm_provider": type(self.llm).__name__,
            "system_prompt": self.system_prompt
        }


