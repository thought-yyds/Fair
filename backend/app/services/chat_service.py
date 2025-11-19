"""
聊天服务层 - 处理聊天相关的业务逻辑
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import threading

from app.models.db_models import ChatSession, ChatMessage, ChatAttachment, ChatSettings
from app.config import settings
from app.models.schemas import (
    ChatSessionCreate, ChatMessageCreate, ChatAttachmentCreate,
    ChatRequest, ChatResponse, FileUploadResponse, FileAnalysisRequest,
    FileAnalysisResponse, ChatSettingsCreate
)
from app.services.memory_service import MemoryService


class ChatService:
    """聊天服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        # 记忆服务（懒加载失败会抛错，在使用前确保API Key配置）
        try:
            self.memory_service = MemoryService(db)
        except Exception:
            self.memory_service = None
    
    # -------------------------- 会话管理 --------------------------
    
    def create_session(self, session_data: ChatSessionCreate, user_id: Optional[str] = None) -> ChatSession:
        """创建新的聊天会话"""
        try:
            # 创建会话
            session = ChatSession(
                user_id=user_id or session_data.user_id,
                title=session_data.title or "新对话"
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            return session
        except Exception as e:
            self.db.rollback()
            raise Exception(f"创建会话失败: {str(e)}")
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话信息"""
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
    
    def get_user_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[ChatSession]:
        """获取用户的会话列表"""
        query = self.db.query(ChatSession).filter(ChatSession.is_active == True)
        
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
        
        return query.order_by(desc(ChatSession.updated_at)).limit(limit).all()
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """更新会话标题"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session.title = title
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新会话标题失败: {str(e)}")
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话（软删除）"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session.is_active = False
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"删除会话失败: {str(e)}")
    
    # -------------------------- 消息管理 --------------------------
    
    def create_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """创建新消息"""
        try:
            # 检查会话是否存在
            session = self.get_session(message_data.session_id)
            if not session:
                raise Exception("会话不存在")
            
            # 创建消息
            message = ChatMessage(
                session_id=message_data.session_id,
                role=message_data.role,
                content=message_data.content,
                message_type=message_data.message_type,
                message_metadata=message_data.metadata
            )
            
            self.db.add(message)
            
            # 更新会话的更新时间
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(message)
            
            return message
        except Exception as e:
            self.db.rollback()
            raise Exception(f"创建消息失败: {str(e)}")
    
    def get_session_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """获取会话的消息列表"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).limit(limit).all()
    
    def get_message_count(self, session_id: str) -> int:
        """获取会话的消息数量"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).count()
    
    # -------------------------- 文件上传和管理 --------------------------
    
    def upload_file(self, file, session_id: str, message_id: Optional[int] = None) -> FileUploadResponse:
        """上传文件"""
        try:
            # 检查会话是否存在
            session = self.get_session(session_id)
            if not session:
                return FileUploadResponse(
                    success=False,
                    error="会话不存在"
                )
            
            # 创建上传目录
            upload_dir = os.path.join("uploads", "chat", session_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成唯一文件名
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # 保存文件
            file.save(file_path)
            
            # 读取文件内容（如果是文本文件）
            content = None
            if file.content_type and file.content_type.startswith('text/'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    pass  # 如果读取失败，content保持为None
            
            # 创建附件记录
            attachment = ChatAttachment(
                session_id=session_id,
                message_id=message_id,
                name=file.filename,
                file_type=file.content_type or 'application/octet-stream',
                file_size=os.path.getsize(file_path),
                file_path=file_path,
                content=content
            )
            
            self.db.add(attachment)
            self.db.commit()
            self.db.refresh(attachment)
            
            return FileUploadResponse(
                success=True,
                attachment_id=attachment.attachment_id,
                file_name=attachment.name,
                file_size=attachment.file_size
            )
            
        except Exception as e:
            self.db.rollback()
            return FileUploadResponse(
                success=False,
                error=f"文件上传失败: {str(e)}"
            )
    
    def get_attachment(self, attachment_id: str) -> Optional[ChatAttachment]:
        """获取附件信息"""
        return self.db.query(ChatAttachment).filter(
            ChatAttachment.attachment_id == attachment_id
        ).first()
    
    def analyze_file(self, request: FileAnalysisRequest) -> FileAnalysisResponse:
        """分析文件内容"""
        try:
            attachment = self.get_attachment(request.attachment_id)
            if not attachment:
                return FileAnalysisResponse(
                    success=False,
                    error="附件不存在"
                )
            
            # 这里可以集成AI分析功能
            # 暂时返回模拟的分析结果
            analysis_result = self._mock_file_analysis(attachment, request.prompt)
            
            return FileAnalysisResponse(
                success=True,
                analysis=analysis_result
            )
            
        except Exception as e:
            return FileAnalysisResponse(
                success=False,
                error=f"文件分析失败: {str(e)}"
            )
    
    def _mock_file_analysis(self, attachment: ChatAttachment, prompt: Optional[str] = None) -> str:
        """模拟文件分析（实际项目中应该调用AI服务）"""
        if attachment.content:
            # 如果是文本文件，返回内容摘要
            content_preview = attachment.content[:200] + "..." if len(attachment.content) > 200 else attachment.content
            return f"文件分析结果：\n\n文件名：{attachment.name}\n文件类型：{attachment.file_type}\n文件大小：{attachment.file_size} 字节\n\n内容预览：\n{content_preview}\n\n[注意：这是模拟分析结果，实际项目中需要集成AI服务]"
        else:
            return f"文件信息：\n\n文件名：{attachment.name}\n文件类型：{attachment.file_type}\n文件大小：{attachment.file_size} 字节\n\n[注意：这是模拟分析结果，实际项目中需要集成AI服务]"
    
    # -------------------------- AI聊天功能 --------------------------
    
    def send_message(self, request: ChatRequest) -> ChatResponse:
        """发送消息并获取AI回复"""
        try:
            # 获取或创建会话
            session_id = request.session_id
            if not session_id:
                # 创建新会话
                session_data = ChatSessionCreate(
                    user_id=request.user_id,
                    title=request.message[:30] + "..." if len(request.message) > 30 else request.message
                )
                session = self.create_session(session_data, request.user_id)
                session_id = session.session_id
            
            # 保存用户消息
            user_message_data = ChatMessageCreate(
                session_id=session_id,
                role="user",
                content=request.message,
                message_type="text"
            )
            user_message = self.create_message(user_message_data)

            # 更新记忆：加入用户消息
            memory_context_text = None
            if self.memory_service:
                try:
                    self.memory_service.add_message(session_id, "user", request.message)
                    memory_vars = self.memory_service.get_memory_context(session_id)
                    # 将记忆上下文转为简短文本传入模型
                    if isinstance(memory_vars, dict) and "chat_history" in memory_vars:
                        memory_context_text = str(memory_vars["chat_history"])
                except Exception:
                    # 记忆不可用时不影响正常回复
                    memory_context_text = None
            
            # 生成AI回复（这里暂时返回模拟回复）
            combined_context = request.context or memory_context_text
            ai_response = self._generate_ai_response(request.message, combined_context)
            
            # 保存AI回复
            ai_message_data = ChatMessageCreate(
                session_id=session_id,
                role="assistant",
                content=ai_response,
                message_type="text"
            )
            ai_message = self.create_message(ai_message_data)

            # 更新记忆：加入AI回复并尝试保存摘要
            if self.memory_service:
                try:
                    self.memory_service.add_message(session_id, "assistant", ai_response)
                    self.memory_service.save_memory(session_id)
                except Exception:
                    pass
            
            return ChatResponse(
                success=True,
                message=ai_response,
                session_id=session_id,
                message_id=ai_message.id,
                timestamp=ai_message.created_at
            )
            
        except Exception as e:
            return ChatResponse(
                success=False,
                message=f"处理消息失败: {str(e)}",
                session_id=request.session_id or "",
                message_id=0,
                timestamp=datetime.utcnow()
            )
    
    def _generate_ai_response(self, user_message: str, context: Optional[str] = None) -> str:
        """生成AI回复（调用火山引擎 Ark 实现）"""
        # 延迟导入，避免在未安装 SDK 时阻断其它功能
        try:
            from volcenginesdkarkruntime import Ark  # type: ignore
        except Exception as import_err:
            raise Exception(
                "未安装火山引擎 Ark SDK，请先安装: pip install volcengine-ark-runtime"
            ) from import_err

        # 读取配置与环境变量
        api_key = (
            os.environ.get("ARK_API_KEY")
            or os.environ.get("VOLC_ARK_API_KEY")
            or os.environ.get("VOLC_ARK_APIKEY")
            or os.environ.get("VOLCENGINE_ARK_API_KEY")
            or getattr(settings, "ai_api_key", "")
        )
        if not api_key:
            raise Exception("未配置 Ark API Key，请设置 ARK_API_KEY 或 VOLC_ARK_API_KEY 环境变量")

        base_url = (
            os.environ.get("ARK_BASE_URL")
            or os.environ.get("VOLC_ARK_BASE_URL")
            or getattr(settings, "ai_api_url", None)
            or "https://ark.cn-beijing.volces.com/api/v3"
        )

        model = (
            os.environ.get("ARK_MODEL")
            or os.environ.get("VOLC_ARK_MODEL")
            or getattr(settings, "ai_model", None)
            or "doubao-seed-1-6-250615"
        )

        # 组装消息（文本为主；若未来有图片，可扩展 content 列表）
        content_items: list[dict] = [{"type": "text", "text": user_message}]
        if context:
            content_items.append({"type": "text", "text": f"[上下文]\n{context}"})

        messages = [
            {
                "role": "user",
                "content": content_items,
            }
        ]

        try:
            client = Ark(base_url=base_url, api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                extra_headers={"x-is-encrypted": "true"},
            )

            # 兼容不同返回结构，尽最大可能提取文本
            text = None
            try:
                choices = getattr(response, "choices", None)
                if choices:
                    first = choices[0]
                    # 尝试多种结构提取
                    if isinstance(first, dict):
                        # 可能是 dict 结构
                        msg = first.get("message") or {}
                        parts = msg.get("content") or []
                        text_parts = []
                        for p in parts:
                            if isinstance(p, dict) and p.get("type") == "text":
                                text_parts.append(p.get("text", ""))
                        text = "".join(text_parts) if text_parts else msg.get("content")
                    else:
                        # 对象结构，尝试属性访问
                        msg = getattr(first, "message", None)
                        if msg is not None:
                            parts = getattr(msg, "content", None)
                            if isinstance(parts, list):
                                text_parts = []
                                for p in parts:
                                    if isinstance(p, dict) and p.get("type") == "text":
                                        text_parts.append(p.get("text", ""))
                                text = "".join(text_parts)
                            elif isinstance(parts, str):
                                text = parts
            except Exception:
                pass

            if not text:
                # 最后兜底为字符串化
                text = str(response)

            return text.strip() if isinstance(text, str) else ""
        except Exception as e:
            raise Exception(f"调用火山引擎 Ark 失败: {str(e)}")
    
    # -------------------------- 流式响应 --------------------------
    
    def _stream_ai_response(self, user_message: str, context: Optional[str] = None):
        """直接从 Ark 使用流式输出，逐段产出文本"""
        try:
            from volcenginesdkarkruntime import Ark  # type: ignore
        except Exception as import_err:
            raise Exception(
                "未安装火山引擎 Ark SDK，请先安装: pip install volcengine-ark-runtime"
            ) from import_err

        api_key = (
            os.environ.get("ARK_API_KEY")
            or os.environ.get("VOLC_ARK_API_KEY")
            or os.environ.get("VOLC_ARK_APIKEY")
            or os.environ.get("VOLCENGINE_ARK_API_KEY")
            or getattr(settings, "ai_api_key", "")
        )
        if not api_key:
            raise Exception("未配置 Ark API Key，请设置 ARK_API_KEY 或 VOLC_ARK_API_KEY 环境变量")

        base_url = (
            os.environ.get("ARK_BASE_URL")
            or os.environ.get("VOLC_ARK_BASE_URL")
            or getattr(settings, "ai_api_url", None)
            or "https://ark.cn-beijing.volces.com/api/v3"
        )

        model = (
            os.environ.get("ARK_MODEL")
            or os.environ.get("VOLC_ARK_MODEL")
            or getattr(settings, "ai_model", None)
            or "doubao-seed-1-6-250615"
        )

        # 组装消息
        content_items: list[dict] = [{"type": "text", "text": user_message}]
        if context:
            content_items.append({"type": "text", "text": f"[上下文]\n{context}"})

        messages = [
            {
                "role": "user",
                "content": content_items,
            }
        ]

        client = Ark(base_url=base_url, api_key=api_key)

        # 优先尝试官方流式接口
        try:
            # 常见模式：传 stream=True 返回迭代器/生成器
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,  # type: ignore
                extra_headers={"x-is-encrypted": "true"},
            )

            for event in stream:
                # 兼容多种事件结构，尽最大可能抽取增量文本
                delta_text = None
                try:
                    # dict 结构
                    if isinstance(event, dict):
                        choices = event.get("choices")
                        if choices:
                            first = choices[0]
                            delta = first.get("delta") or {}
                            # OpenAI 风格：delta -> content 或 content 列表
                            if isinstance(delta, dict):
                                content = delta.get("content")
                                if isinstance(content, list):
                                    parts = []
                                    for p in content:
                                        if isinstance(p, dict) and p.get("type") == "text":
                                            parts.append(p.get("text", ""))
                                    delta_text = "".join(parts) if parts else None
                                elif isinstance(content, str):
                                    delta_text = content
                    else:
                        # 对象结构
                        choices = getattr(event, "choices", None)
                        if choices:
                            first = choices[0]
                            delta = getattr(first, "delta", None)
                            if delta is not None:
                                content = getattr(delta, "content", None)
                                if isinstance(content, list):
                                    parts = []
                                    for p in content:
                                        if isinstance(p, dict) and p.get("type") == "text":
                                            parts.append(p.get("text", ""))
                                    delta_text = "".join(parts) if parts else None
                                elif isinstance(content, str):
                                    delta_text = content
                except Exception:
                    delta_text = None

                if delta_text:
                    yield delta_text

            return
        except Exception:
            # 回退：如果 SDK/参数不支持流式，就用非流式降级并手动拆分
            full_text = self._generate_ai_response(user_message, context)
            # 以较细粒度切分，尽可能拟真流式
            for token in full_text.split():
                yield token + " "

    def send_message_stream(self, request: ChatRequest):
        """流式发送消息（生成器）"""
        try:
            # 获取或创建会话
            session_id = request.session_id
            if not session_id:
                session_data = ChatSessionCreate(
                    user_id=request.user_id,
                    title=request.message[:30] + "..." if len(request.message) > 30 else request.message
                )
                session = self.create_session(session_data, request.user_id)
                session_id = session.session_id
            
            # 保存用户消息
            user_message_data = ChatMessageCreate(
                session_id=session_id,
                role="user",
                content=request.message,
                message_type="text"
            )
            user_message = self.create_message(user_message_data)
            
            # 准备记忆上下文
            memory_context_text = None
            if self.memory_service:
                try:
                    self.memory_service.add_message(session_id, "user", request.message)
                    memory_vars = self.memory_service.get_memory_context(session_id)
                    if isinstance(memory_vars, dict) and "chat_history" in memory_vars:
                        memory_context_text = str(memory_vars["chat_history"])
                except Exception:
                    memory_context_text = None

            # 生成流式AI回复
            combined_context = request.context or memory_context_text

            # 真正流式产出
            final_text_parts: list[str] = []
            for delta in self._stream_ai_response(request.message, combined_context):
                final_text_parts.append(delta)
                yield {
                    "content": delta,
                    "session_id": session_id,
                    "message_id": user_message.id
                }
            
            # 保存完整的AI回复
            ai_response = "".join(final_text_parts).strip()
            ai_message_data = ChatMessageCreate(
                session_id=session_id,
                role="assistant",
                content=ai_response,
                message_type="text"
            )
            ai_message = self.create_message(ai_message_data)

            # 更新记忆并保存摘要（异步，不阻塞流关闭）
            if self.memory_service:
                def _bg_save():
                    try:
                        self.memory_service.add_message(session_id, "assistant", ai_response)
                        self.memory_service.save_memory(session_id)
                    except Exception:
                        pass
                threading.Thread(target=_bg_save, daemon=True).start()
            
        except Exception as e:
            yield {
                "content": f"处理消息失败: {str(e)}",
                "session_id": request.session_id or "",
                "message_id": 0
            }
    
    # -------------------------- 设置管理 --------------------------
    
    def get_settings(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取聊天设置"""
        query = self.db.query(ChatSettings)
        
        if user_id:
            query = query.filter(ChatSettings.user_id == user_id)
        else:
            query = query.filter(ChatSettings.user_id.is_(None))  # 全局设置
        
        settings = query.all()
        
        # 转换为字典格式
        result = {}
        for setting in settings:
            result[setting.settings_key] = setting.settings_value
        
        return result
    
    def update_settings(self, settings_data: ChatSettingsCreate, user_id: Optional[str] = None) -> bool:
        """更新聊天设置"""
        try:
            # 查找现有设置
            existing_setting = self.db.query(ChatSettings).filter(
                and_(
                    ChatSettings.settings_key == settings_data.settings_key,
                    ChatSettings.user_id == (user_id or settings_data.user_id)
                )
            ).first()
            
            if existing_setting:
                # 更新现有设置
                existing_setting.settings_value = settings_data.settings_value
                existing_setting.updated_at = datetime.utcnow()
            else:
                # 创建新设置
                new_setting = ChatSettings(
                    user_id=user_id or settings_data.user_id,
                    settings_key=settings_data.settings_key,
                    settings_value=settings_data.settings_value
                )
                self.db.add(new_setting)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新设置失败: {str(e)}")
    
    # -------------------------- 搜索功能 --------------------------
    
    def search_conversations(self, query: str, user_id: Optional[str] = None, limit: int = 20) -> List[ChatSession]:
        """搜索会话"""
        search_query = self.db.query(ChatSession).filter(
            and_(
                ChatSession.is_active == True,
                ChatSession.title.contains(query)
            )
        )
        
        if user_id:
            search_query = search_query.filter(ChatSession.user_id == user_id)
        
        return search_query.order_by(desc(ChatSession.updated_at)).limit(limit).all()
    
    def export_conversation(self, session_id: str, format: str = "json") -> str:
        """导出会话"""
        session = self.get_session(session_id)
        if not session:
            raise Exception("会话不存在")
        
        messages = self.get_session_messages(session_id)
        
        if format == "json":
            data = {
                "session": {
                    "id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                },
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            }
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        elif format == "txt":
            lines = [f"会话: {session.title}", f"创建时间: {session.created_at}", ""]
            for msg in messages:
                role_name = "用户" if msg.role == "user" else "AI助手"
                lines.append(f"[{role_name}] {msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(msg.content)
                lines.append("")
            return "\n".join(lines)
        
        else:
            raise Exception(f"不支持的导出格式: {format}")
