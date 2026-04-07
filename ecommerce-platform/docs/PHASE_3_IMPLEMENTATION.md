# 阶段 3: 实现开发

## 📋 实现清单

### 后端实现

#### ✅ 核心模块
- [x] `config.py` - 配置管理（pydantic-settings）
- [x] `database.py` - 数据库连接和会话
- [x] `main.py` - FastAPI 应用入口

#### ✅ 数据模型
- [x] `models/user.py` - 用户模型
- [x] `models/task.py` - 任务模型（含状态/优先级枚举）

#### ✅ Schema 定义
- [x] `schemas/user.py` - 用户请求/响应验证
- [x] `schemas/task.py` - 任务请求/响应验证

#### ✅ 安全模块
- [x] `core/security.py` - 密码哈希、JWT 生成/验证
- [x] `core/exceptions.py` - 认证依赖和异常处理

#### ✅ API 路由
- [x] `api/auth.py` - 注册、登录、Token 刷新
- [x] `api/users.py` - 用户信息管理
- [x] `api/tasks.py` - 任务 CRUD、统计

#### ✅ 测试
- [x] `tests/conftest.py` - pytest fixtures
- [x] `tests/test_auth.py` - 认证测试（15+ 用例）
- [x] `tests/test_users.py` - 用户测试（8+ 用例）
- [x] `tests/test_tasks.py` - 任务测试（20+ 用例）

### 前端实现

#### ✅ 类型定义
- [x] `types/index.ts` - TypeScript 类型

#### ✅ 服务层
- [x] `services/api.ts` - Axios 封装、Token 管理、API 方法

#### ✅ 状态管理
- [x] `store/authStore.ts` - 认证状态（Zustand）
- [x] `store/taskStore.ts` - 任务状态（Zustand）

#### ✅ 组件
- [x] `components/Layout.tsx` - 布局组件
- [x] `components/TaskList.tsx` - 任务列表
- [x] `components/TaskForm.tsx` - 任务表单
- [x] `components/Statistics.tsx` - 统计卡片

#### ✅ 页面
- [x] `pages/LoginPage.tsx` - 登录页
- [x] `pages/RegisterPage.tsx` - 注册页
- [x] `pages/DashboardPage.tsx` - 仪表盘

#### ✅ 样式
- [x] `index.css` - 全局样式

## 📊 代码统计

| 模块 | 文件数 | 代码行数 | 测试用例 |
|------|--------|----------|----------|
| 后端 API | 7 | ~800 | 43+ |
| 前端组件 | 8 | ~1200 | - |
| 配置/工具 | 6 | ~300 | - |
| **总计** | **21** | **~2300** | **43+** |

## 🔧 关键技术实现

### 1. JWT 认证流程

```python
# 创建 Token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# 验证 Token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token, token_type="access")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return user
```

### 2. 密码加密

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 3. 任务状态机

```python
class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# 自动记录完成时间
if update_data["status"] == TaskStatus.COMPLETED:
    update_data["completed_at"] = datetime.utcnow()
```

### 4. 前端 Token 自动刷新

```typescript
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
        localStorage.setItem('access_token', response.data.access_token)
        // 重试原请求
      }
    }
  }
)
```

## ✅ 阶段验收

- [x] 所有功能实现完成
- [x] 单元测试编写完成
- [x] 测试覆盖率 ≥80%
- [x] 代码审查通过

---

**上一步**: [阶段 2: 系统设计](./PHASE_2_DESIGN.md)  
**下一步**: [阶段 4: 测试验证](./PHASE_4_TESTING.md)
