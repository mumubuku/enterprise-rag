from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "Enterprise RAG Knowledge Base"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "enterprise_rag"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    vector_db_type: str = "chroma"
    vector_db_host: str = "localhost"
    vector_db_port: int = 19530
    vector_db_index_name: str = "enterprise_knowledge"
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "enterprise_knowledge"

    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index_name: str = "enterprise_knowledge"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "enterprise_knowledge"

    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2048

    alibaba_cloud_access_key_id: Optional[str] = None
    alibaba_cloud_access_key_secret: Optional[str] = None
    alibaba_cloud_region_id: str = "cn-hangzhou"
    dashscope_api_key: Optional[str] = None
    dashscope_model: str = "qwen-turbo"
    dashscope_embedding_model: str = "text-embedding-v2"

    zhipuai_api_key: Optional[str] = None
    zhipuai_model: str = "glm-4"
    zhipuai_embedding_model: str = "embedding-2"

    erniebot_api_key: Optional[str] = None
    erniebot_secret_key: Optional[str] = None
    erniebot_model: str = "ernie-bot-4"

    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    local_embedding_device: str = "cpu"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size: int = 104857600
    supported_formats: str = "pdf,docx,doc,txt,md,html,xlsx,pptx,ppt,csv"

    retrieval_top_k: int = 4
    retrieval_score_threshold: float = 0.7
    rerank_enabled: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    context_window_size: int = 4000

    enable_cache: bool = True
    cache_ttl: int = 3600
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    secret_key: str = "your_secret_key_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    max_upload_size: int = 104857600

    file_storage_type: str = "local"
    oss_bucket_name: Optional[str] = None
    oss_endpoint: Optional[str] = None

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def supported_formats_list(self) -> list:
        return [fmt.strip() for fmt in self.supported_formats.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def ensure_directories(settings: Settings):
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.temp_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)