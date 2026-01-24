#!/usr/bin/env python3
"""
简化测试脚本 - 验证系统核心逻辑（不依赖外部包）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_config():
    """测试配置加载"""
    print("⚙️  测试配置加载...")
    
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        
        print(f"✅ 应用名称: {settings.app_name}")
        print(f"✅ 应用版本: {settings.app_version}")
        print(f"✅ 数据库地址: {settings.db_host}:{settings.db_port}")
        print(f"✅ 向量数据库类型: {settings.vector_db_type}")
        print(f"✅ Chroma持久化目录: {settings.chroma_persist_dir}")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """测试数据库模型"""
    print("\n🗄️  测试数据库模型...")
    
    try:
        from src.models.database import Base, User, KnowledgeBase, Document, DocumentChunk
        
        # 检查模型定义
        print(f"✅ Base类: {Base}")
        print(f"✅ User模型: {User.__tablename__}")
        print(f"✅ KnowledgeBase模型: {KnowledgeBase.__tablename__}")
        print(f"✅ Document模型: {Document.__tablename__}")
        print(f"✅ DocumentChunk模型: {DocumentChunk.__tablename__}")
        
        # 检查字段
        user_columns = [col.name for col in User.__table__.columns]
        print(f"✅ User表字段: {', '.join(user_columns)}")
        
        # 检查字段名是否正确（不使用保留字）
        for col in User.__table__.columns:
            if col.name == 'metadata':
                print(f"❌ 发现保留字段名: {col.name}")
                return False
        
        for col in Document.__table__.columns:
            if col.name == 'metadata':
                print(f"❌ 发现保留字段名: {col.name}")
                return False
        
        for col in DocumentChunk.__table__.columns:
            if col.name == 'metadata':
                print(f"❌ 发现保留字段名: {col.name}")
                return False
        
        print("✅ 所有字段名正确，无保留字")
        
        return True
    except Exception as e:
        print(f"❌ 数据库模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas():
    """测试API模型"""
    print("\n📋 测试API模型...")
    
    try:
        from src.models.schemas import (
            UserRegister,
            UserLogin,
            TokenResponse,
            UserResponse,
            KnowledgeBaseCreate,
            SearchRequest,
            QARequest
        )
        
        print(f"✅ UserRegister: {UserRegister}")
        print(f"✅ UserLogin: {UserLogin}")
        print(f"✅ TokenResponse: {TokenResponse}")
        print(f"✅ UserResponse: {UserResponse}")
        print(f"✅ KnowledgeBaseCreate: {KnowledgeBaseCreate}")
        print(f"✅ SearchRequest: {SearchRequest}")
        print(f"✅ QARequest: {QARequest}")
        
        # 测试模型实例化
        user_data = UserRegister(
            username="test",
            email="test@example.com",
            password="test123456"
        )
        print(f"✅ UserRegister实例化成功: {user_data.username}")
        
        return True
    except Exception as e:
        print(f"❌ API模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_project_structure():
    """测试项目结构"""
    print("\n📁 测试项目结构...")
    
    required_files = [
        "src/config/settings.py",
        "src/models/database.py",
        "src/models/schemas.py",
        "src/services/auth_service.py",
        "src/services/knowledge_base_service.py",
        "src/core/document_processor.py",
        "src/core/embeddings.py",
        "src/core/vector_store.py",
        "src/core/llm.py",
        "src/core/rag_engine.py",
        "src/api/main.py",
        "src/api/auth.py",
        "src/utils/dependencies.py",
        "requirements.txt",
        "deploy/docker/docker-compose.yml",
        "deploy/docker/Dockerfile",
        "deploy/docker/start.sh",
        "deploy/docker/start.bat",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    print(f"✅ 所有必需文件存在 ({len(required_files)} 个)")
    return True


def test_docker_config():
    """测试Docker配置"""
    print("\n🐳 测试Docker配置...")
    
    try:
        import yaml
        
        docker_compose_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'deploy/docker/docker-compose.yml'
        )
        
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ Docker Compose版本: {config['version']}")
        print(f"✅ 服务数量: {len(config['services'])}")
        
        for service_name in config['services']:
            print(f"✅ 服务: {service_name}")
        
        # 检查PostgreSQL配置
        if 'postgres' in config['services']:
            postgres = config['services']['postgres']
            print(f"✅ PostgreSQL镜像: {postgres['image']}")
            print(f"✅ PostgreSQL端口: {postgres['ports']}")
        
        # 检查API配置
        if 'api' in config['services']:
            api = config['services']['api']
            print(f"✅ API端口: {api['ports']}")
            print(f"✅ API依赖: {api.get('depends_on', [])}")
        
        return True
    except Exception as e:
        print(f"❌ Docker配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_requirements():
    """测试依赖配置"""
    print("\n📦 测试依赖配置...")
    
    try:
        requirements_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'requirements.txt'
        )
        
        with open(requirements_path, 'r') as f:
            requirements = f.read()
        
        # 检查关键依赖
        key_packages = [
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'pydantic',
            'langchain',
            'chromadb',
            'python-jose',
            'passlib',
        ]
        
        missing_packages = []
        for package in key_packages:
            if package not in requirements.lower():
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ 缺少关键依赖: {', '.join(missing_packages)}")
            return False
        
        print(f"✅ 所有关键依赖存在 ({len(key_packages)} 个)")
        
        # 统计依赖数量
        lines = [line for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
        print(f"✅ 依赖包总数: {len(lines)}")
        
        return True
    except Exception as e:
        print(f"❌ 依赖配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("  企业RAG知识库 - 核心逻辑测试")
    print("=" * 50)
    print()
    
    results = []
    
    # 运行测试
    results.append(("配置加载", test_config()))
    results.append(("数据库模型", test_database_models()))
    results.append(("API模型", test_schemas()))
    results.append(("项目结构", test_project_structure()))
    results.append(("Docker配置", test_docker_config()))
    results.append(("依赖配置", test_requirements()))
    
    # 显示结果
    print("\n" + "=" * 50)
    print("  测试结果汇总")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print("\n🎉 所有核心测试通过！")
        print("\n📝 注意：完整功能测试需要安装Python依赖包")
        print("   运行: pip install -r requirements.txt")
        print("\n🚀 一键启动：")
        print("   cd deploy/docker")
        print("   ./start.sh  # Linux/Mac")
        print("   start.bat  # Windows")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())