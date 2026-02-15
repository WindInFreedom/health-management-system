"""
FastAPI 主应用

健康管理系统 AI 微服务 API

作者: Health Management System Team
日期: 2026-02-15
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建 FastAPI 应用
app = FastAPI(
    title="Health Management AI API",
    description="智能健康管理系统 AI 微服务接口",
    version="2.0.0",
    docs_url="/api/v2/docs",
    redoc_url="/api/v2/redoc",
    openapi_url="/api/v2/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )


# 健康检查端点
@app.get("/api/v2/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Health Management AI API",
        "version": "2.0.0",
        "docs": "/api/v2/docs"
    }


# 导入路由
from api.routes import prediction, risk_assessment, ai_advice

# 注册路由
app.include_router(prediction.router, prefix="/api/v2", tags=["Prediction"])
app.include_router(risk_assessment.router, prefix="/api/v2", tags=["Risk Assessment"])
app.include_router(ai_advice.router, prefix="/api/v2", tags=["AI Advice"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
