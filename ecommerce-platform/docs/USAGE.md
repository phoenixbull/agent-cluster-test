# 任务管理 API - 使用指南

## 项目结构

```
simple-task-api/
├── main.py              # 主程序（FastAPI 应用）
├── test_main.py         # 测试文件
├── requirements.txt     # 依赖列表
├── README.md            # 项目说明
└── tasks.db             # SQLite 数据库（运行后自动生成）
```

## 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

## 启动服务

```bash
# 方式一：使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方式二：直接运行
python main.py
```

## 访问 API

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## API 使用示例

### 1. 创建任务

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 FastAPI",
    "description": "完成入门教程"
  }'
```

响应：
```json
{
  "id": 1,
  "title": "学习 FastAPI",
  "description": "完成入门教程",
  "completed": false,
  "created_at": "2026-03-30T12:00:00",
  "updated_at": "2026-03-30T12:00:00"
}
```

### 2. 获取任务列表

```bash
# 获取全部
curl http://localhost:8000/tasks

# 分页
curl "http://localhost:8000/tasks?skip=0&limit=5"

# 筛选已完成
curl "http://localhost:8000/tasks?completed=true"
```

### 3. 获取任务详情

```bash
curl http://localhost:8000/tasks/1
```

### 4. 更新任务

```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 FastAPI 完成",
    "completed": true
  }'
```

### 5. 删除任务

```bash
curl -X DELETE http://localhost:8000/tasks/1
```

## 运行测试

```bash
# 安装测试依赖
pip install pytest httpx

# 运行测试
pytest test_main.py -v
```

## 数据模型

### Task 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(200) | 任务标题（必填） |
| description | String(1000) | 任务描述（可选） |
| completed | Boolean | 是否完成（默认 false） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## API 端点一览

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/` | 根路径 | - |
| GET | `/health` | 健康检查 | - |
| GET | `/tasks` | 获取任务列表 | skip, limit, completed |
| GET | `/tasks/{id}` | 获取任务详情 | path: id |
| POST | `/tasks` | 创建任务 | body: title, description, completed |
| PUT | `/tasks/{id}` | 更新任务 | path: id, body: title, description, completed |
| DELETE | `/tasks/{id}` | 删除任务 | path: id |

## 特性

- ✅ RESTful API 设计
- ✅ SQLite 数据库（无需配置）
- ✅ 自动 API 文档（Swagger UI）
- ✅ 数据验证（Pydantic）
- ✅ 分页支持
- ✅ 状态筛选
- ✅ 单元测试

---

**版本**: 1.0.0  
**技术栈**: FastAPI + SQLAlchemy + SQLite
