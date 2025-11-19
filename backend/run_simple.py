#!/usr/bin/env python3
"""
简化的FastAPI启动脚本，用于调试
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.main import app
    import uvicorn
    
    print("🚀 启动FastAPI服务器...")
    print(f"📁 项目根目录: {project_root}")
    print(f"🐍 Python路径: {sys.path[0]}")
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保安装了所有依赖包:")
    print("pip install fastapi uvicorn sqlalchemy python-multipart python-docx")
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
