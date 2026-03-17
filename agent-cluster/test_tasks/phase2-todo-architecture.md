# 🏗️ 技术架构设计文档

**项目名称**: 在线待办事项管理系统  
**版本**: 1.0  
**创建时间**: 2026-03-09  
**创建者**: Tech Lead Agent

---

## 1. 架构概述

### 1.1 架构风格
- **类型**: 前后端分离
- **API**: RESTful
- **部署**: Docker 容器化

### 1.2 技术选型

#### 前端技术栈
| 技术 | 选型 | 理由 |
|------|------|------|
| **框架** | React 18 | 生态丰富，组件化好 |
| **语言** | TypeScript 5 | 类型安全，开发体验好 |
| **状态管理** | Zustand | 轻量，易用 |
| **UI 库** | Tailwind CSS | 原子化 CSS，开发快 |
| **构建工具** | Vite | 快速启动，热更新 |

#### 后端技术栈
| 技术 | 选型 | 理由 |
|------|------|------|
| **语言** | Python 3.11 | 开发效率高 |
| **框架** | FastAPI | 性能好，自动文档 |
| **ORM** | SQLAlchemy 2.0 | 功能强大，支持异步 |
| **认证** | JWT (PyJWT) | 无状态，易扩展 |
| **数据库** | PostgreSQL 15 | 稳定可靠，功能强 |
| **缓存** | Redis 7 | 高性能缓存 |

#### 基础设施
| 技术 | 选型 | 理由 |
|------|------|------|
| **容器** | Docker | 环境一致 |
| **部署** | Docker Compose | 简单易用 |
| **CI/CD** | GitHub Actions | 免费，集成好 |
| **监控** | Prometheus + Grafana | 开源，功能强 |

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Web 浏览器 │  │  移动端   │  │  平板    │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
└───────┼─────────────┼─────────────┼─────────────────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │      Nginx 反向代理        │
        │      (端口 80/443)         │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     Frontend (React)      │
        │      (端口 3000)          │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     Backend (FastAPI)     │
        │      (端口 8000)          │
        └────┬────────────┬─────────┘
             │            │
    ┌────────▼────┐  ┌───▼────────┐
    │ PostgreSQL  │  │   Redis    │
    │   (5432)    │  │   (6379)   │
    └─────────────┘  └────────────┘
```

---

## 3. API 接口设计

### 3.1 API 规范

**Base URL**: `/api/v1`  
**认证方式**: Bearer Token (JWT)  
**数据格式**: JSON  
**字符编码**: UTF-8

### 3.2 核心接口

#### 用户认证

| 接口 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/auth/register` | POST | 用户注册 | ❌ |
| `/auth/login` | POST | 用户登录 | ❌ |
| `/auth/logout` | POST | 用户登出 | ✅ |
| `/auth/me` | GET | 获取当前用户 | ✅ |

#### 待办事项

| 接口 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/todos` | GET | 获取待办列表 | ✅ |
| `/todos` | POST | 创建待办 | ✅ |
| `/todos/{id}` | GET | 获取待办详情 | ✅ |
| `/todos/{id}` | PUT | 更新待办 | ✅ |
| `/todos/{id}` | DELETE | 删除待办 | ✅ |
| `/todos/{id}/toggle` | POST | 切换完成状态 | ✅ |

#### 分类管理

| 接口 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/categories` | GET | 获取分类列表 | ✅ |
| `/categories` | POST | 创建分类 | ✅ |
| `/categories/{id}` | PUT | 更新分类 | ✅ |
| `/categories/{id}` | DELETE | 删除分类 | ✅ |

#### 统计

| 接口 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/stats/summary` | GET | 获取统计摘要 | ✅ |
| `/stats/completion-rate` | GET | 获取完成率 | ✅ |

---

## 4. 数据库设计

### 4.1 ER 图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │       │   todos     │       │ categories  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │───┐   │ id (PK)     │   ┌───│ id (PK)     │
│ email       │   │   │ user_id(FK) │───┘   │ user_id(FK) │
│ password    │   └──>│ title       │       │ name        │
│ nickname    │       │ description │       │ color       │
│ avatar      │       │ priority    │       │ sort_order  │
│ created_at  │       │ status      │       │ created_at  │
└─────────────┘       │ due_date    │       └─────────────┘
                      │ created_at  │
                      │ updated_at  │
                      │ completed_at│
                      └─────────────┘
```

### 4.2 表结构

#### users - 用户表
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    avatar VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

#### todos - 待办表
```sql
CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(10) DEFAULT 'medium',  -- high, medium, low
    status VARCHAR(20) DEFAULT 'pending',   -- pending, completed
    due_date DATE,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_todos_user_id ON todos(user_id);
CREATE INDEX idx_todos_status ON todos(status);
CREATE INDEX idx_todos_priority ON todos(priority);
CREATE INDEX idx_todos_category ON todos(category_id);
```

#### categories - 分类表
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_user_id ON categories(user_id);
```

---

## 5. 部署架构

### 5.1 Docker 服务

```yaml
services:
  - nginx (反向代理)
  - frontend (React 应用)
  - backend (FastAPI 应用)
  - postgres (数据库)
  - redis (缓存)
  - prometheus (监控)
  - grafana (可视化)
```

### 5.2 端口分配

| 服务 | 容器端口 | 主机端口 |
|------|----------|----------|
| Nginx | 80 | 80 |
| Frontend | 3000 | - |
| Backend | 8000 | - |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Prometheus | 9090 | 9090 |
| Grafana | 3000 | 3001 |

---

## 6. 安全设计

### 6.1 认证授权
- **JWT Token**: Access Token (7 天)
- **密码加密**: bcrypt (cost=12)
- **权限控制**: 基于用户的资源隔离

### 6.2 数据安全
- **SQL 注入**: 使用 ORM，参数化查询
- **XSS 防护**: 输入过滤，输出转义
- **CSRF 防护**: CSRF Token

### 6.3 接口安全
- **速率限制**: 每 IP 每分钟 60 次请求
- **输入验证**: Pydantic Schema 验证
- **CORS**: 严格限制允许的源

---

**文档版本**: v1.0  
**最后更新**: 2026-03-09  
**审核状态**: ✅ 已完成
