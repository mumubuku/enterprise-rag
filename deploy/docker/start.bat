@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   企业RAG知识库 - 一键启动脚本
echo ==========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    echo    访问 https://docs.docker.com/get-docker/ 获取安装指南
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    echo    访问 https://docs.docker.com/compose/install/ 获取安装指南
    pause
    exit /b 1
)

echo ✅ Docker环境检查通过
echo.

REM 进入部署目录
cd /d "%~dp0"

REM 检查环境变量文件
if not exist .env (
    echo 📝 创建环境变量文件...
    (
        echo # 大模型API密钥（至少配置一个）
        echo OPENAI_API_KEY=
        echo DASHSCOPE_API_KEY=
        echo ZHIPUAI_API_KEY=
        echo.
        echo # 安全密钥（生产环境请修改）
        echo SECRET_KEY=your-secret-key-change-in-production
    ) > .env
    echo ✅ 环境变量文件已创建: .env
    echo.
    echo ⚠️  请编辑 .env 文件，配置至少一个大模型API密钥
    echo    支持的模型：
    echo    - OpenAI (OPENAI_API_KEY)
    echo    - 阿里云通义千问 (DASHSCOPE_API_KEY)
    echo    - 智谱AI (ZHIPUAI_API_KEY)
    echo.
    set /p EDIT_NOW="是否现在配置API密钥？(y/n): "
    if /i "!EDIT_NOW!"=="y" (
        notepad .env
    )
)

REM 创建必要的目录
echo 📁 创建数据目录...
if not exist data mkdir data
if not exist uploads mkdir uploads
if not exist logs mkdir logs
echo ✅ 数据目录创建完成
echo.

REM 停止并删除旧容器
echo 🛑 停止旧容器...
docker-compose down >nul 2>&1
echo ✅ 旧容器已停止
echo.

REM 构建并启动服务
echo 🚀 构建并启动服务...
docker-compose up -d --build
echo.

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 📊 检查服务状态...
docker-compose ps

echo.
echo ==========================================
echo   🎉 启动成功！
echo ==========================================
echo.
echo 📍 服务地址：
echo    - API服务: http://localhost:8000
echo    - API文档: http://localhost:8000/docs
echo    - 前端界面: http://localhost:3000 (需要单独启动前端)
echo.
echo 📋 默认管理员账号：
echo    - 用户名: admin
echo    - 密码: admin123
echo    (首次启动后请立即修改密码)
echo.
echo 🔧 常用命令：
echo    - 查看日志: docker-compose logs -f
echo    - 停止服务: docker-compose down
echo    - 重启服务: docker-compose restart
echo    - 查看状态: docker-compose ps
echo.
echo 📚 使用文档: README.md
echo.

pause