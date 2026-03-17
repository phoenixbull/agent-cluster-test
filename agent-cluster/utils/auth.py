"""
JWT 认证模块
"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

from .config_loader import config

class JWTAuth:
    """JWT 认证器"""
    
    def __init__(self):
        self.secret_key = config.jwt_secret
        self.algorithm = config.jwt_algorithm
        self.expiration_hours = config.jwt_expiration
    
    def create_token(self, username: str, user_id: str = None) -> str:
        """创建 JWT Token"""
        payload = {
            'username': username,
            'user_id': user_id or hashlib.md5(username.encode()).hexdigest(),
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证 JWT Token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token 过期
        except jwt.InvalidTokenError:
            return None  # Token 无效
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return self.hash_password(password) == hashed


# 全局认证实例
jwt_auth = JWTAuth()


def require_auth(func):
    """认证装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 从请求头或 Cookie 获取 Token
        token = None
        
        # 尝试从参数获取（用于 HTTP 请求）
        if hasattr(args[0], 'headers'):
            auth_header = args[0].headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            
            # 尝试从 Cookie 获取
            if not token:
                cookie = args[0].headers.get('Cookie', '')
                for item in cookie.split(';'):
                    if '=' in item:
                        k, v = item.strip().split('=', 1)
                        if k == 'auth_token':
                            token = v
                            break
        
        if not token:
            return {'error': '未授权', 'code': 401}
        
        # 验证 Token
        payload = jwt_auth.verify_token(token)
        if not payload:
            return {'error': 'Token 无效或已过期', 'code': 401}
        
        # 添加用户信息到 kwargs
        kwargs['user'] = payload
        return func(*args, **kwargs)
    
    return wrapper
