# 企业RAG知识库 - 快速启动指南

## 一键启动（推荐）

### Linux/Mac

```bash
cd deploy/docker
chmod +x start.sh
./start.sh
```

### Windows

```cmd
cd deploy\docker
start.bat
```

## 手动启动

### 1. 配置API密钥

在 `deploy/docker/.env` 文件中配置至少一个大模型API密钥：

```env
# 选择以下任一API密钥配置

# OpenAI (推荐)
OPENAI_API_KEY=sk-your-openai-api-key

# 阿里云通义千问
DASHSCOPE_API_KEY=your-dashscope-api-key

# 智谱AI
ZHIPUAI_API_KEY=your-zhipuai-api-key
```

### 2. 启动服务

```bash
cd deploy/docker
docker-compose up -d --build
```

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止服务

```bash
docker-compose down
```

## 访问服务

启动成功后，可以访问以下地址：

- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 默认账号

系统会自动创建默认管理员账号：

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **首次登录后请立即修改密码！**

## 启动前端

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将在 http://localhost:3000 启动。

## 使用流程

### 1. 登录系统

使用默认管理员账号登录：
- 用户名: `admin`
- 密码: `admin123`

### 2. 创建知识库

1. 点击"知识库管理"
2. 点击"创建知识库"
3. 填写知识库信息：
   - 名称：例如"技术文档库"
   - 描述：知识库的描述
   - 嵌入模型：选择OpenAI、阿里云或本地模型
   - 大模型：选择对应的大模型
4. 点击"创建"

### 3. 上传文档

1. 进入知识库详情
2. 点击"上传文档"
3. 选择文件（支持PDF、Word、Excel、PPT、Markdown、TXT等格式）
4. 等待文档处理完成

### 4. 智能问答

1. 点击"智能问答"
2. 选择知识库
3. 输入问题
4. 获取AI回答和参考来源

## 常见问题

### 1. 端口被占用

如果8000端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8001:8000"  # 改为其他端口
```

### 2. 数据库连接失败

检查PostgreSQL容器是否正常运行：

```bash
docker-compose ps
docker-compose logs postgres
```

### 3. API密钥无效

确保在 `.env` 文件中正确配置了API密钥，并且密钥有效。

### 4. 文档上传失败

检查文件大小是否超过限制（默认100MB），可以在 `.env` 中修改：

```env
MAX_FILE_SIZE=104857600  # 字节
```

### 5. 智能问答无响应

检查：
1. 是否配置了有效的大模型API密钥
2. API密钥是否有足够的额度
3. 网络连接是否正常

## 数据持久化

所有数据都存储在Docker卷中，即使删除容器也不会丢失：

- PostgreSQL数据: `postgres_data` 卷
- 向量数据: `./data/chroma` 目录
- 上传文件: `./uploads` 目录
- 日志文件: `./logs` 目录

## 备份与恢复

### 备份数据

```bash
# 备份PostgreSQL数据
docker-compose exec postgres pg_dump -U postgres enterprise_rag > backup.sql

# 备份向量数据
tar -czf chroma-backup.tar.gz data/chroma

# 备份上传文件
tar -czf uploads-backup.tar.gz uploads
```

### 恢复数据

```bash
# 恢复PostgreSQL数据
docker-compose exec -T postgres psql -U postgres enterprise_rag < backup.sql

# 恢复向量数据
tar -xzf chroma-backup.tar.gz

# 恢复上传文件
tar -xzf uploads-backup.tar.gz
```

## 性能优化

### 1. 调整数据库连接池

在 `.env` 文件中修改：

```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

### 2. 调整向量检索参数

在 `.env` 文件中修改：

```env
RETRIEVAL_TOP_K=4
RETRIEVAL_SCORE_THRESHOLD=0.7
```

### 3. 启用重排序

在 `.env` 文件中修改：

```env
RERANK_ENABLED=True
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

## 监控与日志

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f postgres
```

### 日志文件

日志文件存储在 `./logs/app.log` 中。

## 更新系统

```bash
cd deploy/docker
docker-compose down
docker-compose pull
docker-compose up -d --build
```

## 卸载系统

```bash
cd deploy/docker
docker-compose down -v
rm -rf data uploads logs
```

## 技术支持

如遇到问题，请检查：

1. Docker和Docker Compose版本
2. 系统资源（内存、磁盘空间）
3. 网络连接
4. API密钥有效性

## 许可证

MIT