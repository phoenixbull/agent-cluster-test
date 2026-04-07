#!/usr/bin/env python3
"""
DevOps Agent - 部署前确认模块
发送钉钉确认通知，等待用户回复后再执行部署
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class DeployConfirmationManager:
    """部署确认管理器"""
    
    def __init__(self, dingtalk_notifier):
        """
        初始化部署确认管理器
        
        Args:
            dingtalk_notifier: 钉钉通知器实例
        """
        self.notifier = dingtalk_notifier
        self.pending_confirmations = {}
        self.confirmation_timeout_minutes = 30
    
    def send_deployment_confirmation(
        self,
        project_name: str,
        version: str,
        test_summary: Dict,
        review_summary: Dict,
        changes: List[str],
        environment: str = "production"
    ) -> str:
        """
        发送部署确认通知
        
        Args:
            project_name: 项目名称
            version: 版本号
            test_summary: 测试摘要
            review_summary: 审查摘要
            changes: 变更列表
            environment: 部署环境
        
        Returns:
            确认 ID
        """
        confirmation_id = f"deploy-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 构建 Markdown 消息
        markdown_text = self._build_confirmation_message(
            project_name, version, test_summary, review_summary, 
            changes, environment, confirmation_id
        )
        
        # 发送钉钉通知 (@所有人)
        self.notifier.send_markdown(
            title=f"⚠️ 部署前确认 - {project_name}",
            text=markdown_text,
            at_all=True
        )
        
        # 记录待确认
        self.pending_confirmations[confirmation_id] = {
            "project_name": project_name,
            "version": version,
            "environment": environment,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=self.confirmation_timeout_minutes),
            "status": "pending",
            "test_summary": test_summary,
            "review_summary": review_summary,
            "changes": changes
        }
        
        print(f"✅ 部署确认通知已发送: {confirmation_id}")
        return confirmation_id
    
    def _build_confirmation_message(
        self,
        project_name: str,
        version: str,
        test_summary: Dict,
        review_summary: Dict,
        changes: List[str],
        environment: str,
        confirmation_id: str
    ) -> str:
        """构建确认消息"""
        
        # 测试状态
        test_status = "✅ 通过" if test_summary.get("passed", False) else "❌ 失败"
        test_coverage = test_summary.get("coverage", "N/A")
        
        # 审查状态
        review_status = "✅ 通过" if review_summary.get("approved", False) else "❌ 待审查"
        review_score = review_summary.get("score", "N/A")
        
        # 变更列表
        changes_text = "\n".join([f"- {change}" for change in changes[:5]])
        if len(changes) > 5:
            changes_text += f"\n- ... 还有 {len(changes) - 5} 项"
        
        markdown = f"""## ⚠️ 部署前确认 - 需要人工审批

**项目**: {project_name}
**版本**: {version}
**环境**: {"🔴 生产环境" if environment == "production" else "🟡 测试环境"}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**确认 ID**: `{confirmation_id}`

### 📋 部署前检查

**代码审查**: {review_status} (评分：{review_score}/100)
**测试覆盖**: {test_status} (覆盖率：{test_coverage}%)
**Bug 数量**: {test_summary.get("bug_count", 0)} 个

### 🚀 部署信息

**部署环境**: {environment}
**预计时间**: 5 分钟
**影响范围**: {"全站" if environment == "production" else "测试环境"}

### 📊 本次变更

{changes_text}

---

**请确认是否部署**:

✅ 确认部署：回复 "**部署 {confirmation_id}**" 或 "**deploy {confirmation_id}**"
❌ 取消部署：回复 "**取消 {confirmation_id}**" 或 "**cancel {confirmation_id}**"
📝 查看详情：回复 "**详情 {confirmation_id}**" 或 "**details {confirmation_id}**"

⏱️ **超时时间**: {self.confirmation_timeout_minutes} 分钟（超时自动取消）

---
*此为自动消息，请勿直接回复此消息*"""
        
        return markdown
    
    def process_confirmation_response(
        self,
        user_response: str,
        user_name: str = "用户"
    ) -> Optional[Dict]:
        """
        处理用户确认回复
        
        Args:
            user_response: 用户回复内容
            user_name: 用户名称
        
        Returns:
            确认结果字典，如果无匹配返回 None
        """
        response_lower = user_response.lower().strip()
        
        # 查找匹配的确认 ID
        for confirmation_id, confirmation in list(self.pending_confirmations.items()):
            # 检查是否过期
            if datetime.now() > confirmation["expires_at"]:
                confirmation["status"] = "expired"
                self._send_expiry_notification(confirmation_id)
                continue
            
            # 检查回复是否匹配
            if confirmation_id in response_lower:
                if "部署" in response_lower or "deploy" in response_lower:
                    return self._approve_deployment(confirmation_id, user_name)
                elif "取消" in response_lower or "cancel" in response_lower:
                    return self._cancel_deployment(confirmation_id, user_name)
                elif "详情" in response_lower or "details" in response_lower:
                    return self._send_details(confirmation_id, user_name)
        
        return None
    
    def _approve_deployment(self, confirmation_id: str, user_name: str) -> Dict:
        """批准部署"""
        confirmation = self.pending_confirmations.get(confirmation_id)
        if not confirmation:
            return {"status": "error", "message": "确认 ID 不存在"}
        
        confirmation["status"] = "approved"
        confirmation["approved_by"] = user_name
        confirmation["approved_at"] = datetime.now()
        
        # 发送批准通知
        self.notifier.send_markdown(
            title=f"✅ 部署已批准 - {confirmation['project_name']}",
            text=f"""## ✅ 部署已批准

