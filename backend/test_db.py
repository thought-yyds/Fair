#!/usr/bin/env python3
"""
数据库连接测试脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, engine, Base
from app.config import settings
from sqlalchemy import text

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    print(f"数据库URL: {settings.database_url}")
    
    try:
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功!")
            
        # 创建表
        print("🔧 创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功!")
        
        # 测试数据库会话
        print("🔍 测试数据库会话...")
        db = next(get_db())
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ 数据库会话正常! 现有表: {tables}")
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_files_api():
    """测试文件API"""
    print("\n🔍 测试文件API...")
    try:
        from app.api.endpoints.files import get_article_list
        from app.models import get_db
        
        # 模拟请求
        db = next(get_db())
        try:
            result = get_article_list(db=db, page=1, page_size=10)
            print(f"✅ 文件列表API正常! 返回: {result}")
            return True
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 文件API测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始数据库和API测试...\n")
    
    # 测试数据库连接
    db_ok = test_database_connection()
    
    if db_ok:
        # 测试文件API
        api_ok = test_files_api()
        
        if api_ok:
            print("\n🎉 所有测试通过! 后端应该可以正常启动。")
        else:
            print("\n⚠️ 数据库正常，但API有问题。")
    else:
        print("\n❌ 数据库连接失败，请检查配置。")
