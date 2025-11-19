"""
安全中间件
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import hashlib
import hmac

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS头（仅HTTPS）
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP头
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_records(current_time)
        
        # 检查限流
        if self._is_rate_limited(client_ip, current_time):
            return StarletteResponse(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": str(self.period)}
            )
        
        # 记录请求
        self._record_request(client_ip, current_time)
        
        response = await call_next(request)
        return response
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否超过限流"""
        if client_ip not in self.clients:
            return False
        
        # 计算时间窗口内的请求数
        window_start = current_time - self.period
        requests = [req_time for req_time in self.clients[client_ip] if req_time > window_start]
        
        return len(requests) >= self.calls
    
    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        self.clients[client_ip].append(current_time)
    
    def _cleanup_expired_records(self, current_time: float):
        """清理过期记录"""
        window_start = current_time - self.period
        for client_ip in list(self.clients.keys()):
            self.clients[client_ip] = [
                req_time for req_time in self.clients[client_ip] 
                if req_time > window_start
            ]
            if not self.clients[client_ip]:
                del self.clients[client_ip]

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 检查请求大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 100 * 1024 * 1024:  # 100MB
            return StarletteResponse(
                content="Request too large",
                status_code=413
            )
        
        # 检查User-Agent
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) > 500:
            return StarletteResponse(
                content="Invalid request",
                status_code=400
            )
        
        # 检查Host头
        host = request.headers.get("host", "")
        if not host or len(host) > 255:
            return StarletteResponse(
                content="Invalid host",
                status_code=400
            )
        
        response = await call_next(request)
        return response

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF保护中间件"""
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key.encode()
    
    async def dispatch(self, request: Request, call_next):
        # 跳过GET、HEAD、OPTIONS请求
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            response = await call_next(request)
            return response
        
        # 检查CSRF令牌
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return StarletteResponse(
                content="CSRF token missing",
                status_code=403
            )
        
        # 验证CSRF令牌
        if not self._verify_csrf_token(csrf_token, request):
            return StarletteResponse(
                content="Invalid CSRF token",
                status_code=403
            )
        
        response = await call_next(request)
        return response
    
    def _verify_csrf_token(self, token: str, request: Request) -> bool:
        """验证CSRF令牌"""
        try:
            # 生成期望的令牌
            expected_token = self._generate_csrf_token(request)
            return hmac.compare_digest(token, expected_token)
        except Exception:
            return False
    
    def _generate_csrf_token(self, request: Request) -> str:
        """生成CSRF令牌"""
        # 使用请求路径和时间戳生成令牌
        data = f"{request.url.path}{int(time.time() / 3600)}"  # 1小时有效期
        return hmac.new(
            self.secret_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
