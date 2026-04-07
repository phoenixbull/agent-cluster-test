# 📧 Agent 任务通知功能文档

**版本**: V2.2.0  
**更新时间**: 2026-03-21 11:38  
**状态**: ✅ 已上线

---

## 🎯 功能概述

Agent 集群现在支持实时通知每个 Agent 的任务分配和完成情况，让你随时掌握任务执行状态。

### 通知类型

| 通知类型 | 触发时机 | 内容 | @所有人 |
|----------|----------|------|---------|
| 📥 **任务分配** | Agent 接受任务时 | Agent 名称、任务描述、优先级、阶段 | ❌ |
| ✅ **任务完成** | Agent 完成任务时 | 执行时间、产出物、完成状态 | ❌ |
| 🎉 **PR 就绪** | PR 创建完成 | PR 链接、检查清单 | ❌ |
| ✅ **任务完成** | 整体任务完成 | 任务摘要、结果 | ❌ |
| ❌ **任务失败** | 任务执行失败 | 失败原因、重试次数 | ✅ |
| 🚨 **人工介入** | 需要人工处理 | 详细信息、建议 | ✅ |
| 🚀 **部署确认** | 等待部署确认 | 部署信息、操作指引 | ✅ |

---

## 📋 配置说明

### 配置文件

`cluster_config_v2.json` → `notifications.dingtalk`

### 配置项

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "mode": "enterprise_app",
      "admin_user_ids": ["356820521035955"],
      
      "agent_task_notifications": {
        "enabled": true,           // 是否启用 Agent 任务通知
        "notify_on_assign": true,  // 任务分配时通知
        "notify_on_complete": true, // 任务完成时通知
        "include_task_details": true, // 包含任务详情
        "include_time_estimate": true // 包含预计时间
      },
      
      "events": [
        "agent_task_assigned",    // 任务分配
        "agent_task_complete",    // 任务完成
        "pr_ready",               // PR 就绪
        "task_complete",          // 任务完成
        "task_failed",            // 任务失败
        "human_intervention_needed" // 人工介入
      ],
      
      "at_all": {
        "agent_task_assigned": false,
        "agent_task_complete": false,
        "pr_ready": false,
        "task_complete": false,
        "task_failed": true,
        "human_intervention_needed": true
      }
    }
  }
}
```

---

## 📱 通知示例

### 1. 📥 任务分配通知

```markdown
## 📥 Agent 任务分配通知

**任务 ID**: test-task-001
**Agent**: Codex 后端专家
**任务类型**: backend_development
**阶段**: 3_development
**优先级**: 🔴 high

---

### 📋 任务详情

**描述**: 实现用户登录功能

**预计耗时**: 30 分钟

**创建时间**: 2026-03-21 11:45:00

---

🤖 Agent 集群自动通知
```

### 2. ✅ 任务完成通知

```markdown
## ✅ Agent 任务完成

**任务 ID**: test-task-001
**Agent**: Codex 后端专家
**任务类型**: backend_development
**阶段**: 3_development
**状态**: ✅ completed

---

### 📊 执行结果

**描述**: 实现用户登录功能

**执行时间**: 125.5 秒

**完成时间**: 2026-03-21 11:47:05

---

### 📈 产出物

- login.py (src/auth/login.py)
- test_login.py (tests/test_login.py)

---

🤖 Agent 集群自动通知
```

---

## 🔧 使用方式

### 方式 1: 自动触发（推荐）

任务分配和完成通知会**自动触发**，无需手动调用。

**触发时机**:
- `spawn_sub_agent()` → 发送任务分配通知
- `complete_sub_agent()` → 发送任务完成通知

### 方式 2: 手动触发

```python
from notifiers.dingtalk import get_notifier
import json

# 加载配置
with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

# 获取通知器
notifier = get_notifier(config)

# 发送任务分配通知
task_info = {
    "id": "task-001",
    "description": "实现用户登录",
    "agent": "codex",
    "type": "backend_development",
    "phase": "3_development",
    "priority": "high"
}

agent_info = {
    "name": "Codex 后端专家",
    "role": "backend_specialist"
}

notifier.notify_agent_task_assigned(task_info, agent_info)

