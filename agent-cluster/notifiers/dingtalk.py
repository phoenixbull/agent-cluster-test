#!/usr/bin/env python3
"""
钉钉通知模块
用于发送 Agent 集群状态通知到钉钉群
"""

import json
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Any


class DingTalkNotifier:
    """
    钉钉通知器
    支持发送 Markdown 格式消息到钉钉群
    """
    
    def __init__(self, webhook_url: str, secret: str = None):
        """
        初始化钉钉通知器
        
        Args:
            webhook_url: 钉钉机器人 Webhook URL
            secret: 加签密钥（可选，如果开启了加签保护）
        """
        self.webhook_url = webhook_url
        self.secret = secret
    
    def _generate_sign(self, timestamp: str) -> str:
        """生成加签"""
        if not self.secret:
            return ""
        
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return sign
    
    def _build_webhook_url(self) -> str:
        """构建带签名的 Webhook URL"""
        timestamp = str(round(datetime.now().timestamp() * 1000))
        
        if self.secret:
            sign = self._generate_sign(timestamp)
            return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
        else:
            return self.webhook_url
    
    def _send_request(self, data: Dict[str, Any]) -> bool:
        """发送 HTTP 请求"""
        try:
            # 创建 SSL 上下文（忽略证书验证）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(
                self._build_webhook_url(),
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('errcode') == 0
        except Exception as e:
            print(f"❌ 发送钉钉通知失败：{e}")
            return False
    
    def send_markdown(self, title: str, text: str, at_all: bool = True, at_mobiles: List[str] = None):
        """
        发送 Markdown 格式消息
        
        Args:
            title: 消息标题
            text: Markdown 格式的正文
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表
        """
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "isAtAll": at_all,
                "atMobiles": at_mobiles or []
            }
        }
        
        return self._send_request(data)
    
    def send_text(self, content: str, at_all: bool = True, at_mobiles: List[str] = None):
        """
        发送文本格式消息
        
        Args:
            content: 文本内容
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表
        """
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "isAtAll": at_all,
                "atMobiles": at_mobiles or []
            }
        }
        
        return self._send_request(data)
    
    def send_link(self, title: str, text: str, pic_url: str, message_url: str):
        """
        发送链接卡片消息
        
        Args:
            title: 标题
            text: 说明
            pic_url: 图片 URL
            message_url: 点击跳转的 URL
        """
        data = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "picUrl": pic_url,
                "messageUrl": message_url
            }
        }
        
        return self._send_request(data)


class ClusterNotifier:
    """
    集群通知管理器
    封装各种通知场景
    """
    
    def __init__(self, dingtalk_webhook: str, dingtalk_secret: str = None):
        self.dingtalk = DingTalkNotifier(dingtalk_webhook, dingtalk_secret)
    
    def notify_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        通知任务完成
        
        Args:
            task: 任务信息
            result: 执行结果
        """
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
        
        return self.dingtalk.send_markdown(title, text, at_all=False)
    
    def notify_task_failed(self, task: Dict[str, Any], result: Dict[str, Any], failure_reason: str):
        """
        通知任务失败
        
        Args:
            task: 任务信息
            result: 执行结果
            failure_reason: 失败原因
        """
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
        
        return self.dingtalk.send_markdown(title, text, at_all=True)
    
    def notify_pr_ready(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        通知 PR 已就绪
        
        Args:
            task: 任务信息
            result: 执行结果
        """
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
        
        return self.dingtalk.send_markdown(title, text, at_all=False)
    

    def send_deploy_confirmation(self, workflow: Dict, pr_info: Dict):
        """发送部署确认通知（需要@所有人）"""
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

请在 **30 分钟** 内确认是否部署：

1. 查看 PR: {pr_info.get('pr_url', 'N/A')}
2. 检查代码变更
3. 确认部署或取消

**超时未确认将自动取消部署**

---

