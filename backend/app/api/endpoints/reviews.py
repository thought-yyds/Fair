from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
from typing import Optional

from app.models import get_db
from app.models.db_models import Article, Sentence, Annotation
from app.services.review_service import start_review_task

router = APIRouter(tags=["审查管理"])


@router.post("/start/{article_id}", summary="开始审查文档")
def start_review(
        article_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """启动文档审查任务"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"文档ID {article_id} 不存在")

    if article.status in ["审查中", "已审查"]:
        raise HTTPException(status_code=400, detail=f"文档当前状态为「{article.status}」，无法重复启动审查")

    article.status = "审查中"
    article.review_progress = 0
    db.commit()
    db.refresh(article)

    background_tasks.add_task(start_review_task, article_id=article_id, db=db)

    return {"success": True, "msg": f"文档审查已启动", "data": None}


@router.get("/progress/{article_id}", summary="获取审查进度（单次查询）")
def get_review_progress(
        article_id: int,
        db: Session = Depends(get_db)
):
    """单次查询审查进度（兼容原有逻辑）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"文档ID {article_id} 不存在")

    return {"success": True, "data": {
        "progress": article.review_progress,
        "status": article.status,
        "risk_level": article.risk_level
    }}


@router.get("/progress/sse/{article_id}", summary="SSE实时推送审查进度")
async def review_progress_sse(
        article_id: int,
        db: Session = Depends(get_db),
        response: Response = Response()
):
    """通过SSE实时推送进度，前端无需轮询"""
    # 验证文档存在
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"文档ID {article_id} 不存在")

    # 设置SSE响应头
    response.headers["Content-Type"] = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"  # 禁用反向代理缓冲

    # 异步生成进度事件
    async def event_generator():
        last_progress = -1  # 记录上一次推送的进度，避免重复推送
        while True:
            # 刷新数据库会话，获取最新进度
            db.refresh(article)
            current_progress = article.review_progress
            current_status = article.status

            # 进度有变化才推送（避免重复数据）
            if current_progress != last_progress:
                last_progress = current_progress
                # SSE格式：data: {进度}\n\n
                yield f"data: {current_progress}\n\n"

            # 审查完成（进度100%或状态为已审查），推送完成信号并退出
            if current_progress >= 100 or current_status == "已审查":
                yield "data: complete\n\n"
                break

            # 1秒检查一次进度（可根据需求调整频率）
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), headers=response.headers)


@router.get("/detail/{article_id}", summary="获取审查详情")
def get_review_detail(
        article_id: int,
        db: Session = Depends(get_db)
):
    """获取审查完成后的详细结果（包含违规句子及标注）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"文档ID {article_id} 不存在")

    if article.status != "已审查":
        raise HTTPException(status_code=400, detail="文档尚未完成审查")

    # 关联查询违规句子及对应的标注内容
    violation_sentences = db.query(
        Sentence,
        Annotation.content
    ).outerjoin(
        Annotation,
        Sentence.annotation_id == Annotation.id
    ).filter(
        Sentence.article_id == article_id,
        Sentence.has_problem == True
    ).all()

    # 构建简洁的返回数据（移除无关字段）
    violation_details = [
        {
            "id": sentence.id,
            "content": sentence.content,
            "annotation_content": annotation_content or "未定义违规描述"
            # 移除冗余字段：annotation_id（前端无需关心ID，只需显示描述）
        }
        for sentence, annotation_content in violation_sentences
    ]

    return {"success": True, "data": {
        "article_name": article.name,  # 只返回必要的文档信息
        "review_time": article.review_time,
        "risk_level": article.risk_level,
        "total_violation": len(violation_details),
        "violation_sentences": violation_details
    }}
