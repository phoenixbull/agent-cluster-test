"""
任务 Schema - 请求/响应验证
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from ..models.task import TaskStatus, TaskPriority


# ============== 基础 Schema ==============

class TaskBase(BaseModel):
    """任务基础字段"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


# ============== 创建/更新 Schema ==============

class TaskCreate(TaskBase):
    """创建任务请求"""
    pass


class TaskUpdate(BaseModel):
    """更新任务请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    """更新任务状态"""
    status: TaskStatus


# ============== 响应 Schema ==============

class TaskResponse(TaskBase):
    """任务响应"""
    id: int
    status: TaskStatus
    owner_id: int
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """任务列表响应"""
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskStatistics(BaseModel):
    """任务统计"""
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue: int
    completed_today: int
