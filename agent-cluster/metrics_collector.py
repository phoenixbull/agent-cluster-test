#!/usr/bin/env python3
"""
MVP 运行数据收集脚本
收集增量代码生成的运行数据，用于 V2.1 决策

收集内容:
- 工作流基本信息
- 增量修改尝试次数
- 修改文件数
- 审查通过率
- 回滚次数
- 大文件修改需求
- 依赖问题
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


class MVPMetricsCollector:
    """MVP 运行数据收集器"""
    
    def __init__(self, workspace: str = "~/.openclaw/workspace/agent-cluster"):
        self.workspace = Path(workspace).expanduser()
        self.metrics_dir = self.workspace / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "incremental_mvp_metrics.jsonl"
    
    def collect_workflow_metrics(self, workflow_data: Dict) -> None:
        """
        收集单个工作流的指标
        
        Args:
            workflow_data: 工作流数据 (从 orchestrator 传入)
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_data.get('workflow_id', 'unknown'),
            
            # 基本信息
            "total_files": workflow_data.get('total_files', 0),
            "large_files_count": workflow_data.get('large_files_count', 0),
            
            # 增量修改
            "incremental_attempts": workflow_data.get('incremental_attempts', 0),
            "files_modified": workflow_data.get('files_modified', 0),
            "fallback_to_todo": workflow_data.get('fallback_to_todo', False),
            
            # 审查结果
            "review_passed": workflow_data.get('review_passed', False),
            "review_status": workflow_data.get('review_status', 'unknown'),
            
            # 安全机制
            "rollback_performed": workflow_data.get('rollback_performed', False),
            "feedback_quality_usable": workflow_data.get('feedback_quality_usable', True),
            
            # 问题统计
            "dependency_issues": workflow_data.get('dependency_issues', 0),
            "critical_issues_count": workflow_data.get('critical_issues_count', 0),
            
            # 性能
            "total_time_seconds": workflow_data.get('total_time_seconds', 0),
            "incremental_time_seconds": workflow_data.get('incremental_time_seconds', 0)
        }
        
        # 保存到文件
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + '\n')
        
        print(f"📊 已记录工作流：{workflow_data.get('workflow_id', 'unknown')}")
    
    def get_summary(self, days: int = 1) -> Dict:
        """
        获取汇总统计
        
        Args:
            days: 统计天数
        
        Returns:
            汇总统计数据
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        all_metrics = []
        
        if not self.metrics_file.exists():
            return {"error": "无数据"}
        
        # 读取指标数据
        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    metric = json.loads(line)
                    # 解析时间戳 (兼容不同 Python 版本)
                    ts_str = metric['timestamp'].replace('Z', '+00:00')
                    if '+' not in ts_str and ts_str.count(':') == 2:
                        ts_str += '+00:00'
                    
                    # 使用 strptime 解析
                    try:
                        dt = datetime.strptime(ts_str[:19], '%Y-%m-%dT%H:%M:%S')
                        metric_time = dt.timestamp()
                    except:
                        metric_time = datetime.now().timestamp()  # 回退
                    
                    if metric_time >= cutoff_time:
                        all_metrics.append(metric)
                except Exception as e:
                    print(f"解析失败：{e}")
                    continue
        
        if not all_metrics:
            return {"error": f"最近 {days} 天无数据"}
        
        # 计算统计
        total_workflows = len(all_metrics)
        review_passed = sum(1 for m in all_metrics if m.get('review_passed', False))
        incremental_used = sum(1 for m in all_metrics if m.get('incremental_attempts', 0) > 0)
        rollback_count = sum(1 for m in all_metrics if m.get('rollback_performed', False))
        large_file_count = sum(1 for m in all_metrics if m.get('large_files_count', 0) > 0)
        fallback_to_todo = sum(1 for m in all_metrics if m.get('fallback_to_todo', False))
        dependency_issues = sum(m.get('dependency_issues', 0) for m in all_metrics)
        
        # 计算成功率
        success_rate = round(review_passed / total_workflows * 100, 2) if total_workflows > 0 else 0
        
        # 计算平均修改文件数
        modified_files_list = [m.get('files_modified', 0) for m in all_metrics if m.get('incremental_attempts', 0) > 0]
        avg_modified_files = round(sum(modified_files_list) / len(modified_files_list), 2) if modified_files_list else 0
        
        # 计算平均尝试次数
        attempts_list = [m.get('incremental_attempts', 0) for m in all_metrics if m.get('incremental_attempts', 0) > 0]
        avg_attempts = round(sum(attempts_list) / len(attempts_list), 2) if attempts_list else 0
        
        return {
            "period_days": days,
            "total_workflows": total_workflows,
            "review_passed_count": review_passed,
            "success_rate": success_rate,
            "incremental_used_count": incremental_used,
            "incremental_usage_rate": round(incremental_used / total_workflows * 100, 2) if total_workflows > 0 else 0,
            "rollback_count": rollback_count,
            "large_file_count": large_file_count,
            "fallback_to_todo_count": fallback_to_todo,
            "dependency_issues_count": dependency_issues,
            "avg_modified_files": avg_modified_files,
            "avg_incremental_attempts": avg_attempts,
            "total_time_hours": round(sum(m.get('total_time_seconds', 0) for m in all_metrics) / 3600, 2)
        }
    
    def generate_report(self, days: int = 1) -> str:
        """
        生成数据报告
        
        Args:
            days: 统计天数
        
        Returns:
            报告文本
        """
        summary = self.get_summary(days)
        
        if "error" in summary:
            return f"❌ {summary['error']}"
        
        report = f"""
