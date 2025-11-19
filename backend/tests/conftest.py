"""
测试配置和fixtures
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.db_models import Base
from app.config import get_settings

# 测试数据库URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# 创建测试数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_settings] = lambda: get_settings()
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_file_data():
    """示例文件数据"""
    return {
        "filename": "test_document.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "content": "这是一个测试文档内容"
    }

@pytest.fixture
def sample_review_data():
    """示例审查数据"""
    return {
        "file_id": 1,
        "status": "processing",
        "violations": [
            {
                "type": "政治敏感",
                "content": "测试敏感内容",
                "position": {"start": 0, "end": 10},
                "confidence": 0.95
            }
        ],
        "summary": "发现1处违规内容"
    }
