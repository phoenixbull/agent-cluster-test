#!/usr/bin/env python3
"""
时间估算器 - V2.2 增强版
基于历史数据的项目时间估算
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Complexity(Enum):
    """任务复杂度"""
    TRIVIAL = "trivial"      # 非常简单 (<1 小时)
    SIMPLE = "simple"        # 简单 (1-4 小时)
    MEDIUM = "medium"        # 中等 (4-16 小时)
    COMPLEX = "complex"      # 复杂 (16-40 小时)
    VERY_COMPLEX = "very_complex"  # 非常复杂 (>40 小时)


class TimeEstimator:
    """时间估算器（基于历史数据）"""
    
    def __init__(self, history_path: str = None):
        if history_path:
            self.history_path = Path(history_path)
        else:
            self.history_path = Path("~/.openclaw/workspace/agent-cluster/memory/estimation_history.json").expanduser()
        
        # 确保目录存在
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_history_file()
        
        # 基准时间（小时）
        self.baseline_hours = {
            Complexity.TRIVIAL: 0.5,
            Complexity.SIMPLE: 2,
            Complexity.MEDIUM: 8,
            Complexity.COMPLEX: 24,
            Complexity.VERY_COMPLEX: 60
        }
        
        # 阶段系数
        self.phase_multipliers = {
            "1_requirement": 1.0,
            "2_design": 1.2,
            "3_development": 1.5,
            "4_testing": 0.8,
            "5_review": 0.5,
            "6_deployment": 0.6
        }
    
    def _ensure_history_file(self):
        """确保历史文件存在"""
        if not self.history_path.exists():
            self._write_history({
                "version": "2.2",
                "estimations": [],
                "actuals": []
            })
    
    def _read_history(self) -> Dict:
        """读取历史数据"""
        if self.history_path.exists():
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"estimations": [], "actuals": []}
    
    def _write_history(self, data: Dict):
        """写入历史数据"""
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def estimate_task(self, title: str, description: str = "",
                     phase: str = "3_development",
                     complexity: str = None,
                     tags: List[str] = None) -> Dict:
        """
        估算单个任务时间
        
        Args:
            title: 任务标题
            description: 任务描述
            phase: 阶段 (1_requirement, 2_design, etc.)
            complexity: 复杂度（可选，自动分析）
            tags: 任务标签
        
        Returns:
            估算结果
        """
        # 自动分析复杂度
        if not complexity:
            complexity = self._analyze_complexity(title, description)
        
        # 获取基准时间
        base_hours = self.baseline_hours.get(Complexity(complexity), 8)
        
        # 应用阶段系数
        phase_multiplier = self.phase_multipliers.get(phase, 1.0)
        adjusted_hours = base_hours * phase_multiplier
        
        # 基于历史数据调整
        history_adjustment = self._get_history_adjustment(phase, tags)
        adjusted_hours *= history_adjustment
        
        # 计算置信区间
        confidence = self._calculate_confidence(phase, tags)
        uncertainty = self._calculate_uncertainty(confidence)
        
        estimation = {
            "task_title": title,
            "phase": phase,
            "complexity": complexity,
            "estimated_hours": round(adjusted_hours, 2),
            "min_hours": round(adjusted_hours * (1 - uncertainty), 2),
            "max_hours": round(adjusted_hours * (1 + uncertainty), 2),
            "confidence": confidence,
            "factors": {
                "base_hours": base_hours,
                "phase_multiplier": phase_multiplier,
                "history_adjustment": history_adjustment
            },
            "estimated_at": datetime.now().isoformat()
        }
        
        # 保存估算记录
        self._save_estimation(estimation)
        
        return estimation
    
    def estimate_project(self, tasks: List[Dict]) -> Dict:
        """
        估算整个项目时间
        
        Args:
            tasks: 任务列表，每个任务包含 title, description, phase, complexity
        
        Returns:
            项目估算结果
        """
        task_estimates = []
        total_hours = 0
        total_min = 0
        total_max = 0
        
        for task in tasks:
            estimation = self.estimate_task(
                title=task.get("title", ""),
                description=task.get("description", ""),
                phase=task.get("phase", "3_development"),
                complexity=task.get("complexity"),
                tags=task.get("tags", [])
            )
            task_estimates.append(estimation)
            total_hours += estimation["estimated_hours"]
            total_min += estimation["min_hours"]
            total_max += estimation["max_hours"]
        
        # 计算项目级指标
        avg_confidence = sum(
            self._confidence_to_score(e["confidence"]) 
            for e in task_estimates
        ) / len(task_estimates) if task_estimates else 0
        
        # 添加缓冲时间（基于置信度）
        buffer_percentage = max(0, (100 - avg_confidence * 100) * 0.5)
        buffered_hours = total_hours * (1 + buffer_percentage / 100)
        
        return {
            "task_count": len(tasks),
            "total_estimated_hours": round(total_hours, 2),
            "total_min_hours": round(total_min, 2),
            "total_max_hours": round(total_max, 2),
            "buffered_hours": round(buffered_hours, 2),
            "buffer_percentage": round(buffer_percentage, 2),
            "average_confidence": round(avg_confidence, 2),
            "task_estimates": task_estimates,
            "estimated_at": datetime.now().isoformat(),
            "in_days": round(buffered_hours / 8, 1),  # 按 8 小时工作日
            "in_weeks": round(buffered_hours / 40, 1)  # 按 40 小时工作周
        }
    
    def record_actual(self, task_id: str, actual_hours: float, 
                     estimation: Dict = None) -> bool:
        """记录实际耗时（用于改进估算）"""
        try:
            history = self._read_history()
            
            actual_record = {
                "task_id": task_id,
                "actual_hours": actual_hours,
                "estimated_hours": estimation.get("estimated_hours") if estimation else None,
                "phase": estimation.get("phase") if estimation else None,
                "complexity": estimation.get("complexity") if estimation else None,
                "variance": (actual_hours - estimation.get("estimated_hours", 0)) if estimation else None,
                "variance_percentage": (
                    (actual_hours - estimation["estimated_hours"]) / estimation["estimated_hours"] * 100
                ) if estimation and estimation["estimated_hours"] > 0 else None,
                "recorded_at": datetime.now().isoformat()
            }
            
            if "actuals" not in history:
                history["actuals"] = []
            history["actuals"].append(actual_record)
            
            # 限制历史记录数量
            if len(history["actuals"]) > 1000:
                history["actuals"] = history["actuals"][-1000:]
            
            self._write_history(history)
            print(f"✅ 记录实际耗时：{task_id} - {actual_hours}小时")
            return True
            
        except Exception as e:
            print(f"❌ 记录实际耗时失败：{e}")
            return False
    
    def _analyze_complexity(self, title: str, description: str) -> str:
        """基于关键词分析复杂度"""
        text = f"{title} {description}".lower()
        
        # 复杂度关键词
        complex_keywords = [
            "架构", "重构", "优化", "性能", "安全", "集成", "迁移",
            "architecture", "refactor", "optimize", "performance", "security", "integration", "migration"
        ]
        
        simple_keywords = [
            "修复", "更新", "添加", "修改", "配置",
            "fix", "update", "add", "modify", "config"
        ]
        
        trivial_keywords = [
            "文档", "注释", "格式", "拼写",
            "documentation", "comment", "format", "typo"
        ]
        
        # 计算复杂度分数
        score = 0
        
        for keyword in trivial_keywords:
            if keyword in text:
                score -= 2
        
        for keyword in simple_keywords:
            if keyword in text:
                score -= 1
        
        for keyword in complex_keywords:
            if keyword in text:
                score += 2
        
        # 基于描述长度
        if len(description) > 500:
            score += 1
        if len(description) > 1000:
            score += 1
        
        # 映射到复杂度
        if score <= -2:
            return Complexity.TRIVIAL.value
        elif score <= 0:
            return Complexity.SIMPLE.value
        elif score <= 2:
            return Complexity.MEDIUM.value
        elif score <= 4:
            return Complexity.COMPLEX.value
        else:
            return Complexity.VERY_COMPLEX.value
    
    def _get_history_adjustment(self, phase: str, tags: List[str] = None) -> float:
        """基于历史数据获取调整系数"""
        history = self._read_history()
        actuals = history.get("actuals", [])
        
        if not actuals:
            return 1.0
        
        # 筛选同阶段的历史记录
        phase_actuals = [a for a in actuals if a.get("phase") == phase]
        
        if not phase_actuals:
            return 1.0
        
        # 计算平均偏差
        variances = [
            a.get("variance_percentage", 0) 
            for a in phase_actuals 
            if a.get("variance_percentage") is not None
        ]
        
        if not variances:
            return 1.0
        
        avg_variance = sum(variances) / len(variances)
        
        # 如果历史平均超时 20%，则调整系数为 1.2
        adjustment = 1 + (avg_variance / 100)
        
        # 限制调整范围
        return max(0.5, min(2.0, adjustment))
    
    def _calculate_confidence(self, phase: str, tags: List[str] = None) -> str:
        """计算估算置信度"""
        history = self._read_history()
        actuals = history.get("actuals", [])
        
        # 基于历史数据量
        phase_actuals = [a for a in actuals if a.get("phase") == phase]
        data_points = len(phase_actuals)
        
        if data_points >= 20:
            return "high"
        elif data_points >= 5:
            return "medium"
        else:
            return "low"
    
    def _calculate_uncertainty(self, confidence: str) -> float:
        """计算不确定性范围"""
        uncertainty_map = {
            "high": 0.15,      # ±15%
            "medium": 0.30,    # ±30%
            "low": 0.50        # ±50%
        }
        return uncertainty_map.get(confidence, 0.5)
    
    def _confidence_to_score(self, confidence: str) -> float:
        """置信度转分数"""
        score_map = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5
        }
        return score_map.get(confidence, 0.5)
    
    def _save_estimation(self, estimation: Dict):
        """保存估算记录"""
        history = self._read_history()
        
        if "estimations" not in history:
            history["estimations"] = []
        history["estimations"].append(estimation)
        
        # 限制历史记录数量
        if len(history["estimations"]) > 500:
            history["estimations"] = history["estimations"][-500:]
        
        self._write_history(history)
    
    def get_estimation_accuracy(self) -> Dict:
        """获取估算准确率统计"""
        history = self._read_history()
        actuals = history.get("actuals", [])
        
        if not actuals:
            return {"message": "暂无历史数据"}
        
        # 计算准确率
        accurate = sum(
            1 for a in actuals 
            if a.get("variance_percentage") is not None 
            and abs(a["variance_percentage"]) <= 20
        )
        
        overestimated = sum(
            1 for a in actuals 
            if a.get("variance_percentage") is not None 
            and a["variance_percentage"] < -20
        )
        
        underestimated = sum(
            1 for a in actuals 
            if a.get("variance_percentage") is not None 
            and a["variance_percentage"] > 20
        )
        
        total = len([a for a in actuals if a.get("variance_percentage") is not None])
        
        return {
            "total_records": total,
            "accurate_count": accurate,
            "accurate_percentage": round(accurate / total * 100, 2) if total > 0 else 0,
            "overestimated_count": overestimated,
            "underestimated_count": underestimated,
            "average_variance": round(
                sum(a.get("variance_percentage", 0) or 0 for a in actuals) / total, 2
            ) if total > 0 else 0
        }


# 便捷函数
def get_time_estimator() -> TimeEstimator:
    """获取时间估算器实例"""
    return TimeEstimator()


if __name__ == "__main__":
    # 测试
    estimator = TimeEstimator()
    
    # 测试单个任务估算
    result = estimator.estimate_task(
        title="实现用户登录功能",
        description="支持用户名密码登录，包含验证码和记住登录状态",
        phase="3_development"
    )
    print("任务估算:", result)
    
    # 测试项目估算
    project = estimator.estimate_project([
        {"title": "需求分析", "phase": "1_requirement", "complexity": "medium"},
        {"title": "架构设计", "phase": "2_design", "complexity": "complex"},
        {"title": "后端开发", "phase": "3_development", "complexity": "complex"},
        {"title": "前端开发", "phase": "3_development", "complexity": "medium"},
        {"title": "测试", "phase": "4_testing", "complexity": "medium"}
    ])
    print("项目估算:", project)
