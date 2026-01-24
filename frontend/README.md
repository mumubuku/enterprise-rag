# 企业RAG知识库 - 前端

基于 Vue 3 + Element Plus 的现代化前端界面。

## 技术栈

- **Vue 3**：渐进式JavaScript框架
- **Element Plus**：Vue 3 UI组件库
- **Vue Router**：路由管理
- **Pinia**：状态管理
- **Axios**：HTTP客户端
- **Vite**：构建工具

## 功能特性

### 1. 用户认证
- 用户登录
- 用户注册
- JWT Token认证
- 自动登录

### 2. 仪表盘
- 系统统计概览
- 快速操作入口
- 欢迎页面

### 3. 知识库管理
- 知识库列表
- 创建知识库
- 编辑知识库
- 删除知识库
- 查看知识库详情

### 4. 智能问答
- 知识库选择
- 实时对话
- 参考来源显示
- 相似度展示

### 5. 用户管理（超级用户）
- 用户列表
- 创建用户
- 编辑用户
- 删除用户
- 角色分配

### 6. 角色管理（超级用户）
- 角色列表
- 创建角色
- 权限分配

### 7. 权限管理（超级用户）
- 权限列表
- 创建权限
- 权限分配

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动。

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口
│   │   └── index.js      # API定义
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   ├── layouts/          # 布局组件
│   │   └── MainLayout.vue
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # 状态管理
│   │   ├── auth.js       # 认证状态
│   │   └── knowledgeBase.js  # 知识库状态
│   ├── utils/            # 工具函数
│   │   └── request.js    # HTTP请求封装
│   ├── views/            # 页面组件
│   │   ├── Login.vue     # 登录页
│   │   ├── Register.vue  # 注册页
│   │   ├── Dashboard.vue # 仪表盘
│   │   ├── KnowledgeBases.vue  # 知识库管理
│   │   ├── KnowledgeBaseDetail.vue  # 知识库详情
│   │   ├── Chat.vue      # 智能问答
│   │   ├── Users.vue     # 用户管理
│   │   ├── Roles.vue     # 角色管理
│   │   └── Permissions.vue  # 权限管理
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html            # HTML模板
├── package.json          # 项目配置
├── vite.config.js        # Vite配置
└── README.md             # 项目文档
```

## 界面预览

### 登录页面
- 渐变背景设计
- 现代化表单
- 响应式布局

### 仪表盘
- 统计卡片展示
- 快速操作入口
- 欢迎信息

### 知识库管理
- 表格列表展示
- 创建/编辑对话框
- 操作按钮

### 智能问答
- 左侧知识库选择
- 中间对话区域
- 参考来源展示
- 实时打字效果

## 配置说明

### API代理

在 `vite.config.js` 中配置了API代理：

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

确保后端API在 `http://localhost:8000` 运行。

### 环境变量

可以创建 `.env` 文件配置环境变量：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 开发建议

### 1. 组件开发

- 使用 Vue 3 Composition API
- 遵循单一职责原则
- 组件命名使用 PascalCase

### 2. 样式规范

- 使用 scoped CSS
- 避免使用 !important
- 保持样式一致性

### 3. 状态管理

- 使用 Pinia 进行状态管理
- 合理划分 store
- 避免过度使用全局状态

### 4. API调用

- 统一使用 `src/api/index.js` 中的API方法
- 错误处理由 request 拦截器统一处理
- 使用 async/await 处理异步操作

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## 常见问题

### 1. 跨域问题

如果遇到跨域问题，检查 `vite.config.js` 中的代理配置。

### 2. 登录失败

确保后端API正常运行，检查网络连接。

### 3. 样式不生效

清除浏览器缓存，重新构建项目。

## 部署

### Docker部署

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Nginx部署

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 许可证

MIT