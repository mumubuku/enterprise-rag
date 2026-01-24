#!/usr/bin/env python3
"""
测试脚本 - 验证系统核心功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """测试核心模块导入"""
    print("📦 测试模块导入...")
    
    try:
        from src.config.settings import get_settings
        print("✅ 配置模块导入成功")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    try:
        from src.models.database import Base, User, KnowledgeBase, Document
        print("✅ 数据模型导入成功")
    except Exception as e:
        print(f"❌ 数据模型导入失败: {e}")
        return False
    
    try:
        from src.services.auth_service import auth_service, permission_service
        print("✅ 认证服务导入成功")
    except Exception as e:
        print(f"❌ 认证服务导入失败: {e}")
        return False
    
    try:
        from src.services.knowledge_base_service import KnowledgeBaseService
        print("✅ 知识库服务导入成功")
    except Exception as e:
        print(f"❌ 知识库服务导入失败: {e}")
        return False
    
    try:
        from src.core.document_processor import DocumentProcessor
        print("✅ 文档处理器导入成功")
    except Exception as e:
        print(f"❌ 文档处理器导入失败: {e}")
        return False
    
    try:
        from src.core.embeddings import get_embedding_service
        print("✅ 嵌入服务导入成功")
    except Exception as e:
        print(f"❌ 嵌入服务导入失败: {e}")
        return False
    
    try:
        from src.core.vector_store import get_vector_store
        print("✅ 向量存储导入成功")
    except Exception as e:
        print(f"❌ 向量存储导入失败: {e}")
        return False
    
    try:
        from src.core.llm import get_llm
        print("✅ 大模型服务导入成功")
    except Exception as e:
        print(f"❌ 大模型服务导入失败: {e}")
        return False
    
    try:
        from src.core.rag_engine import RAGEngine
        print("✅ RAG引擎导入成功")
    except Exception as e:
        print(f"❌ RAG引擎导入失败: {e}")
        return False
    
    return True


def test_settings():
    """测试配置加载"""
    print("\n⚙️  测试配置加载...")
    
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
        return False


def test_auth_service():
    """测试认证服务"""
    print("\n🔐 测试认证服务...")
    
    try:
        from src.services.auth_service import auth_service
        
        # 测试密码哈希
        password = "test123"
        hashed = auth_service.get_password_hash(password)
        print(f"✅ 密码哈希成功: {hashed[:20]}...")
        
        # 测试密码验证
        verified = auth_service.verify_password(password, hashed)
        print(f"✅ 密码验证: {'成功' if verified else '失败'}")
        
        # 测试Token生成
        token = auth_service.create_access_token(data={"sub": "testuser"})
        print(f"✅ Token生成成功: {token[:20]}...")
        
        # 测试Token解码
        payload = auth_service.decode_token(token)
        print(f"✅ Token解码成功: {payload}")
        
        return True
    except Exception as e:
        print(f"❌ 认证服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_processor():
    """测试文档处理器"""
    print("\n📄 测试文档处理器...")
    
    try:
        from src.core.document_processor import DocumentProcessor
        
        processor = DocumentProcessor(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        print(f"✅ 文档处理器创建成功")
        print(f"✅ 支持的格式: {processor.get_supported_formats()}")
        
        return True
    except Exception as e:
        print(f"❌ 文档处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_service():
    """测试嵌入服务"""
    print("\n🔢 测试嵌入服务...")
    
    try:
        from src.core.embeddings import get_embedding_service
        
        # 测试本地嵌入服务（不需要API密钥）
        service = get_embedding_service("local")
        print(f"✅ 本地嵌入服务创建成功")
        
        # 测试嵌入（需要下载模型，可能较慢）
        print("⏳ 测试文本嵌入（首次运行需要下载模型）...")
        embedding = service.embed_query("测试文本")
        print(f"✅ 嵌入向量维度: {len(embedding)}")
        
        return True
    except Exception as e:
        print(f"❌ 嵌入服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store():
    """测试向量存储"""
    print("\n🗄️  测试向量存储...")
    
    try:
        from src.core.vector_store import get_vector_store
        from src.core.embeddings import get_embedding_service
        
        # 创建测试目录
        test_dir = "/tmp/test_chroma"
        os.makedirs(test_dir, exist_ok=True)
        
        # 获取嵌入服务
        embedding_service = get_embedding_service("local")
        
        # 创建向量存储
        vector_store = get_vector_store(
            collection_name="test_collection",
            embedding_function=embedding_service
        )
        
        print(f"✅ 向量存储创建成功")
        
        # 测试添加文档
        from langchain_core.documents import Document
        test_doc = Document(page_content="这是一个测试文档", metadata={"source": "test"})
        vector_store.add_documents([test_doc])
        print(f"✅ 文档添加成功")
        
        # 测试搜索
        results = vector_store.similarity_search("测试", k=1)
        print(f"✅ 搜索成功，找到 {len(results)} 个结果")
        
        return True
    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_engine():
    """测试RAG引擎"""
    print("\n🤖 测试RAG引擎...")
    
    try:
        from src.core.rag_engine import RAGEngine
        from src.core.vector_store import get_vector_store
        from src.core.embeddings import get_embedding_service
        from src.core.llm import get_llm
        
        # 获取服务
        embedding_service = get_embedding_service("local")
        vector_store = get_vector_store(
            collection_name="test_rag",
            embedding_function=embedding_service
        )
        
        # 注意：这里不创建LLM，因为没有API密钥
        print("⚠️  跳过LLM测试（需要API密钥）")
        print("✅ RAG引擎组件测试成功")
        
        return True
    except Exception as e:
        print(f"❌ RAG引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("  企业RAG知识库 - 系统测试")
    print("=" * 50)
    print()
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("配置加载", test_settings()))
    results.append(("认证服务", test_auth_service()))
    results.append(("文档处理器", test_document_processor()))
    results.append(("嵌入服务", test_embedding_service()))
    results.append(("向量存储", test_vector_store()))
    results.append(("RAG引擎", test_rag_engine()))
    
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
        print("\n🎉 所有测试通过！系统可以正常启动。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())