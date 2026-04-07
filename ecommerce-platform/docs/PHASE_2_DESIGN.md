# 阶段 2: 系统设计

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Login   │  │ Register │  │Dashboard │  │  Tasks   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                           │                                  │
│                    (Axios + JWT)                            │
└───────────────────────────┼──────────────────────────────────┘
                            │ HTTP/HTTPS
┌───────────────────────────▼──────────────────────────────────┐
│                      API Gateway (FastAPI)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Middleware Layer                    │   │
│  │  CORS │ Auth │ Rate Limit │ Error Handler │ Logger  │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  /auth   │  │  /users  │  │  /tasks  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                           │                                  │
│                    (SQLAlchemy ORM)                         │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                      Database (SQLite/PostgreSQL)             │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │    users     │         │     tasks    │                  │
│  │  - id        │◄────────│  - id        │                  │
│  │  - email     │         │  - title     │                  │
│  │  - username  │         │  - status    │                  │
│  │  - password  │         │  - owner_id  │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 认证流程设计

### JWT Token 结构
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567800,
  "type": "access"
}
```

### Token 生命周期
1. **Access Token**: 30 分钟有效期
2. **Refresh Token**: 7 天有效期
3. **刷新流程**: Access Token 过期 → 使用 Refresh Token 获取新 Token

### 密码安全
- 算法：bcrypt
- Rounds: 12
- 加盐：自动

## 📡 API 设计

### 认证接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| POST | `/api/v1/auth/refresh` | 刷新 Token | ❌ |

### 用户接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/users/me` | 获取当前用户 | ✅ |
| PATCH | `/api/v1/users/me` | 更新用户信息 | ✅ |

### 任务接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/tasks` | 创建任务 | ✅ |
| GET | `/api/v1/tasks` | 获取任务列表 | ✅ |
| GET | `/api/v1/tasks/{id}` | 获取任务详情 | ✅ |
| PATCH | `/api/v1/tasks/{id}` | 更新任务 | ✅ |
| DELETE | `/api/v1/tasks/{id}` | 删除任务 | ✅ |
| GET | `/api/v1/tasks/statistics` | 获取统计 | ✅ |

### 请求/响应示例

#### 创建任务
```http
POST /api/v1/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "完成项目文档",
  "description": "编写 API 文档和用户手册",
  "priority": "high",
  "due_date": "2026-04-01T00:00:00Z"
}
```

#### 响应
```json
{
  "id": 1,
  "title": "完成项目文档",
  "description": "编写 API 文档和用户手册",
  "status": "pending",
  "priority": "high",
  "due_date": "2026-04-01T00:00:00Z",
  "owner_id": 1,
  "created_at": "2026-03-28T12:00:00Z",
  "updated_at": "2026-03-28T12:00:00Z"
}
```

## 🗄️ 数据库设计

### ER 图
```
┌─────────────────┐         ┌─────────────────┐
│     users       │         │     tasks       │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄───────┤│ owner_id (FK)   │
│ email (UNIQUE)  │         │ id (PK)         │
│ username        │         │ title           │
│ hashed_password │         │ description     │
│ is_active       │         │ status          │
│ created_at      │         │ priority        │
│ updated_at      │         │ due_date        │
└─────────────────┘         │ completed_at    │
                            │ created_at      │
                            │ updated_at      │
                            └─────────────────┘
```

## 🎨 前端组件设计

### 组件树
```
App
├── Layout
│   ├── Header
│   ├── Sidebar
│   └── Outlet
│       ├── DashboardPage
│       │   ├── Statistics
│       │   ├── TaskList
│       │   └── TaskForm (Modal)
│       ├── LoginPage
│       └── RegisterPage
```

### 状态管理 (Zustand)
- `authStore`: 用户认证状态
- `taskStore`: 任务数据和操作

## 🔒 安全设计

### OWASP Top 10 防护

| 风险 | 防护措施 |
|------|----------|
| 注入攻击 | SQLAlchemy ORM 参数化查询 |
| 认证失效 | JWT + bcrypt + 密码策略 |
| 敏感数据泄露 | HTTPS + 密码哈希 |
| XXE | 禁用 XML 解析 |
| 访问控制失效 | 用户级权限隔离 |
| 安全配置错误 | 生产环境配置分离 |
| XSS | React 自动转义 |
| 反序列化 | 使用安全序列化库 |
| 日志泄露 | 不记录敏感信息 |
| SSRF | 限制外部请求 |

## ✅ 阶段验收

- [ ] 架构图评审通过
- [ ] API 设计评审通过
- [ ] 数据库设计评审通过
- [ ] 安全设计评审通过

---

**上一步**: [阶段 1: 需求分析](./PHASE_1_REQUIREMENTS.md)  
**下一步**: [阶段 3: 实现开发](./PHASE_3_IMPLEMENTATION.md)
