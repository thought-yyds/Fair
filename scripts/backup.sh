#!/bin/bash

# Fair Platform 备份脚本
# 用于备份数据库和文件

set -e

# 配置
BACKUP_DIR="/backups"
DB_NAME="fair"
DB_USER="fair_user"
DB_HOST="localhost"
DB_PORT="5432"
UPLOAD_DIR="./uploads"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "开始备份 Fair Platform - $TIMESTAMP"

# 1. 备份数据库
echo "备份数据库..."
DB_BACKUP_FILE="$BACKUP_DIR/fair_db_$TIMESTAMP.sql"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$DB_BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "数据库备份成功: $DB_BACKUP_FILE"
    # 压缩数据库备份
    gzip "$DB_BACKUP_FILE"
    echo "数据库备份已压缩: $DB_BACKUP_FILE.gz"
else
    echo "数据库备份失败"
    exit 1
fi

# 2. 备份上传文件
echo "备份上传文件..."
FILES_BACKUP_FILE="$BACKUP_DIR/fair_files_$TIMESTAMP.tar.gz"
if [ -d "$UPLOAD_DIR" ]; then
    tar -czf "$FILES_BACKUP_FILE" -C "$(dirname "$UPLOAD_DIR")" "$(basename "$UPLOAD_DIR")"
    if [ $? -eq 0 ]; then
        echo "文件备份成功: $FILES_BACKUP_FILE"
    else
        echo "文件备份失败"
        exit 1
    fi
else
    echo "上传目录不存在，跳过文件备份"
fi

# 3. 备份配置文件
echo "备份配置文件..."
CONFIG_BACKUP_FILE="$BACKUP_DIR/fair_config_$TIMESTAMP.tar.gz"
tar -czf "$CONFIG_BACKUP_FILE" \
    --exclude="node_modules" \
    --exclude=".git" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="logs" \
    --exclude="temp_reports" \
    .

if [ $? -eq 0 ]; then
    echo "配置文件备份成功: $CONFIG_BACKUP_FILE"
else
    echo "配置文件备份失败"
    exit 1
fi

# 4. 清理过期备份
echo "清理过期备份..."
find "$BACKUP_DIR" -name "fair_*" -type f -mtime +$RETENTION_DAYS -delete
echo "已清理 $RETENTION_DAYS 天前的备份文件"

# 5. 生成备份报告
REPORT_FILE="$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
cat > "$REPORT_FILE" << EOF
Fair Platform 备份报告
=====================

备份时间: $(date)
备份类型: 完整备份

备份文件:
- 数据库: $DB_BACKUP_FILE.gz
- 文件: $FILES_BACKUP_FILE
- 配置: $CONFIG_BACKUP_FILE

备份大小:
$(du -h "$BACKUP_DIR"/*_$TIMESTAMP*)

清理情况:
- 保留天数: $RETENTION_DAYS
- 已清理过期文件

备份状态: 成功
EOF

echo "备份报告已生成: $REPORT_FILE"

# 6. 发送通知（如果配置了webhook）
if [ ! -z "$WEBHOOK_URL" ]; then
    echo "发送备份完成通知..."
    curl -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"Fair Platform 备份完成\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [{
                    \"title\": \"备份时间\",
                    \"value\": \"$(date)\",
                    \"short\": true
                }, {
                    \"title\": \"备份大小\",
                    \"value\": \"$(du -sh "$BACKUP_DIR"/*_$TIMESTAMP* | awk '{print $1}' | tr '\n' ' ')\",
                    \"short\": true
                }]
            }]
        }"
fi

echo "备份完成！"
