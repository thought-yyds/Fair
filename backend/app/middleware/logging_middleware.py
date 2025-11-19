"""
日志中间件
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging import request_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取用户ID（如果有的话）
        user_id = getattr(request.state, 'user_id', None)
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        duration = time.time() - start_time
        
        # 记录请求日志
        request_logger.log_request(
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration,
            user_id=user_id,
            request_id=request_id
        )
        
        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id
        
        return response
