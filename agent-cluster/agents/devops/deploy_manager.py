#!/usr/bin/env python3
"""
部署管理器 - V2.2 增强版
支持多环境部署、自动回滚、部署历史追踪
"""

import json
import asyncio
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class DeploymentStatus(Enum):
    """部署状态枚举"""
    PENDING = "pending"
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    HEALTH_CHECK = "health_check"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class DeploymentManager:
    """部署管理器（支持多环境、回滚）"""
    
    def __init__(self, config_path: str = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 使用绝对路径
            self.config_path = Path(__file__).parent.parent.parent / "configs" / "environments.json"
        
        self.config = self._load_config()
        self.history_path = Path("~/.openclaw/workspace/agent-cluster/memory/deployment_history.json").expanduser()
        
        # 确保历史目录存在
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化部署历史
        self._ensure_history_file()
    
    def _load_config(self) -> Dict:
        """加载环境配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"environments": {}, "deployment": {}, "rollback": {}}
    
    def _ensure_history_file(self):
        """确保部署历史文件存在"""
        if not self.history_path.exists():
            self._write_history({"deployments": [], "version": "2.2"})
    
    def _read_history(self) -> Dict:
        """读取部署历史"""
        if self.history_path.exists():
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"deployments": [], "version": "2.2"}
    
    def _write_history(self, data: Dict):
        """写入部署历史"""
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_environment(self, env_name: str) -> Optional[Dict]:
        """获取环境配置"""
        envs = self.config.get("environments", {})
        return envs.get(env_name)
    
    def list_environments(self) -> List[Dict]:
        """列出所有环境"""
        envs = self.config.get("environments", {})
        return [
            {
                "name": name,
                "config": config
            }
            for name, config in envs.items()
        ]
    
    async def deploy(self, env_name: str, version: str, 
                    commit_hash: str = None, 
                    source_path: str = None,
                    wait_for_approval: bool = True) -> Dict:
        """
        执行部署
        
        Args:
            env_name: 环境名称 (development/staging/production)
            version: 版本号
            commit_hash: Git 提交哈希
            source_path: 源代码路径
            wait_for_approval: 是否需要等待审批
        
        Returns:
            部署结果
        """
        env_config = self.get_environment(env_name)
        if not env_config:
            return {
                "success": False,
                "error": f"环境 {env_name} 不存在",
                "deployment_id": None
            }
        
        # 生成部署 ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        deployment_id = f"deploy-{env_name}-{version}-{timestamp}"
        
        # 创建部署记录
        deployment_record = {
            "id": deployment_id,
            "environment": env_name,
            "version": version,
            "commit_hash": commit_hash,
            "source_path": str(source_path) if source_path else None,
            "status": DeploymentStatus.PENDING.value,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "health_checks": [],
            "logs": [],
            "rollback_to": None
        }
        
        try:
            # 检查是否需要审批
            if env_config.get("require_approval") and wait_for_approval:
                deployment_record["status"] = DeploymentStatus.PENDING.value
                deployment_record["logs"].append("⏳ 等待人工审批...")
                self._update_history(deployment_record)
                
                # 发送审批通知
                await self._send_approval_notification(env_name, version, deployment_id)
                
                # 等待审批（超时自动取消）
                timeout = self.config.get("deployment", {}).get("confirmation_timeout_minutes", 30)
                approved = await self._wait_for_approval(deployment_id, timeout * 60)
                
                if not approved:
                    deployment_record["status"] = DeploymentStatus.CANCELLED.value
                    deployment_record["logs"].append("❌ 部署已取消（超时或拒绝）")
                    deployment_record["completed_at"] = datetime.now().isoformat()
                    self._update_history(deployment_record)
                    return {
                        "success": False,
                        "error": "部署未获得批准",
                        "deployment_id": deployment_id
                    }
            
            # 开始部署
            deployment_record["status"] = DeploymentStatus.DEPLOYING.value
            deployment_record["logs"].append(f"🚀 开始部署到 {env_name}")
            self._update_history(deployment_record)
            
            # 执行部署脚本
            deploy_result = await self._execute_deploy(
                env_name, version, commit_hash, source_path
            )
            
            if not deploy_result["success"]:
                raise Exception(f"部署执行失败：{deploy_result.get('error', '未知错误')}")
            
            deployment_record["logs"].append("✅ 部署执行完成")
            
            # 健康检查
            deployment_record["status"] = DeploymentStatus.HEALTH_CHECK.value
            deployment_record["logs"].append("🏥 执行健康检查...")
            self._update_history(deployment_record)
            
            health_result = await self._health_check(env_name, env_config)
            deployment_record["health_checks"] = health_result["checks"]
            
            if not health_result["success"]:
                raise Exception(f"健康检查失败：{health_result.get('error', '未知错误')}")
            
            deployment_record["logs"].append("✅ 健康检查通过")
            
            # 部署成功
            deployment_record["status"] = DeploymentStatus.COMPLETED.value
            deployment_record["completed_at"] = datetime.now().isoformat()
            deployment_record["logs"].append(f"🎉 部署成功完成！")
            self._update_history(deployment_record)
            
            # 发送成功通知
            await self._send_deployment_notification(env_name, version, deployment_id, True)
            
            return {
                "success": True,
                "deployment_id": deployment_id,
                "environment": env_name,
                "version": version,
                "message": "部署成功"
            }
            
        except Exception as e:
            deployment_record["status"] = DeploymentStatus.FAILED.value
            deployment_record["logs"].append(f"❌ 部署失败：{str(e)}")
            deployment_record["completed_at"] = datetime.now().isoformat()
            self._update_history(deployment_record)
            
            # 发送失败通知
            await self._send_deployment_notification(env_name, version, deployment_id, False, str(e))
            
            # 自动回滚
            if self.config.get("rollback", {}).get("auto_rollback_on_failure", True):
                deployment_record["logs"].append("🔄 触发自动回滚...")
                rollback_result = await self.rollback(env_name, deployment_id)
                
                if rollback_result["success"]:
                    deployment_record["status"] = DeploymentStatus.ROLLED_BACK.value
                    deployment_record["rollback_to"] = rollback_result.get("rolled_back_to")
            
            self._update_history(deployment_record)
            
            return {
                "success": False,
                "error": str(e),
                "deployment_id": deployment_id,
                "auto_rollback_triggered": True
            }
    
    async def _execute_deploy(self, env_name: str, version: str, 
                             commit_hash: str, source_path: str) -> Dict:
        """执行实际部署逻辑"""
        try:
            # 这里可以实现具体的部署逻辑
            # 示例：Docker 部署
            env_config = self.get_environment(env_name)
            
            # 构建 Docker 镜像
            docker_config = self.config.get("deployment", {}).get("docker", {})
            image_tag = f"{docker_config.get('registry')}/{docker_config.get('namespace')}:{version}"
            
            # 模拟部署过程（实际使用时替换为真实部署逻辑）
            await asyncio.sleep(2)  # 模拟部署时间
            
            return {
                "success": True,
                "image": image_tag,
                "message": f"已部署 {version} 到 {env_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _health_check(self, env_name: str, env_config: Dict) -> Dict:
        """执行健康检查"""
        checks = []
        health_config = env_config.get("health_check", {})
        
        if not health_config.get("enabled", True):
            return {"success": True, "checks": []}
        
        # 模拟健康检查（实际使用时替换为真实检查逻辑）
        endpoints = [
            health_config.get("endpoint", "/health"),
            "/api/status",
            "/metrics"
        ]
        
        for endpoint in endpoints[:1]:  # 只检查主 endpoint
            try:
                # 模拟健康检查
                await asyncio.sleep(1)
                checks.append({
                    "endpoint": endpoint,
                    "status": "healthy",
                    "response_time_ms": 150,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                checks.append({
                    "endpoint": endpoint,
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        all_healthy = all(c.get("status") == "healthy" for c in checks)
        
        return {
            "success": all_healthy,
            "checks": checks
        }
    
    async def rollback(self, env_name: str, target_deployment_id: str = None, 
                      target_version: str = None) -> Dict:
        """
        回滚部署
        
        Args:
            env_name: 环境名称
            target_deployment_id: 目标部署 ID（回滚到特定部署）
            target_version: 目标版本号（回滚到特定版本）
        
        Returns:
            回滚结果
        """
        env_config = self.get_environment(env_name)
        if not env_config:
            return {
                "success": False,
                "error": f"环境 {env_name} 不存在"
            }
        
        if not env_config.get("rollback_enabled", True):
            return {
                "success": False,
                "error": f"环境 {env_name} 未启用回滚功能"
            }
        
        try:
            # 查找目标部署
            history = self._read_history()
            target = None
            
            if target_deployment_id:
                for dep in history.get("deployments", []):
                    if dep.get("id") == target_deployment_id:
                        target = dep
                        break
            elif target_version:
                # 查找指定版本的最后一个成功部署
                for dep in reversed(history.get("deployments", [])):
                    if dep.get("version") == target_version and dep.get("status") == "completed":
                        target = dep
                        break
            else:
                # 默认回滚到上一个成功部署
                for dep in reversed(history.get("deployments", [])):
                    if dep.get("environment") == env_name and dep.get("status") == "completed":
                        target = dep
                        break
            
            if not target:
                return {
                    "success": False,
                    "error": "未找到可回滚的目标部署"
                }
            
            # 执行回滚
            rollback_id = f"rollback-{env_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 模拟回滚过程
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "rollback_id": rollback_id,
                "rolled_back_to": target.get("version"),
                "deployment_id": target.get("id"),
                "message": f"已回滚到版本 {target.get('version')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_deployment_history(self, env_name: str = None, 
                               limit: int = 20) -> List[Dict]:
        """获取部署历史"""
        history = self._read_history()
        deployments = history.get("deployments", [])
        
        if env_name:
            deployments = [d for d in deployments if d.get("environment") == env_name]
        
        # 按时间倒序
        deployments.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        
        return deployments[:limit]
    
    def _update_history(self, deployment_record: Dict):
        """更新部署历史"""
        history = self._read_history()
        
        # 更新或添加记录
        found = False
        for i, dep in enumerate(history.get("deployments", [])):
            if dep.get("id") == deployment_record["id"]:
                history["deployments"][i] = deployment_record
                found = True
                break
        
        if not found:
            if "deployments" not in history:
                history["deployments"] = []
            history["deployments"].append(deployment_record)
        
        # 限制历史记录数量
        max_entries = self.config.get("history", {}).get("max_entries", 100)
        if len(history["deployments"]) > max_entries:
            history["deployments"] = history["deployments"][-max_entries:]
        
        self._write_history(history)
    
    async def _send_approval_notification(self, env_name: str, version: str, 
                                         deployment_id: str):
        """发送审批通知"""
        # 这里集成钉钉通知
        print(f"📢 发送部署审批通知：{env_name} - {version} - {deployment_id}")
    
    async def _send_deployment_notification(self, env_name: str, version: str,
                                           deployment_id: str, success: bool,
                                           error: str = None):
        """发送部署结果通知"""
        status = "✅" if success else "❌"
        message = f"{status} 部署{status}：{env_name} - {version}"
        if error:
            message += f"\n错误：{error}"
        print(f"📢 {message}")
    
    async def _wait_for_approval(self, deployment_id: str, timeout_seconds: int) -> bool:
        """等待审批（简化版，实际使用时需要集成审批系统）"""
        # 这里可以实现审批等待逻辑
        # 简化版：直接返回 True（模拟自动通过）
        await asyncio.sleep(1)
        return True


# 便捷函数
def get_deployment_manager() -> DeploymentManager:
    """获取部署管理器实例"""
    return DeploymentManager()


if __name__ == "__main__":
    # 测试
    manager = DeploymentManager()
    print("可用环境:", [e["name"] for e in manager.list_environments()])
    print("最近部署:", len(manager.get_deployment_history()))
