from langchain_chroma import Chroma
from langchain_community.vectorstores import Pinecone, Qdrant
from langchain_core.documents import Document
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
from src.config.settings import get_settings
from src.core.embeddings import BaseEmbeddings
import os

settings = get_settings()


class BaseVectorStore(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        pass

    @abstractmethod
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[Document, float]]:
        pass

    @abstractmethod
    def delete(self, ids: List[str], **kwargs) -> None:
        pass

    @abstractmethod
    def count(self) -> int:
        pass


class ChromaVectorStore(BaseVectorStore):
    def __init__(
        self,
        collection_name: str,
        embedding_function: BaseEmbeddings,
        persist_directory: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=self.persist_directory
        )

    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        return self.vector_store.add_documents(documents, **kwargs)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[Document, float]]:
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )

    def delete(self, ids: List[str], **kwargs) -> None:
        self.vector_store.delete(ids=ids, **kwargs)

    def count(self) -> int:
        try:
            return self.vector_store._collection.count()
        except Exception:
            return 0

    def persist(self) -> None:
        if hasattr(self.vector_store, 'persist'):
            self.vector_store.persist()


class PineconeVectorStore(BaseVectorStore):
    def __init__(
        self,
        index_name: str,
        embedding_function: BaseEmbeddings,
        environment: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.index_name = index_name
        self.embedding_function = embedding_function
        self.environment = environment or settings.pinecone_environment
        self.api_key = api_key or settings.pinecone_api_key
        
        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        
        import pinecone
        pinecone.init(api_key=self.api_key, environment=self.environment)
        
        self.vector_store = Pinecone.from_existing_index(
            index_name=index_name,
            embedding=embedding_function
        )

    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        return self.vector_store.add_documents(documents, **kwargs)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[Document, float]]:
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )

    def delete(self, ids: List[str], **kwargs) -> None:
        self.vector_store.delete(ids=ids, **kwargs)

    def count(self) -> int:
        try:
            import pinecone
            index = pinecone.Index(self.index_name)
            return index.describe_index_stats()['total_vector_count']
        except Exception:
            return 0


class QdrantVectorStore(BaseVectorStore):
    def __init__(
        self,
        collection_name: str,
        embedding_function: BaseEmbeddings,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.api_key = api_key or settings.qdrant_api_key
        
        from qdrant_client import QdrantClient
        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key
        )
        
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=collection_name,
            embeddings=embedding_function
        )

    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        return self.vector_store.add_documents(documents, **kwargs)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[Document, float]]:
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )

    def delete(self, ids: List[str], **kwargs) -> None:
        self.vector_store.delete(ids=ids, **kwargs)

    def count(self) -> int:
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count
        except Exception:
            return 0


class VectorStoreFactory:
    @staticmethod
    def create(
        store_type: str = "chroma",
        collection_name: str = "default",
        embedding_function: Optional[BaseEmbeddings] = None,
        **kwargs
    ) -> BaseVectorStore:
        store_type = store_type.lower()
        
        if store_type == "chroma":
            return ChromaVectorStore(
                collection_name=collection_name,
                embedding_function=embedding_function,
                **kwargs
            )
        
        elif store_type == "pinecone":
            return PineconeVectorStore(
                index_name=collection_name,
                embedding_function=embedding_function,
                **kwargs
            )
        
        elif store_type == "qdrant":
            return QdrantVectorStore(
                collection_name=collection_name,
                embedding_function=embedding_function,
                **kwargs
            )
        
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")


def get_vector_store(
    collection_name: str,
    embedding_function: BaseEmbeddings,
    store_type: Optional[str] = None
) -> BaseVectorStore:
    store_type = store_type or settings.vector_db_type
    return VectorStoreFactory.create(
        store_type=store_type,
        collection_name=collection_name,
        embedding_function=embedding_function
    )