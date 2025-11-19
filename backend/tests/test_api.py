"""
API端点测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

class TestFileAPI:
    """文件API测试"""
    
    def test_upload_file_success(self, client: TestClient, sample_file_data):
        """测试文件上传成功"""
        with patch('app.services.file_service.save_file') as mock_save:
            mock_save.return_value = {"file_id": 1, "filename": "test.pdf"}
            
            files = {"file": ("test.pdf", b"test content", "application/pdf")}
            response = client.post("/api/files/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data
            assert data["filename"] == "test.pdf"
    
    def test_upload_file_invalid_type(self, client: TestClient):
        """测试上传无效文件类型"""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post("/api/files/upload", files=files)
        
        assert response.status_code == 400
        assert "不支持的文件类型" in response.json()["detail"]
    
    def test_get_files_list(self, client: TestClient):
        """测试获取文件列表"""
        with patch('app.services.file_service.get_files') as mock_get:
            mock_get.return_value = {
                "files": [{"id": 1, "filename": "test.pdf", "status": "completed"}],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
            
            response = client.get("/api/files/list?page=1&page_size=10")
            
            assert response.status_code == 200
            data = response.json()
            assert "files" in data
            assert len(data["files"]) == 1
    
    def test_get_file_detail(self, client: TestClient):
        """测试获取文件详情"""
        with patch('app.services.file_service.get_file_by_id') as mock_get:
            mock_get.return_value = {
                "id": 1,
                "filename": "test.pdf",
                "status": "completed",
                "content": "测试内容"
            }
            
            response = client.get("/api/files/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["filename"] == "test.pdf"

class TestReviewAPI:
    """审查API测试"""
    
    def test_start_review(self, client: TestClient):
        """测试开始审查"""
        with patch('app.services.review_service.start_review') as mock_review:
            mock_review.return_value = {"task_id": "test_task_123"}
            
            response = client.post("/api/reviews/start", json={"file_id": 1})
            
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
    
    def test_get_review_status(self, client: TestClient):
        """测试获取审查状态"""
        with patch('app.services.review_service.get_review_status') as mock_status:
            mock_status.return_value = {
                "status": "processing",
                "progress": 50,
                "message": "正在处理中..."
            }
            
            response = client.get("/api/reviews/status/test_task_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert data["progress"] == 50
    
    def test_get_review_result(self, client: TestClient, sample_review_data):
        """测试获取审查结果"""
        with patch('app.services.review_service.get_review_result') as mock_result:
            mock_result.return_value = sample_review_data
            
            response = client.get("/api/reviews/result/test_task_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_id"] == 1
            assert len(data["violations"]) == 1

class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
