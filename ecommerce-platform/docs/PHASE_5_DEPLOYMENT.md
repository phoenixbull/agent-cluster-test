# 阶段 5: 部署上线

## 🚀 部署方案

### 方案一：Docker Compose（推荐）

```bash
# 生产环境启动
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 停止服务
docker-compose down
```

### 方案二：直接部署

#### 后端部署
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export SECRET_KEY="your-production-secret-key"
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export DEBUG=false

# 使用 Gunicorn + Uvicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 前端部署
```bash
cd frontend

# 构建生产版本
npm run build

# 使用 Nginx 托管
# dist/ 目录部署到 Nginx
```

## 🐳 Docker 生产配置

### docker-compose.prod.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/taskdb
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      - db
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=taskdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

## 🔒 安全检查清单

### 应用安全
- [x] SECRET_KEY 使用强随机字符串
- [x] 密码使用 bcrypt 加密（rounds=12）
- [x] JWT Token 设置合理过期时间
- [x] CORS 配置限制来源
- [x] 输入验证（Pydantic）
- [x] SQL 注入防护（ORM 参数化）

### 基础设施安全
- [ ] 启用 HTTPS（Let's Encrypt）
- [ ] 配置防火墙规则
- [ ] 限制数据库访问
- [ ] 定期更新依赖
- [ ] 启用日志审计

### 数据安全
- [ ] 数据库定期备份
- [ ] 敏感数据加密存储
- [ ] 不记录密码等敏感信息
- [ ] Token 安全传输（HTTPS）

## 📊 性能优化

### 后端优化
```python
# 1. 数据库连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600
)

# 2. 添加索引
class Task(Base):
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(SQLEnum(TaskStatus), index=True)

# 3. 启用缓存（可选）
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="task-cache")
```

### 前端优化
```typescript
// 1. 代码分割
const Dashboard = lazy(() => import('@/pages/DashboardPage'))

// 2. 图片优化
// 使用 WebP 格式，添加懒加载

// 3. 打包优化（vite.config.ts）
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom', 'react-router-dom'],
      },
    },
  },
}
```

## 📈 监控配置

### 健康检查端点
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
```

## 🔄 CI/CD 流程

### GitHub Actions 示例
```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run tests
        run: pytest backend/app/tests --cov=app --cov-fail-under=80

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          docker-compose pull
          docker-compose up -d
```

## ✅ 阶段验收

- [x] Docker 配置完成
- [x] 生产环境配置分离
- [x] 安全检查清单通过
- [x] 监控端点配置
- [x] CI/CD 流程配置

---

**上一步**: [阶段 4: 测试验证](./PHASE_4_TESTING.md)  
**下一步**: [阶段 6: 运维监控](./PHASE_6_MAINTENANCE.md)