🤖 AI 产品开发智能体
"""
        
        try:
            self.dingtalk.send_markdown(title, text, at_all=True)
            print(f"   ✅ 部署确认通知已发送")
        except Exception as e:
            print(f"   ❌ 发送部署确认通知失败：{e}")
    
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
        
        try:
            self.dingtalk.send_markdown(title, text, at_all=False)
            print(f"   ✅ 部署完成通知已发送")
        except Exception as e:
            print(f"   ❌ 发送部署完成通知失败：{e}")
    
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
        
        try:
            self.dingtalk.send_markdown(title, text, at_all=False)
            print(f"   ✅ 部署取消通知已发送")
        except Exception as e:
            print(f"   ❌ 发送部署取消通知失败：{e}")

    def notify_human_intervention(self, task: Dict[str, Any], result: Dict[str, Any], failure_reason: str):
        """
        通知需要人工介入
        
        Args:
            task: 任务信息
            result: 执行结果
            failure_reason: 失败原因
        """
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
        
        return self.dingtalk.send_markdown(title, text, at_all=True)
    
    def notify_daily_summary(self, summary: Dict[str, Any]):
        """
        发送每日摘要
        
        Args:
            summary: 摘要信息
        """
        title = f"📊 每日摘要 - {datetime.now().strftime('%Y-%m-%d')}"
        
        text = f"""## 📊 每日工作摘要

**日期**: {datetime.now().strftime('%Y-%m-%d')}

---

### 📈 统计数据

- **完成任务**: {summary.get('completed_tasks', 0)}
- **失败任务**: {summary.get('failed_tasks', 0)}
- **PR 合并**: {summary.get('merged_prs', 0)}
- **代码提交**: {summary.get('commits', 0)}
- **人工投入**: {summary.get('human_time_minutes', 0)} 分钟

---

### 🎯 任务分布

- **后端任务**: {summary.get('backend_tasks', 0)}
- **前端任务**: {summary.get('frontend_tasks', 0)}
- **设计任务**: {summary.get('design_tasks', 0)}
- **Bug 修复**: {summary.get('bugfix_tasks', 0)}

---

### ⚡ 效率指标

- **平均任务耗时**: {summary.get('avg_task_time_minutes', 0)} 分钟
- **AI 完成率**: {summary.get('ai_success_rate', 0):.1f}%
- **人工介入率**: {summary.get('human_intervention_rate', 0):.1f}%

---

🤖 Agent 集群自动报告
"""
        
        return self.dingtalk.send_markdown(title, text, at_all=False)
    
    def notify_cluster_status(self, status: Dict[str, Any]):
        """
        通知集群状态
        
        Args:
            status: 集群状态信息
        """
        title = f"📊 集群状态 - {status.get('name', 'Agent Cluster')}"
        
        running_agents = status.get('running_agents', 0)
        total_agents = status.get('total_agents', 0)
        running_tasks = status.get('running_tasks', 0)
        
        # 状态图标
        if status.get('status') == 'healthy':
            status_icon = "🟢"
        elif status.get('status') == 'degraded':
            status_icon = "🟡"
        else:
            status_icon = "🔴"
        
        text = f"""## {status_icon} 集群状态

**集群**: {status.get('name', 'Agent Cluster')}

**状态**: {status.get('status', 'unknown')}

---

### 🤖 Agent 状态

- **活跃 Agent**: {running_agents}/{total_agents}
- **运行中任务**: {running_tasks}
- **等待中任务**: {status.get('pending_tasks', 0)}

---

### 📈 资源使用

- **内存使用**: {status.get('memory_usage', 'N/A')}
- **CPU 使用**: {status.get('cpu_usage', 'N/A')}
- **今日成本**: ¥{status.get('today_cost', 0):.2f}

---

🕐 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.dingtalk.send_markdown(title, text, at_all=False)


# 使用示例
def main():
    # 配置钉钉机器人
    WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    SECRET = "YOUR_SECRET"  # 如果开启了加签保护
    
    # 创建通知器
    notifier = ClusterNotifier(WEBHOOK_URL, SECRET)
    
    # 测试：任务完成通知
    task = {
        "id": "feat-custom-templates",
        "description": "实现自定义邮件模板功能",
        "agent": "codex",
        "branch": "feat/custom-templates"
    }
    
    result = {
        "pr_number": 341,
        "pr_url": "https://github.com/xxx/pull/341",
        "status": "ready_for_merge",
        "ci_status": "success",
        "reviews": {"approved": 3},
        "execution_time": 1800.5,
        "has_screenshots": True
    }
    
    notifier.notify_pr_ready(task, result)
    print("✅ 测试通知已发送")


if __name__ == "__main__":
    main()
