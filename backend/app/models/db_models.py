from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

# 基础模型类（所有数据库表都继承这个）
Base = declarative_base()


class Article(Base):
    """文档表：存储上传的文件基本信息（保留你原有的所有字段）"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)  # 唯一ID
    name = Column(String(255), nullable=False, unique=True, index=True)  # 文件名（唯一）
    original_path = Column(String(512), nullable=False)  # 原始文件存储路径
    annotated_path = Column(String(512), nullable=False)  # 批注后文件路径
    upload_time = Column(DateTime, default=datetime.utcnow)  # 上传时间
    status = Column(String(20), default="待审查")  # 状态：待审查/审查中/已审查
    review_progress = Column(Integer, default=0)  # 审查进度（0-100）
    risk_level = Column(String(20))  # 文章整体风险等级（仅文章有，Annotation 无）
    review_time = Column(DateTime)  # 审查完成时间

    # 关联：1个文档 → 多个句子（删除文档级联删句子）
    sentences = relationship("Sentence", back_populates="article", cascade="all, delete-orphan")
    # 关联：1个文档 → 多个标注（删除文档级联删标注）
    # annotations = relationship("Annotation", back_populates="article", cascade="all, delete-orphan")


class Sentence(Base):
    """句子表：存储从文档提取的句子（保留你原有的所有字段）"""
    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # 句子内容
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)  # 关联文档
    has_problem = Column(Boolean)  # 是否有问题（True/False）
    annotation_id = Column(Integer, ForeignKey("annotation.id"))  # 关联标注（1:1）
    created_at = Column(DateTime, default=datetime.utcnow)  # 句子创建时间

    # 关联：1个句子 → 1个标注（1:1 核心逻辑）
    annotation = relationship("Annotation", uselist=False, viewonly=True)
    # 关联：1个句子 → 1个文档
    article = relationship("Article", back_populates="sentences")


# app/models/db_models.py（最终版 Annotation 模型）
class Annotation(Base):
    __tablename__ = "annotation"
    # 核心修改：只保留 id（手动指定1-54）、content、created_at
    id = Column(Integer, primary_key=True, autoincrement=False)  # 关闭自增！
    content = Column(String(500), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # 已删除 sentence_id 和 article_id 字段


# -------------------------- 聊天相关数据库模型 --------------------------
class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)  # 会话唯一标识
    user_id = Column(String(255), nullable=True, index=True)  # 用户ID（可选，支持匿名聊天）
    title = Column(String(255), nullable=True)  # 会话标题
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)  # 会话是否活跃
    # 记忆摘要（用于LangChain对话记忆的持久化）
    memory_summary = Column(Text, nullable=True)

    # 关联：1个会话 → 多个消息
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.session_id:
            self.session_id = str(uuid.uuid4())


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' 或 'assistant'
    content = Column(Text, nullable=False)  # 消息内容
    message_type = Column(String(20), default="text", nullable=False)  # 消息类型：text, image, file
    message_metadata = Column(JSON, nullable=True)  # 额外元数据（JSON格式）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联：1个消息 → 1个会话
    session = relationship("ChatSession", back_populates="messages")


class ChatAttachment(Base):
    """聊天附件表"""
    __tablename__ = "chat_attachments"

    id = Column(Integer, primary_key=True, index=True)
    attachment_id = Column(String(255), unique=True, index=True, nullable=False)  # 附件唯一标识
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)  # 文件名
    file_type = Column(String(100), nullable=False)  # 文件类型
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_path = Column(String(512), nullable=False)  # 文件存储路径
    content = Column(Text, nullable=True)  # 文件内容（用于文本文件）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.attachment_id:
            self.attachment_id = str(uuid.uuid4())


class ChatSettings(Base):
    """聊天设置表"""
    __tablename__ = "chat_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # 用户ID（可选，支持全局设置）
    settings_key = Column(String(100), nullable=False, index=True)  # 设置键
    settings_value = Column(JSON, nullable=False)  # 设置值（JSON格式）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)