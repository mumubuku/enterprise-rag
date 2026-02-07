from typing import List, Dict, Any, Optional
import math
from collections import defaultdict
import re


class BM25Retriever:
    """BM25检索器"""
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25
    ):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus = []
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.avg_doc_len = 0
        self._initialized = False
    
    def initialize(self, documents: List[str]):
        """初始化BM25索引"""
        self.corpus = documents
        self.doc_len = [len(doc.split()) for doc in documents]
        self.avg_doc_len = sum(self.doc_len) / len(documents) if self.doc_len else 0
        
        self.doc_freqs = []
        for doc in documents:
            freqs = defaultdict(int)
            tokens = self._tokenize(doc)
            for token in tokens:
                freqs[token] += 1
            self.doc_freqs.append(freqs)
        
        self._compute_idf()
        self._initialized = True
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()
    
    def _compute_idf(self):
        """计算IDF"""
        df = defaultdict(int)
        for freqs in self.doc_freqs:
            for token in freqs:
                df[token] += 1
        
        n_docs = len(self.corpus)
        for token, freq in df.items():
            self.idf[token] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """BM25检索"""
        if not self._initialized:
            return []
        
        query_tokens = self._tokenize(query)
        scores = []
        
        for idx, freqs in enumerate(self.doc_freqs):
            score = 0.0
            doc_len = self.doc_len[idx]
            
            for token in query_tokens:
                if token in freqs:
                    tf = freqs[token]
                    idf = self.idf.get(token, 0)
                    numerator = tf * (self.k1 + 1)
                    # 防止除零错误
                    avg_doc_len_safe = self.avg_doc_len if self.avg_doc_len != 0 else 1.0
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len_safe)
                    score += idf * (numerator / denominator)
            
            if score >= min_score:
                scores.append({
                    'index': idx,
                    'score': score,
                    'content': self.corpus[idx]
                })
        
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:top_k]
    
    def batch_search(
        self,
        queries: List[str],
        top_k: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """批量检索"""
        return [self.search(query, top_k) for query in queries]


class HybridRetriever:
    """混合检索器（BM25 + 向量检索）"""
    
    def __init__(
        self,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        normalize_scores: bool = True
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.normalize_scores = normalize_scores
        self.bm25_retriever = BM25Retriever()
        self._bm25_initialized = False
    
    def initialize_bm25(self, documents: List[str]):
        """初始化BM25"""
        self.bm25_retriever.initialize(documents)
        self._bm25_initialized = True
    
    def hybrid_search(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """混合检索"""
        if not self._bm25_initialized:
            return vector_results[:top_k]
        
        bm25_results = self.bm25_retriever.search(query, top_k=top_k * 2)
        
        if not bm25_results:
            return vector_results[:top_k]
        
        if not vector_results:
            return bm25_results[:top_k]
        
        fused_results = self._fuse_results(
            bm25_results,
            vector_results,
            top_k
        )
        
        return fused_results
    
    def _fuse_results(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """融合BM25和向量检索结果"""
        fused = {}
        
        bm25_scores = {r['index']: r['score'] for r in bm25_results}
        vector_scores = {r['index']: r['score'] for r in vector_results}
        
        all_indices = set(bm25_scores.keys()) | set(vector_scores.keys())
        
        if self.normalize_scores:
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
            max_vector = max(vector_scores.values()) if vector_scores else 1.0
            
            # 防止除零错误
            if max_bm25 == 0:
                max_bm25 = 1.0
            if max_vector == 0:
                max_vector = 1.0
            
            for idx in all_indices:
                bm25_score = bm25_scores.get(idx, 0) / max_bm25
                vector_score = vector_scores.get(idx, 0) / max_vector
                fused[idx] = {
                    'index': idx,
                    'score': self.bm25_weight * bm25_score + self.vector_weight * vector_score,
                    'bm25_score': bm25_score,
                    'vector_score': vector_score
                }
        else:
            for idx in all_indices:
                bm25_score = bm25_scores.get(idx, 0)
                vector_score = vector_scores.get(idx, 0)
                fused[idx] = {
                    'index': idx,
                    'score': self.bm25_weight * bm25_score + self.vector_weight * vector_score,
                    'bm25_score': bm25_score,
                    'vector_score': vector_score
                }
        
        sorted_results = sorted(fused.values(), key=lambda x: x['score'], reverse=True)
        return sorted_results[:top_k]