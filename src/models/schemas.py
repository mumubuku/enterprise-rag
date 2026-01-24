from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ALIBABA = "alibaba"
    ZHIPUAI = "zhipuai"
    ERNIE = "ernie"
    LOCAL = "local"


class VectorDBType(str, Enum):
    CHROMA = "chroma"
    MILVUS = "milvus"
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    department_id: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    department_id: Optional[str]
    is_active: bool
    is_superuser: bool
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    department_id: Optional[str] = None
    is_superuser: bool = False


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, min_length=1, max_length=255)
    full_name: Optional[str] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    resource: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    id: str
    name: str
    resource: str
    action: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBasePermissionCreate(BaseModel):
    user_id: str
    permission_type: str = Field(..., pattern="^(read|write|delete|admin)$")


class KnowledgeBasePermissionResponse(BaseModel):
    id: str
    knowledge_base_id: str
    user_id: str
    permission_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    chunk_size: Optional[int] = Field(default=1000, ge=100, le=4000)
    chunk_overlap: Optional[int] = Field(default=200, ge=0, le=1000)
    retrieval_top_k: Optional[int] = Field(default=4, ge=1, le=20)


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=4000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)
    retrieval_top_k: Optional[int] = Field(None, ge=1, le=20)
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    embedding_model: Optional[str]
    llm_model: Optional[str]
    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    file_size: int
    file_type: str
    chunk_count: int
    status: str


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    file_name: str
    file_size: int
    file_type: str
    chunk_count: int
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    knowledge_base_id: str
    top_k: Optional[int] = Field(default=4, ge=1, le=20)
    score_threshold: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_count: int
    retrieval_time: float


class QARequest(BaseModel):
    question: str = Field(..., min_length=1)
    knowledge_base_id: str
    top_k: Optional[int] = Field(default=4, ge=1, le=20)
    llm_provider: Optional[LLMProvider] = LLMProvider.OPENAI
    llm_model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=8192)
    use_rerank: Optional[bool] = False


class QAResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResult]
    retrieval_time: float
    generation_time: float
    total_time: float
    llm_provider: str
    llm_model: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class StatsResponse(BaseModel):
    total_knowledge_bases: int
    total_documents: int
    total_chunks: int
    total_queries: int
    active_knowledge_bases: int


class FileUploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    file_path: str
    file_url: str
    storage_type: str
