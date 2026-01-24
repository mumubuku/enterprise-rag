#!/bin/bash

echo "=========================================="
echo "  企业RAG知识库 - 本地启动脚本"
echo "=========================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建议使用虚拟环境"
    echo "   创建虚拟环境: python3 -m venv venv"
    echo "   激活虚拟环境: source venv/bin/activate"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 安装依赖
echo ""
echo "📦 安装Python依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建必要的目录
echo ""
echo "📁 创建数据目录..."
mkdir -p data uploads temp logs

# 检查PostgreSQL
echo ""
echo "🗄️  检查PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL已安装"
else
    echo "⚠️  PostgreSQL未安装"
    echo "   请安装PostgreSQL或使用Docker启动PostgreSQL"
    echo ""
    echo "   使用Docker启动PostgreSQL:"
    echo "   docker run -d --name postgres \\"
    echo "     -e POSTGRES_PASSWORD=postgres \\"
    echo "     -e POSTGRES_DB=enterprise_rag \\"
    echo "     -p 5432:5432 \\"
    echo "     postgres:15-alpine"
    echo ""
    read -p "是否现在启动PostgreSQL？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker run -d --name enterprise-rag-postgres \
            -e POSTGRES_PASSWORD=postgres \
            -e POSTGRES_DB=enterprise_rag \
            -p 5432:5432 \
            postgres:15-alpine
        
        echo "⏳ 等待PostgreSQL启动..."
        sleep 5
    fi
fi

# 设置环境变量
export DASHSCOPE_API_KEY="sk-8247bb7734304d468cfaff950eee790c"
export SECRET_KEY="enterprise-rag-secret-key-2024"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
export DB_NAME="enterprise_rag"
export VECTOR_DB_TYPE="chroma"
export CHROMA_PERSIST_DIR="./data/chroma"

# 启动API服务
echo ""
echo "🚀 启动API服务..."
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload