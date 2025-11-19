"""
会话记忆服务（无 LangChain 依赖）
"""
import os
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.db_models import ChatSession, ChatMessage
from app.config import settings


class VolcengineLLMWrapper:
    """火山引擎 LLM 包装器，用于生成摘要"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def __call__(self, prompt: str) -> str:
        """调用火山引擎 API 生成摘要"""
        try:
            from volcenginesdkarkruntime import Ark
            
            client = Ark(base_url=self.base_url, api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": "你是一个专业的对话摘要助手。请简洁地总结对话内容，保留关键信息。"}]
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ],
                extra_headers={"x-is-encrypted": "true"},
            )
            
            # 提取响应文本
            text = None
            try:
                choices = getattr(response, "choices", None)
                if choices:
                    first = choices[0]
                    if isinstance(first, dict):
                        msg = first.get("message") or {}
                        parts = msg.get("content") or []
                        text_parts = []
                        for p in parts:
                            if isinstance(p, dict) and p.get("type") == "text":
                                text_parts.append(p.get("text", ""))
                        text = "".join(text_parts) if text_parts else msg.get("content")
                    else:
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
                text = str(response)
            
            return text.strip() if isinstance(text, str) else ""
        except Exception as e:
            raise Exception(f"调用火山引擎 API 生成摘要失败: {str(e)}")


class MemoryService:
    """会话记忆管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        # 内存缓存：session_id -> {"history": List[Tuple[str, str]], "summary": Optional[str]}
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # 读取配置
        api_key = (
            os.environ.get("ARK_API_KEY")
            or os.environ.get("VOLC_ARK_API_KEY")
            or os.environ.get("VOLC_ARK_APIKEY")
            or os.environ.get("VOLCENGINE_ARK_API_KEY")
            or getattr(settings, "ai_api_key", "")
        )
        
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
        
        if not api_key:
            raise Exception("未配置 Ark API Key，无法使用记忆功能")
        
        # 创建 LLM 包装器
        self.llm = VolcengineLLMWrapper(api_key, base_url, model)
    
    def _format_messages_for_prompt(self, messages: List[Tuple[str, str]], max_chars: int = 2000) -> str:
        """将消息列表格式化为用于摘要的文本，限制长度"""
        lines: List[str] = []
        length = 0
        for role, content in messages:
            line = f"{role}: {content}"
            if length + len(line) > max_chars:
                break
            lines.append(line)
            length += len(line)
        return "\n".join(lines)

    def _summarize(self, prior_summary: Optional[str], recent_messages: List[Tuple[str, str]]) -> str:
        """调用 LLM 生成或更新摘要"""
        messages_text = self._format_messages_for_prompt(recent_messages)
        if prior_summary:
            prompt = (
                "下面是之前对话的摘要与最近的几条对话，请更新摘要，保持精简且保留关键信息：\n\n"
                f"[之前的摘要]\n{prior_summary}\n\n"
                f"[最近对话]\n{messages_text}\n\n"
                "请输出更新后的摘要："
            )
        else:
            prompt = (
                "请对下面的对话内容进行简洁摘要，保留关键信息与结论：\n\n"
                f"[对话]\n{messages_text}\n\n"
                "请输出摘要："
            )
        try:
            return self.llm(prompt)
        except Exception:
            # 出现问题时返回之前的摘要或空字符串，避免打断主流程
            return prior_summary or ""

    def get_or_create_memory(self, session_id: str) -> Dict[str, Any]:
        """获取或创建会话记忆结构"""
        if session_id in self._memory_cache:
            return self._memory_cache[session_id]
        
        # 从数据库加载会话
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
        
        if not session:
            raise Exception(f"会话不存在: {session_id}")
        
        # 加载最近的消息（用于上下文与后续摘要）
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()

        history: List[Tuple[str, str]] = []
        for msg in reversed(messages):
            if msg.role in ("user", "assistant"):
                history.append((msg.role, msg.content))

        memory_struct = {
            "history": history,                 # List[Tuple[role, content]]
            "summary": session.memory_summary,  # Optional[str]
        }
        self._memory_cache[session_id] = memory_struct
        return memory_struct
    
    def save_memory(self, session_id: str) -> bool:
        """保存会话记忆到数据库"""
        try:
            if session_id not in self._memory_cache:
                return False
            
            memory_struct = self._memory_cache[session_id]

            # 取最近若干条用于摘要的消息
            recent_messages: List[Tuple[str, str]] = memory_struct.get("history", [])[-10:]
            prior_summary: Optional[str] = memory_struct.get("summary")

            # 生成并更新摘要
            summary = self._summarize(prior_summary, recent_messages)
            memory_struct["summary"] = summary
            
            # 更新数据库
            session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            
            if session:
                session.memory_summary = summary
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            self.db.rollback()
            raise Exception(f"保存记忆失败: {str(e)}")
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息到记忆"""
        memory_struct = self.get_or_create_memory(session_id)
        history: List[Tuple[str, str]] = memory_struct.get("history", [])
        history.append((role, content))
        # 限制历史长度，避免占用过多内存
        if len(history) > 50:
            del history[0 : len(history) - 50]
        memory_struct["history"] = history
    
    def get_memory_context(self, session_id: str) -> Dict[str, Any]:
        """获取记忆上下文（用于生成提示）"""
        try:
            memory_struct = self.get_or_create_memory(session_id)
            # 返回给上游的上下文统一为 dict，包含：
            # - chat_history: 供模型参考的简短文本（包含摘要+最近对话）
            summary = memory_struct.get("summary")
            recent = memory_struct.get("history", [])[-6:]
            history_text = self._format_messages_for_prompt(recent, max_chars=1200)
            if summary:
                combined = f"摘要：{summary}\n\n最近对话：\n{history_text}"
            else:
                combined = history_text
            return {"chat_history": combined}
        except Exception:
            return {}
    
    def clear_memory(self, session_id: str) -> None:
        """清除会话记忆"""
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
        
        # 清除数据库中的记忆摘要
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if session:
            session.memory_summary = None
            self.db.commit()

