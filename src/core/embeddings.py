from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings, HuggingFaceEmbeddings
from typing import List, Optional
from abc import ABC, abstractmethod
from src.config.settings import get_settings
from functools import lru_cache

settings = get_settings()


class BaseEmbeddings(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass


class OpenAIEmbeddingService(BaseEmbeddings):
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.openai_embedding_model
        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            openai_api_key=settings.openai_api_key
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


class AlibabaEmbeddingService(BaseEmbeddings):
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.dashscope_embedding_model
        self.embeddings = DashScopeEmbeddings(
            model=self.model,
            dashscope_api_key=settings.dashscope_api_key
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


class LocalEmbeddingService(BaseEmbeddings):
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or settings.local_embedding_model
        self.device = device or settings.local_embedding_device
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": self.device}
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


class EmbeddingServiceFactory:
    @staticmethod
    def create(provider: str = "openai", **kwargs) -> BaseEmbeddings:
        provider = provider.lower()
        
        if provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is not configured")
            return OpenAIEmbeddingService(**kwargs)
        
        elif provider == "alibaba" or provider == "dashscope":
            if not settings.dashscope_api_key:
                raise ValueError("DashScope API key is not configured")
            return AlibabaEmbeddingService(**kwargs)
        
        elif provider == "local":
            return LocalEmbeddingService(**kwargs)
        
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")


@lru_cache()
def get_embedding_service(provider: str = "openai") -> BaseEmbeddings:
    return EmbeddingServiceFactory.create(provider)


class EmbeddingCache:
    def __init__(self):
        self._cache = {}

    def get(self, text: str) -> Optional[List[float]]:
        return self._cache.get(text)

    def set(self, text: str, embedding: List[float]):
        self._cache[text] = embedding

    def clear(self):
        self._cache.clear()


class CachedEmbeddingService(BaseEmbeddings):
    def __init__(self, base_service: BaseEmbeddings):
        self.base_service = base_service
        self.cache = EmbeddingCache()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            cached = self.cache.get(text)
            if cached is not None:
                embeddings.append(cached)
            else:
                embedding = self.base_service.embed_query(text)
                self.cache.set(text, embedding)
                embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        cached = self.cache.get(text)
        if cached is not None:
            return cached
        embedding = self.base_service.embed_query(text)
        self.cache.set(text, embedding)
        return embedding