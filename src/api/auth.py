from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.utils.dependencies import get_db, get_current_user, require_superuser, require_permission
from src.services.auth_service import auth_service, permission_service
from src.models.database import User, Role, Permission, Department
from src.models.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    RoleCreate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    DepartmentCreate,
    DepartmentResponse
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = auth_service.get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        department_id=user_data.department_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        department_id=new_user.department_id,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        is_admin=new_user.is_superuser,
        created_at=new_user.created_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = auth_service.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.username})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        department_id=current_user.department_id,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        is_admin=current_user.is_superuser,
        created_at=current_user.created_at
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission("user", "read")),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department_id=user.department_id,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_admin=user.is_superuser,
            created_at=user.created_at
        )
        for user in users
    ]


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("user", "create")),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    hashed_password = auth_service.get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        department_id=user_data.department_id,
        is_superuser=user_data.is_superuser
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission("user", "read")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission("user", "update")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission("user", "delete")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_permission("role", "create")),
    db: Session = Depends(get_db)
):
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )
    
    new_role = Role(
        name=role_data.name,
        description=role_data.description
    )
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return new_role


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_permission("role", "read")),
    db: Session = Depends(get_db)
):
    roles = db.query(Role).all()
    return roles


@router.post("/permissions", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_permission("permission", "create")),
    db: Session = Depends(get_db)
):
    existing_permission = db.query(Permission).filter(
        Permission.name == permission_data.name
    ).first()
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists"
        )
    
    new_permission = Permission(
        name=permission_data.name,
        resource=permission_data.resource,
        action=permission_data.action,
        description=permission_data.description
    )
    
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    
    return new_permission


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    current_user: User = Depends(require_permission("permission", "read")),
    db: Session = Depends(get_db)
):
    permissions = db.query(Permission).all()
    return permissions


@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    current_user: User = Depends(require_permission("user", "update")),
    db: Session = Depends(get_db)
):
    success = permission_service.assign_role_to_user(db, user_id, role_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign role")
    
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: User = Depends(require_permission("user", "update")),
    db: Session = Depends(get_db)
):
    success = permission_service.remove_role_from_user(db, user_id, role_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove role")
    
    return {"message": "Role removed successfully"}


@router.post("/roles/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: str,
    permission_id: str,
    current_user: User = Depends(require_permission("role", "update")),
    db: Session = Depends(get_db)
):
    success = permission_service.assign_permission_to_role(db, role_id, permission_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign permission")
    
    return {"message": "Permission assigned successfully"}


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(require_permission("department", "create")),
    db: Session = Depends(get_db)
):
    existing_department = db.query(Department).filter(
        Department.name == department_data.name
    ).first()
    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department already exists"
        )
    
    new_department = Department(
        name=department_data.name,
        description=department_data.description,
        parent_id=department_data.parent_id
    )
    
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    return new_department


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(require_permission("department", "read")),
    db: Session = Depends(get_db)
):
    departments = db.query(Department).all()
    return departments