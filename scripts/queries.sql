-- ============================================
-- Enterprise RAG 数据库查询 SQL
-- ============================================

-- 1. 查看所有表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- ============================================
-- 2. 查看每个表的数据
-- ============================================

-- 查看用户表
SELECT * FROM users;

-- 查看部门表
SELECT * FROM departments;

-- 查看角色表
SELECT * FROM roles;

-- 查看权限表
SELECT * FROM permissions;

-- 查看知识库表
SELECT * FROM knowledge_bases;

-- 查看文档表
SELECT * FROM documents;

-- 查看文档分块表
SELECT * FROM document_chunks;

-- 查看文档版本表
SELECT * FROM document_versions;

-- 查看查询日志表
SELECT * FROM query_logs;

-- 查看知识库权限表
SELECT * FROM knowledge_base_permissions;

-- 查看用户角色关联表
SELECT * FROM user_roles;

-- 查看用户权限关联表
SELECT * FROM user_permissions;

-- 查看角色权限关联表
SELECT * FROM role_permissions;

-- ============================================
-- 3. 查看表结构
-- ============================================

-- 查看用户表结构
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- 查看知识库表结构
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'knowledge_bases'
ORDER BY ordinal_position;

-- 查看文档表结构
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'documents'
ORDER BY ordinal_position;

-- ============================================
-- 4. 关联查询示例
-- ============================================

-- 查看用户及其部门信息
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.is_active,
    d.name as department_name
FROM users u
LEFT JOIN departments d ON u.department_id = d.id;

-- 查看用户及其角色
SELECT 
    u.id,
    u.username,
    u.email,
    r.name as role_name
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id;

-- 查看知识库及其文档数量
SELECT 
    kb.id,
    kb.name,
    kb.description,
    kb.is_active,
    COUNT(d.id) as document_count
FROM knowledge_bases kb
LEFT JOIN documents d ON kb.id = d.knowledge_base_id
GROUP BY kb.id, kb.name, kb.description, kb.is_active;

-- 查看文档及其分块数量
SELECT 
    d.id,
    d.file_name,
    d.file_type,
    d.is_processed,
    COUNT(dc.id) as chunk_count
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.file_name, d.file_type, d.is_processed;

-- 查看最近的查询日志
SELECT 
    ql.id,
    ql.query,
    ql.answer,
    ql.retrieval_count,
    ql.retrieval_time,
    ql.generation_time,
    ql.total_time,
    ql.created_at,
    u.username,
    kb.name as knowledge_base_name
FROM query_logs ql
LEFT JOIN users u ON ql.user_id = u.id
LEFT JOIN knowledge_bases kb ON ql.knowledge_base_id = kb.id
ORDER BY ql.created_at DESC
LIMIT 20;

-- 查看知识库权限
SELECT 
    kbp.id,
    kb.name as knowledge_base_name,
    u.username as user_name,
    kbp.permission_type,
    kbp.created_at,
    creator.username as created_by
FROM knowledge_base_permissions kbp
JOIN knowledge_bases kb ON kbp.knowledge_base_id = kb.id
JOIN users u ON kbp.user_id = u.id
LEFT JOIN users creator ON kbp.created_by = creator.id;

-- ============================================
-- 5. 统计查询
-- ============================================

-- 统计各表的数据量
SELECT 
    'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'departments', COUNT(*) FROM departments
UNION ALL
SELECT 'roles', COUNT(*) FROM roles
UNION ALL
SELECT 'permissions', COUNT(*) FROM permissions
UNION ALL
SELECT 'knowledge_bases', COUNT(*) FROM knowledge_bases
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'document_chunks', COUNT(*) FROM document_chunks
UNION ALL
SELECT 'document_versions', COUNT(*) FROM document_versions
UNION ALL
SELECT 'query_logs', COUNT(*) FROM query_logs
UNION ALL
SELECT 'knowledge_base_permissions', COUNT(*) FROM knowledge_base_permissions
UNION ALL
SELECT 'user_roles', COUNT(*) FROM user_roles
UNION ALL
SELECT 'user_permissions', COUNT(*) FROM user_permissions
UNION ALL
SELECT 'role_permissions', COUNT(*) FROM role_permissions;

-- ============================================
-- 6. 快速检查数据库是否有数据
-- ============================================

-- 检查是否有用户
SELECT COUNT(*) as user_count FROM users;

-- 检查是否有知识库
SELECT COUNT(*) as kb_count FROM knowledge_bases;

-- 检查是否有文档
SELECT COUNT(*) as doc_count FROM documents;

-- 检查是否有查询日志
SELECT COUNT(*) as query_count FROM query_logs;