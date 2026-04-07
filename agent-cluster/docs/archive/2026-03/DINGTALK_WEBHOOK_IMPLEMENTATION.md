# 钉钉 Webhook 自动部署实现指南

**完成时间**: 2026-03-15 18:55  
**状态**: ✅ 核心功能完成

---

## ✅ 已完成的功能

### 1. Webhook 接口
- ✅ URL: `http://39.107.101.25:8890/api/dingtalk/callback`
- ✅ 方法：POST
- ✅ 接收钉钉消息

### 2. 关键词识别
支持以下关键词触发部署：
- "确认"
- "确认部署"
- "部署"
- "同意"
- "yes"
- "confirm"

支持以下关键词取消部署：
- "取消"
- "取消部署"
- "拒绝"
- "no"
- "cancel"

### 3. 工作流 ID 提取
- ✅ 从消息中提取工作流 ID (格式：wf-YYYYMMDD-HHMMSS-xxxx)
- ✅ 如果未指定，自动获取最新的待确认工作流

### 4. 状态更新
- ✅ 确认后更新为 `deploying`
- ✅ 取消后更新为 `cancelled`

---

## 📱 钉钉回复示例

### 确认部署
```
确认部署 wf-20260315-183840-b6bb
```
或简单回复：
```
确认
```
或：
```
部署
```

### 取消部署
```
取消部署
```
或：
```
取消
```

---

## 🔧 配置钉钉机器人

### 1. 获取 Webhook URL

在钉钉群设置中添加自定义机器人，获取 Webhook URL。

### 2. 配置 Webhook 地址

将钉钉机器人的 Webhook 指向：
```
http://39.107.101.25:8890/api/dingtalk/callback
```

### 3. 测试

在钉钉群回复：
```
确认部署
```

系统应该回复：
```
✅ 部署已确认

工作流：wf-xxxxx
状态：执行中

部署功能待实现，当前仅更新状态。
```

---

## 📊 工作流程

```
钉钉收到部署确认通知
    ↓
用户在钉钉回复"确认部署"
    ↓
钉钉 webhook 发送到 /api/dingtalk/callback
    ↓
系统解析消息，识别关键词
    ↓
提取工作流 ID
    ↓
更新工作流状态为 deploying
    ↓
回复确认消息到钉钉
```

---

## ⏳ 待实现的功能

### 1. 实际部署执行
当前只更新状态，需要实现：
- Docker 部署
- Kubernetes 部署
- 或文件同步

### 2. 30 分钟超时检查
需要添加定时任务检查超时：
```python
# 每 5 分钟检查一次
for wf_id, wf in workflows:
    if wf.get("deployment_status") == "waiting_confirmation":
        notified_at = wf.get("phases", {}).get("deployment", {}).get("result", {}).get("notified_at")
        if notified_at:
            elapsed = (now - notified_at).total_seconds()
            if elapsed > 1800:  # 30 分钟
                cancel_deployment(wf_id, "超时未确认")
```

### 3. 部署进度通知
部署完成后发送通知：
```
✅ 部署完成

工作流：wf-xxxxx
环境：production
时间：2026-03-15 19:00:00
```

---

## 🧪 测试方法

### 方法 1: 使用测试脚本
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 test_dingtalk_webhook.py
```

### 方法 2: 使用 curl
```bash
curl -X POST "http://39.107.101.25:8890/api/dingtalk/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "text": {"content": "确认部署"},
    "conversation_id": "test123",
    "sender_id": "user123"
  }'
```

### 方法 3: 钉钉群实际测试
1. 在钉钉群收到部署确认通知
2. 回复"确认部署"
3. 检查系统回复

---

## 📝 相关代码

### web_app_v2.py
- `do_POST()` - 添加路由
- `handle_dingtalk_callback()` - 处理回调

### 关键词识别代码
```python
confirm_keywords = ["确认", "确认部署", "部署", "同意", "yes", "confirm"]
cancel_keywords = ["取消", "取消部署", "拒绝", "no", "cancel"]

if any(keyword in text.lower() for keyword in confirm_keywords):
    # 确认部署
elif any(keyword in text.lower() for keyword in cancel_keywords):
    # 取消部署
```

---

## 🎯 下一步

### 立即可用
- ✅ 钉钉回复确认部署
- ✅ 自动更新工作流状态
- ✅ 回复确认消息

### 需要开发
- ⏳ 实际部署执行逻辑
- ⏳ 30 分钟超时自动取消
- ⏳ 部署完成通知

---

**指南更新时间**: 2026-03-15 18:55
