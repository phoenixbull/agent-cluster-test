# 钉钉渠道统一配置指南 - 方案 A

## 📊 当前配置状态

### OpenClaw IM Channels（已配置）

```json
{
  "clientId": "dingi8bd93ixhrm34vbd",
  "clientSecret": "PlyR_LbuiaIPVqocSlqj0x313N8p6PbKTGP4OP80K_Vx5PgDxMHK7IFApfy_-jfR",
  "robotCode": "dingi8bd93ixhrm34vbd",
  "corpId": "ding4ec28b66e08c978fee0f45d8e4f7c288",
  "agentId": "4286960567",
  "dmPolicy": "open",
  "groupPolicy": "open",
  "messageType": "markdown"
}
```

**特点**：
- ✅ Stream 模式（WebSocket 长连接）
- ✅ 无需公网 IP
- ✅ 双向通信（可发送可接收）
- ✅ 已在 OpenClaw 中运行

---

## 🎯 迁移目标

将 Agent 集群的钉钉通知整合到 OpenClaw IM Channels，**统一使用企业自建应用**：

```
┌─────────────────┐
│  OpenClaw Core  │
│  (Gateway)      │
└────────┬────────┘
         │
    ┌────▼────┐
    │ DingTalk│
    │ Channel │
    │ (Stream)│
    └────┬────┘
         │
    ┌────▼────────────────────┐
    │  钉钉企业自建应用        │
    │  - Client ID            │
    │  - Client Secret        │
    │  - Agent ID             │
    └─────────────────────────┘
         │
    ┌────▼────┐     ┌──────────────┐
    │ 发送通知 │     │ 接收群消息   │
    │ (API)   │     │ (WebSocket)  │
    └─────────┘     └──────────────┘
```

---

## 📋 配置步骤

### 步骤 1: 更新 `cluster_config_v2.json`

修改钉钉通知配置，使用企业应用凭证：

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

**变化**：
- ❌ 移除 `webhook` 和 `secret`（群机器人配置）
- ✅ 添加 `clientId`, `clientSecret`, `corpId`, `agentId`（企业应用配置）
- ✅ 添加 `mode: "enterprise_app"`

---

### 步骤 2: 更新 `notifiers/dingtalk.py`

修改发送逻辑，使用企业内部 API 而非 Webhook：

