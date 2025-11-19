# Fair Platform 架构文档

## 系统架构概述

Fair Platform 是一个基于微服务架构的智能内容审查平台，采用前后端分离的设计模式，提供文件上传、AI内容分析和报告生成等功能。

## 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户界面层     │    │   负载均衡层     │    │   应用服务层     │
│                │    │                │    │                │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │   Web UI  │  │    │  │   Nginx   │  │    │  │  FastAPI  │  │
│  │   (Vue3)  │  │◄───┤  │  Reverse  │  │◄───┤  │  Backend  │  │
│  └───────────┘  │    │  │   Proxy   │  │    │  └───────────┘  │
│                │    │  └───────────┘  │    │                │
└─────────────────┘    └─────────────────┘    │  ┌───────────┐  │
                                              │  │   AI      │  │
                                              │  │ Service   │  │
                                              │  └───────────┘  │
                                              └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据存储层     │    │   缓存层         │    │   监控层         │
│                │    │                │    │                │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │PostgreSQL │  │◄───┤  │   Redis   │  │    │  │Prometheus │  │
│  │ Database  │  │    │  │   Cache   │  │    │  │ Monitoring│  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│                │    │                │    │                │
│  ┌───────────┐  │    │                │    │  ┌───────────┐  │
│  │File       │  │    │                │    │  │  Grafana  │  │
│  │Storage    │  │    │                │    │  │ Dashboard │  │
│  └───────────┘  │    │                │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 技术栈

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI框架**: Element Plus
- **样式**: Tailwind CSS
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **PDF生成**: jsPDF + jspdf-autotable

### 后端技术栈
- **框架**: FastAPI (Python 3.11)
- **数据库ORM**: SQLAlchemy
- **数据库**: PostgreSQL
- **缓存**: Redis
- **任务队列**: Celery (可选)
- **文件处理**: python-docx, PyPDF2, openpyxl
- **AI集成**: OpenAI API / 自定义模型
- **日志**: Python logging + JSON格式

### 基础设施
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana
- **CI/CD**: GitHub Actions
- **部署**: Kubernetes (可选)

## 核心模块

### 1. 文件管理模块

**功能职责:**
- 文件上传和存储
- 文件类型验证
- 文件元数据管理
- 文件删除和清理

**技术实现:**
```python
# 文件服务
class FileService:
    def save_file(self, filename, file_type, content)
    def get_files(self, page, page_size, filters)
    def get_file_by_id(self, file_id)
    def delete_file(self, file_id)
```

**API端点:**
- `POST /api/files/upload` - 文件上传
- `GET /api/files/list` - 文件列表
- `GET /api/files/{id}` - 文件详情
- `DELETE /api/files/{id}` - 删除文件

### 2. 内容审查模块

**功能职责:**
- AI内容分析
- 违规内容检测
- 审查结果生成
- 实时进度反馈

**技术实现:**
```python
# 审查服务
class ReviewService:
    def start_review(self, file_id)
    def get_review_status(self, task_id)
    def get_review_result(self, task_id)
    def generate_report(self, task_id)
```

**API端点:**
- `POST /api/reviews/start` - 开始审查
- `GET /api/reviews/status/{task_id}` - 审查状态
- `GET /api/reviews/result/{task_id}` - 审查结果
- `GET /api/reviews/report/{task_id}` - 下载报告

### 3. 报告生成模块

**功能职责:**
- PDF报告生成
- 数据可视化
- 报告模板管理
- 批量报告导出

**技术实现:**
```javascript
// PDF生成
const generatePDF = (reviewData) => {
  const pdf = new jsPDF();
  // 添加标题、内容、表格等
  return pdf;
}
```

### 4. 用户界面模块

**功能职责:**
- 文件上传界面
- 审查进度显示
- 结果展示
- 报告下载

**组件结构:**
```
src/
├── components/
│   ├── FileUploader.vue    # 文件上传组件
│   ├── FileList.vue        # 文件列表组件
│   ├── ProgressCard.vue    # 进度显示组件
│   └── RiskBadge.vue       # 风险标识组件
├── views/
│   ├── FileManage.vue      # 文件管理页面
│   └── ReviewPage.vue      # 审查结果页面
└── stores/
    ├── fileStore.ts        # 文件状态管理
    └── reviewStore.ts      # 审查状态管理
```

## 数据流

### 1. 文件上传流程

```
用户选择文件
    ↓
前端验证文件类型和大小
    ↓
发送到后端API
    ↓
后端验证和保存文件
    ↓
返回文件ID和状态
    ↓
更新前端文件列表
```

### 2. 内容审查流程

```
用户点击开始审查
    ↓
后端创建审查任务
    ↓
异步处理文件内容
    ↓
调用AI服务分析
    ↓
生成审查结果
    ↓
通过SSE推送进度
    ↓
前端显示结果
```

### 3. 报告生成流程

```
用户点击下载报告
    ↓
前端收集审查数据
    ↓
调用PDF生成函数
    ↓
创建PDF文档
    ↓
添加内容和格式
    ↓
下载到本地
```

## 数据库设计

### 核心表结构

```sql
-- 文件表
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    content TEXT,
    status VARCHAR(50) DEFAULT 'uploaded',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_time TIMESTAMP
);

-- 审查表
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'started',
    violations JSONB,
    summary JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 违规内容表
CREATE TABLE violations (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES reviews(id),
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    position JSONB,
    confidence DECIMAL(3,2),
    severity VARCHAR(20),
    suggestion TEXT
);
```

## 安全设计

### 1. 输入验证
- 文件类型白名单
- 文件大小限制
- SQL注入防护
- XSS攻击防护

### 2. 访问控制
- API限流
- 请求频率限制
- 文件访问权限
- 敏感数据脱敏

### 3. 数据安全
- 数据库连接加密
- 敏感信息加密存储
- 日志脱敏
- 定期安全审计

## 性能优化

### 1. 前端优化
- 组件懒加载
- 图片压缩
- 代码分割
- 缓存策略

### 2. 后端优化
- 数据库索引
- 查询优化
- 连接池配置
- 异步处理

### 3. 基础设施优化
- CDN加速
- 负载均衡
- 缓存策略
- 资源监控

## 监控和运维

### 1. 应用监控
- 请求响应时间
- 错误率统计
- 资源使用情况
- 业务指标监控

### 2. 基础设施监控
- 服务器资源
- 数据库性能
- 网络状况
- 存储空间

### 3. 日志管理
- 结构化日志
- 日志聚合
- 错误追踪
- 性能分析

## 扩展性设计

### 1. 水平扩展
- 无状态服务设计
- 负载均衡
- 数据库分片
- 缓存集群

### 2. 功能扩展
- 插件化架构
- 微服务拆分
- API版本管理
- 配置中心

### 3. 数据扩展
- 数据分区
- 读写分离
- 数据同步
- 备份恢复

## 部署架构

### 开发环境
```
开发者机器
    ↓
Git仓库
    ↓
本地Docker环境
    ↓
开发数据库
```

### 测试环境
```
GitHub Actions
    ↓
Docker镜像构建
    ↓
测试环境部署
    ↓
自动化测试
```

### 生产环境
```
GitHub Actions
    ↓
Docker镜像构建
    ↓
生产环境部署
    ↓
监控和告警
```

## 未来规划

### 短期目标
- 用户认证系统
- 批量处理功能
- 更多文件格式支持
- 移动端适配

### 中期目标
- 微服务架构
- 多租户支持
- 高级分析功能
- 第三方集成

### 长期目标
- 机器学习优化
- 实时协作
- 企业级功能
- 国际化支持
