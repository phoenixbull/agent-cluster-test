#!/usr/bin/env python3
"""
AI 生成短剧智能体 - FastAPI 后端
"""

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="AI Drama Generator",
    description="AI 生成短剧智能体工作流系统",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "AI Drama Generator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
