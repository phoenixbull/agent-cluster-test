# Agent Cluster V2.7.1 API 使用文档

**版本**: V2.7.1  
**更新日期**: 2026-03-17  
**基础 URL**: `http://localhost:8890`

---

## 📋 目录

1. [快速入门](#快速入门)
2. [认证](#认证)
3. [API 端点](#api 端点)
4. [错误处理](#错误处理)
5. [示例代码](#示例代码)

---

## 快速入门

### 1. 启动服务

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app_v2.py --port 8890
```

### 2. 访问界面

- Web 控制台：`http://localhost:8890`
- API 文档：`http://localhost:8890/docs` (FastAPI 版本)
- 健康检查：`http://localhost:8890/health`
- Prometheus 指标：`http://localhost:8890/metrics`

### 3. 默认账号

- 用户名：`admin`
- 密码：`admin`

**⚠️ 首次使用请修改密码！**

---

## 认证

### JWT Token 认证

大多数 API 端点需要 JWT Token 认证。

#### 1. 获取 Token

```bash
curl -X POST http://localhost:8890/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

**响应**:
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 86400,
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

#### 2. 使用 Token

在请求头或 Cookie 中携带 Token：

**方式 1: Cookie**
```bash
curl http://localhost:8890/api/workflows \
  -H "Cookie: auth_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**方式 2: Authorization Header**
```bash
curl http://localhost:8890/api/workflows \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## API 端点

### 公开端点（无需认证）

| 端点 | 方法 | 说明 | 示例 |
|------|------|------|------|
| `/health` | GET | 健康检查 | `curl /health` |
| `/metrics` | GET | Prometheus 指标 | `curl /metrics` |
| `/api/status` | GET | 集群状态 | `curl /api/status` |
| `/api/login` | POST | 用户登录 | 见认证部分 |
| `/api/agents` | GET | Agent 阵容 | `curl /api/agents` |
| `/api/phases` | GET | 开发流程 | `curl /api/phases` |

### 受保护端点（需要认证）

#### 工作流管理

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/workflows` | GET | 获取工作流列表 | `?status=running&limit=50` |
| `/api/submit` | POST | 提交新任务 | `{requirement, project}` |

**示例 - 获取工作流列表**:
```bash
curl http://localhost:8890/api/workflows \
  -H "Cookie: auth_token=YOUR_TOKEN"
```

**响应**:
```json
{
  "workflows": [
    {
      "workflow_id": "wf_123",
      "requirement": "实现购物车功能",
      "project": "ecommerce",
      "status": "running",
      "phase": 3,
      "created_at": "2026-03-17T10:00:00"
    }
  ]
}
```

**示例 - 提交任务**:
```bash
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "requirement": "实现用户登录功能",
    "project": "default"
  }'
```

#### 部署管理

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/deploy/execute` | POST | 执行部署 | `{workflow_id, environment}` |
| `/api/deploy/stop` | POST | 停止部署 | `{deployment_id}` |
| `/api/deploy/status` | GET | 获取部署状态 | `?deployment_id=xxx` |

**示例 - 执行部署**:
```bash
curl -X POST http://localhost:8890/api/deploy/execute \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "workflow_id": "wf_123",
    "environment": "production"
  }'
```

#### Bug 管理

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/bugs` | GET | 获取 Bug 列表 | `?status=new&limit=50` |
| `/api/bugs/submit` | POST | 提交 Bug | `{title, description, priority}` |

**示例 - 提交 Bug**:
```bash
curl -X POST http://localhost:8890/api/bugs/submit \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "title": "登录页面无法加载",
    "description": "访问登录页面时显示 500 错误",
    "priority": "high",
    "project": "default"
  }'
```

#### 模板管理

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/templates` | GET | 获取模板列表 | - |
| `/api/template/save` | POST | 保存模板 | `{name, description, requirement}` |
| `/api/template/delete` | POST | 删除模板 | `{id}` |

**示例 - 保存模板**:
```bash
curl -X POST http://localhost:8890/api/template/save \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "name": "电商购物车",
    "description": "标准电商购物车功能",
    "requirement": "实现购物车添加、删除、修改数量功能"
  }'
```

#### 成本统计

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/costs` | GET | 获取成本统计 | `?days=30` |

**响应**:
```json
{
  "today": {"total": 0.5, "workflows": 5},
  "week": {"total": 3.2, "workflows": 30},
  "month": {"total": 12.8, "workflows": 120},
  "by_model": {
    "qwen-coder-plus": {"cost": 5.0, "tokens": 100000, "calls": 50}
  }
}
```

#### 用户管理

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/logout` | POST | 用户登出 | - |
| `/api/change-password` | POST | 修改密码 | `{old_password, new_password}` |

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 处理方式 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求参数 |
| 401 | 未授权 | 检查 Token 是否有效 |
| 403 | 权限不足 | 检查用户角色 |
| 404 | 资源不存在 | 检查 URL 和资源 ID |
| 429 | 请求过于频繁 | 等待后重试 |
| 500 | 服务器错误 | 联系管理员 |

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息",
  "code": 400
}
```

### Rate Limiting

API 实施了速率限制：
- **限制**: 100 请求/分钟（可配置）
- **响应头**:
  - `X-RateLimit-Limit`: 总限制数
  - `X-RateLimit-Remaining`: 剩余请求数
  - `Retry-After`: 重试等待时间（秒）

**429 响应**:
```json
{
  "error": "请求过于频繁",
  "retry_after": 30
}
```

---

## 示例代码

### Python 示例

```python
import requests

BASE_URL = 'http://localhost:8890'

# 登录获取 Token
def login(username, password):
    resp = requests.post(f'{BASE_URL}/api/login', json={
        'username': username,
        'password': password
    })
    if resp.status_code == 200:
        return resp.json()['token']
    return None

# 获取工作流列表
def get_workflows(token, status=None):
    headers = {'Cookie': f'auth_token={token}'}
    params = {}
    if status:
        params['status'] = status
    
    resp = requests.get(f'{BASE_URL}/api/workflows', 
                       headers=headers, params=params)
    return resp.json()

# 提交任务
def submit_task(token, requirement, project='default'):
    headers = {
        'Cookie': f'auth_token={token}',
        'Content-Type': 'application/json'
    }
    resp = requests.post(f'{BASE_URL}/api/submit',
                        headers=headers,
                        json={'requirement': requirement, 'project': project})
    return resp.json()

# 使用示例
token = login('admin', 'admin')
if token:
    # 获取运行中的工作流
    workflows = get_workflows(token, status='running')
    print(f"运行中的工作流：{len(workflows['workflows'])}")
    
    # 提交新任务
    result = submit_task(token, '实现用户注册功能')
    print(f"任务提交结果：{result}")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8890';

// 登录
async function login(username, password) {
  const resp = await fetch(`${BASE_URL}/api/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  const data = await resp.json();
  return data.token;
}

// 获取工作流
async function getWorkflows(token, status = null) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  
  const resp = await fetch(`${BASE_URL}/api/workflows?${params}`, {
    headers: {'Cookie': `auth_token=${token}`}
  });
  return await resp.json();
}

// 提交任务
async function submitTask(token, requirement, project = 'default') {
  const resp = await fetch(`${BASE_URL}/api/submit`, {
    method: 'POST',
    headers: {
      'Cookie': `auth_token=${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({requirement, project})
  });
  return await resp.json();
}

// 使用示例
(async () => {
  const token = await login('admin', 'admin');
  
  // 获取工作流
  const workflows = await getWorkflows(token, 'running');
  console.log(`运行中的工作流：${workflows.workflows.length}`);
  
  // 提交任务
  const result = await submitTask(token, '实现商品搜索功能');
  console.log(`任务提交结果：${result.message}`);
})();
```

### cURL 示例

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:8890/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# 获取状态
curl http://localhost:8890/api/status

# 获取工作流
curl http://localhost:8890/api/workflows \
  -H "Cookie: auth_token=$TOKEN"

# 提交任务
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=$TOKEN" \
  -d '{"requirement":"测试 API","project":"default"}'

# 健康检查
curl http://localhost:8890/health

# Prometheus 指标
curl http://localhost:8890/metrics
```

---

## 📞 支持与反馈

如有问题或建议，请：
1. 查看日志：`tail -f logs/web_app_v2.log`
2. 检查健康状态：`curl /health`
3. 联系管理员

**文档版本**: 1.0  
**最后更新**: 2026-03-17
