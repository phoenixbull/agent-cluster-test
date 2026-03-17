# A2A 协议实现 (Agent-to-Agent Protocol)

A2A 用于智能体之间的点对点通信和协作。

## 核心概念

### Task (任务)
任务单元，有完整的生命周期：
- `created` - 任务创建
- `negotiating` - 协商中
- `working` - 执行中
- `completed` - 已完成
- `failed` - 失败

### Artifact (工件)
任务的产出物，可以是：
- 文本内容
- 代码文件
- 数据结果
- 多媒体内容

### Message (消息)
智能体间的通信消息：
- 任务请求
- 进度更新
- 结果返回
- 错误通知

## 使用示例

### 创建 A2A 服务器

```python
from protocols.a2a.server import A2AServer

server = A2AServer(
    name="coder-agent",
    description="代码专家智能体",
    capabilities=["code_review", "debugging", "refactoring"]
)

# 注册技能
@server.skill("code_review")
def review_code(code: str) -> str:
    """审查代码并给出建议"""
    # 实现代码审查逻辑
    return "审查结果..."

# 启动服务器
await server.start(port=5000)
```

### 创建 A2A 客户端

```python
from protocols.a2a.client import A2AClient

client = A2AClient("http://localhost:5000")

# 发现可用服务
services = await client.discover_services()

# 创建任务
task = await client.create_task(
    agent_id="coder-agent",
    task_type="code_review",
    input={"code": "..."}
)

# 等待任务完成
result = await client.wait_for_task(task.id)
```

### Agent 间通信

```python
# 主代理委托任务给子代理
main_agent.delegate(
    target="coder",
    task="审查这段代码...",
    protocol="a2a"
)

# 子代理接受任务
coder_agent.accept_task(task_id)

# 更新进度
coder_agent.update_progress(task_id, 50, "分析中...")

# 完成任务
coder_agent.complete_task(task_id, result="审查报告...")
```

## 任务生命周期

```
created ──> negotiating ──> working ──> completed
                              │
                              └──> failed
```

## 消息格式

```json
{
  "type": "task_request",
  "from": "main-agent",
  "to": "coder-agent",
  "task": {
    "id": "task-123",
    "type": "code_review",
    "input": {"code": "..."},
    "priority": "normal",
    "deadline": "2026-03-04T12:00:00Z"
  }
}
```
