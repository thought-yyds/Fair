"""
聊天API端点
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import json

from app.models.schemas import (
    ChatSessionCreate, ChatSessionSchema, ChatMessageSchema,
    ChatRequest, ChatResponse, ChatHistoryResponse,
    FileUploadResponse, FileAnalysisRequest, FileAnalysisResponse,
    ChatSettingsCreate, ChatSettingsSchema
)
from app.services.chat_service import ChatService
from app.models import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


# -------------------------- 会话管理 --------------------------

@router.post("/conversations", response_model=ChatSessionSchema)
async def create_conversation(
    session_data: ChatSessionCreate,
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: Session = Depends(get_db)
):
    """创建新的聊天会话"""
    try:
        chat_service = ChatService(db)
        session = chat_service.create_session(session_data, user_id)
        
        # 添加消息数量
        message_count = chat_service.get_message_count(session.session_id)
        session_dict = session.__dict__.copy()
        session_dict['message_count'] = message_count
        
        return ChatSessionSchema(**session_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversations", response_model=List[ChatSessionSchema])
async def get_conversations(
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取用户的会话列表"""
    try:
        chat_service = ChatService(db)
        sessions = chat_service.get_user_sessions(user_id, limit)
        
        # 为每个会话添加消息数量
        result = []
        for session in sessions:
            message_count = chat_service.get_message_count(session.session_id)
            session_dict = session.__dict__.copy()
            session_dict['message_count'] = message_count
            result.append(ChatSessionSchema(**session_dict))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ChatSessionSchema)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """获取特定会话信息"""
    try:
        chat_service = ChatService(db)
        session = chat_service.get_session(conversation_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 添加消息数量
        message_count = chat_service.get_message_count(session.session_id)
        session_dict = session.__dict__.copy()
        session_dict['message_count'] = message_count
        
        return ChatSessionSchema(**session_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/conversations/{conversation_id}")
async def update_conversation_title(
    conversation_id: str,
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    """更新会话标题"""
    try:
        chat_service = ChatService(db)
        success = chat_service.update_session_title(conversation_id, title)
        
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"success": True, "message": "标题更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """删除会话"""
    try:
        chat_service = ChatService(db)
        success = chat_service.delete_session(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"success": True, "message": "会话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------- 消息管理 --------------------------

@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessageSchema])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取特定会话的消息列表"""
    try:
        chat_service = ChatService(db)
        messages = chat_service.get_session_messages(conversation_id, limit)
        
        return [ChatMessageSchema(**msg.__dict__) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """发送消息并获取AI回复"""
    try:
        chat_service = ChatService(db)
        response = chat_service.send_message(request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """流式发送消息"""
    try:
        chat_service = ChatService(db)
        
        def generate():
            try:
                for chunk in chat_service.send_message_stream(request):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_chunk = {
                    "content": f"错误: {str(e)}",
                    "session_id": request.session_id or "",
                    "message_id": 0
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                # 禁用反向代理（如 Nginx）的缓冲，确保真正流式
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------- 文件上传和分析 --------------------------

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    message_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """上传文件"""
    try:
        # 检查文件大小（限制为10MB）
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            return FileUploadResponse(
                success=False,
                error="文件大小超过10MB限制"
            )
        
        # 重置文件指针
        await file.seek(0)
        
        chat_service = ChatService(db)
        response = chat_service.upload_file(file, session_id, message_id)
        
        return response
    except Exception as e:
        return FileUploadResponse(
            success=False,
            error=f"文件上传失败: {str(e)}"
        )


@router.post("/analyze", response_model=FileAnalysisResponse)
async def analyze_file(
    request: FileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """分析文件内容"""
    try:
        chat_service = ChatService(db)
        response = chat_service.analyze_file(request)
        
        return response
    except Exception as e:
        return FileAnalysisResponse(
            success=False,
            error=f"文件分析失败: {str(e)}"
        )


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: str,
    db: Session = Depends(get_db)
):
    """下载附件"""
    try:
        chat_service = ChatService(db)
        attachment = chat_service.get_attachment(attachment_id)
        
        if not attachment:
            raise HTTPException(status_code=404, detail="附件不存在")
        
        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=attachment.file_path,
            filename=attachment.name,
            media_type=attachment.file_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------- 设置管理 --------------------------

@router.get("/settings")
async def get_chat_settings(
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: Session = Depends(get_db)
):
    """获取聊天设置"""
    try:
        chat_service = ChatService(db)
        settings = chat_service.get_settings(user_id)
        
        return {"success": True, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings")
async def update_chat_settings(
    settings_data: ChatSettingsCreate,
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: Session = Depends(get_db)
):
    """更新聊天设置"""
    try:
        chat_service = ChatService(db)
        success = chat_service.update_settings(settings_data, user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="更新设置失败")
        
        return {"success": True, "message": "设置更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------- 搜索和导出 --------------------------

@router.get("/search")
async def search_conversations(
    q: str = Query(..., description="搜索关键词"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """搜索会话"""
    try:
        chat_service = ChatService(db)
        sessions = chat_service.search_conversations(q, user_id, limit)
        
        # 为每个会话添加消息数量
        result = []
        for session in sessions:
            message_count = chat_service.get_message_count(session.session_id)
            session_dict = session.__dict__.copy()
            session_dict['message_count'] = message_count
            result.append(ChatSessionSchema(**session_dict))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = Query("json", regex="^(json|txt)$", description="导出格式"),
    db: Session = Depends(get_db)
):
    """导出会话"""
    try:
        chat_service = ChatService(db)
        content = chat_service.export_conversation(conversation_id, format)
        
        if format == "json":
            media_type = "application/json"
            filename = f"conversation_{conversation_id}.json"
        else:
            media_type = "text/plain"
            filename = f"conversation_{conversation_id}.txt"
        
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
