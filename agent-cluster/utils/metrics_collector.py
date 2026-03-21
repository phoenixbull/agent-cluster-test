#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指标收集器模块
负责采集、存储和查询 Agent 集群运行指标
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    HUMAN_INTERVENTION = "human_intervention"


class FailureReason(Enum):
    """失败原因分类"""
    PROMPT_ERROR = "prompt_error"           # Prompt 质量问题
    MODEL_ERROR = "model_error"             # 模型输出异常
    CI_FAILED = "ci_failed"                 # CI 检查失败
    REVIEW_REJECTED = "review_rejected"     # Code Review 不通过
    TIMEOUT = "timeout"                     # 超时
    ENVIRONMENT = "environment"             # 环境问题 (tmux/git 等)
    UNKNOWN = "unknown"                     # 未知原因


@dataclass
class TaskMetrics:
    """单个任务的指标数据"""
    task_id: str
    workflow_id: Optional[str]
    start_time: str
    end_time: Optional[str] = None
    status: str = "pending"
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    agent_used: str = ""
    model_used: str = ""
    pr_number: Optional[int] = None
    ci_passed: Optional[bool] = None
    review_approved: bool = False
    human_intervention: bool = False
    failure_reason: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    phase: str = ""  # 1_requirement, 2_design, 3_development, 4_testing


