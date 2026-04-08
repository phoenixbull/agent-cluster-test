#!/usr/bin/env python3
"""
指标收集模块测试
测试数据收集和报告生成功能
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics_collector import MVPMetricsCollector


class TestMVPMetricsCollector:
    """MVP 指标收集器测试"""
    
    def test_init(self, temp_workspace):
        """测试初始化"""
        collector = MVPMetricsCollector(str(temp_workspace))
        assert collector.workspace == temp_workspace
        assert collector.metrics_dir.exists()
    
    def test_collect_workflow_metrics(self, temp_workspace):
        """测试工作流指标收集"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        test_data = {
            "workflow_id": "wf-test-001",
            "total_files": 150,
            "large_files_count": 5,
            "incremental_attempts": 1,
            "files_modified": 12,
            "fallback_to_todo": False,
            "review_passed": True,
            "review_status": "approved",
            "rollback_performed": False,
            "feedback_quality_usable": True,
            "dependency_issues": 0,
            "critical_issues_count": 3,
            "total_time_seconds": 7500,
            "incremental_time_seconds": 1800
        }
        
        collector.collect_workflow_metrics(test_data)
        
        # 验证数据已保存
        assert collector.metrics_file.exists()
        
        # 验证内容
        with open(collector.metrics_file, 'r') as f:
            saved = json.loads(f.readline())
            assert saved['workflow_id'] == "wf-test-001"
            assert saved['total_files'] == 150
    
    def test_get_summary_with_data(self, temp_workspace):
        """测试汇总统计 - 有数据"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        # 添加测试数据
        for i in range(3):
            collector.collect_workflow_metrics({
                "workflow_id": f"wf-test-{i:03d}",
                "total_files": 100 + i * 50,
                "review_passed": i < 2,  # 2 通过，1 失败
                "incremental_attempts": i
            })
        
        summary = collector.get_summary(days=7)
        
        assert summary['total_workflows'] == 3
        assert summary['review_passed_count'] == 2
        assert summary['success_rate'] == pytest.approx(66.67, 0.01)
    
    def test_get_summary_no_data(self, temp_workspace):
        """测试汇总统计 - 无数据"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        summary = collector.get_summary(days=1)
        
        assert "error" in summary
        assert "无数据" in summary['error']
    
    def test_generate_report(self, temp_workspace):
        """测试报告生成"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        # 添加测试数据
        collector.collect_workflow_metrics({
            "workflow_id": "wf-test-001",
            "total_files": 150,
            "review_passed": True,
            "incremental_attempts": 1
        })
        
        report = collector.generate_report(days=7)
        
        assert "# 📊 MVP 运行数据报告" in report
        assert "wf-test-001" in report or "总工作流数" in report
    
    def test_export_to_json(self, temp_workspace):
        """测试 JSON 导出"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        collector.collect_workflow_metrics({
            "workflow_id": "wf-test-001",
            "total_files": 100,
            "review_passed": True
        })
        
        output_file = collector.export_to_json(days=7)
        
        assert Path(output_file).exists()
        
        # 验证内容
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert 'total_workflows' in data


class TestEdgeCases:
    """边界情况测试"""
    
    def test_large_numbers(self, temp_workspace):
        """测试大数据量"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        # 添加大量数据
        for i in range(100):
            collector.collect_workflow_metrics({
                "workflow_id": f"wf-test-{i:03d}",
                "total_files": 1000,
                "review_passed": i % 2 == 0
            })
        
        summary = collector.get_summary(days=7)
        
        assert summary['total_workflows'] == 100
        assert summary['success_rate'] == 50.0
    
    def test_special_characters(self, temp_workspace):
        """测试特殊字符"""
        collector = MVPMetricsCollector(str(temp_workspace))
        
        collector.collect_workflow_metrics({
            "workflow_id": "wf-测试-001",
            "total_files": 100,
            "review_passed": True
        })
        
        summary = collector.get_summary(days=7)
        
        assert summary['total_workflows'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
