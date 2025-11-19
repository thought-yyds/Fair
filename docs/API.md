# Fair Platform API 文档

## 概述

Fair Platform 是一个智能内容审查平台，提供文件上传、AI内容分析和报告生成功能。

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **API版本**: v1
- **认证方式**: 无（开发阶段）

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

## 文件管理 API

### 1. 上传文件

**POST** `/files/upload`

上传文件到平台进行审查。

**请求参数:**
- `file` (multipart/form-data): 要上传的文件

**支持的文件类型:**
- PDF (.pdf)
- Word文档 (.docx)
- Excel表格 (.xlsx)
- PowerPoint演示文稿 (.pptx)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "file_id": 123,
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "upload_time": "2024-01-01T12:00:00Z"
  }
}
```

### 2. 获取文件列表

**GET** `/files/list`

获取已上传文件的列表。

**查询参数:**
- `page` (int, 可选): 页码，默认为1
- `page_size` (int, 可选): 每页数量，默认为10
- `status` (string, 可选): 文件状态过滤
- `file_type` (string, 可选): 文件类型过滤

**响应示例:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 123,
        "filename": "document.pdf",
        "file_type": "pdf",
        "file_size": 1024000,
        "status": "completed",
        "upload_time": "2024-01-01T12:00:00Z",
        "review_time": "2024-01-01T12:05:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

### 3. 获取文件详情

**GET** `/files/{file_id}`

获取指定文件的详细信息。

**路径参数:**
- `file_id` (int): 文件ID

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "completed",
    "content": "文件内容...",
    "upload_time": "2024-01-01T12:00:00Z",
    "review_time": "2024-01-01T12:05:00Z"
  }
}
```

### 4. 删除文件

**DELETE** `/files/{file_id}`

删除指定的文件。

**路径参数:**
- `file_id` (int): 文件ID

**响应示例:**
```json
{
  "success": true,
  "message": "文件删除成功"
}
```

## 内容审查 API

### 1. 开始审查

**POST** `/reviews/start`

开始对文件进行内容审查。

**请求体:**
```json
{
  "file_id": 123
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "started",
    "message": "审查任务已开始"
  }
}
```

### 2. 获取审查状态

**GET** `/reviews/status/{task_id}`

获取审查任务的当前状态。

**路径参数:**
- `task_id` (string): 任务ID

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "processing",
    "progress": 75,
    "message": "正在分析文档内容...",
    "estimated_time": 30
  }
}
```

**状态说明:**
- `started`: 任务已开始
- `processing`: 正在处理
- `completed`: 处理完成
- `failed`: 处理失败

### 3. 获取审查结果

**GET** `/reviews/result/{task_id}`

获取审查任务的详细结果。

**路径参数:**
- `task_id` (string): 任务ID

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "file_id": 123,
    "status": "completed",
    "violations": [
      {
        "id": 1,
        "type": "政治敏感",
        "content": "敏感内容片段",
        "position": {
          "start": 100,
          "end": 150
        },
        "confidence": 0.95,
        "severity": "high",
        "suggestion": "建议修改为..."
      }
    ],
    "summary": {
      "total_violations": 1,
      "high_risk": 1,
      "medium_risk": 0,
      "low_risk": 0,
      "overall_risk": "high"
    },
    "processing_time": 45.2,
    "completed_time": "2024-01-01T12:05:00Z"
  }
}
```

### 4. 下载审查报告

**GET** `/reviews/report/{task_id}`

下载PDF格式的审查报告。

**路径参数:**
- `task_id` (string): 任务ID

**响应:**
- Content-Type: `application/pdf`
- 文件流

## 系统 API

### 1. 健康检查

**GET** `/health`

检查系统健康状态。

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ai_service": "healthy"
  },
  "version": "1.0.0"
}
```

### 2. 系统指标

**GET** `/metrics`

获取系统运行指标（Prometheus格式）。

## 错误码说明

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| FILE_NOT_FOUND | 404 | 文件不存在 |
| INVALID_FILE_TYPE | 400 | 不支持的文件类型 |
| FILE_TOO_LARGE | 400 | 文件过大 |
| TASK_NOT_FOUND | 404 | 任务不存在 |
| PROCESSING_ERROR | 500 | 处理错误 |
| DATABASE_ERROR | 500 | 数据库错误 |

## 限流说明

- API请求限制：10次/秒
- 文件上传限制：1次/秒
- 单次上传文件大小限制：100MB

## 示例代码

### JavaScript (Fetch)
```javascript
// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/files/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

### Python (requests)
```python
import requests

# 上传文件
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/files/upload', files=files)
result = response.json()
print(result)
```

### cURL
```bash
# 上传文件
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8000/api/files/upload

# 获取文件列表
curl http://localhost:8000/api/files/list?page=1&page_size=10
```
