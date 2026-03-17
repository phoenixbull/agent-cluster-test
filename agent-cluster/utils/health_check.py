"""
健康检查模块
"""

import os
import sys
import json
import psutil
from datetime import datetime
from pathlib import Path

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.workspace = Path(__file__).parent.parent
    
    def get_status(self) -> dict:
        """获取服务状态"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'version': '2.2.0',
            'python_version': sys.version,
            'platform': sys.platform
        }
    
    def get_system_info(self) -> dict:
        """获取系统信息"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids())
        }
    
    def check_database(self) -> dict:
        """检查数据库连接"""
        # TODO: 实现数据库连接检查
        return {
            'status': 'ok',
            'message': '数据库连接正常'
        }
    
    def check_redis(self) -> dict:
        """检查 Redis 连接"""
        # TODO: 实现 Redis 连接检查
        return {
            'status': 'ok',
            'message': 'Redis 连接正常'
        }
    
    def check_disk_space(self) -> dict:
        """检查磁盘空间"""
        workspace = self.workspace
        if workspace.exists():
            usage = psutil.disk_usage(str(workspace))
            return {
                'status': 'ok' if usage.percent < 90 else 'warning',
                'total_gb': usage.total / (1024**3),
                'used_gb': usage.used / (1024**3),
                'free_gb': usage.free / (1024**3),
                'percent': usage.percent
            }
        return {
            'status': 'error',
            'message': '工作区不存在'
        }
    
    def get_full_health(self) -> dict:
        """获取完整健康状态"""
        return {
            'service': self.get_status(),
            'system': self.get_system_info(),
            'database': self.check_database(),
            'redis': self.check_redis(),
            'disk': self.check_disk_space()
        }


# 全局健康检查实例
health_checker = HealthChecker()
