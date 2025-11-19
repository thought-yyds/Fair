#!/bin/bash

# Fair Platform 部署脚本
# 用于自动化部署应用

set -e

# 配置
APP_NAME="fair-platform"
DOCKER_IMAGE="fair-platform:latest"
ENVIRONMENT=${1:-production}
BACKUP_BEFORE_DEPLOY=true

echo "开始部署 Fair Platform - 环境: $ENVIRONMENT"

# 1. 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行"
    exit 1
fi

# 2. 检查Docker Compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

# 3. 备份现有数据（如果启用）
if [ "$BACKUP_BEFORE_DEPLOY" = true ]; then
    echo "备份现有数据..."
    ./scripts/backup.sh
    if [ $? -eq 0 ]; then
        echo "数据备份完成"
    else
        echo "警告: 数据备份失败，继续部署..."
    fi
fi

# 4. 停止现有服务
echo "停止现有服务..."
docker-compose down

# 5. 拉取最新镜像
echo "拉取最新镜像..."
docker-compose pull

# 6. 构建新镜像（如果需要）
echo "构建应用镜像..."
docker-compose build --no-cache

# 7. 启动服务
echo "启动服务..."
docker-compose up -d

# 8. 等待服务启动
echo "等待服务启动..."
sleep 30

# 9. 健康检查
echo "执行健康检查..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "健康检查通过"
        break
    else
        echo "健康检查失败，重试 $((RETRY_COUNT + 1))/$MAX_RETRIES"
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "错误: 健康检查失败，部署可能有问题"
    echo "查看服务日志:"
    docker-compose logs --tail=50
    exit 1
fi

# 10. 运行数据库迁移（如果需要）
echo "运行数据库迁移..."
docker-compose exec backend alembic upgrade head

# 11. 清理旧镜像
echo "清理旧镜像..."
docker image prune -f

# 12. 显示服务状态
echo "服务状态:"
docker-compose ps

# 13. 显示访问信息
echo ""
echo "部署完成！"
echo "访问地址: http://localhost"
echo "API文档: http://localhost/docs"
echo "监控面板: http://localhost:3000 (Grafana)"
echo ""

# 14. 发送部署通知（如果配置了webhook）
if [ ! -z "$WEBHOOK_URL" ]; then
    echo "发送部署完成通知..."
    curl -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"Fair Platform 部署完成\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [{
                    \"title\": \"环境\",
                    \"value\": \"$ENVIRONMENT\",
                    \"short\": true
                }, {
                    \"title\": \"部署时间\",
                    \"value\": \"$(date)\",
                    \"short\": true
                }, {
                    \"title\": \"访问地址\",
                    \"value\": \"http://localhost\",
                    \"short\": false
                }]
            }]
        }"
fi

echo "部署脚本执行完成！"
