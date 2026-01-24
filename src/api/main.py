from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import tempfile
import os
import json
import uuid
from src.config.settings import get_settings, ensure_directories
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.auth_service import permission_service
from src.services.file_storage_service import get_file_storage_service
from src.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    DocumentUploadResponse,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    QARequest,
    QAResponse,
    StatsResponse,
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionResponse,
    FileUploadResponse
)
from src.utils.dependencies import (
    get_db,
    get_current_user,
    require_superuser,
    require_permission,
    require_kb_access,
    require_kb_access_from_path,
    is_superuser
)
from src.models.database import User
from src.api.auth import router as auth_router

settings = get_settings()
ensure_directories(settings)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

kb_service = KnowledgeBaseService()

if settings.file_storage_type == "local":
    os.makedirs(settings.upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        from src.services.knowledge_base_service import DatabaseManager
        from src.models.database import User
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            existing_admin = session.query(User).filter(User.username == 'admin').first()
            
            if not existing_admin:
                print("📊 初始化数据库...")
                from src.services.auth_service import auth_service
                
                admin_password = auth_service.get_password_hash('admin123')
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    hashed_password=admin_password,
                    full_name='系统管理员',
                    is_superuser=True,
                    is_active=True
                )
                session.add(admin_user)
                session.commit()
                print("✅ 默认管理员用户已创建")
                print("   用户名: admin")
                print("   密码: admin123")
            else:
                print("ℹ️  管理员用户已存在")
        finally:
            session.close()
    except Exception as e:
        print(f"⚠️  数据库初始化警告: {e}")