```python
#!/usr/bin/env python3
"""
钉钉通知模块 - 企业自建应用版
使用企业内部 API 发送消息，统一渠道配置
"""

import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Any
import http.client


class DingTalkNotifier:
    """
    钉钉通知器 - 企业自建应用
    使用企业内部 API 发送消息
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化钉钉通知器
        
        Args:
            config: 配置字典，包含 clientId, clientSecret, corpId, agentId
        """
        self.client_id = config.get("clientId", "")
        self.client_secret = config.get("clientSecret", "")
        self.corp_id = config.get("corpId", "")
        self.agent_id = config.get("agentId", "")
        
        self.access_token = None
        self.token_expires_at = 0
        self.token_lock = False
    
    def _get_access_token(self) -> str:
        """获取访问令牌（自动缓存）"""
        now = time.time()
        
        # 检查缓存
        if self.access_token and now < self.token_expires_at:
            return self.access_token
        
        # 防止并发请求
        if self.token_lock:
            time.sleep(0.1)
            return self._get_access_token()
        
        self.token_lock = True
        
        try:
            # 调用钉钉 API 获取 token
            url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
            data = json.dumps({
                "appKey": self.client_id,
                "appSecret": self.client_secret
            }).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                method='POST'
            )
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                self.access_token = result.get('accessToken')
                # Token 有效期 2 小时，提前 10 分钟刷新
                self.token_expires_at = now + 6600
                return self.access_token
        except Exception as e:
            print(f"❌ 获取访问令牌失败：{e}")
            raise e
        finally:
            self.token_lock = False
    
    def send_markdown(self, user_ids: List[str], title: str, text: str, at_all: bool = False):
        """
        发送 Markdown 消息给用户
        
        Args:
            user_ids: 用户 ID 列表
            title: 消息标题
            text: Markdown 格式正文
            at_all: 是否@所有人
        """
        token = self._get_access_token()
        
        url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
        
        data = json.dumps({
            "agentId": self.agent_id,
            "userIdList": user_ids,
            "msgKey": "sampleMarkdown",
            "msgParam": json.dumps({
                "title": title,
                "text": text
            }, ensure_ascii=False)
        }).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'x-acs-dingtalk-access-token': token
            },
            method='POST'
        )
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('processQueryId') is not None
        except Exception as e:
            print(f"❌ 发送消息失败：{e}")
            return False
    
    def send_to_group(self, conversation_id: str, title: str, text: str, at_all: bool = False):
        """
        发送消息到群聊
        
        Args:
            conversation_id: 群会话 ID
            title: 消息标题
            text: Markdown 格式正文
            at_all: 是否@所有人
        """
        token = self._get_access_token()
        
        url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"
        
        at_user_ids = ["@ALL"] if at_all else []
        
        data = json.dumps({
            "agentId": self.agent_id,
            "conversationId": conversation_id,
            "msgKey": "sampleMarkdown",
            "msgParam": json.dumps({
                "title": title,
                "text": text,
                "at": {
                    "atUserIds": at_user_ids,
                    "isAtAll": at_all
                }
            }, ensure_ascii=False)
        }).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'x-acs-dingtalk-access-token': token
            },
            method='POST'
        )
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('processQueryId') is not None
        except Exception as e:
            print(f"❌ 发送群消息失败：{e}")
            return False


class ClusterNotifier:
    """
    集群通知管理器
    封装各种通知场景
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化集群通知器
        
        Args:
            config: 钉钉配置字典
        """
        self.dingtalk = DingTalkNotifier(config)
        self.config = config
    
    def notify_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
        """通知任务完成"""
        title = f"✅ 任务完成 - {task.get('id', 'N/A')}"
        
        text = f"""## ✅ 任务完成

**任务**: {task.get('description', task.get('id', 'N/A'))}

**Agent**: {task.get('agent', 'N/A')}

**PR**: #{result.get('pr_number', 'N/A')}

**状态**: {result.get('status', 'N/A')}

**CI**: {result.get('ci_status', 'N/A')}

**审查通过**: {result.get('reviews', {}).get('approved', 0)} 个

**执行时间**: {result.get('execution_time', 0):.1f} 秒

---

🔗 [查看 PR]({result.get('pr_url', '#')})

📋 可以 Review 并合并了。
"""
        # 发送给指定用户（需要从配置获取）
        return self.dingtalk.send_markdown(["admin"], title, text, at_all=False)
    
    def notify_task_failed(self, task: Dict[str, Any], result: Dict[str, Any], failure_reason: str):
        """通知任务失败"""
        title = f"❌ 任务失败 - {task.get('id', 'N/A')}"
        
        text = f"""## ❌ 任务失败

**任务**: {task.get('description', task.get('id', 'N/A'))}

**Agent**: {task.get('agent', 'N/A')}

**问题**: {failure_reason}

**状态**: {result.get('status', 'N/A')}

**重试次数**: {task.get('retry_count', 0)}/3

**执行时间**: {result.get('execution_time', 0):.1f} 秒

---

⚠️ 需要人工介入。

📋 请检查并决定下一步操作。
"""
        return self.dingtalk.send_markdown(["admin"], title, text, at_all=True)
    
    def notify_pr_ready(self, task: Dict[str, Any], result: Dict[str, Any]):
        """通知 PR 已就绪"""
        pr_number = result.get('pr_number', 'N/A')
        pr_url = result.get('pr_url', f'https://github.com/xxx/pull/{pr_number}')
        
        title = f"🎉 PR #{pr_number} 已就绪"
        
        text = f"""## 🎉 PR 已就绪，可以 Review！

**任务**: {task.get('description', task.get('id', 'N/A'))}

**Agent**: {task.get('agent', 'N/A')}

**分支**: {task.get('branch', 'N/A')}

**PR**: #{pr_number}

---

### ✅ 检查清单

- ✅ CI 全绿
- ✅ Codex Reviewer 批准
- ✅ Gemini Reviewer 批准
- {"✅ UI 截图已附" if result.get('has_screenshots') else "⚠️ 无 UI 改动"}

---

🔗 [查看 PR]({pr_url})

⏱️ Review 预计需要 5-10 分钟
"""
        return self.dingtalk.send_markdown(["admin"], title, text, at_all=False)
    
    def send_deploy_confirmation(self, workflow: Dict, pr_info: Dict, conversation_id: str = None):
        """发送部署确认通知"""
        title = "🚀 部署确认通知"
        
        text = f"""## 🚀 部署确认通知

**工作流**: {workflow.get('id', 'N/A')}
**需求**: {workflow.get('description', 'N/A')[:50]}
**PR**: #{pr_info.get('pr_number', 'N/A')}
**PR 链接**: {pr_info.get('pr_url', 'N/A')}

---

### 📋 部署信息

- **项目**: {workflow.get('project', '默认项目')}
- **环境**: 生产环境
- **提交**: {pr_info.get('commit_hash', 'N/A')}

---

### ⚠️ 部署前检查

- [ ] 代码审查通过
- [ ] 测试覆盖率 ≥ 80%
- [ ] 无高危 Bug
- [ ] CI/CD 通过

---

### 📌 操作指引

请在 **30 分钟** 内回复确认是否部署：

- 回复 **"部署"** 或 **"确认"** → 开始部署
- 回复 **"取消"** → 取消部署

**超时未确认将自动取消部署**

---

🤖 AI 产品开发智能体
"""
        if conversation_id:
            # 发送到群
            return self.dingtalk.send_to_group(conversation_id, title, text, at_all=True)
        else:
            # 发送给个人
            return self.dingtalk.send_markdown(["admin"], title, text, at_all=True)
    
    def send_deploy_complete(self, workflow: Dict, deploy_result: Dict):
        """发送部署完成通知"""
        title = "✅ 部署完成通知"
        
        text = f"""## ✅ 部署完成通知

**工作流**: {workflow.get('id', 'N/A')}
**需求**: {workflow.get('description', 'N/A')[:50]}
**状态**: {deploy_result.get('status', 'N/A')}

---

### 📊 部署结果

- **环境**: {deploy_result.get('environment', '生产环境')}
- **部署时间**: {deploy_result.get('deployed_at', 'N/A')}
- **访问地址**: {deploy_result.get('url', 'N/A')}

---

### 📋 部署详情

**成功**: {deploy_result.get('success', False)}
**耗时**: {deploy_result.get('duration', 'N/A')}

---

🤖 AI 产品开发智能体
"""
        return self.dingtalk.send_markdown(["admin"], title, text, at_all=False)
    
    def send_deploy_cancelled(self, workflow: Dict, reason: str = "超时未确认"):
        """发送部署取消通知"""
        title = "❌ 部署取消通知"
        
        text = f"""## ❌ 部署取消通知

**工作流**: {workflow.get('id', 'N/A')}
**需求**: {workflow.get('description', 'N/A')[:50]}
**原因**: {reason}

---

### 📌 后续操作

1. 检查工作流状态
2. 重新提交部署或修改代码

---

🤖 AI 产品开发智能体
"""
        return self.dingtalk.send_markdown(["admin"], title, text, at_all=False)
    
    def notify_human_intervention(self, task: Dict[str, Any], result: Dict[str, Any], failure_reason: str):
        """通知需要人工介入"""
        title = f"🚨 需要人工介入 - {task.get('id', 'N/A')}"
        
        text = f"""## 🚨 需要人工介入

**任务**: {task.get('description', task.get('id', 'N/A'))}

**Agent**: {task.get('agent', 'N/A')}

**失败原因**: {failure_reason}

**重试次数**: {task.get('retry_count', 0)}/3

---

### 📊 执行结果

```json
{json.dumps(result, indent=2, ensure_ascii=False)}
```

---

⚠️ 请检查并决定下一步操作。
"""
        return self.dingtalk.send_markdown(["admin"], title, text, at_all=True)


# 便捷函数
_notifier: Optional[ClusterNotifier] = None


def get_notifier(config: Dict[str, Any]) -> ClusterNotifier:
    """获取通知器实例"""
    global _notifier
    if _notifier is None:
        _notifier = ClusterNotifier(config)
    return _notifier
```

