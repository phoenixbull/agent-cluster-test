"""
Kubernetes 部署执行器
支持 K8s Deployment、Service、Ingress 配置
"""

import os
import json
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class K8sDeployExecutor:
    """Kubernetes 部署执行器"""
    
    def __init__(self):
        self.k8s_namespace = os.getenv('K8S_NAMESPACE', 'agent-cluster')
        self.k8s_context = os.getenv('K8S_CONTEXT', '')
        
        # K8s 配置目录
        self.k8s_dir = Path(__file__).parent.parent / 'k8s'
        self.k8s_dir.mkdir(exist_ok=True)
    
    def _check_kubectl(self) -> tuple[bool, str]:
        """检查 kubectl 是否可用"""
        try:
            result = subprocess.run(
                ['kubectl', 'version', '--client'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 检查集群连接
                result = subprocess.run(
                    ['kubectl', 'cluster-info'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    return True, 'Kubernetes 集群可用'
                else:
                    return False, '无法连接 Kubernetes 集群'
            else:
                return False, 'kubectl 未安装'
        
        except FileNotFoundError:
            return False, 'kubectl 未安装'
        except Exception as e:
            return False, f'Kubernetes 检查失败：{str(e)}'
    
    def deploy(self, workflow_id: str, project: str, image: str, 
               replicas: int = 3, port: int = 80) -> Dict[str, Any]:
        """
        部署到 Kubernetes
        
        Args:
            workflow_id: 工作流 ID
            project: 项目名称
            image: Docker 镜像
            replicas: 副本数
            port: 服务端口
        
        Returns:
            部署结果
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        deployment_name = f"{project}-{timestamp}"
        
        try:
            # 检查 kubectl
            available, msg = self._check_kubectl()
            if not available:
                return {'success': False, 'error': msg}
            
            # 生成 K8s 配置
            config = self._generate_k8s_config(deployment_name, project, image, replicas, port)
            
            # 保存配置文件
            config_file = self.k8s_dir / f'{deployment_name}.yaml'
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump_all(config, f, default_flow_style=False)
            
            # 应用配置
            result = subprocess.run(
                ['kubectl', 'apply', '-f', str(config_file), '-n', self.k8s_namespace],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # 等待部署完成
                wait_result = subprocess.run(
                    ['kubectl', 'rollout', 'status', f'deployment/{deployment_name}', 
                     '-n', self.k8s_namespace, '--timeout=300s'],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if wait_result.returncode == 0:
                    return {
                        'success': True,
                        'deployment_name': deployment_name,
                        'message': 'Kubernetes 部署成功',
                        'config_file': str(config_file)
                    }
                else:
                    return {'success': False, 'error': f'部署等待超时：{wait_result.stderr}'}
            else:
                return {'success': False, 'error': f'应用配置失败：{result.stderr}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_k8s_config(self, deployment_name: str, project: str, 
                            image: str, replicas: int, port: int) -> List[Dict]:
        """生成 Kubernetes 配置"""
        
        # Deployment
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': deployment_name,
                'namespace': self.k8s_namespace,
                'labels': {
                    'app': project,
                    'version': deployment_name.split('-')[-1]
                }
            },
            'spec': {
                'replicas': replicas,
                'selector': {
                    'matchLabels': {
                        'app': project,
                        'version': deployment_name.split('-')[-1]
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': project,
                            'version': deployment_name.split('-')[-1]
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': project,
                            'image': image,
                            'ports': [{
                                'containerPort': port,
                                'protocol': 'TCP'
                            }],
                            'resources': {
                                'requests': {
                                    'memory': '128Mi',
                                    'cpu': '100m'
                                },
                                'limits': {
                                    'memory': '256Mi',
                                    'cpu': '500m'
                                }
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': port
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
        
        # Service
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f'{deployment_name}-svc',
                'namespace': self.k8s_namespace,
                'labels': {
                    'app': project
                }
            },
            'spec': {
                'selector': {
                    'app': project,
                    'version': deployment_name.split('-')[-1]
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': 80,
                    'targetPort': port
                }],
                'type': 'ClusterIP'
            }
        }
        
        # Ingress (可选)
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f'{deployment_name}-ingress',
                'namespace': self.k8s_namespace,
                'annotations': {
                    'kubernetes.io/ingress.class': 'nginx',
                    'nginx.ingress.kubernetes.io/rewrite-target': '/'
                }
            },
            'spec': {
                'rules': [{
                    'host': f'{project}.example.com',
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': f'{deployment_name}-svc',
                                    'port': {
                                        'number': 80
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        return [deployment, service, ingress]
    
    def rollback(self, deployment_name: str) -> Dict[str, Any]:
        """回滚 Kubernetes 部署"""
        try:
            result = subprocess.run(
                ['kubectl', 'rollout', 'undo', f'deployment/{deployment_name}', 
                 '-n', self.k8s_namespace],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'已回滚到 {deployment_name}',
                    'output': result.stdout
                }
            else:
                return {'success': False, 'error': result.stderr}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self, deployment_name: str) -> Dict[str, Any]:
        """获取部署状态"""
        try:
            # 获取 Deployment 状态
            result = subprocess.run(
                ['kubectl', 'get', 'deployment', deployment_name, 
                 '-n', self.k8s_namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {'success': False, 'error': '部署不存在'}
            
            deployment = json.loads(result.stdout)
            
            # 获取 Pods 状态
            pods_result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', self.k8s_namespace,
                 '-l', f'app={deployment_name.split("-")[0]}', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            pods = json.loads(pods_result.stdout) if pods_result.returncode == 0 else {'items': []}
            
            return {
                'success': True,
                'deployment': {
                    'name': deployment_name,
                    'replicas': deployment['spec']['replicas'],
                    'ready_replicas': deployment['status'].get('readyReplicas', 0),
                    'available_replicas': deployment['status'].get('availableReplicas', 0),
                    'updated_replicas': deployment['status'].get('updatedReplicas', 0)
                },
                'pods': [
                    {
                        'name': pod['metadata']['name'],
                        'status': pod['status']['phase'],
                        'ready': any(c['ready'] for c in pod['status'].get('containerStatuses', []))
                    }
                    for pod in pods['items']
                ]
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


# 全局 K8s 部署执行器实例
k8s_deploy_executor = K8sDeployExecutor()


def get_k8s_deploy_executor() -> K8sDeployExecutor:
    """获取 K8s 部署执行器实例"""
    return k8s_deploy_executor
