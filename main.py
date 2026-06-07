from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, admin, orders
from app.logger import logger

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="洗护门店管理系统后端API，支持订单状态流转、角色权限管理",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(orders.router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"服务启动: {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"API文档地址: http://{settings.HOST}:{settings.PORT}/docs")


@app.get("/", summary="健康检查")
async def health_check():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
