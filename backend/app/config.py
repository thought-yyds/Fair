"""
应用配置管理
"""
import os
from typing import List, Optional
from functools import lru_cache
from pathlib import Path

# 尝试导入 pydantic-settings，如果失败则使用兼容性方案
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
    try:
        # pydantic v2 settings config (if available)
        from pydantic_settings import SettingsConfigDict  # type: ignore
    except Exception:
        SettingsConfigDict = None  # type: ignore
    PYDANTIC_V2 = True
except ImportError:
    # 兼容性方案：使用 pydantic v1 的 BaseSettings
    try:
        from pydantic import BaseSettings, validator
        PYDANTIC_V2 = False
    except ImportError:
        # 如果都导入失败，说明是 Pydantic v2 但没有安装 pydantic-settings
        # 使用环境变量的简单方案
        print("警告: 无法导入 pydantic-settings，使用环境变量配置")
        BaseSettings = None
        PYDANTIC_V2 = False

# 如果无法导入 BaseSettings，创建一个简单的配置类
if BaseSettings is None:
    class BaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

class Settings(BaseSettings):
    """应用配置类"""
    
    def __init__(self, **kwargs):
        if BaseSettings is None:
            # 简单配置类，直接从环境变量读取
            self.app_name = os.getenv("APP_NAME", "Fair Platform")
            self.version = os.getenv("VERSION", "1.0.0")
            self.environment = os.getenv("ENVIRONMENT", "development")
            self.debug = os.getenv("DEBUG", "true").lower() == "true"
            self.secret_key = os.getenv("SECRET_KEY", "set-secret-key-in-env")
            self.database_url = os.getenv("DATABASE_URL", "mysql+pymysql://USER:PASSWORD@HOST:PORT/DBNAME")
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
            self.cors_methods = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
            self.cors_headers = os.getenv("CORS_HEADERS", "*").split(",")
            self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
            self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))
            self.allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", "txt,pdf,doc,docx,xls,xlsx,ppt,pptx").split(",")
            self.log_level = os.getenv("LOG_LEVEL", "INFO")
            self.worker_processes = int(os.getenv("WORKER_PROCESSES", "4"))
            self.worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))
            self.keepalive_timeout = int(os.getenv("KEEPALIVE_TIMEOUT", "65"))
            self.client_max_body_size = os.getenv("CLIENT_MAX_BODY_SIZE", "100M")
        else:
            # 兼容历史环境变量名到现有字段
            if "uploads_dir" in os.environ and "upload_dir" not in kwargs:
                kwargs["upload_dir"] = os.environ.get("uploads_dir")
            if "temp_reports_dir" in os.environ and "temp_dir" not in kwargs:
                kwargs["temp_dir"] = os.environ.get("temp_reports_dir")
            if "allowed_origins" in os.environ and "cors_origins" not in kwargs:
                kwargs["cors_origins"] = os.environ.get("allowed_origins")
            super().__init__(**kwargs)
    
    # 基础配置
    app_name: str = "Fair Platform"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    database_url: str = "mysql+pymysql://USER:PASSWORD@HOST:PORT/DBNAME"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fair"
    db_user: str = "fair_user"
    db_password: str = "fair_password"
    
    # 数据库连接池配置
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # 缓存配置
    cache_ttl: int = 3600
    cache_max_size: int = 1000
    
    # AI服务配置
    ai_api_key: str = ""
    ai_api_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ai_model: str = "doubao-seed-1-6-250615"
    ai_max_tokens: int = 4000
    ai_processing_timeout: int = 60
    
    # 安全配置
    secret_key: str = "set-secret-key-in-env"
    jwt_secret: str = "set-jwt-secret-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # 文件存储配置
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp_reports"
    max_file_size: int = 104857600  # 100MB
    allowed_extensions: List[str] = ["pdf", "docx", "xlsx", "pptx", "txt"]
    
    # 文件处理配置
    file_processing_timeout: int = 300
    max_concurrent_uploads: int = 5
    max_concurrent_reviews: int = 3
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    log_format: str = "json"
    
    # 监控配置
    prometheus_enabled: bool = True
    grafana_enabled: bool = True
    metrics_enabled: bool = True
    
    # 限流配置
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    upload_rate_limit: int = 10
    upload_rate_window: int = 60
    
    # CORS配置
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: List[str] = ["*"]
    
    # 安全头配置
    security_headers_enabled: bool = True
    hsts_enabled: bool = True
    csp_enabled: bool = True
    
    # 邮件配置（可选）
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # 通知配置（可选）
    webhook_url: Optional[str] = None
    notification_enabled: bool = False
    
    # 备份配置
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"  # 每天凌晨2点
    backup_retention_days: int = 30
    
    # 性能配置
    worker_processes: int = 4
    worker_connections: int = 1000
    keepalive_timeout: int = 65
    client_max_body_size: str = "100M"
    
    # 只有在使用 Pydantic 时才添加验证器
    if PYDANTIC_V2 and BaseSettings is not None:
        @field_validator("cors_origins", mode="before")
        @classmethod
        def parse_cors_origins(cls, v):
            if isinstance(v, str):
                return [origin.strip() for origin in v.split(",")]
            return v
        
        @field_validator("cors_methods", mode="before")
        @classmethod
        def parse_cors_methods(cls, v):
            if isinstance(v, str):
                return [method.strip() for method in v.split(",")]
            return v
        
        @field_validator("cors_headers", mode="before")
        @classmethod
        def parse_cors_headers(cls, v):
            if isinstance(v, str):
                return [header.strip() for header in v.split(",")]
            return v
        
        @field_validator("allowed_extensions", mode="before")
        @classmethod
        def parse_allowed_extensions(cls, v):
            if isinstance(v, str):
                return [ext.strip() for ext in v.split(",")]
            return v
        
        @field_validator("environment")
        @classmethod
        def validate_environment(cls, v):
            allowed_envs = ["development", "staging", "production"]
            if v not in allowed_envs:
                raise ValueError(f"环境必须是以下之一: {allowed_envs}")
            return v
        
        @field_validator("log_level")
        @classmethod
        def validate_log_level(cls, v):
            allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if v.upper() not in allowed_levels:
                raise ValueError(f"日志级别必须是以下之一: {allowed_levels}")
            return v.upper()
    elif not PYDANTIC_V2 and BaseSettings is not None:
        @validator("cors_origins", pre=True)
        def parse_cors_origins(cls, v):
            if isinstance(v, str):
                return [origin.strip() for origin in v.split(",")]
            return v
        
        @validator("cors_methods", pre=True)
        def parse_cors_methods(cls, v):
            if isinstance(v, str):
                return [method.strip() for method in v.split(",")]
            return v
        
        @validator("cors_headers", pre=True)
        def parse_cors_headers(cls, v):
            if isinstance(v, str):
                return [header.strip() for header in v.split(",")]
            return v
        
        @validator("allowed_extensions", pre=True)
        def parse_allowed_extensions(cls, v):
            if isinstance(v, str):
                return [ext.strip() for ext in v.split(",")]
            return v
        
        @validator("environment")
        def validate_environment(cls, v):
            allowed_envs = ["development", "staging", "production"]
            if v not in allowed_envs:
                raise ValueError(f"环境必须是以下之一: {allowed_envs}")
            return v
        
        @validator("log_level")
        def validate_log_level(cls, v):
            allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if v.upper() not in allowed_levels:
                raise ValueError(f"日志级别必须是以下之一: {allowed_levels}")
            return v.upper()
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"
    
    @property
    def database_url_safe(self) -> str:
        """安全的数据库URL（隐藏密码）"""
        if "@" in self.database_url:
            return self.database_url.split("@")[0].split("://")[0] + "://***@***"
        return self.database_url

    # -------------------- 兼容性属性（提供历史大写名称） --------------------
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return self.cors_origins

    @property
    def DEBUG(self) -> bool:
        return self.debug

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def ALLOWED_EXTENSIONS(self) -> List[str]:
        return self.allowed_extensions

    @property
    def UPLOADS_DIR(self) -> Path:
        path = Path(self.upload_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            # 创建失败不阻塞运行（比如只读文件系统），调用方再处理
            pass
        return path

    @property
    def MODEL_PATH(self) -> Path:
        # 默认模型路径，可通过环境变量 MODEL_PATH 覆盖
        env_path = os.getenv("MODEL_PATH")
        return Path(env_path) if env_path else Path(r"C:\Users\Lenovo\Desktop\fair_review_platform\weights\Fair_2.pt")

    @property
    def TOKENIZER_PATH(self) -> Path:
        # 默认分词器目录，可通过环境变量 TOKENIZER_PATH 覆盖
        env_path = os.getenv("TOKENIZER_PATH")
        return Path(env_path) if env_path else Path(r"C:\Users\Lenovo\Desktop\fair_review_platform\tokenizer")
    
    # pydantic v2 优先使用 model_config；否则回退到 v1 的 Config
    if PYDANTIC_V2 and 'SettingsConfigDict' in globals() and SettingsConfigDict is not None:  # type: ignore
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="allow",  # 忽略未知环境变量键
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "allow"  # 忽略未知环境变量键

@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()

# 全局配置实例
settings = get_settings()