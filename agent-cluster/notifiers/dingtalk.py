#!/usr/bin/env python3
"""
钉钉通知模块 - 企业自建应用版
使用企业内部 API 发送消息，统一渠道配置

与 OpenClaw DingTalk Channel 使用同一套凭证：
- clientId (AppKey)
- clientSecret (AppSecret)
- corpId (企业 ID)
- agentId (应用 ID)

文档：https://open.dingtalk.com/document/orgapp/server-api-overview
"""

import json
import time
import urllib.parse
import urllib.request
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Any


class DingTalkNotifier:
    """
    钉钉通知器 - 企业自建应用
    使用企业内部 API 发送消息
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化钉钉通知器
        
        Args:
            config: 配置字典，包含 clientId, clientSecret, corpId, agentId, robotCode
        """
        self.client_id = config.get("clientId", "")
        self.client_secret = config.get("clientSecret", "")
        self.corp_id = config.get("corpId", "")
        self.agent_id = config.get("agentId", "")
        self.robot_code = config.get("robotCode", "")
        
        self.access_token = None
        self.token_expires_at = 0
        self.token_lock = False
        
        if not all([self.client_id, self.client_secret, self.agent_id]):
            print("⚠️  钉钉配置不完整，通知功能可能不可用")
    
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
                print(f"✅ 获取钉钉访问令牌成功，有效期至 {datetime.fromtimestamp(self.token_expires_at).strftime('%H:%M:%S')}")
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
            user_ids: 用户 ID 列表（钉钉 userId）
            title: 消息标题
            text: Markdown 格式正文
            at_all: 是否@所有人
        """
        try:
            token = self._get_access_token()
            
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            
            # 构建 @ 列表
            at_user_ids = ["@ALL"] if at_all else []
            
            data = json.dumps({
                "agentId": self.agent_id,
                "robotCode": self.robot_code,
                "userIds": user_ids,
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
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                process_id = result.get('processQueryId')
                if process_id:
                    print(f"✅ 钉钉消息发送成功 (processQueryId: {process_id})")
                    return True
                else:
                    print(f"⚠️  钉钉消息发送失败：{result}")
                    return False
        except Exception as e:
            print(f"❌ 发送钉钉消息失败：{e}")
            return False
    
    def send_to_group(self, conversation_id: str, title: str, text: str, at_all: bool = False):
        """
        发送消息到群聊
        
        Args:
            conversation_id: 群会话 ID（群机器人 webhook 中的 groupId）
            title: 消息标题
            text: Markdown 格式正文
            at_all: 是否@所有人
        """
        try:
            token = self._get_access_token()
            
            url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"
            
            at_user_ids = ["@ALL"] if at_all else []
            
            data = json.dumps({
                "agentId": self.agent_id,
                "robotCode": self.robot_code,
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
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                process_id = result.get('processQueryId')
                if process_id:
                    print(f"✅ 钉钉群消息发送成功 (conversationId: {conversation_id})")
                    return True
                else:
                    print(f"⚠️  钉钉群消息发送失败：{result}")
                    return False
        except Exception as e:
            print(f"❌ 发送钉钉群消息失败：{e}")
            return False
    
    def send_text(self, user_ids: List[str], content: str):
        """
        发送纯文本消息
        
        Args:
            user_ids: 用户 ID 列表
            content: 文本内容
        """
        try:
            token = self._get_access_token()
            
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            
            data = json.dumps({
                "agentId": self.agent_id,
                "userIdList": user_ids,
                "msgKey": "sampleText",
                "msgParam": json.dumps({
                    "content": content
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
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('processQueryId') is not None
        except Exception as e:
            print(f"❌ 发送文本消息失败：{e}")
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
        self.deploy_group_id = config.get("deploy_group_conversation_id", "")
        self.admin_user_ids = config.get("admin_user_ids", ["admin"])
    
    def _get_at_all_flag(self, event: str) -> bool:
        """获取事件是否@所有人"""
        at_all_config = self.config.get("at_all", {})
        return at_all_config.get(event, False)
    
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
        at_all = self._get_at_all_flag('task_complete')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
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
        at_all = self._get_at_all_flag('task_failed')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
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
        at_all = self._get_at_all_flag('pr_ready')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
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
        at_all = self._get_at_all_flag('deploy_confirmation')
        conv_id = conversation_id or self.deploy_group_id
        
        if conv_id:
            return self.dingtalk.send_to_group(conv_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
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
        at_all = self._get_at_all_flag('deploy_complete')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
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
        at_all = self._get_at_all_flag('deploy_cancelled')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
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
        at_all = self._get_at_all_flag('human_intervention_needed')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)


# 便捷函数
_notifier: Optional[ClusterNotifier] = None


def get_notifier(config: Dict[str, Any]) -> ClusterNotifier:
    """获取通知器实例"""
    global _notifier
    if _notifier is None:
        _notifier = ClusterNotifier(config)
    return _notifier


def reset_notifier():
    """重置通知器实例（用于配置更新后）"""
    global _notifier
    _notifier = None


# 使用示例
def main():
    """测试通知功能"""
    # 配置（从 cluster_config_v2.json 读取）
    config = {
        "mode": "enterprise_app",
        "clientId": "dingi8bd93ixhrm34vbd",
        "clientSecret": "PlyR_LbuiaIPVqocSlqj0x313N8p6PbKTGP4OP80K_Vx5PgDxMHK7IFApfy_-jfR",
        "corpId": "ding4ec28b66e08c978fee0f45d8e4f7c288",
        "agentId": "4286960567",
        "admin_user_ids": ["admin"]
    }
    
    notifier = get_notifier(config)
    
    # 测试发送消息
    test_task = {
        "id": "test-task-001",
        "description": "测试任务",
        "agent": "codex"
    }
    
    test_result = {
        "pr_number": 1,
        "pr_url": "https://github.com/test/pull/1",
        "status": "ready_for_merge",
        "ci_status": "success",
        "reviews": {"approved": 2},
        "execution_time": 120.5
    }
    
    print("\n📧 测试发送 PR 就绪通知...")
    notifier.notify_pr_ready(test_task, test_result)
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()
