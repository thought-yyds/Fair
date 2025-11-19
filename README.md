# Fair

面向公平竞争审查业务的一体化平台，集成材料管理、AI 审查助手、知识检索以及可配置的工作流，便于在本地演示或二次开发。

## 功能概览
- **材料管理**：上传 Word/Excel/PDF 文件，跟踪解析状态并生成结构化记录。
- **AI 审查助手**：基于火山引擎 Ark LLM 的多轮对话，支持上下文记忆与结论总结。
- **RAG 检索**：内置文档预处理与向量检索流程，提升针对法规/制度文档的问答效果。
- **审查分析**：自动输出风险点、整改建议及评分，便于复核与导出。

## 技术栈
- 后端：FastAPI、SQLAlchemy、Alembic、MySQL
- AI/Agent：LangChain、火山引擎 Ark API
- 前端：Vue 3 + Vite + TailwindCSS

## 快速开始
1. **安装依赖**
   - 后端：`cd backend && pip install -r requirements.txt`
   - 前端：`npm install`
2. **准备环境变量**
   - 复制根目录 `env.example` 至 `.env`，按需填入 `DATABASE_URL`、`SECRET_KEY`、`VOLC_ARK_API_KEY` 等。
   - 本地运行时可在 `backend/START_MYSQL.md` 了解数据库初始化。
3. **启动服务**
   - 后端：`uvicorn app.main:app --reload`
   - 前端：`npm run dev`
4. **运行示例/测试**
   - 调试 Agent：参考 `backend/Agent/agent_core/langchain_chains.py`
   - 接口验证：`pytest backend/tests -k services`

## 目录指引
- `backend/app`：FastAPI 接口与业务服务
- `backend/Agent`：LLM Agent、RAG 管道以及 LangChain 配置
- `docs/`：API、架构及部署笔记
- `frontend/src`：Vue 端页面、组件与状态管理