@dataclass
class AgentMetrics:
    """单个 Agent 的指标数据"""
    agent_id: str
    agent_name: str
    tasks_assigned: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_duration_seconds: float = 0.0
    success_rate: float = 0.0
    total_cost: float = 0.0
    last_active: Optional[str] = None


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "metrics"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.tasks_file = self.data_dir / "tasks_metrics.jsonl"
        self.summary_file = self.data_dir / "summary_stats.json"
        self.agents_file = self.data_dir / "agents_metrics.json"
        self.hourly_file = self.data_dir / "hourly_stats.jsonl"
        
        self._lock = threading.Lock()
        self._tasks_cache: Dict[str, TaskMetrics] = {}
        self._agents_cache: Dict[str, AgentMetrics] = {}
        self._summary = self._load_summary()
        
        self._load_agents()
    
    def _load_summary(self) -> Dict:
        """加载汇总统计"""
        default_summary = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_cost": 0.0,
            "avg_duration_seconds": 0.0,
            "ci_pass_rate": 0.0,
            "human_intervention_rate": 0.0,
            "last_updated": None,
            "today": {
                "tasks": 0,
                "cost": 0.0,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        }
        
        if self.summary_file.exists():
            try:
                with open(self.summary_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 检查日期，如果是新的一天，重置今日统计
                    today = datetime.now().strftime("%Y-%m-%d")
                    if loaded.get("today", {}).get("date") != today:
                        loaded["today"] = {"tasks": 0, "cost": 0.0, "date": today}
                    loaded.update(default_summary)
                    return loaded
            except Exception as e:
                print(f"加载汇总数据失败：{e}")
        
        return default_summary
    
    def _load_agents(self):
        """加载 Agent 指标"""
        if self.agents_file.exists():
            try:
                with open(self.agents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for agent_id, metrics in data.items():
                        self._agents_cache[agent_id] = AgentMetrics(**metrics)
            except Exception as e:
                print(f"加载 Agent 数据失败：{e}")
    
    def _save_summary(self):
        """保存汇总统计"""
        self._summary["last_updated"] = datetime.now().isoformat()
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(self._summary, f, ensure_ascii=False, indent=2)
    
    def _save_agents(self):
        """保存 Agent 指标"""
        data = {k: asdict(v) for k, v in self._agents_cache.items()}
        with open(self.agents_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ========== 任务指标采集 ==========
    
    def start_task(self, task_id: str, workflow_id: Optional[str] = None,
                   agent_id: str = "", model: str = "", phase: str = "") -> TaskMetrics:
        """开始一个任务"""
        metrics = TaskMetrics(
            task_id=task_id,
            workflow_id=workflow_id,
            start_time=datetime.now().isoformat(),
            status=TaskStatus.RUNNING.value,
            agent_used=agent_id,
            model_used=model,
            phase=phase
        )
        
        with self._lock:
            self._tasks_cache[task_id] = metrics
            self._append_to_file(metrics, self.tasks_file)
            
            # 更新汇总
            self._summary["total_tasks"] += 1
            self._summary["today"]["tasks"] += 1
            
            # 更新 Agent 指标
            if agent_id:
                self._update_agent_task(agent_id, "assigned")
            
            self._save_summary()
        
        return metrics
    
    def complete_task(self, task_id: str, pr_number: Optional[int] = None,
                     ci_passed: bool = True, review_approved: bool = True,
                     input_tokens: int = 0, output_tokens: int = 0,
                     cost: float = 0.0) -> TaskMetrics:
        """完成任务"""
        with self._lock:
            if task_id not in self._tasks_cache:
                print(f"警告：任务 {task_id} 未找到")
                return None
            
            metrics = self._tasks_cache[task_id]
            metrics.end_time = datetime.now().isoformat()
            metrics.status = TaskStatus.COMPLETED.value
            metrics.pr_number = pr_number
            metrics.ci_passed = ci_passed
            metrics.review_approved = review_approved
            metrics.input_tokens = input_tokens
            metrics.output_tokens = output_tokens
            metrics.cost = cost
            
            # 计算持续时间 (兼容 Python 3.6)
            start = datetime.strptime(metrics.start_time.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            end = datetime.strptime(metrics.end_time.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            metrics.duration_seconds = (end - start).total_seconds()
            
            self._tasks_cache[task_id] = metrics
            self._append_to_file(metrics, self.tasks_file)
            
            # 更新汇总统计
            self._summary["completed_tasks"] += 1
            self._summary["total_cost"] += cost
            self._summary["today"]["cost"] += cost
            
            # 更新平均时长 (简单移动平均)
            n = self._summary["completed_tasks"]
            old_avg = self._summary["avg_duration_seconds"]
            self._summary["avg_duration_seconds"] = old_avg + (metrics.duration_seconds - old_avg) / n
            
            # 更新 CI 通过率
            ci_total = sum(1 for t in self._tasks_cache.values() if t.ci_passed is not None)
            ci_passed = sum(1 for t in self._tasks_cache.values() if t.ci_passed)
            self._summary["ci_pass_rate"] = ci_passed / ci_total if ci_total > 0 else 0.0
            
            # 更新人工介入率
            intervention_count = sum(1 for t in self._tasks_cache.values() if t.human_intervention)
            self._summary["human_intervention_rate"] = intervention_count / n if n > 0 else 0.0
            
            # 更新 Agent 指标
            if metrics.agent_used:
                self._update_agent_task(metrics.agent_used, "completed", 
                                       metrics.duration_seconds, cost)
            
            self._save_summary()
            self._save_agents()
        
        return metrics
    
    def fail_task(self, task_id: str, reason: FailureReason,
                  retry_count: int = 0, cost: float = 0.0) -> TaskMetrics:
        """任务失败"""
        with self._lock:
            if task_id not in self._tasks_cache:
                print(f"警告：任务 {task_id} 未找到")
                return None
            
            metrics = self._tasks_cache[task_id]
            metrics.end_time = datetime.now().isoformat()
            metrics.status = TaskStatus.FAILED.value
            metrics.failure_reason = reason.value
            metrics.retry_count = retry_count
            metrics.cost = cost
            
            # 计算持续时间 (兼容 Python 3.6)
            start = datetime.strptime(metrics.start_time.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            end = datetime.strptime(metrics.end_time.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            metrics.duration_seconds = (end - start).total_seconds()
            
            self._tasks_cache[task_id] = metrics
            self._append_to_file(metrics, self.tasks_file)
            
            # 更新汇总
            self._summary["failed_tasks"] += 1
            self._summary["total_cost"] += cost
            self._summary["today"]["cost"] += cost
            
            # 更新 Agent 指标
            if metrics.agent_used:
                self._update_agent_task(metrics.agent_used, "failed", cost=cost)
            
            self._save_summary()
            self._save_agents()
        
        return metrics
    
    def retry_task(self, task_id: str) -> TaskMetrics:
        """任务重试"""
        with self._lock:
            if task_id not in self._tasks_cache:
                return None
            
            metrics = self._tasks_cache[task_id]
            metrics.retry_count += 1
            metrics.status = TaskStatus.RETRYING.value
            
            self._tasks_cache[task_id] = metrics
            
            return metrics
    
    def human_intervention(self, task_id: str, reason: str = "") -> TaskMetrics:
        """需要人工介入"""
        with self._lock:
            if task_id not in self._tasks_cache:
                return None
            
            metrics = self._tasks_cache[task_id]
            metrics.human_intervention = True
            metrics.failure_reason = reason
            metrics.status = TaskStatus.HUMAN_INTERVENTION.value
            
            self._tasks_cache[task_id] = metrics
            self._append_to_file(metrics, self.tasks_file)
            
            self._save_summary()
        
        return metrics
    
    # ========== Agent 指标更新 ==========
    
    def _update_agent_task(self, agent_id: str, event: str,
                          duration: float = 0.0, cost: float = 0.0):
        """更新 Agent 指标"""
        if agent_id not in self._agents_cache:
            self._agents_cache[agent_id] = AgentMetrics(
                agent_id=agent_id,
                agent_name=agent_id,
                last_active=datetime.now().isoformat()
            )
        
        agent = self._agents_cache[agent_id]
        agent.last_active = datetime.now().isoformat()
        
        if event == "assigned":
            agent.tasks_assigned += 1
        elif event == "completed":
            agent.tasks_completed += 1
            agent.total_cost += cost
            # 更新平均时长
            if agent.tasks_completed > 0:
                agent.avg_duration_seconds = (
                    (agent.avg_duration_seconds * (agent.tasks_completed - 1) + duration)
                    / agent.tasks_completed
                )
        elif event == "failed":
            agent.tasks_failed += 1
            agent.total_cost += cost
        
        # 计算成功率
        total = agent.tasks_completed + agent.tasks_failed
        agent.success_rate = agent.tasks_completed / total if total > 0 else 0.0
    
    # ========== 工具方法 ==========
    
    def _append_to_file(self, metrics: Any, file_path: Path):
        """追加记录到 JSONL 文件"""
        if isinstance(metrics, TaskMetrics):
            record = asdict(metrics)
        else:
            record = metrics
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # ========== 查询方法 ==========
    
    def get_summary(self) -> Dict:
        """获取汇总统计"""
        summary = self._summary.copy()
        
        # 修复空闲状态下的误报：当没有任务时，通过率相关指标返回 None
        ci_total = sum(1 for t in self._tasks_cache.values() if t.ci_passed is not None)
        if ci_total == 0:
            summary["ci_pass_rate"] = None
        
        completed = self._summary.get("completed_tasks", 0)
        failed = self._summary.get("failed_tasks", 0)
        total = completed + failed
        if total == 0:
            summary["agent_success_rate"] = None
        
        return summary
    
    def get_agent_stats(self, agent_id: Optional[str] = None) -> Dict:
        """获取 Agent 统计"""
        if agent_id:
            agent = self._agents_cache.get(agent_id)
            return asdict(agent) if agent else {}
        return {k: asdict(v) for k, v in self._agents_cache.items()}
    
    def get_task_history(self, limit: int = 100, 
                         status: Optional[str] = None) -> List[Dict]:
        """获取任务历史"""
        tasks = list(self._tasks_cache.values())
        
        # 按状态过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按时间排序，返回最新的
        tasks.sort(key=lambda t: t.start_time, reverse=True)
        
        return [asdict(t) for t in tasks[:limit]]
    
    def get_hourly_stats(self, hours: int = 24) -> List[Dict]:
        """获取小时级统计"""
        # TODO: 实现小时级聚合统计
        return []
    
    def get_failure_analysis(self, days: int = 7) -> Dict:
        """获取失败分析"""
        failure_counts = {}
        
        for task in self._tasks_cache.values():
            if task.status == TaskStatus.FAILED.value and task.failure_reason:
                reason = task.failure_reason
                failure_counts[reason] = failure_counts.get(reason, 0) + 1
        
        total = sum(failure_counts.values())
        return {
            "total_failures": total,
            "by_reason": {
                k: {"count": v, "percentage": v/total*100 if total > 0 else 0}
                for k, v in failure_counts.items()
            }
        }
    
    def export_report(self, output_path: Optional[Path] = None) -> Dict:
        """导出完整报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self._summary,
            "agents": self.get_agent_stats(),
            "failure_analysis": self.get_failure_analysis(),
            "recent_tasks": self.get_task_history(limit=50)
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report


# ========== 全局实例 ==========

_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# ========== 便捷函数 ==========

def start_task(task_id: str, workflow_id: Optional[str] = None,
               agent_id: str = "", model: str = "", phase: str = "") -> TaskMetrics:
    """便捷函数：开始任务"""
    return get_metrics_collector().start_task(task_id, workflow_id, agent_id, model, phase)


def complete_task(task_id: str, pr_number: Optional[int] = None,
                 ci_passed: bool = True, review_approved: bool = True,
                 input_tokens: int = 0, output_tokens: int = 0,
                 cost: float = 0.0) -> TaskMetrics:
    """便捷函数：完成任务"""
    return get_metrics_collector().complete_task(
        task_id, pr_number, ci_passed, review_approved,
        input_tokens, output_tokens, cost
    )


def fail_task(task_id: str, reason: FailureReason,
              retry_count: int = 0, cost: float = 0.0) -> TaskMetrics:
    """便捷函数：任务失败"""
    return get_metrics_collector().fail_task(task_id, reason, retry_count, cost)


def get_stats() -> Dict:
    """便捷函数：获取统计"""
    return get_metrics_collector().get_summary()


if __name__ == '__main__':
    # 测试代码
    collector = MetricsCollector()
    
    # 模拟任务流程
    task1 = collector.start_task("task-001", "wf-001", "codex", "qwen-coder-plus", "3_development")
    print(f"任务开始：{task1.task_id}")
    
    time.sleep(1)
    
    collector.complete_task(
        "task-001",
        pr_number=123,
        ci_passed=True,
        review_approved=True,
        input_tokens=5000,
        output_tokens=2000,
        cost=0.05
    )
    
    # 获取统计
    stats = collector.get_summary()
    print(f"\n汇总统计:")
    print(f"  总任务数：{stats['total_tasks']}")
    print(f"  完成数：{stats['completed_tasks']}")
    print(f"  总成本：¥{stats['total_cost']:.2f}")
    print(f"  平均时长：{stats['avg_duration_seconds']:.1f}秒")
    print(f"  CI 通过率：{stats['ci_pass_rate']*100:.1f}%")
