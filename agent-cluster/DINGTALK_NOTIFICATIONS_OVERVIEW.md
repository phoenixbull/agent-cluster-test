# 📧 钉钉通知集成清单

**更新时间**: 2026-03-21 11:52  
**版本**: V2.2.0

---

## 📊 钉钉通知集成总览

目前 Agent 集群中有 **5 个主要工作流/模块**集成了钉钉通知：

| 模块 | 通知类型 | 触发条件 | 状态 |
|------|----------|----------|------|
| **1. 监控脚本** | PR 就绪、任务失败、人工介入 | 自动监控 | ✅ 已上线 |
| **2. 集群管理器** | 任务分配、任务完成 | Agent 任务执行 | ✅ 已上线 |
| **3. 编排器 (Zoe)** | 人工介入 | 工作流异常 | ✅ 已上线 |
| **4. Ralph Loop** | 人工介入 | 智能重试失败 | ✅ 已上线 |
| **5. 告警系统** | 系统告警 | 监控指标异常 | ✅ 已上线 |

---

## 1️⃣ 监控脚本 (monitor.py)

**文件**: `monitor.py`  
**功能**: 每 10 分钟自动监控运行中的任务

### 通知类型

| 通知 | 触发条件 | 接收人 |
|------|----------|--------|
| 🎉 **PR 就绪** | PR 可合并（CI 全绿 + 2 个批准） | 管理员 |
| ❌ **任务失败** | 任务执行失败 | @所有人 |
| 🚨 **人工介入** | 需要人工处理 | @所有人 |

### 触发逻辑

```python
# monitor.py:280-300
async def monitor_all(self):
    for task in self.tasks.get("running", []):
        result = await self.monitor_task(task)
        
        if result["status"] == "ready_for_merge":
            await self.notify_completion(task, result)
            # → notify_pr_ready()
        
        elif result["status"] == "failed":
            await self.notify_failure(task, result)
            # → notify_human_intervention()
```

### 配置

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "events": ["pr_ready", "task_failed", "human_intervention_needed"]
    }
  }
}
```

---

## 2️⃣ 集群管理器 (cluster_manager.py)

**文件**: `cluster_manager.py`  
**功能**: 管理 Agent 任务执行和生命周期

### 通知类型

| 通知 | 触发条件 | 接收人 |
|------|----------|--------|
| 📥 **任务分配** | spawn_sub_agent() | 管理员 |
| ✅ **任务完成** | complete_sub_agent() | 管理员 |

### 触发逻辑

```python
# cluster_manager.py:410-450
def spawn_sub_agent(self, agent_id: str, task: str) -> str:
    session_id = self.create_session(agent_id, task)
    sub_agent = SubAgent(session_id, agent_id, task)
    
    # → 发送任务分配通知
    self._notify_task_assigned(sub_agent)
    
    return session_id

def complete_sub_agent(self, session_id: str, result: Dict):
    sub_agent.status = "completed"
    
    # → 发送任务完成通知
    self._notify_task_complete(sub_agent)
```

### 通知内容

**任务分配**:
- Agent 名称和角色
- 任务 ID 和描述
- 任务类型、阶段、优先级
- 预计耗时

**任务完成**:
- 执行时间
- 产出物列表（文件、PR 等）
- 完成状态

### 配置

```json
{
  "notifications": {
    "dingtalk": {
      "agent_task_notifications": {
        "enabled": true,
        "notify_on_assign": true,
        "notify_on_complete": true
      }
    }
  }
}
```

---

## 3️⃣ 编排器 - Zoe (orchestrator.py)

**文件**: `orchestrator.py`  
**功能**: 工作流编排和任务调度

### 通知类型

| 通知 | 触发条件 | 接收人 |
|------|----------|--------|
| 🚨 **人工介入** | 工作流执行异常 | @所有人 |

### 触发逻辑

```python
# orchestrator.py
try:
    result = await self.execute_phase(workflow_id, phase)
except Exception as e:
    # → 发送人工介入通知
    self.notifier.notify_human_intervention(
        task_info, result_info, str(e)
    )
