"""
服务层测试
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.file_service import FileService
from app.services.review_service import ReviewService

class TestFileService:
    """文件服务测试"""
    
    def test_save_file_success(self, db_session, sample_file_data):
        """测试保存文件成功"""
        service = FileService(db_session)
        
        with patch('app.utils.helpers.generate_uuid') as mock_uuid:
            mock_uuid.return_value = "test-uuid-123"
            
            result = service.save_file(
                filename=sample_file_data["filename"],
                file_type=sample_file_data["file_type"],
                file_size=sample_file_data["file_size"],
                content=sample_file_data["content"]
            )
            
            assert result["file_id"] is not None
            assert result["filename"] == sample_file_data["filename"]
    
    def test_get_files_pagination(self, db_session):
        """测试文件分页查询"""
        service = FileService(db_session)
        
        # 创建测试数据
        for i in range(15):
            service.save_file(
                filename=f"test_{i}.pdf",
                file_type="pdf",
                file_size=1024,
                content=f"test content {i}"
            )
        
        # 测试第一页
        result = service.get_files(page=1, page_size=10)
        assert len(result["files"]) == 10
        assert result["total"] == 15
        assert result["page"] == 1
        
        # 测试第二页
        result = service.get_files(page=2, page_size=10)
        assert len(result["files"]) == 5
        assert result["page"] == 2

class TestReviewService:
    """审查服务测试"""
    
    def test_start_review_success(self, db_session):
        """测试开始审查成功"""
        service = ReviewService(db_session)
        
        with patch('app.services.review_service.ReviewService._process_review') as mock_process:
            mock_process.return_value = None
            
            result = service.start_review(file_id=1)
            
            assert "task_id" in result
            assert result["status"] == "started"
    
    def test_get_review_status_processing(self, db_session):
        """测试获取处理中的审查状态"""
        service = ReviewService(db_session)
        
        # 模拟处理中的任务
        with patch('app.services.review_service.ReviewService._get_task_status') as mock_status:
            mock_status.return_value = {
                "status": "processing",
                "progress": 75,
                "message": "正在分析文档内容..."
            }
            
            result = service.get_review_status("test_task_123")
            
            assert result["status"] == "processing"
            assert result["progress"] == 75
    
    def test_get_review_result_completed(self, db_session, sample_review_data):
        """测试获取已完成的审查结果"""
        service = ReviewService(db_session)
        
        with patch('app.services.review_service.ReviewService._get_task_result') as mock_result:
            mock_result.return_value = sample_review_data
            
            result = service.get_review_result("test_task_123")
            
            assert result["file_id"] == 1
            assert result["status"] == "processing"
            assert len(result["violations"]) == 1
            assert result["violations"][0]["type"] == "政治敏感"
