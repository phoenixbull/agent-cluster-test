"""
Rate Limiting 中间件
基于内存的简单实现，生产环境建议使用 Redis
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from functools import wraps
from threading import Lock

from .config_loader import config


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests=None, window_seconds=None):
        self.max_requests = max_requests or config.rate_limit_requests
        self.window_seconds = window_seconds or config.rate_limit_window
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, client_id):
        # type: (str) -> Tuple[bool, int]
        """
        检查请求是否允许
        
        Returns:
            (是否允许，剩余请求数)
        """


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = None, window_seconds: int = None):
        self.max_requests = max_requests or config.rate_limit_requests
        self.window_seconds = window_seconds or config.rate_limit_window
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        检查请求是否允许
        
        Returns:
            (是否允许，剩余请求数)
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        with self.lock:
            # 清理过期请求
            self.requests[client_id] = [
                t for t in self.requests[client_id] 
                if t > window_start
            ]
            
            # 检查是否超限
            current_count = len(self.requests[client_id])
            remaining = self.max_requests - current_count
            
            if current_count >= self.max_requests:
                return False, 0
            
            # 记录新请求
            self.requests[client_id].append(current_time)
            return True, remaining - 1
    
    def get_retry_after(self, client_id):
        # type: (str) -> int
        """获取重试等待时间（秒）"""
        if not self.requests[client_id]:
            return 0
        
        oldest_request = min(self.requests[client_id])
        retry_after = int(oldest_request + self.window_seconds - time.time())
        return max(0, retry_after)
    
    def reset(self, client_id: str):
        """重置客户端请求计数"""
        with self.lock:
            self.requests[client_id] = []


# 全局速率限制器实例
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = None, window_seconds: int = None):
    """
    Rate Limiting 装饰器
    
    Args:
        max_requests: 最大请求数
        window_seconds: 时间窗口（秒）
    """
    limiter = RateLimiter(max_requests, window_seconds)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取客户端 ID（IP 地址或用户 ID）
            client_id = None
            
            # 尝试从请求对象获取
            if args and hasattr(args[0], 'headers'):
                request = args[0]
                client_id = request.headers.get('X-Real-IP', '')
                if not client_id:
                    # 尝试从 user 获取
                    if hasattr(request, 'user'):
                        client_id = request.user.get('user_id', 'anonymous')
            
            if not client_id:
                client_id = 'unknown'
            
            # 检查速率限制
            allowed, remaining = limiter.is_allowed(client_id)
            
            if not allowed:
                retry_after = limiter.get_retry_after(client_id)
                return {
                    'error': '请求过于频繁',
                    'code': 429,
                    'retry_after': retry_after
                }
            
            # 执行请求
            result = func(*args, **kwargs)
            
            # 添加速率限制头信息（如果结果包含 headers）
            if isinstance(result, dict):
                result['rate_limit_remaining'] = remaining
            
            return result
        
        return wrapper
    return decorator


def get_client_ip(headers: Dict[str, str]) -> str:
    """从请求头获取客户端 IP"""
    # 检查 X-Forwarded-For（代理）
    forwarded_for = headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # 检查 X-Real-IP
    real_ip = headers.get('X-Real-IP', '')
    if real_ip:
        return real_ip
    
    return 'unknown'
