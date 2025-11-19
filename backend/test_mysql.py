#!/usr/bin/env python3
"""
MySQL连接测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mysql_connection():
    """测试MySQL连接"""
    print("🔍 测试MySQL连接...")
    
    try:
        from sqlalchemy import create_engine, text
        import os
        
        # 从环境变量或占位符配置
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://USER:PASSWORD@HOST:PORT/fastapi_review_db",
        )

        def mask_password(url: str) -> str:
            if "@" not in url or "://" not in url:
                return url
            scheme, remainder = url.split("://", 1)
            creds, host_part = remainder.split("@", 1)
            if ":" in creds:
                username = creds.split(":", 1)[0]
                masked_creds = f"{username}:***"
            else:
                masked_creds = "***"
            return f"{scheme}://{masked_creds}@{host_part}"

        print(f"📡 连接字符串: {mask_password(DATABASE_URL)}")
        
        # 创建引擎
        engine = create_engine(DATABASE_URL, echo=True)
        
        # 测试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ MySQL连接成功！测试查询结果: {row[0]}")
            
            # 测试数据库是否存在
            result = connection.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in result.fetchall()]
            print(f"📊 可用数据库: {databases}")
            
            if 'fastapi_review_db' in databases:
                print("✅ fastapi_review_db 数据库存在")
            else:
                print("⚠️  fastapi_review_db 数据库不存在，需要创建")
                print("   请在MySQL中执行: CREATE DATABASE fastapi_review_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        
        return True
        
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请安装: pip install pymysql")
        return False
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        print("\n🔧 请检查:")
        print("1. MySQL服务是否启动")
        print("2. 用户名密码是否正确")
        print("3. 数据库是否存在")
        print("4. 连接字符串格式是否正确")
        return False

def test_app_config():
    """测试应用配置"""
    print("\n🔍 测试应用配置...")
    
    try:
        from app.config import settings
        print(f"✅ 配置加载成功")
        print(f"   数据库URL: {settings.DATABASE_URL}")
        print(f"   端口: {settings.PORT}")
        print(f"   调试模式: {settings.DEBUG}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 MySQL连接测试开始...\n")
    
    config_ok = test_app_config()
    mysql_ok = test_mysql_connection()
    
    print(f"\n📋 测试结果:")
    print(f"   配置加载: {'✅' if config_ok else '❌'}")
    print(f"   MySQL连接: {'✅' if mysql_ok else '❌'}")
    
    if config_ok and mysql_ok:
        print("\n🎉 所有测试通过！可以启动应用了")
    else:
        print("\n⚠️  请先解决上述问题再启动应用")
