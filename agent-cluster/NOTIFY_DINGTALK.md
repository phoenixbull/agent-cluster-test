# 钉钉通知配置指南

## ✅ 修改状态

**Telegram → 钉钉 修改已完成！**

| 项目 | 状态 | 说明 |
|------|------|------|
| 钉钉通知模块 | ✅ 已创建 | `notifiers/dingtalk.py` (11.6KB) |
| 配置文件更新 | ✅ 已完成 | `cluster_config_v2.json` |
| Telegram 配置 | ✅ 已禁用 | 保留配置但 enabled: false |
| 钉钉配置 | ✅ 已启用 | 所有通知事件已配置 |

---

## 📋 配置步骤

### 第 1 步：创建钉钉机器人

1. 打开钉钉群 → 群设置 → 智能群助手
2. 点击"添加机器人" → 选择"自定义"
3. 配置机器人：
   - **机器人名字**: Agent 集群助手
   - **发送消息类型**: 选择"文本"或"Markdown"
   - **安全设置**: 选择"加签密钥"（推荐）或"IP 地址"

4. 完成后复制：
   - **Webhook URL**: `https://oapi.dingtalk.com/robot/send?access_token=xxx`
   - **加签密钥**: `SECxxx`

### 第 2 步：更新配置文件

编辑 `cluster_config_v2.json` 中的通知配置：

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
      "secret": "SECxxx",
      "events": [
        "task_complete",
        "task_failed",
        "pr_ready",
        "human_intervention_needed",
        "daily_summary",
        "cluster_status"
      ],
      "at_all": {
        "task_complete": false,
        "task_failed": true,
        "pr_ready": false,
        "human_intervention_needed": true,
        "daily_summary": false,
        "cluster_status": false
      }
    },
    "telegram": {
      "enabled": false
    }
  }
}
```

**替换以下内容**：
- `YOUR_TOKEN` → 你的钉钉机器人 token
- `YOUR_SECRET` → 你的加签密钥（如果有）

### 第 3 步：应用配置

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 备份当前配置
cp cluster_config.json cluster_config_backup.json

# 应用 v2.0 配置（包含钉钉通知）
cp cluster_config_v2.json cluster_config.json

# 验证配置
python3 cluster_manager.py status
```

### 第 4 步：测试通知

```bash
# 发送测试通知
python3 -c "
from notifiers.dingtalk import ClusterNotifier

notifier = ClusterNotifier(
    'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
    'YOUR_SECRET'
)

# 测试 PR 就绪通知
notifier.notify_pr_ready(
    {'id': 'test', 'description': '测试任务', 'agent': 'codex'},
    {
        'pr_number': 999,
        'pr_url': 'https://github.com/test/pull/999',
        'status': 'ready_for_merge',
        'ci_status': 'success',
        'reviews': {'approved': 2},
        'execution_time': 60.0,
        'has_screenshots': True
    }
)

print('✅ 测试通知已发送')
"
```

---

## 📱 通知类型

### 1. PR 就绪通知（人工 Review）

```markdown
## 🎉 PR 已就绪，可以 Review！

**任务**: 实现自定义邮件模板功能

**Agent**: codex

**分支**: feat/custom-templates

**PR**: #341

---

### ✅ 检查清单

- ✅ CI 全绿
- ✅ Codex Reviewer 批准
- ✅ Gemini Reviewer 批准
- ✅ UI 截图已附

---

🔗 [查看 PR](https://github.com/xxx/pull/341)

⏱️ Review 预计需要 5-10 分钟
```

**@设置**: 不@所有人（仅通知相关人员）

---

### 2. 任务完成通知

```markdown
## ✅ 任务完成

**任务**: 实现自定义邮件模板功能

**Agent**: codex

**PR**: #341

**状态**: ready_for_merge

**CI**: success

**审查通过**: 2 个

**执行时间**: 1800.5 秒

---

🔗 [查看 PR](...)

📋 可以 Review 并合并了。
```

**@设置**: 不@所有人

---

### 3. 任务失败通知

```markdown
## ❌ 任务失败

**任务**: 实现自定义邮件模板功能

**Agent**: codex

**问题**: CI 失败：单元测试未通过

**状态**: failed

**重试次数**: 3/3

**执行时间**: 3600.0 秒

---

⚠️ 需要人工介入。

📋 请检查并决定下一步操作。
```

