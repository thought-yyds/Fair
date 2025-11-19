# 🚀 MySQL后端启动指南

## 当前配置
- **数据库**: MySQL
- **连接**: `mysql+pymysql://USER:PASSWORD@HOST:PORT/fastapi_review_db`
- **端口**: 8000

## 📋 启动步骤

### 1. 确保MySQL服务运行
```bash
# Windows: 启动MySQL服务
net start mysql

# 或通过服务管理器启动MySQL服务
```

### 2. 创建数据库（如果不存在）
在MySQL命令行或客户端中执行：
```sql
CREATE DATABASE fastapi_review_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 在PyCharm中安装依赖
```bash
pip install pymysql
```

### 4. 测试MySQL连接
在PyCharm中运行：
```python
python backend/test_mysql.py
```

### 5. 运行数据库迁移（如果需要）
```bash
cd backend
alembic upgrade head
```

### 6. 启动FastAPI服务器
在PyCharm中运行：
```python
python backend/run_simple.py
```

或者直接运行：
```python
python -m app.main
```

## ✅ 验证启动成功

1. **后端**: http://localhost:8000
2. **API文档**: http://localhost:8000/docs
3. **前端**: http://localhost:5173

## 🐛 常见问题

### 1. MySQL连接失败
- 检查MySQL服务是否启动
- 验证用户名密码: 请使用你在本地配置的数据库账号/密码
- 确认端口: `3306`

### 2. 数据库不存在
```sql
CREATE DATABASE fastapi_review_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 缺少pymysql包
```bash
pip install pymysql
```

### 4. 端口冲突
如果8000端口被占用，修改 `backend/app/config.py` 中的 `PORT`

## 📊 数据库表结构
启动后会自动创建以下表：
- `articles` - 文档表
- `sentences` - 句子表  
- `annotations` - 标注表
