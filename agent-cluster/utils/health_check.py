"""
健康检查模块
提供系统健康状态检查端点
"""

import os
import time
import socket
import subprocess
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from .config_loader import config


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.version = '2.3'
    
    def check_service(self):
        # type: () -> Dict[str, Any]
        """检查服务状态"""


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.version = '2.3'
    
    def check_service(self) -> Dict[str, Any]:
        """检查服务状态"""
        return {
            'status': 'healthy',
            'uptime_seconds': int(time.time() - self.start_time),
            'version': self.version,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_database(self):
        # type: () -> Dict[str, Any]
        """检查数据库连接"""
        try:
            db_path = config.database_url.replace('sqlite:///', '')
            db_file = Path(db_path)
            
            # 检查数据库文件是否存在
            if db_file.exists():
                # 检查是否可写
                is_writable = os.access(db_file, os.W_OK)
                return {
                    'status': 'healthy',
                    'path': str(db_file.absolute()),
                    'writable': is_writable
                }
            else:
                return {
                    'status': 'degraded',
                    'message': '数据库文件不存在（首次启动正常）',
                    'path': str(db_file.absolute())
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_github(self):
        # type: () -> Dict[str, Any]
        """检查 GitHub 连接"""
        try:
            if not config.github_token:
                return {
                    'status': 'unhealthy',
                    'message': 'GitHub Token 未配置'
                }
            
            # 简单的网络检查
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
                 'https://api.github.com'],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0 and int(result.stdout) == 200:
                return {'status': 'healthy'}
            else:
                return {
                    'status': 'degraded',
                    'message': f'GitHub API 响应异常：{result.stdout.decode()}'
                }
        except subprocess.TimeoutExpired:
            return {
                'status': 'degraded',
                'message': 'GitHub API 连接超时'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_disk_space(self):
        # type: () -> Dict[str, Any]
        """检查磁盘空间"""
        try:
            stat = os.statvfs('/')
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            used_percent = ((stat.f_blocks - stat.f_bfree) / stat.f_blocks) * 100
            
            status = 'healthy'
            if used_percent > 90:
                status = 'unhealthy'
            elif used_percent > 80:
                status = 'degraded'
            
            return {
                'status': status,
                'total_gb': round(total_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_percent': round(used_percent, 2)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_memory(self):
        # type: () -> Dict[str, Any]
        """检查内存使用"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = int(parts[1].strip().split()[0])
                    mem_info[key] = value
            
            total_mb = mem_info.get('MemTotal', 0) / 1024
            free_mb = mem_info.get('MemFree', 0) / 1024
            available_mb = mem_info.get('MemAvailable', free_mb) / 1024
            used_percent = ((total_mb - available_mb) / total_mb) * 100 if total_mb > 0 else 0
            
            status = 'healthy'
            if used_percent > 90:
                status = 'unhealthy'
            elif used_percent > 80:
                status = 'degraded'
            
            return {
                'status': status,
                'total_mb': round(total_mb, 2),
                'available_mb': round(available_mb, 2),
                'used_percent': round(used_percent, 2)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_port(self, port=None):
        # type: (int) -> Dict[str, Any]
        """检查端口占用"""
        port = port or config.port
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                return {
                    'status': 'healthy',
                    'port': port,
                    'listening': True
                }
            else:
                return {
                    'status': 'unhealthy',
                    'port': port,
                    'listening': False,
                    'message': '端口未监听'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def full_check(self):
        # type: () -> Dict[str, Any]
        """完整健康检查"""
        checks = {
            'service': self.check_service(),
            'database': self.check_database(),
            'github': self.check_github(),
            'disk': self.check_disk_space(),
            'memory': self.check_memory(),
            'port': self.check_port()
        }
        
        # 计算整体状态
        statuses = [check['status'] for check in checks.values()]
        
        if 'unhealthy' in statuses:
            overall = 'unhealthy'
        elif 'degraded' in statuses:
            overall = 'degraded'
        else:
            overall = 'healthy'
        
        return {
            'status': overall,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }


# 全局健康检查实例
health_checker = HealthChecker()


def get_health_status():
    # type: () -> Dict[str, Any]
    """获取健康状态"""
    return health_checker.full_check()