**@设置**: @所有人（需要紧急处理）

---

### 4. 需要人工介入通知

```markdown
## 🚨 需要人工介入

**任务**: 实现自定义邮件模板功能

**Agent**: codex

**失败原因**: 多次重试失败

**重试次数**: 3/3

---

### 📊 执行结果

```json
{...}
```

---

⚠️ 请检查并决定下一步操作。
```

**@设置**: @所有人（需要紧急处理）

---

### 5. 每日摘要（可选）

```markdown
## 📊 每日工作摘要

**日期**: 2026-03-04

---

### 📈 统计数据

- **完成任务**: 15
- **失败任务**: 2
- **PR 合并**: 12
- **代码提交**: 94
- **人工投入**: 25 分钟

---

### 🎯 任务分布

- **后端任务**: 8
- **前端任务**: 5
- **设计任务**: 2
- **Bug 修复**: 4

---

### ⚡ 效率指标

- **平均任务耗时**: 45 分钟
- **AI 完成率**: 88.2%
- **人工介入率**: 11.8%

---

🤖 Agent 集群自动报告
```

**@设置**: 不@所有人（日报）

---

### 6. 集群状态通知（可选）

```markdown
## 🟢 集群状态

**集群**: openclaw-codex-cluster

**状态**: healthy

---

### 🤖 Agent 状态

- **活跃 Agent**: 3/3
- **运行中任务**: 5
- **等待中任务**: 2

---

### 📈 资源使用

- **内存使用**: 4.2GB / 16GB
- **CPU 使用**: 35%
- **今日成本**: ¥12.50

---

🕐 更新时间：2026-03-04 14:00:00
```

**@设置**: 不@所有人

---

## 🔧 代码集成

### 在 monitor.py 中使用

```python
from notifiers.dingtalk import ClusterNotifier

# 初始化通知器
notifier = ClusterNotifier(
    webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
    secret="SECxxx"
)

# 在监控逻辑中使用
async def notify_completion(self, task, result):
    """通知任务完成"""
    self.notifier.notify_pr_ready(task, result)
```

### 在 ralph_loop.py 中使用

```python
from notifiers.dingtalk import ClusterNotifier

class RalphLoop:
    def __init__(self, orchestrator, notifier=None):
        self.notifier = notifier or ClusterNotifier(...)
    
    async def _notify_human_intervention(self, task, result, failure_reason):
        """通知人工介入"""
        self.notifier.notify_human_intervention(task, result, failure_reason)
```

---

## ✅ 验证清单

- [ ] 钉钉机器人已创建
- [ ] Webhook URL 已复制到配置文件
- [ ] 加签密钥已配置（如果有）
- [ ] 配置文件已更新并应用
- [ ] 测试通知已发送成功
- [ ] 钉钉群收到测试消息
- [ ] 通知格式正确（Markdown 渲染正常）
- [ ] @设置符合预期

---

## 🚀 快速应用

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 1. 编辑配置文件，替换 token 和 secret
nano cluster_config_v2.json

# 2. 应用配置
cp cluster_config_v2.json cluster_config.json

# 3. 测试通知
python3 -c "from notifiers.dingtalk import ClusterNotifier; \
notifier = ClusterNotifier('YOUR_WEBHOOK', 'YOUR_SECRET'); \
notifier.notify_pr_ready({'id': 'test', 'description': '测试', 'agent': 'codex'}, \
{'pr_number': 1, 'status': 'ready', 'ci_status': 'success', 'reviews': {'approved': 2}}); \
print('✅ 测试完成')"

# 4. 检查钉钉群是否收到消息
```

---

## 📝 注意事项

1. **安全设置**: 强烈建议启用加签密钥，防止 Webhook 被滥用
2. **频率限制**: 钉钉机器人有发送频率限制，避免短时间内发送过多消息
3. **消息长度**: Markdown 消息最长 4000 字符
4. **网络访问**: 确保服务器可以访问 `oapi.dingtalk.com`
5. **时区**: 钉钉消息时间显示为服务器时区，注意调整

---

**修改完成！** ✅

现在所有通知都会发送到钉钉，而不是 Telegram。
