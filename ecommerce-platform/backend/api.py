"""
Workflow ID Matcher - FastAPI REST API
提供工作流 ID 生成、验证和匹配的 HTTP 接口
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

from workflow_id_match import (
    WorkflowIDGenerator,
    WorkflowIDMatcher,
    IDFormat,
    WorkflowID,
    MatchResult
)

# ========== FastAPI 应用 ==========

app = FastAPI(
    title="Workflow ID Matcher API",
    description="工作流 ID 生成、验证和匹配服务",
    version="1.0.0"
)

# 全局实例
generator = WorkflowIDGenerator(prefix="wf")
matcher = WorkflowIDMatcher()


# ========== Pydantic 模型 ==========

class IDFormatEnum(str, Enum):
    UUID = "uuid"
    TIMESTAMP = "timestamp"
    HASH = "hash"
    COMPOSITE = "composite"


class GenerateRequest(BaseModel):
    """ID 生成请求"""
    format: IDFormatEnum = IDFormatEnum.COMPOSITE
    content: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None


class GenerateResponse(BaseModel):
    """ID 生成响应"""
    id: str
    format: str
    created_at: str
    checksum: str
    metadata: Dict


class ValidateRequest(BaseModel):
    """ID 验证请求"""
    id: str
    format: IDFormatEnum = IDFormatEnum.COMPOSITE


class ValidateResponse(BaseModel):
    """ID 验证响应"""
    valid: bool
    id: str
    format: str
    message: str


class MatchExactRequest(BaseModel):
    """精确匹配请求"""
    input_id: str
    target_id: str


class MatchPatternRequest(BaseModel):
    """模式匹配请求"""
    id: str


class MatchFuzzyRequest(BaseModel):
    """模糊匹配请求"""
    input_id: str
    candidates: List[str]


class MatchResponse(BaseModel):
    """匹配响应"""
    matched: bool
    confidence: float
    match_type: str
    elapsed_ms: float
    message: str
    workflow_id: Optional[Dict] = None


class StatsResponse(BaseModel):
    """统计响应"""
    total_matches: int
    matched: int
    failed: int
    success_rate: float
    by_type: Dict[str, int]
    avg_confidence: float
    avg_elapsed_ms: float


# ========== API 端点 ==========

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "service": "Workflow ID Matcher API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_id(request: GenerateRequest):
    """
    生成工作流 ID
    
    - **format**: ID 格式 (uuid, timestamp, hash, composite)
    - **content**: 哈希格式需要的内容
    - **user_id**: 复合格式的用户 ID
    - **project_id**: 复格式的项目 ID
    """
    try:
        kwargs = {}
        if request.content:
            kwargs["content"] = request.content
        if request.user_id:
            kwargs["user_id"] = request.user_id
        if request.project_id:
            kwargs["project_id"] = request.project_id
        
        workflow_id = generator.generate(
            IDFormat(request.format.value),
            **kwargs
        )
        
        return GenerateResponse(
            id=workflow_id.id,
            format=workflow_id.format.value,
            created_at=workflow_id.created_at,
            checksum=workflow_id.checksum,
            metadata=workflow_id.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate/{format}")
async def generate_id_simple(
    format: IDFormatEnum,
    content: Optional[str] = None,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None
):
    """
    快速生成 ID (GET 方式)
    
    示例：
    - /generate/uuid
    - /generate/hash?content=my_content
    - /generate/composite?user_id=user123&project_id=proj456
    """
    try:
        kwargs = {}
        if content:
            kwargs["content"] = content
        if user_id:
            kwargs["user_id"] = user_id
        if project_id:
            kwargs["project_id"] = project_id
        
        workflow_id = generator.generate(
            IDFormat(format.value),
            **kwargs
        )
        
        return GenerateResponse(
            id=workflow_id.id,
            format=workflow_id.format.value,
            created_at=workflow_id.created_at,
            checksum=workflow_id.checksum,
            metadata=workflow_id.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate", response_model=ValidateResponse)
async def validate_id(request: ValidateRequest):
    """
    验证工作流 ID
    
    - **id**: 要验证的 ID
    - **format**: ID 格式类型
    """
    try:
        workflow_id = WorkflowID(
            id=request.id,
            format=IDFormat(request.format.value),
            created_at="",
            checksum=""
        )
        
        is_valid = matcher.validate_id(workflow_id)
        
        return ValidateResponse(
            valid=is_valid,
            id=request.id,
            format=request.format.value,
            message="ID 格式有效" if is_valid else "ID 格式无效"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/exact", response_model=MatchResponse)
async def match_exact(request: MatchExactRequest):
    """
    精确匹配
    
    比较两个 ID 是否完全相同
    """
    try:
        result = matcher.match_exact(request.input_id, request.target_id)
        
        return MatchResponse(
            matched=result.matched,
            confidence=result.confidence,
            match_type=result.match_type,
            elapsed_ms=result.elapsed_ms,
            message=result.message,
            workflow_id=result.workflow_id.to_dict() if result.workflow_id else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/pattern", response_model=MatchResponse)
async def match_pattern(request: MatchPatternRequest):
    """
    模式匹配
    
    验证 ID 是否符合预定义的格式模式
    """
    try:
        result = matcher.match_pattern(request.id)
        
        return MatchResponse(
            matched=result.matched,
            confidence=result.confidence,
            match_type=result.match_type,
            elapsed_ms=result.elapsed_ms,
            message=result.message,
            workflow_id=result.workflow_id.to_dict() if result.workflow_id else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/fuzzy", response_model=MatchResponse)
async def match_fuzzy(request: MatchFuzzyRequest):
    """
    模糊匹配
    
    在候选列表中找到最相似的 ID
    """
    try:
        result = matcher.match_fuzzy(request.input_id, request.candidates)
        
        return MatchResponse(
            matched=result.matched,
            confidence=result.confidence,
            match_type=result.match_type,
            elapsed_ms=result.elapsed_ms,
            message=result.message,
            workflow_id=result.workflow_id.to_dict() if result.workflow_id else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    获取匹配统计信息
    """
    stats = matcher.get_stats()
    return StatsResponse(**stats)


@app.get("/formats")
async def list_formats():
    """
    列出支持的 ID 格式
    """
    return {
        "formats": [
            {
                "name": "uuid",
                "description": "时间戳 + 随机 UUID",
                "example": "wf-20260331-144618-abc12345"
            },
            {
                "name": "timestamp",
                "description": "纯时间戳",
                "example": "wf-20260407192938796047"
            },
            {
                "name": "hash",
                "description": "内容哈希",
                "example": "wf-20260331-144618-abc123def456"
            },
            {
                "name": "composite",
                "description": "复合元素 (用户 + 项目)",
                "example": "wf-20260331-144618-user123-proj456-abc123"
            }
        ]
    }


# ========== 主入口 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