```

---

## 4️⃣ Ralph Loop (ralph_loop.py)

**文件**: `ralph_loop.py`  
**功能**: 智能重试和学习循环

### 通知类型

| 通知 | 触发条件 | 接收人 |
|------|----------|--------|
| 🚨 **人工介入** | 重试 3 次后仍失败 | @所有人 |

### 触发逻辑

```python
# ralph_loop.py
async def execute_with_retry(self, task, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.execute(task)
        except Exception as e:
            if attempt == max_retries - 1:
                # → 发送人工介入通知
                await self._notify_human_intervention(task, result, str(e))
```

---

## 5️⃣ 告警系统 (utils/alert_manager.py)

**文件**: `utils/alert_manager.py`  
**功能**: 系统监控和告警管理

### 通知类型

| 通知 | 触发条件 | 接收人 |
|------|----------|--------|
| ⚠️ **系统告警** | 监控指标异常 | @所有人 |

### 告警规则

- CPU 使用率 > 90%
- 内存使用率 > 85%
- 任务失败率 > 20%
- API 错误率 > 10%

---

## 📋 完整通知类型清单

### 按通知对象分类

#### 个人通知（不@所有人）

| 通知类型 | 模块 | 说明 |
|----------|------|------|
| 📥 Agent 任务分配 | cluster_manager | Agent 接受新任务 |
| ✅ Agent 任务完成 | cluster_manager | Agent 完成任务 |
| 🎉 PR 就绪 | monitor | PR 可合并 |
| ✅ 任务完成 | monitor | 整体任务完成 |
| 🚀 部署完成 | deploy_listener | 部署成功 |

#### 群通知（@所有人）

| 通知类型 | 模块 | 说明 |
|----------|------|------|
| ❌ 任务失败 | monitor | 任务执行失败 |
| 🚨 人工介入 | orchestrator/ralph | 需要人工处理 |
| 🚀 部署确认 | deploy_listener | 等待部署确认 |
| ⚠️ 系统告警 | alert_manager | 监控指标异常 |

---

## 🎯 通知发送流程

```
┌─────────────────┐
│  工作流触发事件  │
│  (任务/PR/告警) │
└────────┬────────┘
         │
    ┌────▼────┐
    │ 检测事件 │
    │  类型   │
    └────┬────┘
         │
    ┌────▼─────────────────┐
    │ 选择通知类型          │
    │ - 个人通知 / 群通知   │
    │ - @所有人 / 不@       │
    └────┬─────────────────┘
         │
    ┌────▼────┐
    │ 构建    │
    │ 消息体  │
    └────┬────┘
         │
    ┌────▼────┐
    │ 调用    │
    │ 钉钉 API│
    └────┬────┘
         │
    ┌────▼────┐
    │ 钉钉    │
    │ 推送    │
    └─────────┘
```

---

## ⚙️ 配置管理

### 全局配置

位置：`cluster_config_v2.json`

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "mode": "enterprise_app",
      "admin_user_ids": ["356820521035955"],
      
      "agent_task_notifications": {
        "enabled": true,
        "notify_on_assign": true,
        "notify_on_complete": true
      },
      
      "events": [
        "agent_task_assigned",
        "agent_task_complete",
        "pr_ready",
        "task_complete",
        "task_failed",
        "human_intervention_needed"
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

### 各模块配置

| 模块 | 配置项 | 默认值 |
|------|--------|--------|
| monitor.py | 自动启用 | - |
| cluster_manager.py | agent_task_notifications.enabled | true |
| orchestrator.py | 自动启用 | - |
| ralph_loop.py | 自动启用 | - |
| alert_manager.py | 自动启用 | - |

---

## 🧪 测试方法

### 1. 测试监控脚本通知

```bash
# 触发 PR 就绪场景
python3 monitor.py --test-pr-ready
```

### 2. 测试 Agent 任务通知

```bash
# 运行测试脚本
./test_agent_task_notifications.sh
```

### 3. 测试人工介入通知

```bash
# 触发失败场景
python3 orchestrator.py --test-failure
```

---

## 📊 通知统计（示例）

假设一天内有 10 个任务执行：

| 通知类型 | 数量 | 说明 |
|----------|------|------|
| 📥 任务分配 | 10 | 每个任务开始时 |
| ✅ 任务完成 | 8 | 成功完成的任务 |
| 🎉 PR 就绪 | 5 | 生成 PR 的任务 |
| ❌ 任务失败 | 2 | 失败的任务 |
| 🚨 人工介入 | 1 | 需要人工处理 |

**每日通知总数**: 约 20-30 条

---

## 🔍 故障排查

### 问题 1: 收不到某个模块的通知

**检查**:
1. 该模块是否启用了钉钉通知
2. 配置文件中对应 events 是否开启
3. 日志中是否有发送记录

### 问题 2: 通知内容不完整

**检查**:
1. 数据源是否完整（task_info, result_info）
2. 通知方法是否正确构建消息体

### 问题 3: 通知延迟

**可能原因**:
1. Token 刷新（约 2 小时一次）
2. 网络延迟
3. 钉钉 API 限流

---

## 📖 相关文档

- [AGENT_TASK_NOTIFICATIONS.md](./AGENT_TASK_NOTIFICATIONS.md) - Agent 任务通知详解
- [DINGTALK_CONFIG_GUIDE.md](./DINGTALK_CONFIG_GUIDE.md) - 钉钉配置指南
- [MIGRATION_COMPLETE_REPORT.md](./MIGRATION_COMPLETE_REPORT.md) - 企业应用迁移报告

---

**状态**: ✅ 所有工作流通知已集成并测试通过  
**下次更新**: 根据使用反馈优化通知策略
