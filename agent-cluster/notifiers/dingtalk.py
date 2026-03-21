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
                # 钉钉 API 返回 processQueryKey 或 processQueryId 都表示成功
                process_id = result.get('processQueryId') or result.get('processQueryKey')
                if process_id:
                    print(f"✅ 钉钉消息发送成功 (processQueryId: {process_id[:30]}...)")
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
    
    def notify_agent_task_assigned(self, task: Dict[str, Any], agent_info: Dict[str, Any] = None):
        """
        通知 Agent 任务已分配
        
        Args:
            task: 任务信息
            agent_info: Agent 详细信息
        """
        task_id = task.get('id', 'N/A')
        agent_name = agent_info.get('name', task.get('agent', 'N/A')) if agent_info else task.get('agent', 'N/A')
        task_desc = task.get('description', '无描述')
        task_type = task.get('type', task.get('task_type', 'N/A'))
        phase = task.get('phase', 'N/A')
        priority = task.get('priority', 'normal')
        estimated_time = task.get('estimated_time', 'N/A')
        
        # 优先级图标
        priority_icon = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
        
        title = f"📥 {agent_name} 接受新任务"
        
        text = f"""## 📥 Agent 任务分配通知

**任务 ID**: {task_id}
**Agent**: {agent_name}
**任务类型**: {task_type}
**阶段**: {phase}
**优先级**: {priority_icon} {priority}

---

### 📋 任务详情

**描述**: {task_desc[:100]}{'...' if len(task_desc) > 100 else ''}

**预计耗时**: {estimated_time}

**创建时间**: {task.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}

---

🤖 Agent 集群自动通知
"""
        at_all = self._get_at_all_flag('agent_task_assigned')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    def notify_agent_task_complete(self, task: Dict[str, Any], result: Dict[str, Any], agent_info: Dict[str, Any] = None):
        """
        通知 Agent 任务完成
        
        Args:
            task: 任务信息
            result: 执行结果
            agent_info: Agent 详细信息
        """
        task_id = task.get('id', 'N/A')
        agent_name = agent_info.get('name', task.get('agent', 'N/A')) if agent_info else task.get('agent', 'N/A')
        task_desc = task.get('description', '无描述')
        task_type = task.get('type', task.get('task_type', 'N/A'))
        phase = task.get('phase', 'N/A')
        execution_time = result.get('execution_time', 0)
        status = result.get('status', 'completed')
        
        # 状态图标
        status_icon = "✅" if status == "completed" else "⚠️" if status == "partial" else "❌"
        
        title = f"{status_icon} {agent_name} 完成任务"
        
        text = f"""## {status_icon} Agent 任务完成

**任务 ID**: {task_id}
**Agent**: {agent_name}
**任务类型**: {task_type}
**阶段**: {phase}
**状态**: {status_icon} {status}

---

### 📊 执行结果

**描述**: {task_desc[:100]}{'...' if len(task_desc) > 100 else ''}

**执行时间**: {execution_time:.1f} 秒

**完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

### 📈 产出物

{self._format_deliverables(result)}

---

🤖 Agent 集群自动通知
"""
        at_all = self._get_at_all_flag('agent_task_complete')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    def _format_deliverables(self, result: Dict[str, Any]) -> str:
        """格式化产出物列表"""
        deliverables = result.get('deliverables', [])
        if not deliverables:
            # 尝试从其他字段获取
            if result.get('pr_number'):
                return f"- PR: #{result.get('pr_number')}"
            elif result.get('files_modified'):
                return f"- 修改文件：{len(result.get('files_modified', []))} 个"
            elif result.get('output'):
                return f"- 输出：{result.get('output', '')[:100]}"
            else:
                return "- 无特定产出物"
        
        items = []
        for d in deliverables[:5]:  # 最多显示 5 个
            if isinstance(d, dict):
                name = d.get('name', '未知')
                path = d.get('path', '')
                items.append(f"- {name}{' (' + path + ')' if path else ''}")
            else:
                items.append(f"- {d}")
        
        if len(deliverables) > 5:
            items.append(f"- ... 还有 {len(deliverables) - 5} 个")
        
        return '\n'.join(items)
    
    def _get_coverage_message(self, coverage: float) -> str:
        """获取覆盖率消息"""
        if coverage >= 80:
            return "### ✅ 覆盖率达标\n\n测试覆盖率 ≥ 80%，满足质量要求。"
        elif coverage >= 60:
            return "### ⚠️ 覆盖率不足\n\n测试覆盖率 < 80%，建议补充测试用例。"
        else:
            return "### 🔴 覆盖率严重不足\n\n测试覆盖率 < 60%，需要大量补充测试用例。"
    
    # ========== Phase 阶段通知 ==========
    
    def notify_phase1_prd_complete(self, workflow: Dict, prd_info: Dict[str, Any]):
        """
        Phase 1: PRD 完成通知
        
        Args:
            workflow: 工作流信息
            prd_info: PRD 相关信息
        """
        workflow_id = workflow.get('id', 'N/A')
        pm_name = prd_info.get('pm_name', 'Product Manager')
        requirement = prd_info.get('requirement', '无需求描述')
        prd_url = prd_info.get('prd_url', '#')
        user_stories_count = prd_info.get('user_stories', 0)
        acceptance_criteria_count = prd_info.get('acceptance_criteria', 0)
        
        title = f"📄 PRD 完成 - {workflow_id}"
        
        text = f"""## 📄 Phase 1: PRD 文档完成

**工作流**: {workflow_id}
**产品经理**: {pm_name}
**需求**: {requirement[:80]}{'...' if len(requirement) > 80 else ''}

---

### 📋 产出物

- **PRD 文档**: [查看文档]({prd_url})
- **用户故事**: {user_stories_count} 个
- **验收标准**: {acceptance_criteria_count} 个

---

### ✅ Phase 1 完成

需求分析阶段已完成，可以进入 Phase 2 技术设计阶段。

---

🤖 Agent 集群自动通知
"""
        at_all = self._get_at_all_flag('phase_complete')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    def notify_phase4_critical_bug(self, bug: Dict[str, Any]):
        """
        Phase 4: 严重 Bug 通知
        
        Args:
            bug: Bug 信息
        """
        bug_id = bug.get('id', 'N/A')
        severity = bug.get('severity', 'critical')
        module = bug.get('module', 'N/A')
        title_text = bug.get('title', '无标题')
        description = bug.get('description', '无描述')
        reproduction_steps = bug.get('reproduction_steps', 'N/A')
        reporter = bug.get('reporter', 'Tester')
        
        # 严重程度图标
        severity_icon = "🔴" if severity == "critical" else "🟠" if severity == "major" else "🟡"
        
        title = f"{severity_icon} 严重 Bug - {bug_id}"
        
        text = f"""## 🐛 Phase 4: 发现严重 Bug

**Bug ID**: {bug_id}
**严重程度**: {severity_icon} {severity.upper()}
**模块**: {module}
**发现者**: {reporter}

---

### 📋 Bug 详情

**标题**: {title_text}

**描述**: {description[:150]}{'...' if len(description) > 150 else ''}

**复现步骤**: 
{reproduction_steps[:200]}{'...' if len(reproduction_steps) > 200 else ''}

---

### ⚠️ 处理建议

1. 立即评估 Bug 影响范围
2. 优先修复严重 Bug
3. 更新测试用例防止回归

---

🤖 Agent 集群自动通知
"""
        # 严重 Bug 需要@所有人
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all=True)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all=True)
    
    def notify_phase5_review_passed(self, workflow: Dict, review_info: Dict[str, Any]):
        """
        Phase 5: 审查通过通知
        
        Args:
            workflow: 工作流信息
            review_info: 审查相关信息
        """
        workflow_id = workflow.get('id', 'N/A')
        pr_number = review_info.get('pr_number', 'N/A')
        pr_url = review_info.get('pr_url', '#')
        reviewers = review_info.get('reviewers', [])
        approved_count = review_info.get('approved_count', 0)
        security_score = review_info.get('security_score', 0)
        code_quality_score = review_info.get('code_quality_score', 0)
        
        title = f"✅ 审查通过 - PR #{pr_number}"
        
        text = f"""## ✅ Phase 5: 代码审查通过

**工作流**: {workflow_id}
**PR**: #{pr_number} - [查看 PR]({pr_url})

---

### 📊 审查结果

**审查通过**: {approved_count}/{len(reviewers)} 个审查者批准

**审查者**:
{chr(10).join(['- ✅ ' + r.get('name', 'Unknown') + (' (' + r.get('comment', '') + ')' if r.get('comment') else '') for r in reviewers])}

---

### 📈 质量评分

- **安全评分**: {security_score}/100
- **代码质量**: {code_quality_score}/100

---

### ✅ Phase 5 完成

代码审查已通过，可以进入 Phase 6 部署上线阶段。

---

🤖 Agent 集群自动通知
"""
        at_all = self._get_at_all_flag('phase_complete')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    # ========== 中优先级通知（方案 B） ==========
    
    def notify_phase2_design_review(self, workflow: Dict, design_info: Dict[str, Any]):
        """
        Phase 2: 设计评审通知
        
        Args:
            workflow: 工作流信息
            design_info: 设计相关信息
        """
        workflow_id = workflow.get('id', 'N/A')
        tech_lead = design_info.get('tech_lead', 'Tech Lead')
        designer = design_info.get('designer', 'Designer')
        architecture_url = design_info.get('architecture_url', '#')
        ui_design_url = design_info.get('ui_design_url', '#')
        deploy_config_url = design_info.get('deploy_config_url', '#')
        
        title = f"📐 设计评审完成 - {workflow_id}"
        
        text = f"""## 📐 Phase 2: 技术设计完成

**工作流**: {workflow_id}
**技术负责人**: {tech_lead}
**设计师**: {designer}

---

### 📋 产出物

- **架构设计**: [查看文档]({architecture_url})
- **UI 设计**: [查看设计]({ui_design_url})
- **部署配置**: [查看配置]({deploy_config_url})

---

### ✅ Phase 2 完成

技术设计阶段已完成，可以进入 Phase 3 开发实现阶段。

---

🤖 Agent 集群自动通知
"""
        at_all = self._get_at_all_flag('phase_complete')
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    def notify_phase3_code_commit(self, workflow: Dict, commit_info: Dict[str, Any]):
        """
        Phase 3: 代码提交通知
        
        Args:
            workflow: 工作流信息
            commit_info: 提交相关信息
        """
        workflow_id = workflow.get('id', 'N/A')
        agent_name = commit_info.get('agent_name', 'Developer')
        commit_message = commit_info.get('commit_message', '无提交信息')
        files_changed = commit_info.get('files_changed', 0)
        additions = commit_info.get('additions', 0)
        deletions = commit_info.get('deletions', 0)
        commit_url = commit_info.get('commit_url', '#')
        
        title = f"📝 代码提交 - {agent_name}"
        
        text = f"""## 📝 Phase 3: 代码提交

**工作流**: {workflow_id}
**开发者**: {agent_name}

---

### 📋 提交详情

**提交信息**: {commit_message[:80]}{'...' if len(commit_message) > 80 else ''}

**文件变更**: 
- 📄 修改文件：{files_changed} 个
- ➕ 新增行数：{additions} 行
- ➖ 删除行数：{deletions} 行

[查看提交]({commit_url})

---

🤖 Agent 集群自动通知
"""
        at_all = False
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    def notify_phase4_test_coverage(self, workflow: Dict, test_info: Dict[str, Any]):
        """
        Phase 4: 测试覆盖率通知
        
        Args:
            workflow: 工作流信息
            test_info: 测试相关信息
        """
        workflow_id = workflow.get('id', 'N/A')
        tester = test_info.get('tester', 'Tester')
        total_tests = test_info.get('total_tests', 0)
        passed_tests = test_info.get('passed_tests', 0)
        failed_tests = test_info.get('failed_tests', 0)
        coverage = test_info.get('coverage', 0)
        coverage_url = test_info.get('coverage_url', '#')
        test_report_url = test_info.get('test_report_url', '#')
        
        # 覆盖率图标
        coverage_icon = "🟢" if coverage >= 80 else "🟡" if coverage >= 60 else "🔴"
        
        title = f"📊 测试覆盖率报告 - {coverage}%"
        
        text = f"""## 📊 Phase 4: 测试报告

**工作流**: {workflow_id}
**测试工程师**: {tester}

---

### 📈 测试结果

**总测试数**: {total_tests} 个
**通过**: {passed_tests} 个 ✅
**失败**: {failed_tests} 个 ❌
**通过率**: {passed_tests/total_tests*100 if total_tests > 0 else 0:.1f}%

---

### 📊 代码覆盖率

**覆盖率**: {coverage_icon} {coverage}%

[查看覆盖率报告]({coverage_url})

[查看测试报告]({test_report_url})

---

{self._get_coverage_message(coverage)}

---

🤖 Agent 集群自动通知
"""
        at_all = False
        if self.deploy_group_id:
            return self.dingtalk.send_to_group(self.deploy_group_id, title, text, at_all)
        else:
            return self.dingtalk.send_markdown(self.admin_user_ids, title, text, at_all)
    
    def notify_phase5_review_issues(self, workflow: Dict, review_info: Dict[str, Any]):
        """
        Phase 5: 审查问题通知
        
        Args:
            workflow: 工作流信息
            review_info: 审查相关信息
        """
        workflow_id = workflow.get('id', 'N/A')
        pr_number = review_info.get('pr_number', 'N/A')
        pr_url = review_info.get('pr_url', '#')
        reviewers = review_info.get('reviewers', [])
        issues = review_info.get('issues', [])
        critical_count = review_info.get('critical_count', 0)
        major_count = review_info.get('major_count', 0)
        
        # 问题严重程度图标
        severity_icon = "🔴" if critical_count > 0 else "🟠" if major_count > 0 else "🟡"
        
        title = f"{severity_icon} 审查问题 - PR #{pr_number}"
        
        issues_list = '\n'.join([
            f"- **{issue.get('reviewer', 'Unknown')}**: {issue.get('issue', '无描述')}"
            for issue in issues[:5]
        ])
        
        if len(issues) > 5:
            issues_list += f"\n- ... 还有 {len(issues) - 5} 个问题"
        
        text = f"""## {severity_icon} Phase 5: 审查发现问题

**工作流**: {workflow_id}
**PR**: #{pr_number} - [查看 PR]({pr_url})

---

### 📋 审查问题

**严重问题**: {critical_count} 个 🔴
**主要问题**: {major_count} 个 🟠
**次要问题**: {len(issues) - critical_count - major_count} 个 🟡

---

### ⚠️ 问题详情

{issues_list}

---

### 📌 处理建议

1. 优先修复严重问题（Critical）
2. 其次修复主要问题（Major）
3. 修复完成后重新提交审查

---

🤖 Agent 集群自动通知
"""
        # 有严重问题时@所有人
        at_all = critical_count > 0
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
