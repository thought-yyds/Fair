from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.db_models import Base  # 导入修正后的基础模型

# 创建数据库引擎（SQLite 特殊配置）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 会话工厂：独立会话，线程安全
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库会话依赖：FastAPI 自动注入，用完关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 首次运行自动创建所有表（基于修正后的 DB 模型）
Base.metadata.create_all(bind=engine)

# 导入修正后的所有模型类（Annotation 已删多余字段）
from app.models.db_models import Article, Sentence, Annotation
from app.models.schemas import (
    ArticleSchema,
    SentenceSchema,
    AnnotationSchema,
    ReviewProgressSchema
)

# 导出列表：方便其他文件导入
__all__ = [
    "Base", "engine", "SessionLocal", "get_db",
    "Article", "Sentence", "Annotation",
    "ArticleSchema", "SentenceSchema", "AnnotationSchema",
    "ReviewProgressSchema"
]