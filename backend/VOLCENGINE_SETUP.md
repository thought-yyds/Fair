# 火山引擎API配置指南

## 🔧 配置步骤

### 1. 获取火山引擎API密钥

1. 登录火山引擎控制台：https://console.volcengine.com/
2. 进入AI服务 -> 大模型服务
3. 创建API密钥
4. 获取模型端点ID

### 2. 配置环境变量

创建 `.env` 文件（在 `backend` 目录下）：

```bash
# AI服务配置 - 火山引擎
AI_API_KEY=your_volcengine_api_key_here
AI_API_URL=https://ark.cn-beijing.volces.com/api/v3
AI_MODEL=ep-20241220123456-abcdef  # 替换为你的模型端点ID
AI_MAX_TOKENS=4000

# 数据库配置 - MySQL
DATABASE_URL=mysql://fair_user:fair_password@localhost:3306/fair
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fair
DB_USER=fair_user
DB_PASSWORD=fair_password
```

### 3. 安装依赖

```bash
cd backend
pip install httpx  # 用于HTTP请求
```

### 4. 启动服务

```bash
cd backend
python -m app.main
```

## 📋 功能特性

### ✅ 已集成的功能

1. **智能对话**：使用火山引擎大模型进行自然语言对话
2. **流式响应**：支持实时流式输出，提升用户体验
3. **文档分析**：使用AI分析上传的文档内容
4. **内容摘要**：自动生成文档摘要
5. **风险评估**：AI驱动的风险评估功能

### 🔄 API端点

- `POST /api/chat/message` - 发送消息
- `POST /api/chat/stream` - 流式对话
- `POST /api/chat/analyze` - 文档分析
- `GET /api/chat/conversations` - 获取对话列表
- `POST /api/chat/conversations` - 创建新对话

## 🛠️ 自定义配置

### 修改模型参数

在 `backend/app/config.py` 中修改：

```python
# AI服务配置 - 火山引擎
ai_api_key: str = "your_api_key"
ai_api_url: str = "https://ark.cn-beijing.volces.com/api/v3"
ai_model: str = "your_model_endpoint_id"
ai_max_tokens: int = 4000
ai_processing_timeout: int = 60
```

### 自定义系统提示

在 `backend/app/api/endpoints/chat.py` 中修改 `generate_ai_response_with_volcengine` 函数：

```python
system_prompt = "你的自定义系统提示..."
```

## 🚨 注意事项

1. **API密钥安全**：不要将API密钥提交到版本控制系统
2. **费用控制**：火山引擎按使用量计费，注意控制调用频率
3. **错误处理**：已实现优雅的错误处理，API失败时会返回默认回复
4. **超时设置**：默认60秒超时，可根据需要调整

## 🔍 故障排除

### 常见问题

1. **API密钥错误**：检查 `.env` 文件中的 `AI_API_KEY` 是否正确
2. **模型端点错误**：确认 `AI_MODEL` 是否为有效的端点ID
3. **网络连接问题**：检查网络连接和防火墙设置
4. **超时错误**：增加 `ai_processing_timeout` 值

### 调试模式

在 `backend/app/config.py` 中设置：

```python
debug: bool = True
log_level: str = "DEBUG"
```

## 📞 支持

如果遇到问题，请检查：

1. 火山引擎控制台中的API使用情况
2. 后端日志文件 `logs/app.log`
3. 网络连接状态
4. API密钥和模型端点配置

---

**配置完成后，你的AI智能助手就可以使用火山引擎的强大AI能力了！** 🎉
