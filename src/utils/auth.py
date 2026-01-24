from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import httpx
import json
from src.config.settings import get_settings

settings = get_settings()
security = HTTPBearer()


class UserInfo:
    def __init__(
        self,
        user_id: str,
        username: str,
        department_id: Optional[str] = None,
        roles: List[str] = None,
        permissions: List[str] = None
    ):
        self.user_id = user_id
        self.username = username
        self.department_id = department_id
        self.roles = roles or []
        self.permissions = permissions or []


class PermissionService:
    def __init__(self):
        self.java_auth_url = getattr(settings, 'JAVA_AUTH_URL', 'http://localhost:8080/api/auth/validate')
        self.java_permission_url = getattr(settings, 'JAVA_PERMISSION_URL', 'http://localhost:8080/api/permission/check')
        self.timeout = 5.0

    async def validate_token(self, token: str) -> Optional[UserInfo]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.java_auth_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return UserInfo(
                        user_id=data.get('userId'),
                        username=data.get('username'),
                        department_id=data.get('departmentId'),
                        roles=data.get('roles', []),
                        permissions=data.get('permissions', [])
                    )
                return None
        except Exception as e:
            print(f"Token validation failed: {e}")
            return None

    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.java_permission_url,
                    json={
                        "userId": user_id,
                        "resource": resource,
                        "action": action
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('allowed', False)
                return False
        except Exception as e:
            print(f"Permission check failed: {e}")
            return False

    async def check_knowledge_base_access(
        self,
        user_id: str,
        kb_id: str,
        action: str = "read"
    ) -> bool:
        return await self.check_permission(
            user_id=user_id,
            resource=f"knowledge_base:{kb_id}",
            action=action
        )


permission_service = PermissionService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserInfo:
    token = credentials.credentials
    user_info = await permission_service.validate_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


async def require_permission(resource: str, action: str):
    async def check(user: UserInfo = Security(get_current_user)):
        has_permission = await permission_service.check_permission(
            user_id=user.user_id,
            resource=resource,
            action=action
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {resource}"
            )
        
        return user
    
    return check


async def require_kb_access(kb_id: str, action: str = "read"):
    async def check(user: UserInfo = Security(get_current_user)):
        has_access = await permission_service.check_knowledge_base_access(
            user_id=user.user_id,
            kb_id=kb_id,
            action=action
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No access to knowledge base {kb_id}"
            )
        
        return user
    
    return check


def is_admin(user: UserInfo) -> bool:
    return "admin" in user.roles or "super_admin" in user.roles


async def require_admin(user: UserInfo = Security(get_current_user)):
    if not is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user