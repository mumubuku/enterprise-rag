from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from src.models.database import Base, KnowledgeBase, Document, DocumentChunk, QueryLog
from src.core.document_processor import DocumentProcessor
from src.core.vector_store import BaseVectorStore, get_vector_store
from src.core.embeddings import BaseEmbeddings, get_embedding_service
from src.core.llm import BaseLLM, get_llm
from src.core.rag_engine import RAGEngine, HybridRAGEngine
from src.config.settings import get_settings
import os
import shutil

settings = get_settings()


class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self):
        self.engine.dispose()


class KnowledgeBaseService:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()
        self.db_manager.create_tables()
        self._rag_engines: Dict[str, RAGEngine] = {}

    def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        retrieval_top_k: int = 4
    ) -> KnowledgeBase:
        session = self.db_manager.get_session()
        try:
            kb = KnowledgeBase(
                name=name,
                description=description,
                embedding_model=embedding_model,
                llm_model=llm_model,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                retrieval_top_k=retrieval_top_k
            )
            session.add(kb)
            session.commit()
            session.refresh(kb)
            return kb
        finally:
            session.close()

    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        session = self.db_manager.get_session()
        try:
            return session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        finally:
            session.close()

    def list_knowledge_bases(self, active_only: bool = False) -> List[KnowledgeBase]:
        session = self.db_manager.get_session()
        try:
            query = session.query(KnowledgeBase)
            if active_only:
                query = query.filter(KnowledgeBase.is_active == True)
            return query.all()
        finally:
            session.close()

    def update_knowledge_base(
        self,
        kb_id: str,
        **kwargs
    ) -> Optional[KnowledgeBase]:
        session = self.db_manager.get_session()
        try:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if kb:
                for key, value in kwargs.items():
                    if hasattr(kb, key):
                        setattr(kb, key, value)
                session.commit()
                session.refresh(kb)
                if kb_id in self._rag_engines:
                    del self._rag_engines[kb_id]
            return kb
        finally:
            session.close()

    def delete_knowledge_base(self, kb_id: str) -> bool:
        session = self.db_manager.get_session()
        try:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if kb:
                session.delete(kb)
                session.commit()
                if kb_id in self._rag_engines:
                    del self._rag_engines[kb_id]
                return True
            return False
        finally:
            session.close()

    def add_document(
        self,
        kb_id: str,
        file_path: str,
        original_filename: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        session = self.db_manager.get_session()
        try:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")

            processor = DocumentProcessor(
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap
            )

            chunks = processor.process_file(file_path, additional_metadata)
            if not chunks:
                raise ValueError(f"Failed to process document: No chunks generated from file {file_path}")

            embedding_provider = kb.embedding_model or "alibaba"
            embedding_service = get_embedding_service(embedding_provider)

            vector_store = get_vector_store(
                collection_name=kb_id,
                embedding_function=embedding_service
            )

            vector_ids = vector_store.add_documents(chunks)

            file_info = processor.get_file_info(file_path)
            
            display_filename = original_filename or file_info["file_name"]

            doc = Document(
                knowledge_base_id=kb_id,
                file_name=display_filename,
                file_path=file_path,
                file_size=file_info["file_size"],
                file_type=file_info["file_type"],
                chunk_count=len(chunks),
                doc_metadata=additional_metadata,
                is_processed=True
            )
            session.add(doc)
            session.flush()
            
            doc_id = doc.id

            for idx, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                doc_chunk = DocumentChunk(
                    document_id=doc_id,
                    chunk_index=idx,
                    content=chunk.page_content,
                    vector_id=vector_id,
                    chunk_metadata=chunk.metadata
                )
                session.add(doc_chunk)

            session.commit()
            session.refresh(doc)
            return doc
        finally:
            session.close()

    def add_directory(
        self,
        kb_id: str,
        directory_path: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        session = self.db_manager.get_session()
        try:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")

            processor = DocumentProcessor(
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap
            )

            chunks = processor.process_directory(directory_path, additional_metadata)
            if not chunks:
                return []

            embedding_provider = kb.embedding_model or "alibaba"
            embedding_service = get_embedding_service(embedding_provider)

            vector_store = get_vector_store(
                collection_name=kb_id,
                embedding_function=embedding_service
            )

            vector_ids = vector_store.add_documents(chunks)

            documents = []
            current_doc_id = None
            chunk_idx = 0

            for chunk, vector_id in zip(chunks, vector_ids):
                source = chunk.metadata.get("source", "")
                file_name = chunk.metadata.get("file_name", "")

                if source != current_doc_id:
                    if current_doc_id is not None:
                        session.commit()

                    file_info = processor.get_file_info(source)
                    doc = Document(
                        knowledge_base_id=kb_id,
                        file_name=file_name,
                        file_path=source,
                        file_size=file_info["file_size"],
                        file_type=file_info["file_type"],
                        chunk_count=0,
                        doc_metadata=additional_metadata,
                        is_processed=True
                    )
                    session.add(doc)
                    session.flush()
                    session.refresh(doc)
                    documents.append(doc)
                    current_doc_id = source
                    chunk_idx = 0

                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_idx,
                    content=chunk.page_content,
                    vector_id=vector_id,
                    chunk_metadata=chunk.metadata
                )
                session.add(doc_chunk)
                chunk_idx += 1

                doc.chunk_count = chunk_idx

            session.commit()
            return documents
        finally:
            session.close()

    def get_documents(self, kb_id: str) -> List[Document]:
        session = self.db_manager.get_session()
        try:
            return session.query(Document).filter(Document.knowledge_base_id == kb_id).all()
        finally:
            session.close()

    def delete_document(self, doc_id: str) -> bool:
        session = self.db_manager.get_session()
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                chunks = session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
                vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]

                if vector_ids:
                    embedding_provider = doc.knowledge_base.embedding_model or "alibaba"
                    embedding_service = get_embedding_service(embedding_provider)
                    vector_store = get_vector_store(
                        collection_name=doc.knowledge_base_id,
                        embedding_function=embedding_service
                    )
                    vector_store.delete(vector_ids)

                session.delete(doc)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_rag_engine(self, kb_id: str) -> RAGEngine:
        if kb_id not in self._rag_engines:
            kb = self.get_knowledge_base(kb_id)
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")

            embedding_provider = kb.embedding_model or "alibaba"
            embedding_service = get_embedding_service(embedding_provider)

            vector_store = get_vector_store(
                collection_name=kb_id,
                embedding_function=embedding_service
            )

            llm_provider = kb.llm_model or "alibaba"
            llm = get_llm(llm_provider)

            if settings.rerank_enabled:
                self._rag_engines[kb_id] = HybridRAGEngine(
                    vector_store=vector_store,
                    llm=llm,
                    embedding_service=embedding_service,
                    use_rerank=True
                )
            else:
                self._rag_engines[kb_id] = RAGEngine(
                    vector_store=vector_store,
                    llm=llm,
                    embedding_service=embedding_service
                )

        return self._rag_engines[kb_id]

    def get_stats(self) -> Dict[str, Any]:
        session = self.db_manager.get_session()
        try:
            total_kbs = session.query(KnowledgeBase).count()
            active_kbs = session.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).count()
            total_docs = session.query(Document).count()
            total_chunks = session.query(DocumentChunk).count()
            total_queries = session.query(QueryLog).count()

            return {
                "total_knowledge_bases": total_kbs,
                "active_knowledge_bases": active_kbs,
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "total_queries": total_queries
            }
        finally:
            session.close()