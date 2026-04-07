"""
用户 Schema - 请求/响应验证
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ============== 基础 Schema ==============

class UserBase(BaseModel):
    """用户基础字段"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


# ============== 创建/更新 Schema ==============

class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


# ============== 响应 Schema ==============

class UserResponse(UserBase):
    """用户响应"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


# ============== 管理员 Schema ==============

class UserListResponse(BaseModel):
    """用户列表响应"""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