# 📊 MVP 运行数据报告

**统计周期**: 最近 {days} 天  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📈 核心指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **总工作流数** | {summary['total_workflows']} | 统计周期内的工作流总数 |
| **成功率** | {summary['success_rate']}% | 审查通过的工作流比例 |
| **增量修改使用率** | {summary['incremental_usage_rate']}% | 触发增量修改的工作流比例 |
| **平均修改文件数** | {summary['avg_modified_files']} | 每次增量修改的平均文件数 |
| **平均尝试次数** | {summary['avg_incremental_attempts']} | 增量修改的平均尝试次数 |

---

## 🔍 详细统计

### 审查结果
- ✅ 通过：{summary['review_passed_count']}
- ❌ 失败：{summary['total_workflows'] - summary['review_passed_count']}

### 增量修改
- 使用次数：{summary['incremental_used_count']}
- 回滚次数：{summary['rollback_count']}
- 平均尝试：{summary['avg_incremental_attempts']} 次

### 大文件处理
- 大文件工作流：{summary['large_file_count']}
- 使用 TODO 注释：{summary['fallback_to_todo_count']}
- TODO 使用率：{round(summary['fallback_to_todo_count']/max(summary['large_file_count'],1)*100, 2)}%

### 依赖问题
- 依赖问题总数：{summary['dependency_issues_count']}
- 平均每工作流：{round(summary['dependency_issues_count']/max(summary['total_workflows'],1), 2)} 次

---

## 🎯 V2.1 决策建议

### 大文件函数级修改 (🔴 高优先级)

**触发条件**: 大文件修改需求 > 3 次

**当前数据**:
- 大文件工作流：{summary['large_file_count']} 次
- TODO 注释使用：{summary['fallback_to_todo_count']} 次

**建议**: {"✅ 建议实施" if summary['fallback_to_todo_count'] > 3 else "⏳ 继续观察"}

### 多文件依赖处理 (🟡 中优先级)

**触发条件**: 依赖问题 > 3 次

**当前数据**:
- 依赖问题总数：{summary['dependency_issues_count']} 次

**建议**: {"✅ 建议实施" if summary['dependency_issues_count'] > 3 else "⏳ 继续观察"}

---

## 📝 备注

- 数据收集开始时间：2026-04-08 10:00
- 下次评估时间：2026-04-11 (收集 2 天数据后)
- 数据文件位置：`metrics/incremental_mvp_metrics.jsonl`

---

**报告生成完成** ✅
"""
        
        return report
    
    def export_to_json(self, days: int = 1) -> str:
        """
        导出 JSON 格式数据
        
        Args:
            days: 统计天数
        
        Returns:
            JSON 文件路径
        """
        summary = self.get_summary(days)
        output_file = self.metrics_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return str(output_file)


# 便捷函数
def collect_metrics(workflow_data: Dict):
    """便捷函数：收集工作流指标"""
    collector = MVPMetricsCollector()
    collector.collect_workflow_metrics(workflow_data)


def get_mvp_report(days: int = 1) -> str:
    """便捷函数：获取 MVP 报告"""
    collector = MVPMetricsCollector()
    return collector.generate_report(days)


if __name__ == "__main__":
    # 命令行使用
    import argparse
    
    parser = argparse.ArgumentParser(description='MVP 运行数据收集')
    parser.add_argument('--action', choices=['collect', 'report', 'summary', 'export'], 
                       default='report', help='操作类型')
    parser.add_argument('--days', type=int, default=1, help='统计天数')
    parser.add_argument('--output', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    collector = MVPMetricsCollector()
    
    if args.action == 'report':
        report = collector.generate_report(args.days)
        print(report)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n💾 报告已保存到：{args.output}")
    
    elif args.action == 'summary':
        summary = collector.get_summary(args.days)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    elif args.action == 'export':
        output_file = collector.export_to_json(args.days)
        print(f"💾 数据已导出到：{output_file}")
    
    else:
        print("用法：python3 metrics_collector.py [--action report|summary|export] [--days N]")
