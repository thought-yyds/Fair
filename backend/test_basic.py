#!/usr/bin/env python3
"""
基本功能测试
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试基本导入"""
    print("🔍 测试基本导入...")
    
    try:
        from app.config import settings
        print("✅ 配置导入成功")
        print(f"   数据库URL: {settings.DATABASE_URL}")
        print(f"   上传目录: {settings.UPLOADS_DIR}")
    except Exception as e:
        print(f"❌ 配置导入失败: {e}")
        return False
    
    try:
        from app.models import get_db, Article
        print("✅ 数据库模型导入成功")
    except Exception as e:
        print(f"❌ 数据库模型导入失败: {e}")
        return False
    
    try:
        from app.api.endpoints import files, reviews
        print("✅ API端点导入成功")
    except Exception as e:
        print(f"❌ API端点导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        from app.models import get_db, Article
        from sqlalchemy.orm import Session
        
        # 获取数据库会话
        db_gen = get_db()
        db: Session = next(db_gen)
        
        # 测试查询
        count = db.query(Article).count()
        print(f"✅ 数据库连接成功，当前文档数量: {count}")
        
        # 关闭会话
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始基本功能测试...\n")
    
    if test_imports():
        test_database()
    
    print("\n✨ 测试完成！")
