"""
JWT 认证模块 - 增强版
支持 Token 黑名单、刷新 Token、密码强度检查
"""

import jwt
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set, Tuple
from functools import wraps
from threading import Lock

from .config_loader import config


class PasswordValidator:
    """密码验证器"""
    
    MIN_LENGTH = 6
    REQUIRE_UPPERCASE = False
    REQUIRE_LOWERCASE = False
    REQUIRE_DIGIT = False
    REQUIRE_SPECIAL = False
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        """
        验证密码强度
        
        Returns:
            (是否有效，错误信息)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f'密码长度至少 {cls.MIN_LENGTH} 位'
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, '密码必须包含大写字母'
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, '密码必须包含小写字母'
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, '密码必须包含数字'
        
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, '密码必须包含特殊字符'
        
        return True, ''


class TokenBlacklist:
    """Token 黑名单（用于登出）"""
    
    def __init__(self):
        self.blacklist: Set[str] = set()
        self.expiry_map: Dict[str, datetime] = {}
        self.lock = Lock()
    
    def add(self, token: str, exp: datetime):
        """添加 Token 到黑名单"""
        with self.lock:
            self.blacklist.add(token)
            self.expiry_map[token] = exp
    
    def is_blacklisted(self, token: str) -> bool:
        """检查 Token 是否在黑名单中"""
        with self.lock:
            # 清理过期 Token
            now = datetime.utcnow()
            expired = [t for t, exp in self.expiry_map.items() if exp < now]
            for t in expired:
                self.blacklist.discard(t)
                del self.expiry_map[t]
            
            return token in self.blacklist
    
    def clear(self):
        """清空黑名单"""
        with self.lock:
            self.blacklist.clear()
            self.expiry_map.clear()


class JWTAuth:
    """JWT 认证器"""
    
    def __init__(self):
        self.secret_key = config.jwt_secret
        self.algorithm = config.jwt_algorithm
        self.expiration_hours = config.jwt_expiration
        self.blacklist = TokenBlacklist()
        
        # 默认用户（生产环境应使用数据库）
        self.users = {
            'admin': {
                'password': self.hash_password('admin'),
                'role': 'admin'
            }
        }
    
    def create_token(self, username: str, user_id: str = None, refresh: bool = False) -> str:
        """创建 JWT Token"""
        exp_hours = self.expiration_hours * 7 if refresh else self.expiration_hours
        
        payload = {
            'username': username,
            'user_id': user_id or hashlib.md5(username.encode()).hexdigest(),
            'exp': datetime.utcnow() + timedelta(hours=exp_hours),
            'iat': datetime.utcnow(),
            'type': 'refresh' if refresh else 'access'
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        # Python 3 中 jwt.encode 返回 bytes，需要解码
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token
    
    def verify_token(self, token: str, check_blacklist: bool = True) -> Optional[Dict[str, Any]]:
        """验证 JWT Token"""
        try:
            # 检查黑名单
            if check_blacklist and self.blacklist.is_blacklisted(token):
                return None
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token 过期
        except jwt.InvalidTokenError:
            return None  # Token 无效
    
    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """使用刷新 Token 获取新的访问 Token"""
        payload = self.verify_token(refresh_token, check_blacklist=True)
        if not payload or payload.get('type') != 'refresh':
            return None
        
        return self.create_token(payload['username'], payload['user_id'], refresh=False)
    
    def logout(self, token: str):
        """登出（将 Token 加入黑名单）"""
        payload = self.verify_token(token, check_blacklist=False)
        if payload:
            exp = datetime.fromtimestamp(payload['exp'])
            self.blacklist.add(token, exp)
    
    def hash_password(self, password: str) -> str:
        """哈希密码（加盐）"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            salt, hash_hex = hashed.split('$')
            hash_obj = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            )
            return hash_obj.hex() == hash_hex
        except (ValueError, AttributeError):
            # 兼容旧版简单哈希
            return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    def add_user(self, username: str, password: str, role: str = 'user') -> Tuple[bool, str]:
        """添加用户"""
        if username in self.users:
            return False, '用户已存在'
        
        valid, error = PasswordValidator.validate(password)
        if not valid:
            return False, error
        
        self.users[username] = {
            'password': self.hash_password(password),
            'role': role
        }
        return True, ''
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """修改密码"""
        if username not in self.users:
            return False, '用户不存在'
        
        if not self.verify_password(old_password, self.users[username]['password']):
            return False, '原密码错误'
        
        valid, error = PasswordValidator.validate(new_password)
        if not valid:
            return False, error
        
        self.users[username]['password'] = self.hash_password(new_password)
        return True, ''
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        if username not in self.users:
            return None
        
        if not self.verify_password(password, self.users[username]['password']):
            return None
        
        return {
            'username': username,
            'user_id': hashlib.md5(username.encode()).hexdigest(),
            'role': self.users[username]['role']
        }


# 全局认证实例
jwt_auth = JWTAuth()


def require_auth(func):
    """认证装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 从请求头或 Cookie 获取 Token
        token = None
        
        # 尝试从参数获取（用于 HTTP 请求）
        if args and hasattr(args[0], 'headers'):
            request = args[0]
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            
            # 尝试从 Cookie 获取
            if not token:
                cookie = request.headers.get('Cookie', '')
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


def require_admin(func):
    """管理员认证装饰器"""
    @wraps(func)
    @require_auth
    def wrapper(*args, **kwargs):
        user = kwargs.get('user', {})
        if user.get('role') != 'admin':
            return {'error': '需要管理员权限', 'code': 403}
        return func(*args, **kwargs)
    
    return wrapper
