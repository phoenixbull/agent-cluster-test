# 钉钉双向通知配置指南

## 概述

Agent 集群 V2.2 支持**双向钉钉通知**：

| 方向 | 功能 | 状态 |
|------|------|------|
| **发送** | 任务完成、PR 就绪、部署确认等通知 | ✅ 已配置 |
| **接收** | 钉钉群消息触发、部署确认回复 | ✅ 新增 |

## 发送通知（已配置）

### 现有配置

在 `cluster_config_v2.json` 中已配置：

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
      "secret": "SECxxx",
      "events": ["phase_complete", "pr_ready", "task_failed", "human_intervention_needed"],
      "at_all": {
        "task_failed": true,
        "human_intervention_needed": true
      }
    }
  }
}
```

### 支持的通知事件

| 事件 | 说明 | @所有人 |
|------|------|---------|
| `pr_ready` | PR 就绪，可 Review | ❌ |
| `task_complete` | 任务完成 | ❌ |
| `task_failed` | 任务失败 | ✅ |
| `human_intervention_needed` | 需要人工介入 | ✅ |
| `deploy_confirmation` | 部署确认通知 | ✅ |
| `deploy_complete` | 部署完成 | ❌ |
| `deploy_cancelled` | 部署取消 | ❌ |

---

## 接收消息（新增）

### 功能

1. **钉钉群消息触发 Agent 任务**
2. **部署确认回复**（在钉钉群回复"部署"或"取消"）

### 配置步骤

#### 1️⃣ 创建钉钉企业自建应用

1. 访问 [钉钉开放平台](https://open.dingtalk.com/)
2. 进入 **企业应用** → **创建应用**
3. 选择 **企业内部开发** → **H5 微应用**
4. 填写应用信息（名称如 "Agent 集群助手"）

#### 2️⃣ 配置事件订阅

1. 在应用管理页面，进入 **事件订阅**
2. 点击 **开通事件订阅**
3. 配置回调地址：

```
回调地址：http://服务器 IP:8890/api/dingtalk/callback
或（推荐）：https://你的域名/api/dingtalk/callback
```

4. 设置 **Token**（回调验证 token）：
   - 默认：`openclaw_callback_token_2026`
   - 可在 `cluster_config_v2.json` 中修改

5. 选择订阅的事件类型：
   - ✅ 群消息
   - ✅ 机器人消息
   - ✅ 应用通知

6. 保存后，钉钉会发送验证请求

#### 3️⃣ 配置加签密钥（可选但推荐）

1. 在事件订阅页面，开启 **签名验证**
2. 复制 **签名密钥**
3. 在 `web_app_v2.py` 中配置（或添加到 config）：

```python
# 在 cluster_config_v2.json 中添加
"dingtalk": {
  "callback_token": "你的回调 token",
  "callback_secret": "你的签名密钥"
}
```

#### 4️⃣ 添加机器人到群

1. 在钉钉群设置 → **智能群助手**
2. 添加机器人 → 选择你创建的企业应用
3. 设置机器人名称和头像

#### 5️⃣ 测试回调

发送测试消息到群，查看日志：

```bash
tail -f /home/admin/.openclaw/workspace/agent-cluster/logs/web_app.log
```

看到类似输出表示成功：

```
📱 收到钉钉消息：部署 (from 老五)
✅ 收到部署确认：老五
```

---

## 使用方式

### 部署确认流程

1. **触发部署** → Agent 集群发送部署确认通知到钉钉群
2. **群内回复** → 在钉钉群回复：
   - "部署" / "确认" / "deploy" / "approve" → 开始部署
   - "取消" / "cancel" / "reject" → 取消部署
3. **超时处理** → 30 分钟未确认自动取消

### 消息触发任务（待扩展）

未来可扩展支持：

```
@Agent 集群 创建任务：实现用户登录功能
@Agent 集群 状态查询
@Agent 集群 PR #123 审查结果
```

---

## 安全配置

### 1. Nginx 反向代理（推荐）

如果通过公网访问，建议配置 Nginx：

```nginx
location /api/dingtalk/callback {
    proxy_pass http://127.0.0.1:8890/api/dingtalk/callback;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # 仅允许钉钉 IP 访问（可选）
    # allow 钉钉 IP 段;
    # deny all;
}
```

### 2. 防火墙配置

```bash
# 仅开放 443 端口（HTTPS）
ufw allow 443/tcp

# 或限制特定 IP
ufw allow from 钉钉 IP to any port 8890
```

### 3. Token 安全

- 修改默认 `callback_token`
- 定期轮换密钥
- 使用 HTTPS 传输

---

## 故障排查

### 回调验证失败

**症状**: 钉钉显示 "回调失败"

**解决**:
1. 检查回调地址是否公网可访问
2. 确认 Token 配置一致
3. 查看日志：`tail -f logs/web_app.log`

### 消息未收到

**症状**: 钉钉发送消息后无日志

**解决**:
1. 确认机器人已添加到群
2. 检查事件订阅是否开启 "群消息"
3. 确认应用权限

### 签名验证失败

**症状**: 日志显示 "签名验证失败"

**解决**:
1. 确认回调 Token 与钉钉配置一致
2. 检查时间同步（服务器时间误差 < 5 分钟）

---

## API 端点

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/dingtalk/callback` | GET | ❌ | 钉钉回调验证 |
| `/api/dingtalk/callback` | POST | ❌ | 接收钉钉消息 |

---

## 配置示例

### cluster_config_v2.json 完整配置

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
      "secret": "SEC_YOUR_SECRET",
      "callback_token": "openclaw_callback_token_2026",
      "callback_secret": "YOUR_CALLBACK_SECRET",
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

## 下一步

### 已实现 ✅
- [x] 钉钉回调端点
- [x] 签名验证
- [x] 部署确认处理
- [x] 消息解析

### 待扩展 📋
- [ ] 群消息触发任务创建
- [ ] 自然语言任务解析
- [ ] 任务状态查询
- [ ] PR Review 通知增强
- [ ] 多群支持

---

## 相关文档

- [钉钉开放平台文档](https://open.dingtalk.com/document/orgapp/receive-callbacks)
- [钉钉事件订阅](https://open.dingtalk.com/document/orgapp/event-subscription)
- [Agent 集群 API 文档](./API_DOCUMENTATION.md)

---

**最后更新**: 2026-03-21  
**版本**: V2.2.0