# 发送任务完成通知
result_info = {
    "status": "completed",
    "execution_time": 125.5,
    "deliverables": [
        {"name": "login.py", "path": "src/auth/login.py"}
    ]
}

notifier.notify_agent_task_complete(task_info, result_info, agent_info)
```

---

## 📊 通知流程

```
任务创建
   ↓
spawn_sub_agent()
   ↓
📥 发送任务分配通知 → 钉钉
   ↓
Agent 执行任务
   ↓
任务完成
   ↓
complete_sub_agent()
   ↓
✅ 发送任务完成通知 → 钉钉
```

---

## 🎯 优先级说明

| 优先级 | 图标 | 说明 |
|--------|------|------|
| `high` | 🔴 | 高优先级，紧急任务 |
| `medium` | 🟡 | 中优先级，重要任务 |
| `normal` | 🟢 | 普通优先级，日常任务 |

---

## 📈 产出物格式

支持多种产出物类型：

### 代码文件
```json
{
  "deliverables": [
    {"name": "login.py", "path": "src/auth/login.py"},
    {"name": "test_login.py", "path": "tests/test_login.py"}
  ]
}
```

### PR
```json
{
  "deliverables": [],
  "pr_number": 123,
  "pr_url": "https://github.com/xxx/pull/123"
}
```

### 修改文件统计
```json
{
  "deliverables": [],
  "files_modified": 5
}
```

---

## ⚙️ 高级配置

### 1. 只接收特定 Agent 的通知

```json
{
  "agent_task_notifications": {
    "enabled": true,
    "filter_agents": ["codex", "claude-code"],  // 只接收这些 Agent 的通知
    "exclude_agents": ["tester"]  // 排除这些 Agent
  }
}
```

### 2. 按阶段过滤通知

```json
{
  "agent_task_notifications": {
    "enabled": true,
    "filter_phases": ["3_development", "4_testing"]  // 只接收这些阶段
  }
}
```

### 3. 按优先级过滤

```json
{
  "agent_task_notifications": {
    "enabled": true,
    "min_priority": "medium"  // 只接收 medium 及以上优先级
  }
}
```

---

## 🔍 故障排查

### 问题 1: 收不到任务分配通知

**检查**:
1. `agent_task_notifications.enabled` 是否为 `true`
2. `notify_on_assign` 是否为 `true`
3. `admin_user_ids` 是否配置正确

### 问题 2: 通知内容不完整

**检查**:
1. `include_task_details` 是否为 `true`
2. `include_time_estimate` 是否为 `true`
3. task_info 是否包含必需字段

### 问题 3: 通知延迟

**可能原因**:
1. Token 刷新（约 2 小时一次）
2. 网络延迟
3. 钉钉 API 限流

**解决**:
- Token 已自动缓存，无需手动处理
- 检查网络连接
- 避免频繁发送（建议间隔 > 1 秒）

---

## 📖 相关文件

| 文件 | 说明 |
|------|------|
| `cluster_config_v2.json` | 配置文件 |
| `notifiers/dingtalk.py` | 通知实现 |
| `cluster_manager.py` | 集成逻辑 |
| `test_agent_task_notifications.sh` | 测试脚本 |

---

## 🧪 测试

运行测试脚本：

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./test_agent_task_notifications.sh
```

**预期输出**:
```
======================================
📧 Agent 任务通知测试
======================================

1️⃣  语法检查...
   ✅ 语法检查通过

2️⃣  测试任务分配通知...
✅ 钉钉消息发送成功 (processQueryId: ...)
结果：✅ 成功

3️⃣  测试任务完成通知...
✅ 钉钉消息发送成功 (processQueryId: ...)
结果：✅ 成功

======================================
测试完成！
```

---

## 🎯 最佳实践

1. **合理设置优先级**
   - 紧急任务用 `high`
   - 日常任务用 `normal`

2. **提供详细的任务描述**
   - 描述清晰有助于理解任务
   - 包含关键信息（如模块、功能）

3. **记录产出物**
   - 完成任务时记录修改的文件
   - 便于追踪和 Review

4. **避免通知过载**
   - 非关键任务可不发送完成通知
   - 使用优先级过滤

---

**状态**: ✅ 功能已上线并测试通过  
**下次更新**: 根据使用反馈优化
