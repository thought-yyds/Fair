# Fair

面向公平竞争审查业务的一体化平台，覆盖材料管理、流程审查、结果导出与可观测性，另附 AI 审查助手模块以增强问答效率。

## 公平竞争审查平台
- **材料采集与管理**：支持 Word/Excel/PDF 上传，自动解析形成结构化案件。
- **流程与分析引擎**：基于 FastAPI + SQLAlchemy 的服务层配合 MySQL 持久化，输出风险点、整改建议和评分。
- **RAG 检索**：`backend/RAG` 模块提供文档清洗、特征抽取与向量检索，提升法规类问答准确率。
- **监控与部署**：提供 Prometheus/Grafana 配置、Docker 打包脚本以及数据库初始化脚本，方便本地演示和上线。

### 技术栈
- 后端：FastAPI、SQLAlchemy、Alembic、MySQL
- 前端：Vue 3、Vite、TailwindCSS、Pinia
- 支撑组件：Docker、Prometheus、Grafana

### 快速开始
1. **安装依赖**
   - 后端：`cd backend && pip install -r requirements.txt`
   - 前端：`npm install`
2. **准备环境变量**
   - 复制根目录 `env.example` 至 `.env`，填入 `DATABASE_URL`、`SECRET_KEY`、`VOLC_ARK_API_KEY` 等。
   - 数据库初始化参考 `backend/START_MYSQL.md` 与 `init_mysql.sql`。
3. **启动服务**
   - 后端：`uvicorn app.main:app --reload`
   - 前端：`npm run dev`
4. **验证**
   - API：`pytest backend/tests -k services`
   - 前端访问 `http://localhost:5173`

## 目录指引
- `backend/app`：REST API、业务服务、记忆/审查逻辑
- `backend/RAG`：文档处理、向量检索与分类
- `docs/`：API、架构、部署指南
- `frontend/src`：Vue 页面、组件、状态管理

---

## AI 审查助手
- **多轮对话**：基于 FastAPI 接口与前端 Chat 页面，实现加密上下文传递及回复。
- **记忆管理**：`backend/app/services/memory_service.py` 自研 `MemoryService`，使用 SQLAlchemy 读写 `ChatSession`/`ChatMessage`，将最近消息与摘要缓存在内存中，并通过火山引擎 Ark LLM（`VolcengineLLMWrapper`）增量生成 `memory_summary`。每次调用会返回「摘要 + 最近对话」上下文，既控制 token，又保持连续性。
- **框架依赖**：整体不依赖 LangChain，直接调用 Ark Runtime SDK；前端使用 Pinia 存储会话，后端利用 FastAPI 路由和中间件管理会话安全。
- **部署要点**：需要配置 `VOLC_ARK_API_KEY`、`VOLC_ARK_BASE_URL`、`VOLC_ARK_MODEL` 等环境变量，确保数据库迁移已创建聊天表，再执行 `uvicorn app.main:app --reload`。

