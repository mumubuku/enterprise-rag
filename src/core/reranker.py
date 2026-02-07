from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseReranker(ABC):
    """重排序模型基类"""
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """重排序文档"""
        pass


class BGEReranker(BaseReranker):
    """BGE重排序模型"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: Optional[str] = None
    ):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
    
    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, device=self.device)
            except ImportError:
                raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")
        return self._model
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """使用BGE模型重排序"""
        if not documents:
            return []
        
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        
        results = []
        for idx, (doc, score) in enumerate(zip(documents, scores)):
            results.append({
                'index': idx,
                'content': doc,
                'score': float(score)
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]


class CohereReranker(BaseReranker):
    """Cohere重排序模型"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "rerank-multilingual-v3.0"
    ):
        self.api_key = api_key
        self.model = model
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """使用Cohere API重排序"""
        if not documents:
            return []
        
        try:
            import cohere
            client = cohere.Client(self.api_key)
            
            response = client.rerank(
                query=query,
                documents=documents,
                top_n=top_k,
                model=self.model
            )
            
            results = []
            for result in response.results:
                results.append({
                    'index': result.index,
                    'content': documents[result.index],
                    'score': result.relevance_score
                })
            
            return results
        except ImportError:
            raise ImportError("请安装 cohere: pip install cohere")
        except Exception as e:
            raise Exception(f"Cohere API调用失败: {str(e)}")


class RerankerFactory:
    """重排序模型工厂"""
    
    @staticmethod
    def create(
        reranker_type: str = "bge",
        **kwargs
    ) -> BaseReranker:
        """创建重排序模型"""
        reranker_type = reranker_type.lower()
        
        if reranker_type == "bge":
            return BGEReranker(
                model_name=kwargs.get("model_name", "BAAI/bge-reranker-v2-m3"),
                device=kwargs.get("device")
            )
        elif reranker_type == "cohere":
            return CohereReranker(
                api_key=kwargs.get("api_key"),
                model=kwargs.get("model", "rerank-multilingual-v3.0")
            )
        else:
            raise ValueError(f"不支持的重排序模型类型: {reranker_type}")


class QueryRewriter:
    """查询改写器"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def rewrite_query(
        self,
        query: str,
        context: Optional[str] = None,
        num_variations: int = 3
    ) -> List[str]:
        """改写查询"""
        if not self.llm:
            return self._simple_rewrite(query, num_variations)
        
        return self._llm_rewrite(query, context, num_variations)
    
    def _simple_rewrite(self, query: str, num_variations: int) -> List[str]:
        """简单改写"""
        variations = [query]
        
        words = query.split()
        if len(words) > 2:
            variations.append(" ".join(words[1:]))
            variations.append(" ".join(words[:-1]))
        
        if len(words) > 3:
            variations.append(" ".join(words[::2]))
        
        return variations[:num_variations]
    
    def _llm_rewrite(
        self,
        query: str,
        context: Optional[str],
        num_variations: int
    ) -> List[str]:
        """使用LLM改写"""
        prompt = f"""请为以下查询生成{num_variations}个不同的改写版本，保持原意不变但使用不同的表达方式。

原始查询: {query}

{f"上下文: {context}" if context else ""}

请只输出改写后的查询，每行一个："""
        
        try:
            response = self.llm.generate([prompt])
            variations = [line.strip() for line in response.split('\n') if line.strip()]
            return variations[:num_variations]
        except Exception as e:
            print(f"LLM改写失败: {e}")
            return self._simple_rewrite(query, num_variations)


class MultiPathRetriever:
    """多路召回检索器"""
    
    def __init__(
        self,
        hybrid_retriever,
        reranker: Optional[BaseReranker] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        num_paths: int = 3
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.query_rewriter = query_rewriter
        self.num_paths = num_paths
    
    def retrieve(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """多路召回检索"""
        all_results = []
        
        for path_idx in range(self.num_paths):
            if path_idx == 0:
                current_query = query
            else:
                if self.query_rewriter:
                    variations = self.query_rewriter.rewrite_query(query, num_variations=self.num_paths - 1)
                    if path_idx - 1 < len(variations):
                        current_query = variations[path_idx - 1]
                    else:
                        current_query = query
                else:
                    current_query = query
            
            path_results = self.hybrid_retriever.hybrid_search(
                current_query,
                vector_results,
                top_k=top_k * 2
            )
            
            for result in path_results:
                result['path'] = path_idx
                all_results.append(result)
        
        fused_results = self._fuse_multi_path(all_results, top_k)
        
        if self.reranker:
            fused_results = self._rerank_results(query, fused_results, top_k)
        
        return fused_results
    
    def _fuse_multi_path(
        self,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """融合多路召回结果"""
        fused = {}
        
        for result in results:
            idx = result['index']
            if idx not in fused:
                fused[idx] = {
                    'index': idx,
                    'score': result['score'],
                    'paths': set(),
                    'content': result.get('content', '')
                }
            else:
                fused[idx]['score'] = max(fused[idx]['score'], result['score'])
            
            fused[idx]['paths'].add(result['path'])
        
        for idx in fused:
            fused[idx]['path_count'] = len(fused[idx]['paths'])
            fused[idx]['score'] *= (1 + 0.1 * fused[idx]['path_count'])
        
        sorted_results = sorted(fused.values(), key=lambda x: x['score'], reverse=True)
        return sorted_results[:top_k]
    
    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """重排序结果"""
        if not results:
            return []
        
        documents = [r.get('content', '') for r in results]
        reranked = self.reranker.rerank(query, documents, top_k)
        
        for rerank_result in reranked:
            original_idx = rerank_result['index']
            if original_idx < len(results):
                results[original_idx]['rerank_score'] = rerank_result['score']
        
        results.sort(key=lambda x: x.get('rerank_score', x['score']), reverse=True)
        return results[:top_k]