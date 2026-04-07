"""
博客 API - FastAPI + SQLite
包含文章 CRUD 和分页功能
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ========== 数据库配置 ==========
DATABASE_URL = "sqlite:///./blog.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ========== 数据模型 ==========
class PostModel(Base):
    """文章数据模型"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 创建表
Base.metadata.create_all(bind=engine)


# ========== Pydantic 模型 ==========
class PostBase(BaseModel):
    """文章基础模型"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    author: Optional[str] = Field(None, max_length=100)


class PostCreate(PostBase):
    """创建文章请求"""
    pass


class PostUpdate(BaseModel):
    """更新文章请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, max_length=100)


class PostResponse(PostBase):
    """文章响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """文章列表响应"""
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ========== FastAPI 应用 ==========
app = FastAPI(
    title="博客 API",
    description="简单的博客 API - 文章 CRUD 和分页",
    version="1.0.0"
)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== API 端点 ==========

@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """创建文章"""
    db_post = PostModel(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts", response_model=PostListResponse)
def get_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取文章列表（分页）"""
    # 查询总数
    total = db.query(PostModel).count()
    
    # 计算总页数
    pages = (total + page_size - 1) // page_size
    
    # 分页查询
    offset = (page - 1) * page_size
    posts = db.query(PostModel)\
        .order_by(PostModel.created_at.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()
    
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """获取文章详情"""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    return post


@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: Session = Depends(get_db)
):
    """更新文章"""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """删除文章"""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    db.delete(post)
    db.commit()
    return None


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "博客 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}
