# 📋 钉钉通知配置与测试指南

## ✅ 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 钉钉通知模块 | ✅ 已创建 | `notifiers/dingtalk.py` |
| 模块加载测试 | ✅ 通过 | 所有类和方法可用 |
| 配置文件 | ⚠️ 待更新 | 需要配置 Webhook URL |
| 实际通知测试 | ⏳ 待配置 | 需要钉钉机器人 Webhook |

---

## 🔧 配置步骤

### 第 1 步：创建钉钉机器人

1. **打开钉钉群**
   - 选择要接收通知的钉钉群

2. **添加机器人**
   - 群设置 → 智能群助手 → 添加机器人
   - 选择 **"自定义"** 机器人

3. **配置机器人**
   ```
   机器人名字：Agent 集群助手
   发送消息类型：Markdown
   安全设置：加签密钥 (推荐)
   ```

4. **复制配置信息**
   - ✅ **Webhook URL**: `https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx`
   - ✅ **加签密钥**: `SECxxxxxxxxxx` (如果选择了加签)

---

### 第 2 步：运行测试脚本

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 运行交互式测试
python3 test_dingtalk.py
```

脚本会提示输入：
- **Webhook URL**: 粘贴第 1 步复制的 URL
- **加签密钥**: 粘贴第 1 步复制的密钥（可选）

测试会发送 5 条消息：
1. ✅ 基本文本测试
2. 🎉 PR 就绪通知
3. ✅ 任务完成通知
4. ❌ 任务失败通知 (@所有人)
5. 🚨 人工介入通知 (@所有人)

---

### 第 3 步：验证通知

检查钉钉群是否收到以下消息：

#### 消息 1: 基本文本测试
```
🤖 Agent 集群通知测试

这是一条测试消息，如果您看到这条消息，说明钉钉通知功能正常工作！
```

#### 消息 2: PR 就绪通知
```
## 🎉 PR 已就绪，可以 Review！

**任务**: 测试钉钉通知功能
**Agent**: codex
**PR**: #999

### ✅ 检查清单
- ✅ CI 全绿
- ✅ Codex Reviewer 批准
- ✅ Gemini Reviewer 批准

🔗 [查看 PR](...)
⏱️ Review 预计需要 5-10 分钟
```

#### 消息 3: 任务完成通知
```
## ✅ 任务完成

**任务**: 测试钉钉通知功能
**Agent**: codex
**PR**: #1000
**审查通过**: 2 个
```

#### 消息 4: 任务失败通知 (@所有人)
```
## ❌ 任务失败

**任务**: 修复支付模块 bug
**问题**: CI 失败：单元测试未通过
**重试次数**: 3/3

⚠️ 需要人工介入。
```

#### 消息 5: 人工介入通知 (@所有人)
```
## 🚨 需要人工介入

**任务**: 重构核心模块
**失败原因**: 多次重试失败

⚠️ 请检查并决定下一步操作。
```

---

## 🔍 故障排查

### 问题 1: 收不到消息

**检查项**:
- [ ] Webhook URL 是否正确
- [ ] 机器人是否在群内
- [ ] 服务器是否可以访问 `oapi.dingtalk.com`

**测试网络**:
```bash
curl -I https://oapi.dingtalk.com
```

### 问题 2: 消息发送失败

**错误信息**: `400 invalid access_token`

**解决方法**:
- 检查 Webhook URL 中的 `access_token` 是否正确
- 重新创建机器人获取新的 token

**错误信息**: `401 timestamp is expired`

**解决方法**:
- 检查服务器时间是否准确
- 确保加签密钥正确

### 问题 3: Markdown 渲染异常

**检查项**:
- [ ] Markdown 格式是否正确
- [ ] 链接 URL 是否完整
- [ ] 消息长度是否超过 4000 字符

---

## 🚀 快速测试（一行命令）

如果有 Webhook URL，可以直接运行：

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 替换 YOUR_WEBHOOK 为实际的 URL
python3 -c "
from notifiers.dingtalk import DingTalkNotifier
n = DingTalkNotifier('YOUR_WEBHOOK', None)
n.send_text('🤖 钉钉通知测试 - 如果您看到这条消息，说明配置成功！', at_all=False)
print('✅ 测试消息已发送')
"
```

---

## 📝 配置文件更新

测试成功后，更新 `cluster_config.json`:

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
      "secret": "YOUR_SECRET",
      "events": [
        "task_complete",
        "task_failed",
        "pr_ready",
        "human_intervention_needed"
      ]
    },
    "telegram": {
      "enabled": false
    }
  }
}
```

---

## ✅ 完成标志

当你在钉钉群看到测试消息时，说明：

- ✅ 钉钉通知模块工作正常
- ✅ Webhook 配置正确
- ✅ 可以接收 Agent 集群通知
- ✅ 人工 Review 通知将发送到钉钉

---

**下一步**: 请提供钉钉机器人 Webhook URL，我可以帮你运行实际测试！
