from sqlalchemy.orm import Session
from src.models.database import Base, User, Role, Permission
from src.services.auth_service import auth_service
from src.config.settings import get_settings
import sys

settings = get_settings()


def init_database():
    """初始化数据库，创建默认数据"""
    from src.services.knowledge_base_service import DatabaseManager
    
    db_manager = DatabaseManager()
    
    print("📊 创建数据库表...")
    db_manager.create_tables()
    print("✅ 数据库表创建完成")
    
    session = db_manager.get_session()
    
    try:
        # 检查是否已存在管理员用户
        existing_admin = session.query(User).filter(User.username == 'admin').first()
        
        if existing_admin:
            print("ℹ️  管理员用户已存在，跳过创建")
            return
        
        print("👤 创建默认管理员用户...")
        
        # 创建默认管理员
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
        session.flush()
        
        # 创建默认角色
        print("🔐 创建默认角色...")
        
        admin_role = Role(
            name='admin',
            description='系统管理员，拥有所有权限'
        )
        session.add(admin_role)
        session.flush()
        
        user_role = Role(
            name='user',
            description='普通用户'
        )
        session.add(user_role)
        session.flush()
        
        # 创建默认权限
        print("🔑 创建默认权限...")
        
        permissions = [
            # 知识库权限
            Permission(name='knowledge_base:create', resource='knowledge_base', action='create', description='创建知识库'),
            Permission(name='knowledge_base:read', resource='knowledge_base', action='read', description='读取知识库'),
            Permission(name='knowledge_base:update', resource='knowledge_base', action='update', description='更新知识库'),
            Permission(name='knowledge_base:delete', resource='knowledge_base', action='delete', description='删除知识库'),
            
            # 用户管理权限
            Permission(name='user:create', resource='user', action='create', description='创建用户'),
            Permission(name='user:read', resource='user', action='read', description='读取用户'),
            Permission(name='user:update', resource='user', action='update', description='更新用户'),
            Permission(name='user:delete', resource='user', action='delete', description='删除用户'),
            
            # 角色管理权限
            Permission(name='role:create', resource='role', action='create', description='创建角色'),
            Permission(name='role:read', resource='role', action='read', description='读取角色'),
            Permission(name='role:update', resource='role', action='update', description='更新角色'),
            Permission(name='role:delete', resource='role', action='delete', description='删除角色'),
            
            # 权限管理权限
            Permission(name='permission:create', resource='permission', action='create', description='创建权限'),
            Permission(name='permission:read', resource='permission', action='read', description='读取权限'),
            Permission(name='permission:update', resource='permission', action='update', description='更新权限'),
            Permission(name='permission:delete', resource='permission', action='delete', description='删除权限'),
            
            # 部门管理权限
            Permission(name='department:create', resource='department', action='create', description='创建部门'),
            Permission(name='department:read', resource='department', action='read', description='读取部门'),
            Permission(name='department:update', resource='department', action='update', description='更新部门'),
            Permission(name='department:delete', resource='department', action='delete', description='删除部门'),
        ]
        
        for perm in permissions:
            session.add(perm)
        
        session.flush()
        
        # 为管理员角色分配所有权限
        print("🔗 为管理员角色分配权限...")
        for perm in permissions:
            admin_role.permissions.append(perm)
        
        # 为管理员用户分配管理员角色
        admin_user.roles.append(admin_role)
        
        session.commit()
        
        print("✅ 数据库初始化完成")
        print("")
        print("📋 默认管理员账号：")
        print("   用户名: admin")
        print("   密码: admin123")
        print("   ⚠️  首次登录后请立即修改密码！")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 数据库初始化失败: {e}")
        raise
    finally:
        session.close()
        db_manager.close()


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)