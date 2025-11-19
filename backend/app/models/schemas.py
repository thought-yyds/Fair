from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# -------------------------- 1. 文档相关 Schema（删除与 Annotation 的无关关联）--------------------------
class ArticleBase(BaseModel):
    name: str = Field(..., max_length=255, description="文件名（唯一，必填）")
    original_path: str = Field(..., max_length=512, description="原始文件路径（必填，后端内部使用）")
    annotated_path: str = Field(..., max_length=512, description="批注后文件路径（必填，后端内部使用）")
    status: str = Field("待审查", pattern="^(待审查|审查中|已审查)$", description="文档状态")
    review_progress: int = Field(0, ge=0, le=100, description="审查进度（0-100）")
    risk_level: Optional[str] = Field(None, pattern="^(无风险|低风险|中风险|高风险)$", description="文章整体风险等级")


class ArticleCreate(ArticleBase):
    pass  # 创建请求无需 ID/时间


class ArticleSchema(ArticleBase):
    id: int = Field(..., description="文档唯一ID（自增）")
    upload_time: datetime = Field(..., description="上传时间")
    review_time: Optional[datetime] = Field(None, description="审查完成时间")
    # 关联数据：仅保留 Sentence 关联（删除原 annotations 关联，因 Annotation 已与 Article 解耦）
    sentences: Optional[List["SentenceSchema"]] = Field(None, description="文档关联的句子列表")

    class Config:
        from_attributes = True


# -------------------------- 2. 前端专用文档响应 Schema（无修改，保持过滤敏感路径）--------------------------
class ArticleResponseSchema(BaseModel):
    id: int = Field(..., description="文档唯一ID（用于后续操作，如审查/删除）")
    name: str = Field(..., max_length=255, description="原始文件名（前端展示用）")
    status: str = Field(..., pattern="^(待审查|审查中|已审查)$", description="文档状态（前端展示/状态判断）")
    review_progress: int = Field(..., ge=0, le=100, description="审查进度（前端进度条展示）")
    risk_level: Optional[str] = Field(None, pattern="^(无风险|低风险|中风险|高风险)$", description="风险等级（前端展示）")
    upload_time: datetime = Field(..., description="上传时间（前端排序/展示）")
    review_time: Optional[datetime] = Field(None, description="审查完成时间（审查后展示）")

    class Config:
        from_attributes = True


# -------------------------- 3. 句子相关 Schema（无核心修改，仅关联逻辑适配新 Annotation）--------------------------
class SentenceBase(BaseModel):
    content: str = Field(..., description="句子内容（必填）")
    has_problem: Optional[bool] = Field(None, description="是否有问题")
    annotation_id: Optional[int] = Field(None, description="关联标注ID（1:1，对应 Annotation 表的 id）")
    article_id: int = Field(..., description="所属文档ID（必填）")


class SentenceCreate(SentenceBase):
    pass  # 创建请求无需 ID/时间


class SentenceSchema(SentenceBase):
    id: int = Field(..., description="句子唯一ID（自增）")
    created_at: datetime = Field(..., description="句子创建时间")
    # 关联标注：保持与 AnnotationSchema 的关联（用于前端展示违规原因）
    annotation: Optional["AnnotationSchema"] = Field(None, description="句子对应的违规描述（前端展示用）")

    class Config:
        from_attributes = True


# -------------------------- 4. 标注映射表 Schema（核心修改：删除 sentence_id/article_id，添加手动 id 约束）--------------------------
class AnnotationBase(BaseModel):
    """标注基础模型：仅保留“标签→描述”核心字段（纯映射，与句子/文档解耦）"""
    id: int = Field(..., ge=1, le=54, description="模型输出的违规标签（1-54，手动指定，唯一）")
    content: str = Field(..., max_length=500, description="违规描述（如“包含敏感信息”，必填且唯一）")


class AnnotationCreate(AnnotationBase):
    pass  # 创建映射时，仅需传 id（1-54）和 content（无需其他字段）


class AnnotationSchema(AnnotationBase):
    """标注响应模型：新增创建时间，无多余关联字段"""
    created_at: datetime = Field(..., description="映射数据添加时间")

    class Config:
        from_attributes = True


# -------------------------- 5. 审查进度 Schema（无修改）--------------------------
class ReviewProgressSchema(BaseModel):
    progress: int = Field(..., ge=0, le=100, description="当前审查进度（前端进度条更新）")
    status: str = Field(..., description="当前文档状态（前端状态判断，如是否可重复审查）")
    risk_level: Optional[str] = Field(None, description="文章整体风险等级（审查完成后返回）")


