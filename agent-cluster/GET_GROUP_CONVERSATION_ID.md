# 📱 获取群会话 ID 的简单方法

## 方法 1: 通过钉钉群设置（推荐）⭐

### 步骤

1. **打开钉钉群**
2. **点击右上角「...」或群设置**
3. **向下滚动找到「群信息」或「更多信息」**
4. **查找以下字段之一**:
   - 群 ID
   - 群号
   - Conversation ID

### 格式

群会话 ID 通常是以下格式之一：
- `cid_xxxxxx`
- `group_xxxxxx`
- 或者一长串字符如 `cidwo2nkGbyBArYd1Sjbh8A`

---

## 方法 2: 通过机器人日志（需要 @机器人）

### 步骤

1. **在钉钉群里 @机器人 发送消息**
   - 例如："@Agent 集群助手 测试"

2. **运行命令查看日志**:
   ```bash
   # 方法 A: 使用 openclaw 命令
   openclaw logs --max-bytes 100000 | grep -A 10 "Inbound" | tail -30
   
   # 方法 B: 直接查看日志文件
   journalctl -u openclaw-gateway --since "2 minutes ago" | grep -i conversation
   ```

3. **找到 `conversationId` 字段**:
   ```json
   {
     "conversationId": "cid_xxxxxx",  // ← 这就是你要的！
     "conversationType": "group",
     "userId": "356820521035955"
   }
   ```

---

## 方法 3: 使用 Python 脚本捕获

### 步骤

1. **运行捕获脚本**:
   ```bash
   cd /home/admin/.openclaw/workspace/agent-cluster
   python3 capture_conversation_id.py
   ```

2. **在钉钉群里 @机器人 发送消息**

3. **脚本会显示 conversationId**

---

## 🎯 推荐方法

**推荐使用方法 1（钉钉群设置）**，因为：
- ✅ 最直接，无需技术工具
- ✅ 信息准确
- ✅ 随时可查看

---

## 📝 配置示例

获取到群 ID 后，编辑 `cluster_config_v2.json`:

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "mode": "enterprise_app",
      "admin_user_ids": ["356820521035955"],
      "deploy_group_conversation_id": "cid_xxxxxx",  // ← 填入你的群 ID
      ...
    }
  }
}
```

---

## ⚠️ 注意事项

1. **区分消息 ID 和群会话 ID**
   - 消息 ID: `msgWWnrlsTfjdTRXCTrZ3Wc0w==` (每次消息都不同)
   - 群会话 ID: `cid_xxxxxx` (固定不变)

2. **群会话 ID 是固定的**
   - 不会随消息变化
   - 同一个群始终使用同一个 ID

3. **机器人必须在群里**
   - 如果机器人不在群里，无法发送群消息

---

## 🔍 验证配置

配置完成后，运行测试：

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./test_dingtalk_enterprise.sh
```

如果配置了群 ID，会看到：
```
4️⃣  测试群消息...
   使用群 ID: cid_xxxxxx
   ✅ 群消息发送成功
```

---

**更新时间**: 2026-03-21 11:35  
**状态**: 等待用户提供群会话 ID
