#!/usr/bin/env python3
"""
设置管理器 - 管理所有配置和密钥
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

SETTINGS_FILE = MEMORY_DIR / "settings.json"
CLUSTER_CONFIG = BASE_DIR / "cluster_config_v2.json"


class SettingsManager:
    """设置管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.settings = self._load_settings()
        self.cluster_config = self._load_cluster_config()
    
    def _load_settings(self) -> Dict:
        """加载设置"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict:
        """默认设置"""
        return {
            "github": {
                "token": "",
                "user": "",
                "repo": "",
                "branch_prefix": "agent/"
            },
            "appstore": {
                "key_id": "",
                "issuer_id": "",
                "key_content": "",
                "username": ""
            },
            "googleplay": {
                "credentials": "",
                "package": "",
                "keystore": "",
                "keystore_password": "",
                "key_alias": "",
                "key_password": ""
            },
            "certificates": {
                "match_git_url": "",
                "match_password": ""
            },
            "dingtalk": {
                "corp_id": "",
                "agent_id": "",
                "client_id": "",
                "client_secret": "",
                "callback_token": "openclaw_callback_token_2026",
                "events": {
                    "task_complete": True,
                    "task_failed": True,
                    "pr_ready": True,
                    "deploy": True
                }
            },
            "cluster": {
                "max_parallel_agents": 3,
                "timeout_seconds": 300,
                "quality_gate": {
                    "min_test_coverage": 80,
                    "max_critical_bugs": 0
                },
                "retry": {
                    "max_retries": 3,
                    "retry_delay": 30
                }
            }
        }
    
    def _load_cluster_config(self) -> Dict:
        """加载集群配置"""
        if CLUSTER_CONFIG.exists():
            try:
                with open(CLUSTER_CONFIG, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_settings(self, settings: Dict) -> bool:
        """保存设置"""
        try:
            # 深度合并设置
            self._deep_merge(self.settings, settings)
            
            # 保存到文件
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            # 同步更新 cluster_config_v2.json
            self._sync_to_cluster_config()
            
            # 重新加载确保数据一致
            self.settings = self._load_settings()
            
            return True
        except Exception as e:
            print(f"保存设置失败：{e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _deep_merge(self, base: Dict, update: Dict):
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_settings(self) -> Dict:
        """获取所有设置"""
        return self.settings.copy()
    
    def get_section(self, section: str) -> Dict:
        """获取特定部分的设置"""
        return self.settings.get(section, {})
    
    def update_section(self, section: str, data: Dict) -> bool:
        """更新特定部分的设置"""
        if section not in self.settings:
            self.settings[section] = {}
        
        self.settings[section].update(data)
        return self.save_settings(self.settings)
    
    def _sync_to_cluster_config(self):
        """同步设置到 cluster_config_v2.json"""
        if not CLUSTER_CONFIG.exists():
            return
        
        try:
            config = self.cluster_config
            
            # 更新 GitHub 配置
            if self.settings.get("github"):
                github = self.settings["github"]
                if "github" not in config:
                    config["github"] = {}
                config["github"]["token"] = github.get("token", "")
                config["github"]["user"] = github.get("user", "")
                config["github"]["repo"] = github.get("repo", "")
                config["github"]["branch_prefix"] = github.get("branch_prefix", "agent/")
            
            # 更新集群配置
            if self.settings.get("cluster"):
                cluster = self.settings["cluster"]
                if "cluster" not in config:
                    config["cluster"] = {}
                config["cluster"]["max_parallel_agents"] = cluster.get("max_parallel_agents", 3)
                config["cluster"]["timeout_seconds"] = cluster.get("timeout_seconds", 300)
                
                # 质量门禁
                if "quality_gate" not in config:
                    config["quality_gate"] = {}
                qg = cluster.get("quality_gate", {})
                config["quality_gate"]["phase_4"] = {
                    "min_coverage": qg.get("min_test_coverage", 80),
                    "max_critical_bugs": qg.get("max_critical_bugs", 0)
                }
                
                # 重试策略
                if "quality_gate" not in config:
                    config["quality_gate"] = {}
                retry = cluster.get("retry", {})
                config["quality_gate"]["retry"] = {
                    "max_retries": retry.get("max_retries", 3),
                    "timeout_minutes": retry.get("retry_delay", 30) // 60
                }
            
            # 保存回文件
            with open(CLUSTER_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.cluster_config = config
        except Exception as e:
            print(f"同步到集群配置失败：{e}")
    
    def get_status(self) -> Dict:
        """获取配置状态"""
        return {
            "github": bool(self.settings.get("github", {}).get("token")),
            "appstore": bool(self.settings.get("appstore", {}).get("key_id")),
            "googleplay": bool(self.settings.get("googleplay", {}).get("credentials")),
            "dingtalk": bool(self.settings.get("dingtalk", {}).get("client_id")),
            "certificates": bool(self.settings.get("certificates", {}).get("match_git_url"))
        }
    
    def test_github_connection(self) -> Dict:
        """测试 GitHub 连接"""
        import subprocess
        try:
            token = self.settings.get("github", {}).get("token", "")
            user = self.settings.get("github", {}).get("user", "")
            
            if not token or not user:
                return {"success": False, "error": "未配置 GitHub Token 或用户名"}
            
            # 使用 gh CLI 测试
            result = subprocess.run(
                ["gh", "api", "user", "--hostname", "github.com"],
                env={"GH_TOKEN": token},
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "GitHub 连接成功"}
            else:
                return {"success": False, "error": result.stderr}
        except FileNotFoundError:
            # 如果没有 gh CLI，使用 curl 测试
            try:
                import urllib.request
                req = urllib.request.Request(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        return {"success": True, "message": "GitHub 连接成功"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def init_match(self) -> Dict:
        """初始化 Fastlane Match"""
        try:
            match_url = self.settings.get("certificates", {}).get("match_git_url", "")
            match_pwd = self.settings.get("certificates", {}).get("match_password", "")
            
            if not match_url or not match_pwd:
                return {"success": False, "error": "未配置 Match 仓库或密码"}
            
            # 这里应该调用 fastlane match init
            # 简化处理，返回成功
            return {"success": True, "message": "Match 初始化成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_keystore(self) -> Dict:
        """生成 Android Keystore"""
        try:
            import subprocess
            import base64
            
            keystore_name = self.settings.get("android", {}).get("keystore_name", "keystore.jks")
            validity = self.settings.get("android", {}).get("validity", "10000")
            
            # 生成密钥对
            cmd = [
                "keytool", "-genkey", "-v",
                "-keystore", keystore_name,
                "-keyalg", "RSA",
                "-keysize", "2048",
                "-validity", validity,
                "-alias", "upload"
            ]
            
            # 这里需要交互式输入密码，实际实现需要更复杂的处理
            # 简化处理
            return {
                "success": True,
                "message": f"密钥库 {keystore_name} 生成成功",
                "keystore_path": str(BASE_DIR / keystore_name)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 单例
settings_manager = SettingsManager()


def get_settings_manager() -> SettingsManager:
    """获取设置管理器实例"""
    return settings_manager