# -------------------------- 6. AI聊天机器人相关 Schema --------------------------
class ChatSessionBase(BaseModel):
    """聊天会话基础模型"""
    user_id: Optional[str] = Field(None, max_length=255, description="用户ID（可选，支持匿名聊天）")
    title: Optional[str] = Field(None, max_length=255, description="会话标题")


class ChatSessionCreate(ChatSessionBase):
    """创建聊天会话请求"""
    pass


class ChatSessionSchema(ChatSessionBase):
    """聊天会话响应模型"""
    id: int = Field(..., description="会话唯一ID")
    session_id: str = Field(..., max_length=255, description="会话唯一标识")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")
    is_active: bool = Field(..., description="会话是否活跃")
    message_count: Optional[int] = Field(None, description="消息数量")

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    """聊天消息基础模型"""
    role: str = Field(..., pattern="^(user|assistant)$", description="消息角色：user（用户）/assistant（AI机器人）")
    content: str = Field(..., description="消息内容")
    message_type: str = Field("text", pattern="^(text|image|file)$", description="消息类型")
    metadata: Optional[str] = Field(None, description="额外元数据（JSON格式）")


class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息请求"""
    session_id: str = Field(..., max_length=255, description="所属会话ID")


class ChatMessageSchema(ChatMessageBase):
    """聊天消息响应模型"""
    id: int = Field(..., description="消息唯一ID")
    session_id: str = Field(..., max_length=255, description="所属会话ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ChatAttachmentBase(BaseModel):
    """聊天附件基础模型"""
    name: str = Field(..., max_length=255, description="文件名")
    file_type: str = Field(..., max_length=100, description="文件类型")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    content: Optional[str] = Field(None, description="文件内容（用于文本文件）")


class ChatAttachmentCreate(ChatAttachmentBase):
    """创建聊天附件请求"""
    session_id: str = Field(..., max_length=255, description="所属会话ID")
    message_id: Optional[int] = Field(None, description="关联消息ID")


class ChatAttachmentSchema(ChatAttachmentBase):
    """聊天附件响应模型"""
    id: int = Field(..., description="附件唯一ID")
    attachment_id: str = Field(..., max_length=255, description="附件唯一标识")
    session_id: str = Field(..., max_length=255, description="所属会话ID")
    message_id: Optional[int] = Field(None, description="关联消息ID")
    file_path: str = Field(..., max_length=512, description="文件存储路径")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """AI聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息内容")
    session_id: Optional[str] = Field(None, max_length=255, description="会话ID（可选，不提供则创建新会话）")
    user_id: Optional[str] = Field(None, max_length=255, description="用户ID（可选）")
    context: Optional[str] = Field(None, description="上下文信息（可选）")
    attachments: Optional[List[dict]] = Field(None, description="附件列表")


class ChatResponse(BaseModel):
    """AI聊天响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="AI回复内容")
    session_id: str = Field(..., description="会话ID")
    message_id: int = Field(..., description="AI消息ID")
    timestamp: datetime = Field(..., description="回复时间")


class ChatHistoryResponse(BaseModel):
    """聊天历史响应模型"""
    session: ChatSessionSchema = Field(..., description="会话信息")
    messages: List[ChatMessageSchema] = Field(..., description="消息列表")


class ChatSettingsBase(BaseModel):
    """聊天设置基础模型"""
    settings_key: str = Field(..., max_length=100, description="设置键")
    settings_value: dict = Field(..., description="设置值（JSON格式）")


class ChatSettingsCreate(ChatSettingsBase):
    """创建聊天设置请求"""
    user_id: Optional[str] = Field(None, max_length=255, description="用户ID（可选）")


class ChatSettingsSchema(ChatSettingsBase):
    """聊天设置响应模型"""
    id: int = Field(..., description="设置唯一ID")
    user_id: Optional[str] = Field(None, max_length=255, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool = Field(..., description="上传是否成功")
    attachment_id: Optional[str] = Field(None, description="附件ID")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小")
    error: Optional[str] = Field(None, description="错误信息")


class FileAnalysisRequest(BaseModel):
    """文件分析请求模型"""
    attachment_id: str = Field(..., description="附件ID")
    prompt: Optional[str] = Field(None, description="分析提示词")


class FileAnalysisResponse(BaseModel):
    """文件分析响应模型"""
    success: bool = Field(..., description="分析是否成功")
    analysis: Optional[str] = Field(None, description="分析结果")
    error: Optional[str] = Field(None, description="错误信息")


# 解决循环引用（SentenceSchema 与 AnnotationSchema 互相引用，需最后更新）
SentenceSchema.update_forward_refs()
ArticleSchema.update_forward_refs()