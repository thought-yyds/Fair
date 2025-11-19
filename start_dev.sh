#!/bin/bash

echo "启动公平审查大数据平台开发环境..."
echo

echo "1. 启动后端 FastAPI 服务器..."
cd backend
python -m app.main &
BACKEND_PID=$!

echo "等待后端启动..."
sleep 3

echo "2. 启动前端 Vue 开发服务器..."
cd ..
npm run dev &
FRONTEND_PID=$!

echo
echo "开发环境启动完成！"
echo "后端地址: http://localhost:8000"
echo "前端地址: http://localhost:5173"
echo "API文档: http://localhost:8000/docs"
echo
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
wait

# 清理进程
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
