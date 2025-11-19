@echo off
echo 启动公平审查大数据平台开发环境...
echo.

echo 1. 启动后端 FastAPI 服务器...
start "FastAPI Backend" cmd /k "cd backend && python -m app.main"

echo 等待后端启动...
timeout /t 3 /nobreak > nul

echo 2. 启动前端 Vue 开发服务器...
start "Vue Frontend" cmd /k "npm run dev"

echo.
echo 开发环境启动完成！
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo API文档: http://localhost:8000/docs
echo.
pause
