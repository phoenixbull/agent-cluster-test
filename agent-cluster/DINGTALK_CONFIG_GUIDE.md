# 📧 钉钉通知配置指南

## ✅ 测试状态

- ✅ **Token 获取**: 成功
- ✅ **语法检查**: 通过
- ⏳ **消息发送**: 需要配置用户 ID 或群 ID

---

## 🔧 配置步骤

### 步骤 1: 获取钉钉用户 ID

**方法 A: 通过钉钉管理后台**

1. 访问 [钉钉管理后台](https://oa.dingtalk.com/)
2. 进入 **通讯录**
3. 找到你的账号
4. 点击查看详情
5. 复制 **userId** 字段（不是姓名！）

**方法 B: 通过 API 获取**

```bash
# 先获取 token
TOKEN=$(curl -X POST "https://api.dingtalk.com/v1.0/oauth2/accessToken" \
  -H "Content-Type: application/json" \
  -d '{"appKey":"dingi8bd93ixhrm34vbd","appSecret":"PlyR_LbuiaIPVqocSlqj0x313N8p6PbKTGP4OP80K_Vx5PgDxMHK7IFApfy_-jfR"}' \
  | jq -r '.accessToken')

# 获取用户信息（需要 unionId）
curl -X GET "https://api.dingtalk.com/v1.0/users/你的 unionId" \
  -H "x-acs-dingtalk-access-token: $TOKEN"
```

**方法 C: 通过 OpenClaw 日志**

如果你在钉钉中与机器人对话，OpenClaw 日志会显示你的 userId：

```bash
openclaw logs | grep dingtalk
```

---

### 步骤 2: 配置 admin_user_ids

编辑 `cluster_config_v2.json`：

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "mode": "enterprise_app",
      "clientId": "dingi8bd93ixhrm34vbd",
      "clientSecret": "PlyR_LbuiaIPVqocSlqj0x313N8p6PbKTGP4OP80K_Vx5PgDxMHK7IFApfy_-jfR",
      "corpId": "ding4ec28b66e08c978fee0f45d8e4f7c288",
      "agentId": "4286960567",
      "robotCode": "dingi8bd93ixhrm34vbd",
      "admin_user_ids": ["你的 userId"],  // ← 添加这行
      "events": [...],
      "at_all": {...}
    }
  }
}
```

**示例**：
```json
"admin_user_ids": ["manager123", "developer456"]
```

---

### 步骤 3: （可选）配置群会话 ID

如果需要发送群通知，需要配置群会话 ID：

**获取群会话 ID**：

1. 在钉钉群中 @机器人 发送任意消息
2. 查看 OpenClaw 日志：
   ```bash
   openclaw logs | grep dingtalk
   ```
3. 找到 `conversationId` 字段（格式：`cid_xxxxxx`）

**配置**：
```json
{
  "notifications": {
    "dingtalk": {
      "deploy_group_conversation_id": "cid_xxxxxx"
    }
  }
}
```

---

### 步骤 4: 验证配置

运行测试脚本：

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./test_dingtalk_enterprise.sh
```

**预期输出**：
```
======================================
📧 钉钉企业应用通知测试
======================================

1️⃣  语法检查...
   ✅ 语法检查通过

2️⃣  测试获取访问令牌...
   ✅ 获取 Token 成功：deeed51957eb34aebd59...

3️⃣  测试发送消息...
   使用用户 ID: ['manager123']
   ✅ 测试消息发送成功

4️⃣  测试群消息...
   使用群 ID: cid_xxxxxx
   ✅ 群消息发送成功

======================================
测试完成！
```

---

### 步骤 5: 重启服务

```bash
# 停止旧服务
pkill -f "python3 web_app_v2.py"

# 启动新服务
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app_v2.py --port 8890 &

# 查看日志
tail -f logs/web_app.log
```

---

## 📊 完整配置示例

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "mode": "enterprise_app",
      "clientId": "dingi8bd93ixhrm34vbd",
      "clientSecret": "PlyR_LbuiaIPVqocSlqj0x313N8p6PbKTGP4OP80K_Vx5PgDxMHK7IFApfy_-jfR",
      "corpId": "ding4ec28b66e08c978fee0f45d8e4f7c288",
      "agentId": "4286960567",
      "robotCode": "dingi8bd93ixhrm34vbd",
      "admin_user_ids": ["manager123"],
      "deploy_group_conversation_id": "cid_abc123xyz",
      "events": [
        "phase_complete",
        "pr_ready",
        "deploy_confirmation",
        "deploy_complete",
        "deploy_cancelled",
        "task_failed",
        "human_intervention_needed"
      ],
      "at_all": {
        "phase_complete": false,
        "pr_ready": false,
        "deploy_confirmation": true,
        "deploy_complete": false,
        "deploy_cancelled": false,
        "task_failed": true,
        "human_intervention_needed": true
      }
    }
  }
}
```

---

## 🔍 故障排查

### 问题 1: userId 不存在

**错误**: `staffId.notExisted`

**解决**:
1. 确认 userId 正确（从钉钉管理后台复制）
2. 确认用户在应用可见范围内
3. 确认用户未被禁用

### 问题 2: 群会话 ID 不存在

**错误**: `conversation not found`

**解决**:
1. 确认机器人已在群内
2. 确认群会话 ID 格式正确（`cid_xxxxxx`）
3. 在群内发送一条消息激活会话

### 问题 3: 应用权限不足

**错误**: `permission denied`

**解决**:
1. 钉钉开放平台 → 应用管理
2. 权限管理 → 添加必要权限
3. 重新发布应用

---

## 📝 注意事项

1. **userId 不是用户名**：必须用钉钉系统的 userId
2. **应用可见范围**：用户必须在应用的可见范围内
3. **Token 缓存**：Token 自动缓存 2 小时，无需担心频繁刷新
4. **API 配额**：个人消息 500 次/分钟，群消息 2000 次/分钟

---

## 📖 相关文档

- [MIGRATION_COMPLETE_REPORT.md](./MIGRATION_COMPLETE_REPORT.md) - 迁移报告
- [MIGRATION_TO_ENTERPRISE_APP.md](./MIGRATION_TO_ENTERPRISE_APP.md) - 迁移指南
- [钉钉用户管理 API](https://open.dingtalk.com/document/orgapp/query-user-details)

---

**更新时间**: 2026-03-21 11:07  
**状态**: ✅ 配置指南完成