def get_kb_service():
    return kb_service


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(require_permission("knowledge_base", "create")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        kb = service.create_knowledge_base(
            name=kb_data.name,
            description=kb_data.description,
            embedding_model=kb_data.embedding_model,
            llm_model=kb_data.llm_model,
            chunk_size=kb_data.chunk_size,
            chunk_overlap=kb_data.chunk_overlap,
            retrieval_top_k=kb_data.retrieval_top_k
        )
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            llm_model=kb.llm_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            retrieval_top_k=kb.retrieval_top_k,
            is_active=kb.is_active,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            document_count=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        kbs = service.list_knowledge_bases(active_only=active_only)
        
        if not is_superuser(current_user):
            accessible_kb_ids = permission_service.get_accessible_knowledge_bases(
                service.db_manager.get_session(),
                current_user,
                "read"
            )
            kbs = [kb for kb in kbs if kb.id in accessible_kb_ids]
        
        return [
            KnowledgeBaseResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                embedding_model=kb.embedding_model,
                llm_model=kb.llm_model,
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap,
                retrieval_top_k=kb.retrieval_top_k,
                is_active=kb.is_active,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
                document_count=0
            )
            for kb in kbs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(require_kb_access_from_path("read")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        kb = service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            llm_model=kb.llm_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            retrieval_top_k=kb.retrieval_top_k,
            is_active=kb.is_active,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            document_count=0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    kb_data: KnowledgeBaseUpdate,
    current_user: User = Depends(require_kb_access_from_path("write")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        kb = service.update_knowledge_base(
            kb_id,
            **kb_data.model_dump(exclude_unset=True)
        )
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            llm_model=kb.llm_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            retrieval_top_k=kb.retrieval_top_k,
            is_active=kb.is_active,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            document_count=0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/knowledge-bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(require_kb_access_from_path("delete")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        success = service.delete_knowledge_base(kb_id)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"message": "Knowledge base deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge-bases/{kb_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_kb_access_from_path("write")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        content = await file.read()
        original_filename = file.filename
        
        file_storage = get_file_storage_service()
        file_path, file_url = await file_storage.save_file(
            content,
            original_filename,
            subfolder=f"kb/{kb_id}"
        )
        
        doc = service.add_document(kb_id, file_path, original_filename=original_filename)
        return DocumentUploadResponse(
            document_id=doc.id,
            file_name=doc.file_name,
            file_size=doc.file_size,
            file_type=doc.file_type,
            chunk_count=doc.chunk_count,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge-bases/{kb_id}/documents/directory")
async def upload_directory(
    kb_id: str,
    directory_path: str,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        if not os.path.exists(directory_path):
            raise HTTPException(status_code=404, detail="Directory not found")
        
        docs = service.add_directory(kb_id, directory_path)
        return {
            "message": "Directory uploaded successfully",
            "document_count": len(docs),
            "documents": [
                {
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "chunk_count": doc.chunk_count
                }
                for doc in docs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge-bases/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        docs = service.get_documents(kb_id)
        return [
            DocumentResponse(
                id=doc.id,
                knowledge_base_id=doc.knowledge_base_id,
                file_name=doc.file_name,
                file_size=doc.file_size,
                file_type=doc.file_type,
                chunk_count=doc.chunk_count,
                is_processed=doc.is_processed,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in docs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        success = service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge-bases/{kb_id}/permissions", response_model=KnowledgeBasePermissionResponse)
async def grant_knowledge_base_permission(
    kb_id: str,
    permission_data: KnowledgeBasePermissionCreate,
    current_user: User = Depends(require_kb_access_from_path("admin")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        session = service.db_manager.get_session()
        kb_permission = permission_service.grant_knowledge_base_permission(
            session,
            kb_id,
            permission_data.user_id,
            permission_data.permission_type,
            current_user.id
        )
        return KnowledgeBasePermissionResponse(
            id=kb_permission.id,
            knowledge_base_id=kb_permission.knowledge_base_id,
            user_id=kb_permission.user_id,
            permission_type=kb_permission.permission_type,
            created_at=kb_permission.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/knowledge-bases/{kb_id}/permissions/{user_id}/{permission_type}")
async def revoke_knowledge_base_permission(
    kb_id: str,
    user_id: str,
    permission_type: str,
    current_user: User = Depends(require_kb_access_from_path("admin")),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        session = service.db_manager.get_session()
        success = permission_service.revoke_knowledge_base_permission(
            session,
            kb_id,
            user_id,
            permission_type
        )
        if not success:
            raise HTTPException(status_code=404, detail="Permission not found")
        return {"message": "Permission revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search", response_model=SearchResponse)
async def search(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        rag_engine = service.get_rag_engine(search_request.knowledge_base_id)
        result = rag_engine.search_only(
            query=search_request.query,
            top_k=search_request.top_k,
            score_threshold=search_request.score_threshold,
            filters=search_request.filters
        )
        
        return SearchResponse(
            query=result["query"],
            results=[
                SearchResult(
                    chunk_id=r.get("metadata", {}).get("chunk_id", ""),
                    document_id=r.get("metadata", {}).get("document_id", ""),
                    content=r["content"],
                    score=r["score"],
                    metadata=r.get("metadata")
                )
                for r in result["results"]
            ],
            total_count=result["count"],
            retrieval_time=result["retrieval_time"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/qa", response_model=QAResponse)
async def question_answer(
    qa_request: QARequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        rag_engine = service.get_rag_engine(qa_request.knowledge_base_id)
        result = rag_engine.query(
            question=qa_request.question,
            top_k=qa_request.top_k,
            **qa_request.model_dump(exclude={"question", "knowledge_base_id", "top_k"}, exclude_unset=True)
        )
        
        return QAResponse(
            question=result["question"],
            answer=result["answer"],
            sources=[
                SearchResult(
                    chunk_id=s.get("metadata", {}).get("chunk_id", ""),
                    document_id=s.get("metadata", {}).get("document_id", ""),
                    content=s["content"],
                    score=s["score"],
                    metadata=s.get("metadata")
                )
                for s in result["sources"]
            ],
            retrieval_time=result["retrieval_time"],
            generation_time=result["generation_time"],
            total_time=result["total_time"],
            llm_provider=type(rag_engine.llm).__name__,
            llm_model=getattr(rag_engine.llm, 'model', 'unknown')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/qa/stream")
async def question_answer_stream(
    qa_request: QARequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        rag_engine = service.get_rag_engine(qa_request.knowledge_base_id)
        
        async def generate():
            for chunk in rag_engine.stream_query(
                question=qa_request.question,
                top_k=qa_request.top_k,
                **qa_request.model_dump(exclude={"question", "knowledge_base_id", "top_k"}, exclude_unset=True)
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(require_superuser),
    service: KnowledgeBaseService = Depends(get_kb_service)
):
    try:
        stats = service.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    storage_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """通用文件上传接口，支持本地存储和OSS"""
    try:
        if file.size and file.size > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 ({settings.max_upload_size} bytes)"
            )

        content = await file.read()
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        file_type = file_ext.lstrip('.')

        storage = storage_type or settings.file_storage_type
        file_storage = get_file_storage_service(storage)

        file_path, file_url = await file_storage.save_file(
            content,
            file.filename,
            subfolder=f"{file_id[:2]}"
        )

        return FileUploadResponse(
            file_id=file_id,
            file_name=file.filename,
            file_size=len(content),
            file_type=file_type,
            file_path=file_path,
            file_url=file_url,
            storage_type=storage
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/files/{file_id}")
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取文件信息"""
    try:
        storage = settings.file_storage_type
        file_storage = get_file_storage_service(storage)

        file_path = f"{file_id[:2]}/{file_id}"
        file_url = await file_storage.get_file_url(file_path)

        return {
            "file_id": file_id,
            "file_url": file_url,
            "storage_type": storage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    try:
        storage = settings.file_storage_type
        file_storage = get_file_storage_service(storage)

        file_path = f"{file_id[:2]}/{file_id}"
        success = await file_storage.delete_file(file_path)

        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )