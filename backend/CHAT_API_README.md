# 聊天API功能说明

## 概述

本系统新增了完整的AI聊天机器人功能，支持：
- 多会话管理
- 实时消息发送
- 文件上传和分析
- 流式响应
- 聊天设置管理
- 会话搜索和导出

## 数据库表结构

### 1. chat_sessions (聊天会话表)
- `id`: 主键
- `session_id`: 会话唯一标识 (UUID)
- `user_id`: 用户ID (可选，支持匿名聊天)
- `title`: 会话标题
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `is_active`: 是否活跃

### 2. chat_messages (聊天消息表)
- `id`: 主键
- `session_id`: 所属会话ID
- `role`: 消息角色 (user/assistant)
- `content`: 消息内容
- `message_type`: 消息类型 (text/image/file)
- `metadata`: 额外元数据 (JSON)
- `created_at`: 创建时间

### 3. chat_attachments (聊天附件表)
- `id`: 主键
- `attachment_id`: 附件唯一标识 (UUID)
- `session_id`: 所属会话ID
- `message_id`: 关联消息ID (可选)
- `name`: 文件名
- `file_type`: 文件类型
- `file_size`: 文件大小
- `file_path`: 文件存储路径
- `content`: 文件内容 (文本文件)
- `created_at`: 创建时间

### 4. chat_settings (聊天设置表)
- `id`: 主键
- `user_id`: 用户ID (可选)
- `settings_key`: 设置键
- `settings_value`: 设置值 (JSON)
- `created_at`: 创建时间
- `updated_at`: 更新时间

## API端点

### 会话管理
- `POST /api/chat/conversations` - 创建新会话
- `GET /api/chat/conversations` - 获取会话列表
- `GET /api/chat/conversations/{conversation_id}` - 获取特定会话
- `PUT /api/chat/conversations/{conversation_id}` - 更新会话标题
- `DELETE /api/chat/conversations/{conversation_id}` - 删除会话

### 消息管理
- `GET /api/chat/conversations/{conversation_id}/messages` - 获取会话消息
- `POST /api/chat/message` - 发送消息
- `POST /api/chat/stream` - 流式发送消息

### 文件管理
- `POST /api/chat/upload` - 上传文件
- `POST /api/chat/analyze` - 分析文件
- `GET /api/chat/attachments/{attachment_id}` - 下载附件

### 设置管理
- `GET /api/chat/settings` - 获取聊天设置
- `PUT /api/chat/settings` - 更新聊天设置

### 搜索和导出
- `GET /api/chat/search` - 搜索会话
- `GET /api/chat/conversations/{conversation_id}/export` - 导出会话

## 使用示例

### 1. 创建会话
```python
import requests

response = requests.post("http://localhost:8000/api/chat/conversations", json={
    "title": "新对话",
    "user_id": "user123"
})
session = response.json()
session_id = session["session_id"]
```

### 2. 发送消息
```python
response = requests.post("http://localhost:8000/api/chat/message", json={
    "message": "你好，请介绍一下你自己",
    "session_id": session_id,
    "user_id": "user123"
})
chat_response = response.json()
print(chat_response["message"])
```

### 3. 流式响应
```python
response = requests.post("http://localhost:8000/api/chat/stream", json={
    "message": "请详细介绍一下你的功能",
    "session_id": session_id
}, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]
            if data_str == '[DONE]':
                break
            data = json.loads(data_str)
            print(data.get('content', ''), end='', flush=True)
```

### 4. 文件上传
```python
files = {'file': open('document.pdf', 'rb')}
data = {
    'session_id': session_id,
    'message_id': message_id  # 可选
}
response = requests.post("http://localhost:8000/api/chat/upload", files=files, data=data)
```

## 部署说明

### 1. 数据库迁移
```bash
# 运行数据库迁移
alembic upgrade head
```

### 2. 启动服务
```bash
# 启动后端服务
python -m app.main
```

### 3. 测试API
```bash
# 运行测试脚本
python test_chat_api.py
```

## 前端集成

前端已经实现了完整的聊天界面，包括：
- `ChatPage.vue` - 聊天页面组件
- `chatApi.ts` - API调用封装
- `chatStore.ts` - 状态管理
- `chat.ts` - 类型定义

前端会自动调用后端API，无需额外配置。

## 注意事项

1. **AI服务集成**: 当前使用模拟AI回复，实际部署时需要集成真实的AI服务（如OpenAI、Claude等）

2. **文件存储**: 文件存储在 `uploads/chat/` 目录下，确保有足够的磁盘空间

3. **安全性**: 生产环境需要添加适当的身份验证和授权机制

4. **性能优化**: 对于大量消息的会话，建议实现分页加载

5. **错误处理**: 所有API都有完善的错误处理机制，返回详细的错误信息

## 扩展功能

可以根据需要添加以下功能：
- 消息加密
- 多语言支持
- 消息模板
- 智能推荐
- 语音消息
- 图片生成
- 代码执行