---

### 步骤 3: 更新 `web_app_v2.py`

修改导入和初始化逻辑：

```python
# 在文件顶部修改导入
from notifiers.dingtalk import get_notifier  # 使用新的企业应用版本

# 在 WebUIHandler 类中修改初始化
def __init__(self, *args, **kwargs):
    # ... 其他初始化代码 ...
    self.dingtalk_config = self._load_dingtalk_config()
    self.dingtalk_notifier = get_notifier(self.dingtalk_config)  # 使用企业应用通知器
    super().__init__(*args, **kwargs)

def _load_dingtalk_config(self):
    """加载钉钉配置（企业应用模式）"""
    default = {
        "mode": "enterprise_app",
        "clientId": "",
        "clientSecret": "",
        "corpId": "",
        "agentId": ""
    }
    if CLUSTER_CONFIG.exists():
        try:
            cfg = self.cluster_config.get("notifications", {}).get("dingtalk", {})
            default.update(cfg)
        except: pass
    return default
```

---

### 步骤 4: 修改回调处理

由于使用 Stream 模式，**无需配置回调地址**！

OpenClaw DingTalk Channel 已经通过 WebSocket 接收消息，你需要：

1. **在 OpenClaw 中配置消息路由**，将钉钉消息转发到 agent-cluster
2. 或使用现有的 `dingtalk_receiver.py` 作为独立服务

