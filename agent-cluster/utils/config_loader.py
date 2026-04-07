"""
配置加载器 - 从环境变量和配置文件加载
优先使用环境变量，其次使用配置文件
"""

import os
import json
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple
from dotenv import load_dotenv

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self):
        # 加载 .env 文件
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # 基础路径
        self.base_path = Path(__file__).parent.parent
        
        # 从环境变量加载配置
        self.load_from_env()
        
        # 从配置文件加载
        self.load_from_file()
    
    def load_from_env(self):
        """从环境变量加载配置"""
        # GitHub 配置
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.github_user = os.getenv('GITHUB_USER', 'phoenixbull')
        self.github_repo = os.getenv('GITHUB_REPO', 'agent-cluster-test')
        
        # 钉钉配置
        self.dingtalk_webhook = os.getenv('DINGTALK_WEBHOOK', '')
        self.dingtalk_secret = os.getenv('DINGTALK_SECRET', '')
        
        # 数据库配置
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///agent_cluster.db')
        
        # Redis 配置
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_password = os.getenv('REDIS_PASSWORD', '')
        
        # JWT 配置
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
        self.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.jwt_expiration = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        
        # 服务配置
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', '8890'))
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # 安全配置
        self.rate_limit_requests = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
        self.rate_limit_window = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
        
        # CORS 配置
        cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
        self.cors_allowed_origins = [o.strip() for o in cors_origins.split(',') if o.strip()]
    
    def load_from_file(self):
        """从配置文件加载"""
        config_path = self.base_path / 'cluster_config_v2.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.cluster_config = json.load(f)
        else:
            self.cluster_config = {}
        
        # 加载项目配置
        projects_path = self.base_path / 'projects.json'
        if projects_path.exists():
            with open(projects_path, 'r', encoding='utf-8') as f:
                self.projects = json.load(f)
        else:
            self.projects = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return getattr(self, key, default)
    
    def is_production(self) -> bool:
        """是否生产环境"""
        return not self.debug
    
    def validate(self) -> Tuple[bool, List[str]]:
        """验证配置完整性"""
        errors = []  # type: List[str]
        
        # 必需的配置
        if not self.github_token:
            errors.append('GITHUB_TOKEN 未配置')
        
        if not self.dingtalk_webhook:
            errors.append('DINGTALK_WEBHOOK 未配置')
        
        if self.jwt_secret == 'change-me-in-production':
            errors.append('JWT_SECRET_KEY 使用默认值，生产环境请修改')
        
        # 警告
        warnings = []  # type: List[str]
        if self.debug:
            warnings.append('当前为调试模式，生产环境请设置 DEBUG=false')
        
        return len(errors) == 0, errors, warnings


# 全局配置实例
config = ConfigLoader()


def get_config() -> ConfigLoader:
    """获取配置实例"""
    return config


def validate_config():
    # type: () -> Tuple[bool, List[str]]
    """验证配置"""
    return config.validate()
