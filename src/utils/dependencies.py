from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from src.services.auth_service import auth_service, permission_service
from src.services.knowledge_base_service import DatabaseManager
from src.models.database import User

security = HTTPBearer()
db_manager = DatabaseManager()


def get_db():
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user


def require_permission(resource: str, action: str):
    async def check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not permission_service.has_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {resource}"
            )
        return current_user
    
    return check


def require_kb_access(kb_id: str, permission_type: str = "read"):
    async def check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not permission_service.has_knowledge_base_access(db, current_user, kb_id, permission_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No {permission_type} access to knowledge base {kb_id}"
            )
        return current_user
    
    return check


def require_kb_access_from_path(permission_type: str = "read"):
    async def check(
        kb_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not permission_service.has_knowledge_base_access(db, current_user, kb_id, permission_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No {permission_type} access to knowledge base {kb_id}"
            )
        return current_user
    
    return check


def is_superuser(user: User) -> bool:
    return user.is_superuser