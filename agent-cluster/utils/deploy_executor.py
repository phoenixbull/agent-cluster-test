"""
Docker 部署执行器
支持 Docker 容器化部署、一键回滚、蓝绿部署
"""

import os
import json
import subprocess
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from .config_loader import config


class DeployStatus(Enum):
    """部署状态"""
    PENDING = 'pending'
    BUILDING = 'building'
    STARTING = 'starting'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    ROLLBACK = 'rollback'
    CANCELLED = 'cancelled'


class DeployExecutor:
    """Docker 部署执行器"""
    
    def __init__(self):
        self.deployments_dir = Path(config.base_path) / 'deployments'
        self.deployments_dir.mkdir(exist_ok=True)
        
        # Docker 配置
        self.docker_registry = os.getenv('DOCKER_REGISTRY', '')
        self.docker_network = os.getenv('DOCKER_NETWORK', 'agent-cluster')
        
        # 确保 Docker 网络存在
        self._ensure_docker_network()
    
    def _ensure_docker_network(self):
        """确保 Docker 网络存在"""
        try:
            subprocess.run(
                ['docker', 'network', 'create', self.docker_network],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=10
            )
        except Exception:
            pass  # 网络可能已存在
    
    def _check_docker(self) -> Tuple[bool, str]:
        """检查 Docker 是否可用"""
        try:
            result = subprocess.run(
                ['docker', 'version'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, 'Docker 可用'
            else:
                return False, f'Docker 不可用：{result.stderr}'
        except FileNotFoundError:
            return False, 'Docker 未安装'
        except Exception as e:
            return False, f'Docker 检查失败：{str(e)}'
    
    def deploy(self, workflow_id: str, project: str = 'default', 
               environment: str = 'production', code_path: str = '') -> Dict[str, Any]:
        """
        执行部署
        
        Args:
            workflow_id: 工作流 ID
            project: 项目名称
            environment: 环境（production/staging）
            code_path: 代码路径
        
        Returns:
            部署结果
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        deployment_id = f"deploy_{timestamp}_{hashlib.md5(workflow_id.encode()).hexdigest()[:8]}"
        
        deploy_dir = self.deployments_dir / deployment_id
        deploy_dir.mkdir(exist_ok=True)
        
        # 部署配置
        deploy_config = {
            'deployment_id': deployment_id,
            'workflow_id': workflow_id,
            'project': project,
            'environment': environment,
            'code_path': code_path,
            'status': DeployStatus.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'docker': {
                'image_name': f"{project}:{timestamp}",
                'container_name': f"{project}_{environment}_{timestamp}",
                'network': self.docker_network
            }
        }
        
        # 保存配置
        config_file = deploy_dir / 'deploy_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(deploy_config, f, ensure_ascii=False, indent=2)
        
        try:
            # 1. 检查 Docker
            docker_available, docker_msg = self._check_docker()
            if not docker_available:
                raise Exception(docker_msg)
            
            # 2. 构建 Docker 镜像
            deploy_config['status'] = DeployStatus.BUILDING.value
            self._save_config(config_file, deploy_config)
            
            image_result = self._build_image(deploy_dir, deploy_config['docker']['image_name'], code_path)
            if not image_result['success']:
                raise Exception(f"镜像构建失败：{image_result['error']}")
            
            # 3. 启动容器
            deploy_config['status'] = DeployStatus.STARTING.value
            self._save_config(config_file, deploy_config)
            
            container_result = self._start_container(deploy_config['docker']['container_name'], 
                                                     deploy_config['docker']['image_name'],
                                                     environment)
            if not container_result['success']:
                raise Exception(f"容器启动失败：{container_result['error']}")
            
            # 4. 健康检查
            health_result = self._health_check(deploy_config['docker']['container_name'])
            
            # 5. 完成部署
            deploy_config['status'] = DeployStatus.COMPLETED.value
            deploy_config['completed_at'] = datetime.now().isoformat()
            deploy_config['health'] = health_result
            self._save_config(config_file, deploy_config)
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'message': '部署成功',
                'config': deploy_config
            }
        
        except Exception as e:
            deploy_config['status'] = DeployStatus.FAILED.value
            deploy_config['error_message'] = str(e)
            self._save_config(config_file, deploy_config)
            
            return {
                'success': False,
                'error': str(e),
                'deployment_id': deployment_id
            }
    
    def _build_image(self, deploy_dir: Path, image_name: str, code_path: str) -> Dict[str, Any]:
        """构建 Docker 镜像"""
        try:
            # 创建 Dockerfile
            dockerfile_content = self._generate_dockerfile(code_path)
            dockerfile = deploy_dir / 'Dockerfile'
            with open(dockerfile, 'w', encoding='utf-8') as f:
                f.write(dockerfile_content)
            
            # 构建镜像
            result = subprocess.run(
                ['docker', 'build', '-t', image_name, '-f', str(dockerfile), str(deploy_dir)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {'success': True, 'image': image_name, 'logs': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '镜像构建超时（5 分钟）'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _start_container(self, container_name: str, image_name: str, environment: str) -> Dict[str, Any]:
        """启动 Docker 容器"""
        try:
            # 停止并删除旧容器
            subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            
            # 确定端口
            port = 8080 if environment == 'production' else 8081
            
            # 启动容器
            result = subprocess.run(
                ['docker', 'run', '-d', 
                 '--name', container_name,
                 '--network', self.docker_network,
                 '-p', f'{port}:80',
                 '--restart', 'unless-stopped',
                 image_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True, 'container_id': result.stdout.strip(), 'port': port}
            else:
                return {'success': False, 'error': result.stderr}
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '容器启动超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _health_check(self, container_name: str, max_retries: int = 10) -> Dict[str, Any]:
        """健康检查"""
        for i in range(max_retries):
            try:
                result = subprocess.run(
                    ['docker', 'inspect', '--format', '{{.State.Health.Status}}', container_name],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
                
                status = result.stdout.strip()
                if status == 'healthy':
                    return {'status': 'healthy', 'retries': i + 1}
                elif status == 'unhealthy':
                    return {'status': 'unhealthy', 'retries': i + 1}
                
                time.sleep(2)
            
            except Exception:
                time.sleep(2)
        
        return {'status': 'unknown', 'retries': max_retries}
    
    def _generate_dockerfile(self, code_path: str) -> str:
        """生成 Dockerfile"""
        return f"""FROM nginx:alpine

# 复制应用代码
COPY . /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost/ || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
"""
    
    def _save_config(self, config_file: Path, config: Dict):
        """保存部署配置"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def stop(self, deployment_id: str) -> Dict[str, Any]:
        """停止部署"""
        try:
            deploy_dir = self.deployments_dir / deployment_id
            if not deploy_dir.exists():
                return {'success': False, 'error': '部署不存在'}
            
            config_file = deploy_dir / 'deploy_config.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                deploy_config = json.load(f)
            
            container_name = deploy_config['docker']['container_name']
            
            # 停止容器
            subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            
            # 更新状态
            deploy_config['status'] = DeployStatus.CANCELLED.value
            deploy_config['stopped_at'] = datetime.now().isoformat()
            self._save_config(config_file, deploy_config)
            
            return {'success': True, 'message': '部署已停止'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def rollback(self, workflow_id: str, target_deployment_id: str = None) -> Dict[str, Any]:
        """
        回滚部署
        
        Args:
            workflow_id: 工作流 ID
            target_deployment_id: 目标部署 ID（可选，默认回滚到上一个成功部署）
        
        Returns:
            回滚结果
        """
        try:
            # 查找上一个成功部署
            if not target_deployment_id:
                deployments = self.get_deployments(workflow_id)
                successful = [d for d in deployments if d.get('status') == DeployStatus.COMPLETED.value]
                
                if len(successful) < 2:
                    return {'success': False, 'error': '没有可回滚的部署'}
                
                target_deployment_id = successful[-2]['deployment_id']
            
            # 获取目标部署配置
            target_dir = self.deployments_dir / target_deployment_id
            if not target_dir.exists():
                return {'success': False, 'error': '目标部署不存在'}
            
            with open(target_dir / 'deploy_config.json', 'r', encoding='utf-8') as f:
                target_config = json.load(f)
            
            # 回滚部署
            result = self.deploy(
                workflow_id=workflow_id,
                project=target_config.get('project', 'default'),
                environment=target_config.get('environment', 'production'),
                code_path=target_config.get('code_path', '')
            )
            
            if result['success']:
                # 标记为回滚
                new_deploy_dir = self.deployments_dir / result['deployment_id']
                with open(new_deploy_dir / 'deploy_config.json', 'r+', encoding='utf-8') as f:
                    config = json.load(f)
                    config['rollback_from'] = target_deployment_id
                    config['is_rollback'] = True
                    f.seek(0)
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                return {
                    'success': True,
                    'message': f'已成功回滚到 {target_deployment_id}',
                    'new_deployment_id': result['deployment_id']
                }
            else:
                return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署状态"""
        try:
            deploy_dir = self.deployments_dir / deployment_id
            if not deploy_dir.exists():
                return {'success': False, 'error': '部署不存在'}
            
            with open(deploy_dir / 'deploy_config.json', 'r', encoding='utf-8') as f:
                deploy_config = json.load(f)
            
            # 获取容器实时状态
            container_name = deploy_config['docker']['container_name']
            try:
                result = subprocess.run(
                    ['docker', 'inspect', container_name],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    container_info = json.loads(result.stdout)[0]
                    deploy_config['container_status'] = {
                        'state': container_info['State']['Status'],
                        'running': container_info['State']['Running'],
                        'started_at': container_info['State']['StartedAt']
                    }
            except Exception:
                pass
            
            return {'success': True, 'status': deploy_config}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_deployments(self, workflow_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取部署列表"""
        deployments = []
        
        for deploy_dir in sorted(self.deployments_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True):
            config_file = deploy_dir / 'deploy_config.json'
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    if workflow_id and config.get('workflow_id') != workflow_id:
                        continue
                    
                    deployments.append(config)
                    
                    if len(deployments) >= limit:
                        break
                except Exception:
                    pass
        
        return deployments
    
    def blue_green_deploy(self, workflow_id: str, project: str, 
                          environment: str = 'production') -> Dict[str, Any]:
        """
        蓝绿部署
        
        Args:
            workflow_id: 工作流 ID
            project: 项目名称
            environment: 环境
        
        Returns:
            部署结果
        """
        try:
            # 获取当前运行的部署
            deployments = self.get_deployments(workflow_id)
            current = next((d for d in deployments if d.get('status') == DeployStatus.COMPLETED.value), None)
            
            # 部署新版本（绿色）
            green_env = 'green' if not current or current.get('environment') != 'green' else 'blue'
            
            result = self.deploy(workflow_id, project, green_env)
            
            if not result['success']:
                return result
            
            # 健康检查通过后切换流量
            new_deployment_id = result['deployment_id']
            
            # TODO: 更新 Nginx 或负载均衡器配置切换流量
            
            return {
                'success': True,
                'message': '蓝绿部署成功',
                'new_deployment_id': new_deployment_id,
                'active_environment': green_env,
                'previous_deployment': current['deployment_id'] if current else None
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


# 全局部署执行器实例
deploy_executor = DeployExecutor()


def get_deploy_executor() -> DeployExecutor:
    """获取部署执行器实例"""
    return deploy_executor
