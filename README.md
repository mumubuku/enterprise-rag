# Enterprise RAG Knowledge Base

企业级RAG（检索增强生成）知识库系统，支持多格式文档处理、多种向量数据库、多种大模型集成。

## 功能特性

- 多格式文档支持：PDF、Word、Excel、PPT、Markdown、TXT、HTML、CSV
- 多种向量数据库：Chroma、Pinecone、Qdrant
- 多种大模型集成：OpenAI GPT、阿里云通义千问、智谱AI、本地模型
- 智能文档分割：支持按段落、句子、语义分割
- 高效检索：向量相似度搜索、混合检索、重排序
- 流式输出：支持实时流式问答
- RESTful API：完整的API接口
- 多种部署方式：Docker、Kubernetes

## 技术栈

- **编程语言**：Python 3.10+
- **框架**：LangChain、FastAPI
- **向量数据库**：Chroma、Pinecone、Qdrant
- **结构化数据库**：PostgreSQL
- **大模型**：OpenAI、阿里云DashScope、智谱AI
- **部署**：Docker、Kubernetes

## 项目结构

```
enterprise-rag/
├── src/
│   ├── api/                      # API接口
│   │   └── main.py               # FastAPI主程序
│   ├── core/                     # 核心功能
│   │   ├── document_processor.py # 文档处理
│   │   ├── embeddings.py         # 向量化服务
│   │   ├── vector_store.py       # 向量存储
│   │   ├── llm.py                # 大模型集成
│   │   └── rag_engine.py         # RAG引擎
│   ├── models/                   # 数据模型
│   │   ├── database.py           # 数据库模型
│   │   └── schemas.py            # API模型
│   ├── services/                 # 业务服务
│   │   └── knowledge_base_service.py  # 知识库服务
│   ├── utils/                    # 工具函数
│   └── config/                   # 配置管理
│       └── settings.py           # 配置文件
├── deploy/                       # 部署配置
│   ├── docker/                   # Docker配置
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── k8s/                      # Kubernetes配置
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── pvc.yaml
│       ├── deployment.yaml
│       └── service.yaml
├── requirements.txt              # Python依赖
├── pyproject.toml                # Poetry配置
├── .env.example                  # 环境变量示例
└── README.md                     # 项目文档
```

## 快速开始

### 1. 环境准备

- Python 3.10+
- PostgreSQL 15+
- （可选）Redis

### 2. 安装依赖

```bash
# 使用pip
pip install -r requirements.txt

# 或使用poetry
poetry install
```

### 3. 配置环境变量

复制`.env.example`为`.env`并配置相关参数：

```bash
cp .env.example .env
```

至少需要配置以下参数：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=enterprise_rag

# 大模型配置（至少配置一个）
OPENAI_API_KEY=your_openai_api_key
# 或
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 4. 启动服务

```bash
# 直接运行
python -m src.api.main

# 或使用uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在`http://localhost:8000`启动，API文档可访问`http://localhost:8000/docs`。

## Docker部署

### 1. 构建镜像

```bash
docker build -f deploy/docker/Dockerfile -t enterprise-rag:latest .
```

### 2. 使用Docker Compose

```bash
cd deploy/docker
docker-compose up -d
```

## Kubernetes部署

### 1. 应用配置

```bash
# 应用ConfigMap
kubectl apply -f deploy/k8s/configmap.yaml

# 应用Secret（需先填充敏感信息）
kubectl apply -f deploy/k8s/secret.yaml

# 应用PVC
kubectl apply -f deploy/k8s/pvc.yaml

# 应用Deployment
kubectl apply -f deploy/k8s/deployment.yaml

# 应用Service
kubectl apply -f deploy/k8s/service.yaml
```

### 2. 访问服务

```bash
# 获取服务地址
kubectl get services enterprise-rag-api-service
```

## API使用示例

### 创建知识库

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "企业文档库",
    "description": "企业内部文档知识库",
    "embedding_model": "openai",
    "llm_model": "openai",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "retrieval_top_k": 4
  }'
```

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/{kb_id}/documents" \
  -F "file=@document.pdf"
```

### 检索文档

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何使用这个系统？",
    "knowledge_base_id": "{kb_id}",
    "top_k": 4
  }'
```

### 智能问答

```bash
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何使用这个系统？",
    "knowledge_base_id": "{kb_id}",
    "top_k": 4,
    "llm_provider": "openai"
  }'
```

### 流式问答

```bash
curl -X POST "http://localhost:8000/api/v1/qa/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何使用这个系统？",
    "knowledge_base_id": "{kb_id}",
    "top_k": 4
  }'
```

## 配置说明

### 向量数据库选择

系统支持多种向量数据库，通过环境变量`VECTOR_DB_TYPE`配置：

- `chroma`：轻量级本地向量数据库（默认）
- `pinecone`：云托管向量数据库
- `qdrant`：高性能向量数据库

### 大模型选择

系统支持多种大模型，通过API参数`llm_provider`配置：

- `openai`：OpenAI GPT系列
- `alibaba`：阿里云通义千问
- `zhipuai`：智谱AI GLM系列

### 嵌入模型选择

系统支持多种嵌入模型，通过知识库配置`embedding_model`指定：

- `openai`：OpenAI嵌入模型
- `alibaba`：阿里云嵌入模型
- `local`：本地Sentence Transformers模型

## 性能优化

### 1. 向量缓存

启用向量缓存可以减少重复计算：

```env
ENABLE_CACHE=True
```

### 2. 重排序

启用重排序可以提高检索精度：

```env
RERANK_ENABLED=True
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

### 3. 批量处理

对于大量文档，建议使用批量上传接口：

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/{kb_id}/documents/directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/documents"
  }'
```

## 注意事项

1. 首次使用前请确保已配置好相应的API密钥
2. PostgreSQL数据库需提前创建
3. 向量数据库会自动创建，无需手动配置
4. 生产环境建议关闭DEBUG模式
5. 建议使用Kubernetes部署时配置适当的资源限制

## 许可证

MIT