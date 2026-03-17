"""
配置加载模块
从环境变量或.env 文件加载配置
"""

import os
from pathlib import Path
from typing import Optional

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self):
        self.env_file = Path(__file__).parent.parent / '.env'
        self._load_env_file()
    
    def _load_env_file(self):
        """加载.env 文件"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
    
    def get(self, key: str, default: str = '') -> str:
        """获取环境变量"""
        return os.environ.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数环境变量"""
        try:
            return int(os.environ.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔环境变量"""
        value = os.environ.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @property
    def github_token(self) -> str:
        """GitHub Token"""
        return self.get('GITHUB_TOKEN')
    
    @property
    def github_user(self) -> str:
        """GitHub 用户名"""
        return self.get('GITHUB_USER', 'phoenixbull')
    
    @property
    def github_repo(self) -> str:
        """GitHub 仓库"""
        return self.get('GITHUB_REPO', 'agent-cluster-test')
    
    @property
    def dingtalk_webhook(self) -> str:
        """钉钉 Webhook"""
        return self.get('DINGTALK_WEBHOOK')
    
    @property
    def dingtalk_secret(self) -> str:
        """钉钉密钥"""
        return self.get('DINGTALK_SECRET')
    
    @property
    def database_url(self) -> str:
        """数据库 URL"""
        return self.get('DATABASE_URL', 'sqlite:///agent_cluster.db')
    
    @property
    def redis_host(self) -> str:
        """Redis 主机"""
        return self.get('REDIS_HOST', 'localhost')
    
    @property
    def redis_port(self) -> int:
        """Redis 端口"""
        return self.get_int('REDIS_PORT', 6379)
    
    @property
    def jwt_secret(self) -> str:
        """JWT 密钥"""
        return self.get('JWT_SECRET_KEY', 'change-this-secret-key')
    
    @property
    def jwt_algorithm(self) -> str:
        """JWT 算法"""
        return self.get('JWT_ALGORITHM', 'HS256')
    
    @property
    def jwt_expiration(self) -> int:
        """JWT 过期时间（小时）"""
        return self.get_int('JWT_EXPIRATION_HOURS', 24)
    
    @property
    def host(self) -> str:
        """服务主机"""
        return self.get('HOST', '0.0.0.0')
    
    @property
    def port(self) -> int:
        """服务端口"""
        return self.get_int('PORT', 8890)
    
    @property
    def debug(self) -> bool:
        """调试模式"""
        return self.get_bool('DEBUG', False)


# 全局配置实例
config = ConfigLoader()
