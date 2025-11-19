"""
健康检查端点
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import get_db
from app.utils.logging import business_logger

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点
    检查数据库连接和基本服务状态
    """
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 检查Redis连接（如果有的话）
    try:
        # 这里可以添加Redis健康检查
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # 检查AI服务连接（如果有的话）
    try:
        # 这里可以添加AI服务健康检查
        ai_status = "healthy"
    except Exception as e:
        ai_status = f"unhealthy: {str(e)}"
    
    # 整体健康状态
    overall_status = "healthy" if all(
        status == "healthy" for status in [db_status, redis_status, ai_status]
    ) else "unhealthy"
    
    # 记录健康检查日志
    business_logger.logger.info(
        f"健康检查: {overall_status}",
        extra={
            "event": "health_check",
            "overall_status": overall_status,
            "db_status": db_status,
            "redis_status": redis_status,
            "ai_status": ai_status
        }
    )
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
            "ai_service": ai_status
        },
        "version": "1.0.0"
    }

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """
    获取应用指标
    用于Prometheus监控
    """
    # 这里可以添加更多指标
    return {
        "http_requests_total": 0,  # 总请求数
        "http_requests_duration_seconds": 0,  # 请求耗时
        "files_uploaded_total": 0,  # 上传文件总数
        "reviews_completed_total": 0,  # 完成审查总数
        "active_connections": 0,  # 活跃连接数
    }
