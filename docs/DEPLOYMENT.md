# Fair Platform 部署文档

## 概述

本文档介绍如何部署 Fair Platform 智能内容审查平台。

## 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Linux (Ubuntu 20.04+ 推荐)

### 推荐配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **操作系统**: Linux (Ubuntu 22.04 LTS)

## 部署方式

### 方式一：Docker Compose（推荐）

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/fair-platform.git
cd fair-platform
```

#### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

#### 3. 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 4. 验证部署
```bash
# 检查健康状态
curl http://localhost/health

# 访问Web界面
open http://localhost
```

### 方式二：Kubernetes

#### 1. 创建命名空间
```bash
kubectl create namespace fair-platform
```

#### 2. 创建配置
```bash
# 创建ConfigMap
kubectl apply -f k8s/configmap.yaml

# 创建Secret
kubectl apply -f k8s/secret.yaml
```

#### 3. 部署应用
```bash
# 部署数据库
kubectl apply -f k8s/postgres.yaml

# 部署Redis
kubectl apply -f k8s/redis.yaml

# 部署后端
kubectl apply -f k8s/backend.yaml

# 部署前端
kubectl apply -f k8s/frontend.yaml

# 部署Nginx
kubectl apply -f k8s/nginx.yaml
```

#### 4. 检查部署状态
```bash
kubectl get pods -n fair-platform
kubectl get services -n fair-platform
```

### 方式三：手动部署

#### 1. 安装依赖

**后端依赖:**
```bash
# 安装Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装Python依赖
cd backend
pip install -r requirements.txt
```

**前端依赖:**
```bash
# 安装Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装依赖
npm install

# 构建前端
npm run build
```

**数据库:**
```bash
# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb fair
sudo -u postgres createuser fair_user
sudo -u postgres psql -c "ALTER USER fair_user PASSWORD 'fair_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fair TO fair_user;"
```

#### 2. 配置应用

**后端配置:**
```bash
cd backend
cp config.py.example config.py
# 编辑 config.py 文件
```

**前端配置:**
```bash
# 编辑 vite.config.ts 中的API地址
```

#### 3. 启动服务

**启动后端:**
```bash
cd backend
python main.py
```

**启动前端:**
```bash
npm run dev
```

## 环境配置

### 必需环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://fair_user:fair_password@localhost:5432/fair

# Redis配置
REDIS_URL=redis://localhost:6379

# AI服务配置
AI_API_KEY=your_ai_api_key
AI_API_URL=https://api.example.com

# 安全配置
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret

# 文件存储配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### 可选环境变量

```bash
# 监控配置
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password

# 通知配置
WEBHOOK_URL=https://hooks.slack.com/services/...
```

## 监控和日志

### 访问监控面板

- **Grafana**: http://localhost:3000
  - 用户名: admin
  - 密码: admin123

- **Prometheus**: http://localhost:9090

### 查看日志

```bash
# Docker方式
docker-compose logs -f backend
docker-compose logs -f frontend

# 手动部署
tail -f logs/app.log
```

### 健康检查

```bash
# 检查API健康状态
curl http://localhost/api/health

# 检查数据库连接
curl http://localhost/api/health | jq '.services.database'

# 检查Redis连接
curl http://localhost/api/health | jq '.services.redis'
```

## 备份和恢复

### 数据库备份

```bash
# 创建备份
pg_dump -h localhost -U fair_user fair > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
psql -h localhost -U fair_user fair < backup_20240101_120000.sql
```

### 文件备份

```bash
# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/

# 恢复文件
tar -xzf uploads_backup_20240101_120000.tar.gz
```

## 性能优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_files_upload_time ON files(upload_time);
CREATE INDEX idx_reviews_task_id ON reviews(task_id);

-- 分析表统计信息
ANALYZE files;
ANALYZE reviews;
```

### 应用优化

```bash
# 增加工作进程
# 在 docker-compose.yml 中修改
command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# 启用Gzip压缩
# 在 nginx.conf 中已配置
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL状态
   sudo systemctl status postgresql
   
   # 检查连接
   psql -h localhost -U fair_user -d fair
   ```

2. **文件上传失败**
   ```bash
   # 检查文件权限
   ls -la uploads/
   
   # 检查磁盘空间
   df -h
   ```

3. **AI服务调用失败**
   ```bash
   # 检查API密钥
   echo $AI_API_KEY
   
   # 测试API连接
   curl -H "Authorization: Bearer $AI_API_KEY" $AI_API_URL/health
   ```

### 日志分析

```bash
# 查看错误日志
grep "ERROR" logs/app.log

# 查看访问日志
tail -f /var/log/nginx/access.log

# 查看系统资源使用
htop
```

## 安全建议

1. **更改默认密码**
   - 数据库密码
   - Grafana密码
   - 系统用户密码

2. **配置防火墙**
   ```bash
   # 只开放必要端口
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

3. **启用HTTPS**
   - 配置SSL证书
   - 更新Nginx配置

4. **定期更新**
   ```bash
   # 更新系统包
   sudo apt update && sudo apt upgrade
   
   # 更新Docker镜像
   docker-compose pull
   docker-compose up -d
   ```

## 联系支持

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的GitHub Issues
3. 联系技术支持团队