**项目**: {confirmation['project_name']}
**版本**: {confirmation['version']}
**批准人**: {user_name}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

正在开始部署...""",
            at_all=False
        )
        
        return {
            "status": "approved",
            "confirmation_id": confirmation_id,
            "deployment_info": confirmation
        }
    
    def _cancel_deployment(self, confirmation_id: str, user_name: str) -> Dict:
        """取消部署"""
        confirmation = self.pending_confirmations.get(confirmation_id)
        if not confirmation:
            return {"status": "error", "message": "确认 ID 不存在"}
        
        confirmation["status"] = "cancelled"
        confirmation["cancelled_by"] = user_name
        confirmation["cancelled_at"] = datetime.now()
        
        # 发送取消通知
        self.notifier.send_markdown(
            title=f"❌ 部署已取消 - {confirmation['project_name']}",
            text=f"""## ❌ 部署已取消

**项目**: {confirmation['project_name']}
**版本**: {confirmation['version']}
**取消人**: {user_name}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

部署已取消，如需重新部署请重新触发流程。""",
            at_all=False
        )
        
        return {
            "status": "cancelled",
            "confirmation_id": confirmation_id
        }
    
    def _send_details(self, confirmation_id: str, user_name: str) -> Dict:
        """发送详细信息"""
        confirmation = self.pending_confirmations.get(confirmation_id)
        if not confirmation:
            return {"status": "error", "message": "确认 ID 不存在"}
        
        details_text = f"""## 📊 部署详细信息

**项目**: {confirmation['project_name']}
**版本**: {confirmation['version']}
**环境**: {confirmation['environment']}

### 测试摘要
- 覆盖率：{confirmation['test_summary'].get('coverage', 'N/A')}%
- Bug 数：{confirmation['test_summary'].get('bug_count', 0)}

### 审查摘要
- 评分：{confirmation['review_summary'].get('score', 'N/A')}/100
- 状态：{'通过' if confirmation['review_summary'].get('approved') else '待审查'}

### 变更列表
{chr(10).join(['- ' + c for c in confirmation['changes']])}

---

请回复确认指令继续。"""
        
        self.notifier.send_markdown(
            title=f"📊 部署详情 - {confirmation['project_name']}",
            text=details_text,
            at_all=False
        )
        
        return {
            "status": "details_sent",
            "confirmation_id": confirmation_id
        }
    
    def _send_expiry_notification(self, confirmation_id: str):
        """发送超时通知"""
        confirmation = self.pending_confirmations.get(confirmation_id)
        if not confirmation:
            return
        
        self.notifier.send_markdown(
            title=f"⏱️ 部署确认超时 - {confirmation['project_name']}",
            text=f"""## ⏱️ 部署确认超时

**项目**: {confirmation['project_name']}
**版本**: {confirmation['version']}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

部署确认已超时 ({self.confirmation_timeout_minutes} 分钟)，自动取消。

如需部署，请重新触发流程。""",
            at_all=False
        )
    
    def check_expired_confirmations(self):
        """检查并处理过期的确认"""
        now = datetime.now()
        expired_count = 0
        
        for confirmation_id, confirmation in list(self.pending_confirmations.items()):
            if confirmation["status"] == "pending" and now > confirmation["expires_at"]:
                confirmation["status"] = "expired"
                self._send_expiry_notification(confirmation_id)
                expired_count += 1
        
        if expired_count > 0:
            print(f"⚠️ 清理了 {expired_count} 个过期的部署确认")
    
    def get_confirmation_status(self, confirmation_id: str) -> Optional[Dict]:
        """获取确认状态"""
        return self.pending_confirmations.get(confirmation_id)
    
    def cleanup_old_confirmations(self, days: int = 7):
        """清理旧的确认记录"""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        
        for confirmation_id, confirmation in self.pending_confirmations.items():
            if confirmation["created_at"] < cutoff:
                to_remove.append(confirmation_id)
        
        for confirmation_id in to_remove:
            del self.pending_confirmations[confirmation_id]
        
        if to_remove:
            print(f"🧹 清理了 {len(to_remove)} 个旧确认记录")


# 主函数 - 供集群调用
def request_deployment_confirmation(
    dingtalk_notifier,
    project_name: str,
    version: str,
    test_summary: Dict,
    review_summary: Dict,
    changes: List[str],
    environment: str = "production"
) -> str:
    """
    请求部署确认
    
    Args:
        dingtalk_notifier: 钉钉通知器
        project_name: 项目名称
        version: 版本号
        test_summary: 测试摘要
        review_summary: 审查摘要
        changes: 变更列表
        environment: 部署环境
    
    Returns:
        确认 ID
    """
    manager = DeployConfirmationManager(dingtalk_notifier)
    return manager.send_deployment_confirmation(
        project_name, version, test_summary, review_summary, 
        changes, environment
    )


if __name__ == "__main__":
    # 测试
    print("部署确认模块测试")
