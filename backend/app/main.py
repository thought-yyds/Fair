# app/main.py（核心入口，启动FastAPI）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.endpoints import files, reviews, chat

# 创建FastAPI实例（自动生成文档的配置）
app = FastAPI(
    title="公平审查大数据平台API",
    description="支持文档上传、AI审查、风险评估、报告生成的完整API服务",
    version="1.0.0",
    docs_url="/docs",  # 自动文档地址（Swagger UI）
    redoc_url="/redoc" # 另一种文档风格（ReDoc）
)

# 配置CORS（解决前端跨域问题）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # 允许的前端地址
    allow_credentials=True,                  # 允许携带Cookie
    allow_methods=["*"],                     # 允许所有HTTP方法
    allow_headers=["*"],                     # 允许所有HTTP头
)

# 注册API路由（前缀统一为/api，方便前端调用）
app.include_router(files.router, prefix="/api/files")
app.include_router(reviews.router, prefix="/api/reviews")
app.include_router(chat.router)  # 聊天API路由（已在router中定义了/api/chat前缀）

# 根路由（测试用）
@app.get("/", summary="首页")
async def root():
    return {
        "message": "公平审查大数据平台API已启动",
        "提示": "访问 /docs 查看完整接口文档",
        "当前环境": "开发环境" if settings.DEBUG else "生产环境"
    }

# 启动命令：在项目根目录执行 python -m app.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",  # 指向当前文件的app实例
        host="0.0.0.0",  # 允许外部访问（局域网内其他设备可访问）
        port=settings.PORT,  # 端口（从配置读取）
        reload=settings.DEBUG  # 开发环境自动重载（代码改后无需重启）
    )