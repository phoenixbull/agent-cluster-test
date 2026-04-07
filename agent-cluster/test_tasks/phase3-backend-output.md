# 💻 Phase 3 - 后端开发输出

**开发者**: Codex Agent (后端专家)  
**技术栈**: Python 3.11 + FastAPI + SQLAlchemy  
**完成时间**: 2026-03-09  

---

## 📁 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── category.py
│   │   └── comment.py
│   ├── schemas/             # Pydantic Schema
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── category.py
│   │   └── comment.py
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── posts.py
│   │   ├── categories.py
│   │   └── comments.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── post.py
│   │   └── comment.py
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── security.py      # 密码加密、JWT
│       └── dependencies.py  # 依赖注入
├── tests/                   # 测试代码
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_posts.py
│   └── test_comments.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🔧 核心代码

### 1. 数据库模型 (models/post.py)

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), default="draft")  # draft, published, archived
    view_count = Column(Integer, default=0)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("PostTag", back_populates="post", cascade="all, delete-orphan")
```

### 2. API Schema (schemas/post.py)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str
    status: str = "draft"
    category_id: Optional[int] = None

class PostCreate(PostBase):
    """创建文章"""
    pass

class PostUpdate(BaseModel):
    """更新文章"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None

class PostResponse(PostBase):
    """文章响应"""
    id: int
    user_id: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 3. API 路由 (api/posts.py)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

@router.get("", response_model=List[schemas.PostResponse])
def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = "published",
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    posts = db.query(models.Post).filter(
        models.Post.status == status
    ).order_by(
        models.Post.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return posts

@router.get("/{post_id}", response_model=schemas.PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """获取文章详情"""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 增加阅读量
    post.view_count += 1
    db.commit()
    
    return post

@router.post("", response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建文章"""
    db_post = models.Post(**post.dict(), user_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: int,
    post: schemas.PostUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新文章"""
    db_post = db.query(models.Post).filter(
        models.Post.id == post_id,
        models.Post.user_id == current_user.id
    ).first()
    
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    update_data = post.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文章"""
    db_post = db.query(models.Post).filter(
        models.Post.id == post_id,
        models.Post.user_id == current_user.id
    ).first()
    
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    db.delete(db_post)
    db.commit()
    return {"message": "删除成功"}
```

### 4. 认证服务 (services/auth.py)

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """密码加密"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(db: Session, email: str, password: str):
    """认证用户"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
```

### 5. 主应用入口 (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import auth, posts, categories, comments

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="博客系统 API",
    description="个人博客系统后端 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(categories.router)
app.include_router(comments.router)

@app.get("/")
def root():
    return {
        "message": "博客系统 API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

---

## 📦 依赖配置

### requirements.txt

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pydantic==2.5.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
alembic==1.13.1
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ✅ 完成功能

| 功能 | 状态 | 代码行数 |
|------|------|----------|
| 用户认证 | ✅ 完成 | ~200 行 |
| 文章管理 | ✅ 完成 | ~300 行 |
| 分类管理 | ✅ 完成 | ~150 行 |
| 评论系统 | ✅ 完成 | ~200 行 |
| 数据库模型 | ✅ 完成 | ~250 行 |

**总代码量**: ~1100 行  
**测试覆盖率**: 待测试

---

**状态**: ✅ Phase 3-Backend 完成  
**下一步**: Phase 3-Frontend (Claude-Code)
