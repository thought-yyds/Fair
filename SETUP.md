# 公平审查大数据平台 - 部署指南

## 🚀 快速启动

### 方法一：使用启动脚本（推荐）

**Windows:**
```bash
# 双击运行
start_dev.bat
```

**Linux/Mac:**
```bash
# 给脚本执行权限
chmod +x start_dev.sh
# 运行脚本
./start_dev.sh
```

### 方法二：手动启动

#### 1. 启动后端 FastAPI 服务器

```bash
# 进入后端目录
cd backend

# 安装依赖（首次运行）
pip install -r requirements.txt

# 启动服务器
python -m app.main
```

后端将在 `http://localhost:8000` 启动

#### 2. 启动前端 Vue 开发服务器

```bash
# 在项目根目录
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 📋 环境要求

### 后端要求
- Python 3.8+
- FastAPI
- SQLAlchemy
- PyTorch（用于AI模型）
- Transformers

### 前端要求
- Node.js 16+
- Vue 3
- TypeScript
- TailwindCSS
- Element Plus

## 🔧 配置说明

### 后端配置
后端配置文件位于 `backend/app/config.py`，主要配置项：

- `PORT`: 服务器端口（默认8000）
- `DATABASE_URL`: 数据库连接（默认SQLite）
- `ALLOWED_ORIGINS`: 允许的前端地址
- `MODEL_PATH`: AI模型文件路径
- `TOKENIZER_PATH`: 分词器路径

### 前端配置
前端配置文件位于 `vite.config.ts`，主要配置项：

- `proxy`: API代理配置（转发到后端8000端口）

## 📚 API文档

启动后端后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔄 完整的数据流转

### 1. 文件上传流程
```
前端上传文件 → POST /api/files/upload → 后端保存文件 → 返回文件信息
```

### 2. 文件审查流程
```
用户点击开始审查 → POST /api/reviews/start/{id} → 后端启动异步审查 → 返回启动成功
前端轮询进度 → GET /api/reviews/progress/{id} → 后端返回进度 → 前端更新UI
审查完成 → 状态变为"已审查" → 显示风险等级
```

### 3. 查看详情流程
```
用户点击查看详情 → GET /api/reviews/detail/{id} → 后端返回违规句子 → 前端展示详情
```

## 🐛 常见问题

### 1. 端口冲突
如果8000端口被占用，修改 `backend/app/config.py` 中的 `PORT` 配置

### 2. 跨域问题
确保 `ALLOWED_ORIGINS` 包含前端地址 `http://localhost:5173`

### 3. AI模型加载失败
检查 `weights/Fair_2.pt` 和 `tokenizer/` 目录是否存在

### 4. 数据库问题
首次运行会自动创建SQLite数据库，如有问题可删除 `fair_review.db` 重新创建

## 📁 项目结构

```
myProject/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/endpoints/   # API接口
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   └── uploads/            # 上传文件存储
├── src/                    # 前端代码
│   ├── api/               # API调用
│   ├── components/        # Vue组件
│   ├── views/             # 页面组件
│   └── types/             # TypeScript类型
└── weights/               # AI模型文件
```

## 🎯 开发建议

1. **后端开发**: 修改API后重启后端服务
2. **前端开发**: 使用 `npm run dev` 热重载
3. **数据库**: 使用Alembic进行数据库迁移
4. **调试**: 查看浏览器控制台和后端日志
