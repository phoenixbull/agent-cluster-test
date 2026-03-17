"""
部署执行模块
实现实际的 Docker 部署功能
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config_loader import config

class DeployExecutor:
    """部署执行器"""
    
    def __init__(self):
        self.workspace = Path(__file__).parent.parent
        self.deployments_dir = self.workspace / 'deployments'
        self.deployments_dir.mkdir(exist_ok=True)
    
    def deploy(self, workflow_id: str, project: str, code_path: str) -> Dict[str, Any]:
        """
        执行部署
        
        Args:
            workflow_id: 工作流 ID
            project: 项目名称
            code_path: 代码路径
        
        Returns:
            部署结果
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            deployment_id = f"{project}_{timestamp}"
            deployment_dir = self.deployments_dir / deployment_id
            deployment_dir.mkdir(exist_ok=True)
            
            # 1. 准备部署配置
            deploy_config = {
                'workflow_id': workflow_id,
                'project': project,
                'code_path': code_path,
                'deployment_id': deployment_id,
                'deployed_at': datetime.now().isoformat(),
                'status': 'deploying'
            }
            
            # 保存部署配置
            config_file = deployment_dir / 'deploy_config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(deploy_config, f, indent=2, ensure_ascii=False)
            
            # 2. 创建 Dockerfile
            dockerfile = deployment_dir / 'Dockerfile'
            self._create_dockerfile(dockerfile, code_path)
            
            # 3. 创建 docker-compose.yml
            compose_file = deployment_dir / 'docker-compose.yml'
            self._create_compose_file(compose_file, deployment_id)
            
            # 4. 构建 Docker 镜像
            print(f"[{datetime.now()}] 构建 Docker 镜像...")
            build_result = self._build_image(deployment_dir, deployment_id)
            
            if not build_result['success']:
                deploy_config['status'] = 'failed'
                deploy_config['error'] = build_result.get('error', '构建失败')
                self._save_deploy_config(config_file, deploy_config)
                return deploy_config
            
            # 5. 启动容器
            print(f"[{datetime.now()}] 启动 Docker 容器...")
            start_result = self._start_container(deployment_id)
            
            if not start_result['success']:
                deploy_config['status'] = 'failed'
                deploy_config['error'] = start_result.get('error', '启动失败')
                self._save_deploy_config(config_file, deploy_config)
                return deploy_config
            
            # 6. 更新部署状态
            deploy_config['status'] = 'deployed'
            deploy_config['container_id'] = start_result.get('container_id')
            deploy_config['image_id'] = build_result.get('image_id')
            deploy_config['port'] = start_result.get('port', 8080)
            self._save_deploy_config(config_file, deploy_config)
            
            print(f"[{datetime.now()}] 部署成功：{deployment_id}")
            return deploy_config
            
        except Exception as e:
            print(f"[{datetime.now()}] 部署异常：{e}")
            return {
                'status': 'failed',
                'error': str(e),
                'workflow_id': workflow_id,
                'project': project
            }
    
    def _create_dockerfile(self, path: Path, code_path: str):
        """创建 Dockerfile"""
        dockerfile_content = f"""FROM python:3.9-slim

WORKDIR /app

# 复制代码
COPY {code_path} /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt || true

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "app.py"]
"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
    
    def _create_compose_file(self, path: Path, deployment_id: str):
        """创建 docker-compose.yml"""
        compose_content = f"""version: '3.8'

services:
  app:
    image: {deployment_id}:latest
    container_name: {deployment_id}
    ports:
      - "8080:8080"
    restart: unless-stopped
    environment:
      - ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(compose_content)
    
    def _build_image(self, build_dir: Path, image_name: str) -> Dict[str, Any]:
        """构建 Docker 镜像"""
        try:
            result = subprocess.run(
                ['docker', 'build', '-t', f'{image_name}:latest', '.'],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # 获取镜像 ID
                image_result = subprocess.run(
                    ['docker', 'images', '-q', f'{image_name}:latest'],
                    capture_output=True,
                    text=True
                )
                return {
                    'success': True,
                    'image_id': image_result.stdout.strip()[:12],
                    'logs': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '构建超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _start_container(self, deployment_id: str) -> Dict[str, Any]:
        """启动 Docker 容器"""
        try:
            # 检查是否已有容器运行
            subprocess.run(
                ['docker', 'rm', '-f', deployment_id],
                capture_output=True
            )
            
            # 启动容器
            result = subprocess.run(
                ['docker', 'run', '-d', '--name', deployment_id, '-p', '8080:8080', f'{deployment_id}:latest'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'container_id': result.stdout.strip()[:12],
                    'port': 8080
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _save_deploy_config(self, path: Path, config: Dict):
        """保存部署配置"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def stop(self, deployment_id: str) -> Dict[str, Any]:
        """停止部署"""
        try:
            subprocess.run(['docker', 'stop', deployment_id], capture_output=True)
            subprocess.run(['docker', 'rm', deployment_id], capture_output=True)
            return {'success': True, 'message': f'已停止部署：{deployment_id}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def rollback(self, workflow_id: str) -> Dict[str, Any]:
        """回滚部署"""
        # TODO: 实现回滚逻辑
        return {
            'success': False,
            'error': '回滚功能待实现'
        }
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署状态"""
        try:
            result = subprocess.run(
                ['docker', 'inspect', deployment_id],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                info = json.loads(result.stdout)[0]
                return {
                    'status': 'running' if info['State']['Running'] else 'stopped',
                    'container_id': deployment_id,
                    'started_at': info['State']['StartedAt'],
                    'health': info.get('State', {}).get('Health', {}).get('Status', 'unknown')
                }
            else:
                return {'status': 'not_found', 'error': '部署不存在'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# 全局部署执行器实例
deploy_executor = DeployExecutor()
