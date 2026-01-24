import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.database import User, Role, Permission, KnowledgeBasePermission, KnowledgeBase
from src.config.settings import get_settings

settings = get_settings()


class AuthService:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password[:72].encode('utf-8'), hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password[:72].encode('utf-8'), salt).decode('utf-8')

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def authenticate_user(self, session: Session, username: str, password: str) -> Optional[User]:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user


class PermissionService:
    def __init__(self):
        pass

    def has_permission(self, user: User, resource: str, action: str) -> bool:
        if user.is_superuser:
            return True

        for permission in user.permissions:
            if permission.resource == resource and permission.action == action:
                return True

        for role in user.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True

        return False

    def has_knowledge_base_access(self, session: Session, user: User, kb_id: str, permission_type: str) -> bool:
        if user.is_superuser:
            return True

        kb_permission = session.query(KnowledgeBasePermission).filter(
            KnowledgeBasePermission.knowledge_base_id == kb_id,
            KnowledgeBasePermission.user_id == user.id,
            KnowledgeBasePermission.permission_type == permission_type
        ).first()

        return kb_permission is not None

    def get_accessible_knowledge_bases(self, session: Session, user: User, permission_type: str = "read") -> List[str]:
        if user.is_superuser:
            kb_ids = session.query(KnowledgeBase.id).all()
            return [kb_id[0] for kb_id in kb_ids]

        kb_permissions = session.query(KnowledgeBasePermission.knowledge_base_id).filter(
            KnowledgeBasePermission.user_id == user.id,
            KnowledgeBasePermission.permission_type == permission_type
        ).distinct().all()

        return [kb_id[0] for kb_id in kb_permissions]

    def grant_knowledge_base_permission(
        self,
        session: Session,
        kb_id: str,
        user_id: str,
        permission_type: str,
        created_by: str
    ) -> KnowledgeBasePermission:
        existing = session.query(KnowledgeBasePermission).filter(
            KnowledgeBasePermission.knowledge_base_id == kb_id,
            KnowledgeBasePermission.user_id == user_id,
            KnowledgeBasePermission.permission_type == permission_type
        ).first()

        if existing:
            return existing

        kb_permission = KnowledgeBasePermission(
            knowledge_base_id=kb_id,
            user_id=user_id,
            permission_type=permission_type,
            created_by=created_by
        )
        session.add(kb_permission)
        session.commit()
        session.refresh(kb_permission)
        return kb_permission

    def revoke_knowledge_base_permission(
        self,
        session: Session,
        kb_id: str,
        user_id: str,
        permission_type: str
    ) -> bool:
        kb_permission = session.query(KnowledgeBasePermission).filter(
            KnowledgeBasePermission.knowledge_base_id == kb_id,
            KnowledgeBasePermission.user_id == user_id,
            KnowledgeBasePermission.permission_type == permission_type
        ).first()

        if kb_permission:
            session.delete(kb_permission)
            session.commit()
            return True
        return False

    def assign_role_to_user(self, session: Session, user_id: str, role_id: str) -> bool:
        user = session.query(User).filter(User.id == user_id).first()
        role = session.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            return False

        if role not in user.roles:
            user.roles.append(role)
            session.commit()
        return True

    def remove_role_from_user(self, session: Session, user_id: str, role_id: str) -> bool:
        user = session.query(User).filter(User.id == user_id).first()
        role = session.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            return False

        if role in user.roles:
            user.roles.remove(role)
            session.commit()
        return True

    def assign_permission_to_user(self, session: Session, user_id: str, permission_id: str) -> bool:
        user = session.query(User).filter(User.id == user_id).first()
        permission = session.query(Permission).filter(Permission.id == permission_id).first()

        if not user or not permission:
            return False

        if permission not in user.permissions:
            user.permissions.append(permission)
            session.commit()
        return True

    def assign_permission_to_role(self, session: Session, role_id: str, permission_id: str) -> bool:
        role = session.query(Role).filter(Role.id == role_id).first()
        permission = session.query(Permission).filter(Permission.id == permission_id).first()

        if not role or not permission:
            return False

        if permission not in role.permissions:
            role.permissions.append(permission)
            session.commit()
        return True


auth_service = AuthService()
permission_service = PermissionService()