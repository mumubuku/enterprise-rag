from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Optional, Dict, Any, Tuple, Iterator
from src.core.vector_store import BaseVectorStore
from src.core.llm import BaseLLM
from src.core.embeddings import BaseEmbeddings
from src.config.settings import get_settings
import time

settings = get_settings()


class RAGEngine:
    def __init__(
        self,
        vector_store: BaseVectorStore,
        llm: BaseLLM,
        embedding_service: Optional[BaseEmbeddings] = None,
        system_prompt: Optional[str] = None
    ):
        self.vector_store = vector_store
        self.llm = llm
        self.embedding_service = embedding_service
        
        self.system_prompt = system_prompt or (
            "你是一个专业的企业知识库助手。请根据提供的上下文信息回答用户的问题。"
            "如果上下文中没有相关信息，请明确告知用户。"
            "请保持回答简洁、准确、专业。"
        )
        
        self.default_prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "上下文信息：\n{context}\n\n问题：{question}")
        ])

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        start_time = time.time()
        
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filters
        )
        
        filtered_results = [
            (doc, score) for doc, score in results
            if score >= score_threshold
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
        **kwargs
    ) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"上下文信息：\n{context}\n\n问题：{question}")
        ]
        
        return self.llm.generate(messages, **kwargs)

    def query(
        self,
        question: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        **llm_kwargs
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        documents, retrieval_time = self.retrieve(
            query=question,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
        
        if not documents:
            return {
                "question": question,
                "answer": "抱歉，我在知识库中没有找到相关信息来回答您的问题。",
                "sources": [],
                "retrieval_time": retrieval_time,
                "generation_time": 0.0,
                "total_time": time.time() - start_time
            }
        
        context = self.format_context(documents)
        
        gen_start_time = time.time()
        answer = self.generate_answer(question, context, **llm_kwargs)
        generation_time = time.time() - gen_start_time
        
        sources = [
            {
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            }
            for doc, score in documents
        ]
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "total_time": time.time() - start_time
        }

    def stream_query(
        self,
        question: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        **llm_kwargs
    ) -> Iterator[Dict[str, Any]]:
        start_time = time.time()
        
        documents, retrieval_time = self.retrieve(
            query=question,
            top_k=top_k,
            score_threshold=score_threshold,
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
                "done": True
            }
            return
        
        context = self.format_context(documents)
        
        sources = [
            {
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            }
            for doc, score in documents
        ]
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"上下文信息：\n{context}\n\n问题：{question}")
        ]
        
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
                "done": False
            }
        
        yield {
            "question": question,
            "answer": full_answer,
            "sources": sources,
            "retrieval_time": retrieval_time,
            "generation_time": time.time() - gen_start_time,
            "total_time": time.time() - start_time,
            "done": True
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


class HybridRAGEngine(RAGEngine):
    def __init__(
        self,
        vector_store: BaseVectorStore,
        llm: BaseLLM,
        embedding_service: Optional[BaseEmbeddings] = None,
        system_prompt: Optional[str] = None,
        use_rerank: bool = False,
        rerank_model: Optional[str] = None
    ):
        super().__init__(vector_store, llm, embedding_service, system_prompt)
        self.use_rerank = use_rerank
        self.rerank_model = rerank_model or settings.rerank_model

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        documents, retrieval_time = super().retrieve(
            query=query,
            top_k=top_k * 2,
            score_threshold=score_threshold,
            filters=filters
        )
        
        if self.use_rerank and len(documents) > top_k:
            documents = self._rerank(query, documents, top_k)
        
        return documents, retrieval_time

    def _rerank(
        self,
        query: str,
        documents: List[Tuple[Document, float]],
        top_k: int
    ) -> List[Tuple[Document, float]]:
        try:
            from sentence_transformers import CrossEncoder
            model = CrossEncoder(self.rerank_model)
            
            doc_texts = [doc.page_content for doc, _ in documents]
            scores = model.predict([[query, doc_text] for doc_text in doc_texts])
            
            reranked = sorted(
                zip(documents, scores),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [(doc, float(score)) for (doc, _), score in reranked[:top_k]]
        except Exception as e:
            print(f"Reranking failed: {e}, using original results")
            return documents[:top_k]