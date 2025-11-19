"""
日志配置和工具
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json

class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
            
        return json.dumps(log_entry, ensure_ascii=False)

class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger("request")
    
    def log_request(self, method: str, url: str, status_code: int, 
                   duration: float, user_id: Optional[str] = None,
                   request_id: Optional[str] = None):
        """记录请求日志"""
        self.logger.info(
            f"{method} {url} - {status_code}",
            extra={
                "method": method,
                "url": url,
                "status_code": status_code,
                "duration": duration,
                "user_id": user_id,
                "request_id": request_id
            }
        )

class BusinessLogger:
    """业务日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger("business")
    
    def log_file_upload(self, filename: str, file_size: int, user_id: Optional[str] = None):
        """记录文件上传日志"""
        self.logger.info(
            f"文件上传: {filename}",
            extra={
                "event": "file_upload",
                "filename": filename,
                "file_size": file_size,
                "user_id": user_id
            }
        )
    
    def log_review_start(self, file_id: int, task_id: str, user_id: Optional[str] = None):
        """记录审查开始日志"""
        self.logger.info(
            f"开始审查文件: {file_id}",
            extra={
                "event": "review_start",
                "file_id": file_id,
                "task_id": task_id,
                "user_id": user_id
            }
        )
    
    def log_review_complete(self, file_id: int, task_id: str, 
                           violations_count: int, user_id: Optional[str] = None):
        """记录审查完成日志"""
        self.logger.info(
            f"审查完成: {file_id}, 发现 {violations_count} 处违规",
            extra={
                "event": "review_complete",
                "file_id": file_id,
                "task_id": task_id,
                "violations_count": violations_count,
                "user_id": user_id
            }
        )

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """设置日志配置"""
    
    # 创建日志目录
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # 设置特定日志器级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 全局日志记录器实例
request_logger = RequestLogger()
business_logger = BusinessLogger()
