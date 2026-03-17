"""
Prometheus 指标导出器
为 Agent Cluster 提供 Prometheus 格式的监控指标
"""

import time
import json
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .database import get_database
from .config_loader import config


class MetricsExporter:
    """Prometheus 指标导出器"""
    
    def __init__(self):
        self.db = get_database()
        self.start_time = time.time()
    
    def get_metrics(self) -> str:
        """获取 Prometheus 格式的指标"""
        metrics = []
        
        # ========== 基础指标 ==========
        
        # 运行时间
        uptime = time.time() - self.start_time
        metrics.append(f'# HELP process_uptime_seconds 进程运行时间')
        metrics.append(f'# TYPE process_uptime_seconds counter')
        metrics.append(f'process_uptime_seconds {uptime:.2f}')
        
        # 进程内存
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        memory_kb = int(line.split()[1])
                        memory_bytes = memory_kb * 1024
                        metrics.append(f'# HELP process_resident_memory_bytes 进程内存使用')
                        metrics.append(f'# TYPE process_resident_memory_bytes gauge')
                        metrics.append(f'process_resident_memory_bytes {memory_bytes}')
                        break
        except Exception:
            pass
        
        # 进程 CPU
        try:
            with open('/proc/self/stat', 'r') as f:
                stat = f.read().split()
                utime = int(stat[13])
                stime = int(stat[14])
                cpu_seconds = (utime + stime) / 100.0  # 转换为秒
                metrics.append(f'# HELP process_cpu_seconds_total 进程 CPU 使用总时间')
                metrics.append(f'# TYPE process_cpu_seconds_total counter')
                metrics.append(f'process_cpu_seconds_total {cpu_seconds:.2f}')
        except Exception:
            pass
        
        # ========== 工作流指标 ==========
        
        workflows = self.db.get_workflows(limit=1000)
        
        # 工作流状态计数
        status_counts = {}
        for wf in workflows:
            status = wf.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        metrics.append(f'# HELP workflow_status 工作流状态')
        metrics.append(f'# TYPE workflow_status gauge')
        for status, count in status_counts.items():
            metrics.append(f'workflow_status{{status="{status}"}} {count}')
        
        # 工作流创建速率
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_workflows = [wf for wf in workflows if datetime.fromisoformat(wf['created_at']) >= today_start]
        
        metrics.append(f'# HELP workflow_created_total 今日创建工作流总数')
        metrics.append(f'# TYPE workflow_created_total counter')
        metrics.append(f'workflow_created_total {len(today_workflows)}')
        
        # ========== 部署指标 ==========
        
        from .deploy_executor import get_deploy_executor
        executor = get_deploy_executor()
        deployments = executor.get_deployments(limit=100)
        
        deploy_status_counts = {}
        for dep in deployments:
            status = dep.get('status', 'unknown')
            deploy_status_counts[status] = deploy_status_counts.get(status, 0) + 1
        
        metrics.append(f'# HELP deployment_status 部署状态')
        metrics.append(f'# TYPE deployment_status gauge')
        for status, count in deploy_status_counts.items():
            metrics.append(f'deployment_status{{status="{status}"}} {count}')
        
        # ========== 成本指标 ==========
        
        cost_stats = self.db.get_cost_stats(days=1)
        
        metrics.append(f'# HELP cost_total 今日总成本')
        metrics.append(f'# TYPE cost_total gauge')
        metrics.append(f'cost_total {cost_stats.get("total_cost", 0):.4f}')
        
        metrics.append(f'# HELP cost_calls 今日总调用次数')
        metrics.append(f'# TYPE cost_calls counter')
        metrics.append(f'cost_calls {cost_stats.get("total_calls", 0)}')
        
        # ========== HTTP 请求指标（模拟） ==========
        
        # 这些需要在实际请求中记录
        metrics.append(f'# HELP http_requests_total HTTP 请求总数')
        metrics.append(f'# TYPE http_requests_total counter')
        metrics.append(f'http_requests_total{{method="GET",endpoint="/api/status"}} 0')
        metrics.append(f'http_requests_total{{method="GET",endpoint="/api/workflows"}} 0')
        metrics.append(f'http_requests_total{{method="POST",endpoint="/api/login"}} 0')
        
        metrics.append(f'# HELP http_request_duration_seconds HTTP 请求延迟')
        metrics.append(f'# TYPE http_request_duration_seconds histogram')
        metrics.append(f'http_request_duration_seconds_bucket{{le="0.1"}} 0')
        metrics.append(f'http_request_duration_seconds_bucket{{le="0.5"}} 0')
        metrics.append(f'http_request_duration_seconds_bucket{{le="1.0"}} 0')
        metrics.append(f'http_request_duration_seconds_bucket{{le="5.0"}} 0')
        metrics.append(f'http_request_duration_seconds_bucket{{le="+Inf"}} 0')
        metrics.append(f'http_request_duration_seconds_count 0')
        metrics.append(f'http_request_duration_seconds_sum 0.0')
        
        # ========== 系统指标 ==========
        
        # 磁盘使用
        try:
            stat = os.statvfs(config.base_path)
            total_bytes = stat.f_blocks * stat.f_frsize
            avail_bytes = stat.f_bavail * stat.f_frsize
            used_percent = ((stat.f_blocks - stat.f_bfree) / stat.f_blocks) * 100
            
            metrics.append(f'# HELP node_filesystem_size_bytes 文件系统总大小')
            metrics.append(f'# TYPE node_filesystem_size_bytes gauge')
            metrics.append(f'node_filesystem_size_bytes{{mountpoint="{config.base_path}"}} {total_bytes}')
            
            metrics.append(f'# HELP node_filesystem_avail_bytes 文件系统可用空间')
            metrics.append(f'# TYPE node_filesystem_avail_bytes gauge')
            metrics.append(f'node_filesystem_avail_bytes{{mountpoint="{config.base_path}"}} {avail_bytes}')
            
            metrics.append(f'# HELP node_filesystem_free_percent 文件系统可用百分比')
            metrics.append(f'# TYPE node_filesystem_free_percent gauge')
            metrics.append(f'node_filesystem_free_percent{{mountpoint="{config.base_path}"}} {100 - used_percent:.2f}')
        except Exception:
            pass
        
        return '\n'.join(metrics) + '\n'


# 全局指标导出器实例
metrics_exporter = MetricsExporter()


def get_metrics_exporter() -> MetricsExporter:
    """获取指标导出器实例"""
    return metrics_exporter


def get_prometheus_metrics() -> str:
    """获取 Prometheus 格式指标"""
    return metrics_exporter.get_metrics()
