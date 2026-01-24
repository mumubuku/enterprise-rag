#!/bin/bash

set -e

echo "=========================================="
echo "  企业RAG知识库 - 一键启动脚本"
echo "=========================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "   访问 https://docs.docker.com/get-docker/ 获取安装指南"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    echo "   访问 https://docs.docker.com/compose/install/ 获取安装指南"
    exit 1
fi

echo "✅ Docker环境检查通过"
echo ""

# 进入部署目录
cd "$(dirname "$0")"

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cat > .env << EOF
# 大模型API密钥（至少配置一个）
OPENAI_API_KEY=
DASHSCOPE_API_KEY=
ZHIPUAI_API_KEY=

# 安全密钥（生产环境请修改）
SECRET_KEY=$(openssl rand -hex 32)
EOF
    echo "✅ 环境变量文件已创建: .env"
    echo ""
    echo "⚠️  请编辑 .env 文件，配置至少一个大模型API密钥"
    echo "   支持的模型："
    echo "   - OpenAI (OPENAI_API_KEY)"
    echo "   - 阿里云通义千问 (DASHSCOPE_API_KEY)"
    echo "   - 智谱AI (ZHIPUAI_API_KEY)"
    echo ""
    read -p "是否现在配置API密钥？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi

# 检查是否配置了API密钥
source .env
if [ -z "$OPENAI_API_KEY" ] && [ -z "$DASHSCOPE_API_KEY" ] && [ -z "$ZHIPUAI_API_KEY" ]; then
    echo "⚠️  警告：未配置任何大模型API密钥"
    echo "   系统将无法进行智能问答功能"
    echo ""
    read -p "是否继续启动？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消启动"
        exit 0
    fi
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data uploads logs
echo "✅ 数据目录创建完成"
echo ""

# 停止并删除旧容器
echo "🛑 停止旧容器..."
docker-compose down 2>/dev/null || true
echo "✅ 旧容器已停止"
echo ""

# 构建并启动服务
echo "🚀 构建并启动服务..."
docker-compose up -d --build
echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 等待数据库就绪
echo ""
echo "⏳ 等待数据库初始化..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        echo "✅ 数据库已就绪"
        break
    fi
    attempt=$((attempt + 1))
    echo "   等待中... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ 数据库启动超时"
    docker-compose logs postgres
    exit 1
fi

# 等待API服务就绪
echo ""
echo "⏳ 等待API服务启动..."
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ API服务已就绪"
        break
    fi
    attempt=$((attempt + 1))
    echo "   等待中... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ API服务启动超时"
    docker-compose logs api
    exit 1
fi

echo ""
echo "=========================================="
echo "  🎉 启动成功！"
echo "=========================================="
echo ""
echo "📍 服务地址："
echo "   - API服务: http://localhost:8000"
echo "   - API文档: http://localhost:8000/docs"
echo "   - 前端界面: http://localhost:3000 (需要单独启动前端)"
echo ""
echo "📋 默认管理员账号："
echo "   - 用户名: admin"
echo "   - 密码: admin123"
echo "   (首次启动后请立即修改密码)"
echo ""
echo "🔧 常用命令："
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 查看状态: docker-compose ps"
echo ""
echo "📚 使用文档: README.md"
echo ""