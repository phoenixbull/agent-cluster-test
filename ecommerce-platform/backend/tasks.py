"""
任务 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..models.task import Task, TaskStatus, TaskPriority
from ..schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatistics,
)
from ..core.security import get_current_user

router = APIRouter(prefix="/tasks", tags=["任务管理"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新任务"""
    task = Task(
        **task_data.model_dump(),
        owner_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[TaskPriority] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务列表（支持分页和筛选）"""
    query = db.query(Task).filter(Task.owner_id == current_user.id)
    
    # 应用筛选
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if priority:
        query = query.filter(Task.priority == priority)
    
    # 统计总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size).all()
    
    return TaskListResponse(
        items=[TaskResponse.model_validate(task) for task in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个任务详情"""
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新任务"""
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 更新字段
    update_data = task_data.model_dump(exclude_unset=True)
    
    # 如果状态变为已完成，记录完成时间
    if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()
    elif "status" in update_data and update_data["status"] != TaskStatus.COMPLETED:
        update_data["completed_at"] = None
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    db.delete(task)
    db.commit()
    return None


@router.get("/statistics", response_model=TaskStatistics)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务统计信息"""
    tasks = db.query(Task).filter(Task.owner_id == current_user.id).all()
    
    by_status = {}
    by_priority = {}
    overdue = 0
    completed_today = 0
    today = datetime.utcnow().date()
    
    for task in tasks:
        # 按状态统计
        status_key = task.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1
        
        # 按优先级统计
        priority_key = task.priority.value
        by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
        
        # 统计过期任务
        if task.due_date and task.due_date.date() < today and task.status != TaskStatus.COMPLETED:
            overdue += 1
        
        # 统计今天完成的任务
        if task.completed_at and task.completed_at.date() == today:
            completed_today += 1
    
    return TaskStatistics(
        total=len(tasks),
        by_status=by_status,
        by_priority=by_priority,
        overdue=overdue,
        completed_today=completed_today,
    )
