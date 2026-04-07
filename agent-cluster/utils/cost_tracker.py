#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成本统计模块
跟踪和统计 LLM API 调用成本
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading

# 模型定价（元/千 token）
MODEL_PRICING = {
    "qwen-max": {"input": 0.04, "output": 0.12},
    "qwen-plus": {"input": 0.004, "output": 0.012},
    "qwen-turbo": {"input": 0.002, "output": 0.006},
    "qwen-coder-plus": {"input": 0.004, "output": 0.012},
    "qwen-vl-plus": {"input": 0.006, "output": 0.018},
    "qwen-long": {"input": 0.001, "output": 0.003},
}


class CostTracker:
    """成本跟踪器"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cost_file = self.data_dir / "cost_stats.json"
        self.records_file = self.data_dir / "cost_records.jsonl"
        self._lock = threading.Lock()
        self._load_data()
    
    def _load_data(self):
        """加载成本数据"""
        self.stats = {
            "today": {"total": 0.0, "workflows": 0, "date": datetime.now().strftime("%Y-%m-%d")},
            "week": {"total": 0.0, "workflows": 0},
            "month": {"total": 0.0, "workflows": 0},
            "by_model": {},
            "by_workflow": [],
        }
        
        if self.cost_file.exists():
            try:
                with open(self.cost_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 检查是否需要重置今日统计
                    today = datetime.now().strftime("%Y-%m-%d")
                    if loaded.get("today", {}).get("date") != today:
                        loaded["today"] = {"total": 0.0, "workflows": 0, "date": today}
                    self.stats.update(loaded)
            except Exception as e:
                print(f"加载成本数据失败：{e}")
    
    def _save_data(self):
        """保存成本数据"""
        with self._lock:
            with open(self.cost_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def record_call(self, model: str, input_tokens: int, output_tokens: int, 
                    workflow_id: Optional[str] = None) -> float:
        """
        记录一次 API 调用
        
        Args:
            model: 模型名称
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            workflow_id: 工作流 ID
            
        Returns:
            本次调用的成本（元）
        """
        pricing = MODEL_PRICING.get(model, {"input": 0.004, "output": 0.012})
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000
        
        with self._lock:
            # 更新今日统计
            self.stats["today"]["total"] += cost
            self.stats["today"]["workflows"] += 1
            
            # 更新周统计
            self.stats["week"]["total"] += cost
            self.stats["week"]["workflows"] += 1
            
            # 更新月统计
            self.stats["month"]["total"] += cost
            self.stats["month"]["workflows"] += 1
            
            # 更新模型统计
            if model not in self.stats["by_model"]:
                self.stats["by_model"][model] = {"calls": 0, "tokens": 0, "cost": 0.0}
            self.stats["by_model"][model]["calls"] += 1
            self.stats["by_model"][model]["tokens"] += input_tokens + output_tokens
            self.stats["by_model"][model]["cost"] += cost
            
            # 记录工作流成本
            if workflow_id:
                workflow_cost = next(
                    (w for w in self.stats["by_workflow"] if w["workflow_id"] == workflow_id),
                    None
                )
                if workflow_cost:
                    workflow_cost["cost"] += cost
                    workflow_cost["calls"] += 1
                else:
                    self.stats["by_workflow"].append({
                        "workflow_id": workflow_id,
                        "cost": cost,
                        "calls": 1,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # 保存到文件
        self._save_data()
        
        # 追加到记录文件
        record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "workflow_id": workflow_id
        }
        with open(self.records_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        return cost
    
    def record_workflow_complete(self, workflow_id: str, total_cost: float):
        """记录工作流完成"""
        with self._lock:
            # 清理旧的工作流记录（保留最近 100 条）
            self.stats["by_workflow"] = [
                w for w in self.stats["by_workflow"]
                if w["workflow_id"] != workflow_id
            ][-100:]
        
        self._save_data()
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        self._load_data()  # 重新加载确保数据最新
        return {
            "today": self.stats["today"],
            "week": self.stats["week"],
            "month": self.stats["month"],
            "by_model": self.stats["by_model"],
            "average_per_workflow": (
                self.stats["today"]["total"] / self.stats["today"]["workflows"]
                if self.stats["today"]["workflows"] > 0 else 0
            )
        }
    
    def reset_daily(self):
        """重置每日统计（在日期变更时调用）"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.stats["today"].get("date") != today:
            self.stats["today"] = {"total": 0.0, "workflows": 0, "date": today}
            self._save_data()
    
    def get_cost_estimate(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """估算成本（不记录）"""
        pricing = MODEL_PRICING.get(model, {"input": 0.004, "output": 0.012})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000


# 全局实例
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """获取成本跟踪器实例"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def record_api_call(model: str, input_tokens: int, output_tokens: int, 
                   workflow_id: Optional[str] = None) -> float:
    """便捷函数：记录 API 调用"""
    return get_cost_tracker().record_call(model, input_tokens, output_tokens, workflow_id)


def get_cost_stats() -> Dict:
    """便捷函数：获取成本统计"""
    return get_cost_tracker().get_stats()


if __name__ == '__main__':
    # 测试
    tracker = CostTracker()
    
    # 模拟记录
    cost1 = tracker.record_call("qwen-plus", 1000, 500, "wf-test-001")
    print(f"调用 1 成本：¥{cost1:.4f}")
    
    cost2 = tracker.record_call("qwen-coder-plus", 2000, 1000, "wf-test-001")
    print(f"调用 2 成本：¥{cost2:.4f}")
    
    # 获取统计
    stats = tracker.get_stats()
    print(f"\n今日统计:")
    print(f"  总成本：¥{stats['today']['total']:.2f}")
    print(f"  工作流数：{stats['today']['workflows']}")
    print(f"\n按模型统计:")
    for model, data in stats['by_model'].items():
        print(f"  {model}: ¥{data['cost']:.2f} ({data['calls']} 次调用)")
