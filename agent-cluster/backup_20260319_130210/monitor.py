#!/usr/bin/env python3
"""
Agent 集群监控脚本
每 10 分钟检查所有 Agent 状态
"""

import json
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加 notifiers 和 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from notifiers.dingtalk import ClusterNotifier
from metrics_collector import (
    get_metrics_collector,
    start_task,
    complete_task,
    fail_task,
    FailureReason
)


class ClusterMonitor:
    """集群监控器"""
    
    def __init__(self, config_path: str = "cluster_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.task_registry_path = Path("~/.openclaw/workspace/agent-cluster/tasks.json").expanduser()
        self.tasks = self._load_tasks()
        
        # 初始化钉钉通知器
        notifications = self.config.get("notifications", {})
        dingtalk_config = notifications.get("dingtalk", {})
        
        if dingtalk_config.get("enabled"):
            self.notifier = ClusterNotifier(
                dingtalk_config.get("webhook", ""),
                dingtalk_config.get("secret", "")
            )
            print("✅ 钉钉通知器已初始化")
        else:
            self.notifier = None
            print("⚠️ 钉钉通知未启用")
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _load_tasks(self) -> Dict:
        """加载任务注册表（增强版：处理空文件、损坏文件）"""
        default_tasks = {"running": [], "completed": [], "failed": [], "version": "2.2"}
        
        if not self.task_registry_path.exists():
            print(f"ℹ️ tasks.json 不存在，创建默认文件")
            self._save_tasks(default_tasks)
            return default_tasks
        
        try:
            # 检查文件大小，空文件直接返回默认值
            if self.task_registry_path.stat().st_size == 0:
                print("⚠️ tasks.json 为空，使用默认格式并自动修复")
                self._save_tasks(default_tasks)
                return default_tasks
            
            with open(self.task_registry_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
                # 再次检查内容是否为空
                if not content:
                    print("⚠️ tasks.json 内容为空，使用默认格式并自动修复")
                    self._save_tasks(default_tasks)
                    return default_tasks
                
                data = json.loads(content)
                
                # 确保是字典格式，如果是数组则转换为字典
                if isinstance(data, dict):
                    # 添加版本字段（如果没有）
                    if "version" not in data:
                        data["version"] = "2.1"
                    return data
                else:
                    print("⚠️ tasks.json 格式不正确 (应为字典)，使用默认格式")
                    self._save_tasks(default_tasks)
                    return default_tasks
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ tasks.json JSON 解析失败：{e}，使用默认格式并自动修复")
            self._save_tasks(default_tasks)
            return default_tasks
        except Exception as e:
            print(f"⚠️ 加载 tasks.json 发生未知错误：{e}，使用默认格式")
            self._save_tasks(default_tasks)
            return default_tasks
    
    def _save_tasks(self, tasks: Dict = None):
        """保存任务注册表（带文件锁）"""
        if tasks is None:
            tasks = self.tasks
        
        # 确保目录存在
        self.task_registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 添加版本和时间戳
        if isinstance(tasks, dict):
            tasks["version"] = "2.2"
            tasks["last_updated"] = datetime.now().isoformat()
        
        with open(self.task_registry_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    def _save_tasks(self):
        """保存任务注册表"""
        with open(self.task_registry_path, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)
    
    async def check_tmux_session(self, session_name: str) -> bool:
        """检查 tmux 会话是否存活"""
        try:
            result = await asyncio.create_subprocess_exec(
                "tmux", "has-session", "-t", session_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception as e:
            print(f"检查 tmux 会话失败：{e}")
            return False
    
    async def check_pr_status(self, branch: str) -> Optional[Dict]:
        """检查 PR 状态"""
        try:
            # 使用 gh CLI 检查 PR
            result = await asyncio.create_subprocess_exec(
                "gh", "pr", "view", branch, "--json", "number,state,mergeable,commits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.home() / ".openclaw/workspace"
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                return json.loads(stdout)
        except Exception as e:
            print(f"检查 PR 状态失败：{e}")
        return None
    
    async def check_ci_status(self, pr_number: int) -> str:
        """检查 CI 状态"""
        try:
            result = await asyncio.create_subprocess_exec(
                "gh", "pr", "checks", str(pr_number), "--json", "name,state",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.home() / ".openclaw/workspace"
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                checks = json.loads(stdout)
                # 所有检查都通过才算成功
                if all(c.get("state") == "PASS" for c in checks):
                    return "success"
                elif any(c.get("state") == "FAIL" for c in checks):
                    return "failed"
                return "pending"
        except Exception as e:
            print(f"检查 CI 状态失败：{e}")
        return "unknown"
    
    async def check_review_status(self, pr_number: int) -> Dict:
        """检查审查状态"""
        try:
            result = await asyncio.create_subprocess_exec(
                "gh", "pr", "reviews", str(pr_number), "--json", "author,state,body",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.home() / ".openclaw/workspace"
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                reviews = json.loads(stdout)
                return {
                    "approved": sum(1 for r in reviews if r.get("state") == "APPROVED"),
                    "changes_requested": sum(1 for r in reviews if r.get("state") == "CHANGES_REQUESTED"),
                    "comments": [r.get("body") for r in reviews if r.get("body")]
                }
        except Exception as e:
            print(f"检查审查状态失败：{e}")
        return {"approved": 0, "changes_requested": 0, "comments": []}
    
    async def monitor_task(self, task: Dict) -> Dict:
        """监控单个任务"""
        task_id = task.get("id")
        tmux_session = task.get("tmux_session")
        branch = task.get("branch")
        
        # 获取指标收集器
        self.metrics = get_metrics_collector()
        
        result = {
            "task_id": task_id,
            "status": "unknown",
            "issues": []
        }
        
        # 1. 检查 tmux 会话
        if tmux_session:
            session_alive = await self.check_tmux_session(tmux_session)
            if not session_alive:
                result["issues"].append("tmux_session_dead")
                result["status"] = "failed"
        
        # 2. 检查 PR 状态
        if branch:
            pr = await self.check_pr_status(branch)
            if pr:
                result["pr_number"] = pr.get("number")
                result["pr_state"] = pr.get("state")
                
                # 3. 检查 CI 状态
                ci_status = await self.check_ci_status(pr.get("number"))
                result["ci_status"] = ci_status
                
                if ci_status == "failed":
                    result["issues"].append("ci_failed")
                
                # 4. 检查审查状态
                reviews = await self.check_review_status(pr.get("number"))
                result["reviews"] = reviews
                
                if reviews.get("changes_requested", 0) > 0:
                    result["issues"].append("review_changes_requested")
                
                # 判断是否完成
                if (pr.get("state") == "OPEN" and 
                    ci_status == "success" and 
                    reviews.get("approved", 0) >= 2):
                    result["status"] = "ready_for_merge"
                elif pr.get("state") == "MERGED":
                    result["status"] = "completed"
                else:
                    result["status"] = "in_progress"
            else:
                result["status"] = "no_pr"
        
        return result
    
    async def monitor_all(self):
        """监控所有运行中的任务"""
        running_tasks = self.tasks.get('running', []) if isinstance(self.tasks, dict) else []
        print(f"\n📊 开始监控 {len(running_tasks)} 个任务...")
        
        completed_tasks = []
        failed_tasks = []
        ready_tasks = []
        
        for task in self.tasks.get("running", []):
            result = await self.monitor_task(task)
            
            print(f"\n任务：{task.get('id')}")
            print(f"  状态：{result['status']}")
            
            if result["status"] == "completed" or result["status"] == "ready_for_merge":
                completed_tasks.append(task)
                print(f"  ✅ 任务完成/可合并")
                await self.notify_completion(task, result)
            
            elif result["status"] == "failed" or result["issues"]:
                failed_tasks.append({
                    "task": task,
                    "result": result
                })
                print(f"  ❌ 任务失败/有问题：{result['issues']}")
                await self.notify_failure(task, result)
            
            elif result["status"] == "ready_for_merge":
                ready_tasks.append({
                    "task": task,
                    "result": result
                })
                print(f"  🎉 准备合并")
        
        # 更新任务状态
        self._update_task_status(completed_tasks, failed_tasks)
        
        # 摘要
        print(f"\n📊 监控摘要:")
        print(f"  完成：{len(completed_tasks)}")
        print(f"  失败：{len(failed_tasks)}")
        print(f"  准备合并：{len(ready_tasks)}")
    
    def _update_task_status(self, completed_tasks: List, failed_tasks: List):
        """更新任务状态"""
        # 移动完成的任务
        for task in completed_tasks:
            self.tasks["running"].remove(task)
            task["completed_at"] = datetime.now().isoformat()
            self.tasks["completed"].append(task)
            
            # 记录指标：任务完成
            if hasattr(self, 'metrics'):
                self.metrics.complete_task(
                    task_id=task.get("id"),
                    pr_number=task.get("pr_number"),
                    ci_passed=task.get("ci_status") == "success",
                    review_approved=task.get("reviews", {}).get("approved", 0) >= 2,
                    cost=task.get("cost", 0.0)
                )
        
        # 更新失败的任务
        for failed in failed_tasks:
            task = failed["task"]
            result = failed["result"]
            task["retry_count"] = task.get("retry_count", 0) + 1
            
            if task["retry_count"] >= 3:
                # 超过最大重试次数，移到失败列表
                self.tasks["running"].remove(task)
                task["failed_at"] = datetime.now().isoformat()
                self.tasks["failed"].append(task)
                
                # 记录指标：任务失败
                if hasattr(self, 'metrics'):
                    # 分析失败原因
                    failure_reason = self._analyze_failure_reason(result)
                    self.metrics.fail_task(
                        task_id=task.get("id"),
                        reason=failure_reason,
                        retry_count=task["retry_count"],
                        cost=task.get("cost", 0.0)
                    )
        
        self._save_tasks()
    
    def _analyze_failure_reason(self, result: Dict) -> FailureReason:
        """分析失败原因"""
        issues = result.get("issues", [])
        
        if "ci_failed" in issues:
            return FailureReason.CI_FAILED
        elif "review_changes_requested" in issues:
            return FailureReason.REVIEW_REJECTED
        elif "tmux_session_dead" in issues:
            return FailureReason.ENVIRONMENT
        elif "timeout" in issues:
            return FailureReason.TIMEOUT
        else:
            return FailureReason.UNKNOWN
    
    async def notify_completion(self, task: Dict, result: Dict):
        """通知任务完成"""
        message = f"""
✅ 任务完成

任务：{task.get('description', task.get('id'))}
PR: #{result.get('pr_number')}
状态：{result.get('status')}
CI: {result.get('ci_status')}
审查通过：{result.get('reviews', {}).get('approved', 0)}

可以 Review 并合并了。
"""
        print(message)
        
        # 发送钉钉通知
        if self.notifier:
            try:
                self.notifier.notify_pr_ready(task, result)
                print("📱 钉钉通知已发送")
            except Exception as e:
                print(f"❌ 发送钉钉通知失败：{e}")
    
    async def notify_failure(self, task: Dict, result: Dict):
        """通知任务失败"""
        failure_reason = ", ".join(result.get('issues', ['未知错误']))
        message = f"""
❌ 任务失败

任务：{task.get('description', task.get('id'))}
问题：{result.get('issues')}
状态：{result.get('status')}
重试次数：{task.get('retry_count', 0)}/3

需要人工介入。
"""
        print(message)
        
        # 发送钉钉通知
        if self.notifier:
            try:
                self.notifier.notify_human_intervention(task, result, failure_reason)
                print("📱 钉钉通知已发送 (@所有人)")
            except Exception as e:
                print(f"❌ 发送钉钉通知失败：{e}")
    
    async def cleanup_old_tasks(self):
        """清理旧任务"""
        cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 天前
        
        self.tasks["completed"] = [
            t for t in self.tasks["completed"]
            if datetime.fromisoformat(t.get("completed_at", "1970-01-01")).timestamp() > cutoff
        ]
        
        self.tasks["failed"] = [
            t for t in self.tasks["failed"]
            if datetime.fromisoformat(t.get("failed_at", "1970-01-01")).timestamp() > cutoff
        ]
        
        self._save_tasks()
        print("✅ 已清理 7 天前的任务记录")


async def main():
    monitor = ClusterMonitor()
    await monitor.monitor_all()
    
    # 每周清理一次
    if datetime.now().weekday() == 0:  # 周一
        await monitor.cleanup_old_tasks()


if __name__ == "__main__":
    # Python 3.6 compatibility
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