---

## 🎯 架构对比

### 之前（混合模式）

```
发送通知 → 群机器人 Webhook
         ↓
      钉钉群
         ↓
接收消息 ← 企业应用回调（需公网）
```

### 现在（统一模式）

```
┌─────────────────┐
│  OpenClaw Core  │
│  (Gateway)      │
└────────┬────────┘
         │ WebSocket (Stream)
    ┌────▼────┐
    │ DingTalk│
    │ Channel │
    └────┬────┘
         │
    ┌────▼────────────────────┐
    │  钉钉企业自建应用        │
    │  (同一套凭证)           │
    └─────────────────────────┘
         │
    ┌────▼────┐     ┌──────────────┐
    │ 发送通知 │     │ 接收群消息   │
    │ (API)   │     │ (WebSocket)  │
    └─────────┘     └──────────────┘
```

---

## ✅ 优势

| 对比项 | 混合模式 | 统一模式 |
|--------|----------|----------|
| **配置复杂度** | 两套配置 | 一套配置 |
| **公网要求** | 需要（回调） | 不需要（Stream） |
| **渠道一致性** | ❌ 不一致 | ✅ 一致 |
| **维护成本** | 高 | 低 |
| **消息追溯** | ❌ 困难 | ✅ 容易 |
| **安全性** | 中 | 高 |

---

## 📋 迁移检查清单

- [ ] 备份现有配置
- [ ] 更新 `cluster_config_v2.json`
- [ ] 更新 `notifiers/dingtalk.py`
- [ ] 更新 `web_app_v2.py`
- [ ] 测试发送通知
- [ ] 测试接收消息
- [ ] 验证部署确认流程
- [ ] 更新文档

---

## 🔧 测试命令

```bash
# 1. 语法检查
cd /home/admin/.openclaw/workspace/agent-cluster
python3 -m py_compile web_app_v2.py
python3 -m py_compile notifiers/dingtalk.py

# 2. 重启 Web 服务
pkill -f "python3 web_app_v2.py"
python3 web_app_v2.py --port 8890 &

# 3. 查看日志
tail -f logs/web_app.log

# 4. 测试发送
curl -X POST http://localhost:8890/api/test-dingtalk
```

---

**需要我帮你执行具体的代码修改吗？**
