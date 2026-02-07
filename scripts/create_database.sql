-- ============================================
-- Enterprise RAG 数据库创建 SQL
-- ============================================

-- 创建数据库（如果不存在）
-- CREATE DATABASE enterprise_rag;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    department_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. 部门表
-- ============================================
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. 角色表
-- ============================================
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. 权限表
-- ============================================
CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(255),
    action VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. 知识库表
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    embedding_model VARCHAR(255),
    llm_model VARCHAR(255),
    chunk_size INTEGER DEFAULT 1000,
    chunk_overlap INTEGER DEFAULT 200,
    retrieval_top_k INTEGER DEFAULT 4,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. 文档表
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(255) PRIMARY KEY,
    knowledge_base_id VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    file_path TEXT,
    file_url TEXT,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
);

-- ============================================
-- 7. 文档分块表
-- ============================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    chunk_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- ============================================
-- 8. 文档版本表
-- ============================================
CREATE TABLE IF NOT EXISTS document_versions (
    id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    version_number INTEGER NOT NULL,
    file_path TEXT,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- ============================================
-- 9. 查询日志表
-- ============================================
CREATE TABLE IF NOT EXISTS query_logs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    knowledge_base_id VARCHAR(255),
    query TEXT NOT NULL,
    answer TEXT,
    retrieval_count INTEGER,
    retrieval_time FLOAT,
    generation_time FLOAT,
    total_time FLOAT,
    log_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL
);

-- ============================================
-- 10. 知识库权限表
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_base_permissions (
    id VARCHAR(255) PRIMARY KEY,
    knowledge_base_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    permission_type VARCHAR(50) NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================
-- 11. 用户角色关联表
-- ============================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id VARCHAR(255) NOT NULL,
    role_id VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- ============================================
-- 12. 用户权限关联表
-- ============================================
CREATE TABLE IF NOT EXISTS user_permissions (
    user_id VARCHAR(255) NOT NULL,
    permission_id VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id, permission_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- ============================================
-- 13. 角色权限关联表
-- ============================================
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id VARCHAR(255) NOT NULL,
    permission_id VARCHAR(255) NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- ============================================
-- 创建索引
-- ============================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_department_id ON users(department_id);

-- 知识库表索引
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_name ON knowledge_bases(name);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_is_active ON knowledge_bases(is_active);

-- 文档表索引
CREATE INDEX IF NOT EXISTS idx_documents_kb_id ON documents(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_name ON documents(file_name);
CREATE INDEX IF NOT EXISTS idx_documents_is_processed ON documents(is_processed);

-- 文档分块表索引
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index ON document_chunks(chunk_index);

-- 查询日志表索引
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_kb_id ON query_logs(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);

-- 知识库权限表索引
CREATE INDEX IF NOT EXISTS idx_kb_permissions_kb_id ON knowledge_base_permissions(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_kb_permissions_user_id ON knowledge_base_permissions(user_id);

-- ============================================
-- 插入初始数据
-- ============================================

-- 插入默认管理员用户
INSERT INTO users (id, username, email, password_hash, full_name, is_active, is_superuser)
VALUES (
    'admin',
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqWqYqYqYq',
    '系统管理员',
    TRUE,
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- 插入默认角色
INSERT INTO roles (id, name, description)
VALUES 
    ('admin', '管理员', '系统管理员角色'),
    ('user', '普通用户', '普通用户角色')
ON CONFLICT (name) DO NOTHING;

-- 插入默认权限
INSERT INTO permissions (id, name, description, resource, action)
VALUES 
    ('kb_read', '查看知识库', '查看知识库权限', 'knowledge_base', 'read'),
    ('kb_write', '编辑知识库', '编辑知识库权限', 'knowledge_base', 'write'),
    ('kb_delete', '删除知识库', '删除知识库权限', 'knowledge_base', 'delete'),
    ('doc_read', '查看文档', '查看文档权限', 'document', 'read'),
    ('doc_write', '编辑文档', '编辑文档权限', 'document', 'write'),
    ('doc_delete', '删除文档', '删除文档权限', 'document', 'delete'),
    ('qa_query', '问答查询', '问答查询权限', 'qa', 'query')
ON CONFLICT (name) DO NOTHING;

-- 为管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'admin', id FROM permissions
ON CONFLICT DO NOTHING;

-- 为管理员用户分配管理员角色
INSERT INTO user_roles (user_id, role_id)
VALUES ('admin', 'admin')
ON CONFLICT DO NOTHING;