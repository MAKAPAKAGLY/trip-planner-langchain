"""FastAPI 应用主入口"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.trip import router as trip_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="智能旅行助手 API",
    description="基于多智能体协作的智能旅行规划服务",
    version="1.0.0",
)

# CORS 配置 — 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "智能旅行助手 API",
        "docs": "/docs",
        "health": "/api/trip/health",
    }
