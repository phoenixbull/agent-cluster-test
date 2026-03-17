#!/usr/bin/env python3
"""
DevOps Agent - 部署自动化工具
"""

import os
import yaml
from typing import Dict, List


class DeploymentGenerator:
    """部署配置生成器"""
    
    def generate_dockerfile(self, app_type: str = "python") -> str:
        """
        生成 Dockerfile
        
        Args:
            app_type: 应用类型 (python/node)
        
        Returns:
            Dockerfile 内容
        """
        if app_type == "python":
            return '''# Python FastAPI 应用 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        elif app_type == "node":
            return '''# Node.js React 应用 Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 生产镜像
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
'''
        return ""
    
    def generate_docker_compose(self, services: List[str]) -> str:
        """
        生成 docker-compose.yml
        
        Args:
            services: 服务列表
        
        Returns:
            docker-compose 配置
        """
        compose = {
            "version": "3.8",
            "services": {}
        }
        
        # 后端服务
        if "backend" in services:
            compose["services"]["backend"] = {
                "build": "./backend",
                "ports": ["8000:8000"],
                "environment": [
                    "DATABASE_URL=postgresql://user:pass@db:5432/blog",
                    "REDIS_URL=redis://redis:6379"
                ],
                "depends_on": ["db", "redis"],
                "volumes": ["./backend:/app"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                    "interval": "30s",
                    "timeout": "3s",
                    "retries": 3
                }
            }
        
        # 前端服务
        if "frontend" in services:
            compose["services"]["frontend"] = {
                "build": "./frontend",
                "ports": ["80:80"],
                "depends_on": ["backend"]
            }
        
        # 数据库
        if "db" in services:
            compose["services"]["db"] = {
                "image": "postgres:15",
                "environment": [
                    "POSTGRES_USER=user",
                    "POSTGRES_PASSWORD=pass",
                    "POSTGRES_DB=blog"
                ],
                "volumes": ["pgdata:/var/lib/postgresql/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U user"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5
                }
            }
        
        # Redis
        if "redis" in services:
            compose["services"]["redis"] = {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "volumes": ["redisdata:/data"]
            }
        
        # 监控
        if "monitoring" in services:
            compose["services"]["prometheus"] = {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"]
            }
            
            compose["services"]["grafana"] = {
                "image": "grafana/grafana:latest",
                "ports": ["3000:3000"],
                "environment": ["GF_SECURITY_ADMIN_PASSWORD=admin"],
                "volumes": ["grafanadata:/var/lib/grafana"]
            }
        
        # 卷
        compose["volumes"] = {
            "pgdata": None,
            "redisdata": None,
            "grafanadata": None
        }
        
        return yaml.dump(compose, default_flow_style=False, allow_unicode=True)
    
    def generate_github_actions(self, workflow_type: str = "ci_cd") -> str:
        """
        生成 GitHub Actions 工作流
        
        Args:
            workflow_type: 工作流类型 (ci_cd/deploy)
        
        Returns:
            GitHub Actions 配置
        """
        if workflow_type == "ci_cd":
            workflow = {
                "name": "CI/CD Pipeline",
                "on": {
                    "push": {
                        "branches": ["main", "develop"]
                    },
                    "pull_request": {
                        "branches": ["main"]
                    }
                },
                "jobs": {
                    "test": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {"uses": "actions/checkout@v3"},
                            {
                                "name": "Set up Python",
                                "uses": "actions/setup-python@v4",
                                "with": {"python-version": "3.11"}
                            },
                            {
                                "name": "Install dependencies",
                                "run": "pip install -r requirements.txt"
                            },
                            {
                                "name": "Run tests",
                                "run": "pytest --cov=app --cov-report=xml"
                            },
                            {
                                "name": "Upload coverage",
                                "uses": "codecov/codecov-action@v3"
                            }
                        ]
                    },
                    "build": {
                        "needs": "test",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {"uses": "actions/checkout@v3"},
                            {
                                "name": "Build Docker image",
                                "run": "docker build -t blog-backend:${{ github.sha }} ./backend"
                            },
                            {
                                "name": "Push to registry",
                                "run": "echo 'Push to your registry'"
                            }
                        ]
                    },
                    "deploy": {
                        "needs": "build",
                        "runs-on": "ubuntu-latest",
                        "if": "github.ref == 'refs/heads/main'",
                        "steps": [
                            {"uses": "actions/checkout@v3"},
                            {
                                "name": "Deploy to production",
                                "run": "echo 'Deploy to production'"
                            }
                        ]
                    }
                }
            }
            
            return yaml.dump(workflow, default_flow_style=False, allow_unicode=True)
        
        return ""
    
    def generate_prometheus_config(self) -> str:
        """
        生成 Prometheus 监控配置
        
        Returns:
            Prometheus 配置
        """
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "alerting": {
                "alertmanagers": [{
                    "static_configs": [{"targets": ["alertmanager:9093"]}]
                }]
            },
            "rule_files": ["/etc/prometheus/rules/*.yml"],
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [{"targets": ["localhost:9090"]}]
                },
                {
                    "job_name": "backend",
                    "static_configs": [{"targets": ["backend:8000"]}],
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "node",
                    "static_configs": [{"targets": ["node-exporter:9100"]}]
                }
            ]
        }
        
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)
    
    def generate_grafana_dashboard(self) -> Dict:
        """
        生成 Grafana 仪表板配置
        
        Returns:
            Grafana 仪表板 JSON
        """
        dashboard = {
            "dashboard": {
                "title": "博客系统监控",
                "panels": [
                    {
                        "id": 1,
                        "title": "QPS",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(http_requests_total[5m])"
                        }]
                    },
                    {
                        "id": 2,
                        "title": "响应时间",
                        "type": "graph",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
                        }]
                    },
                    {
                        "id": 3,
                        "title": "错误率",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(http_requests_total{status=~'5..'}[5m])"
                        }]
                    },
                    {
                        "id": 4,
                        "title": "CPU 使用率",
                        "type": "gauge",
                        "targets": [{
                            "expr": "node_cpu_seconds_total"
                        }]
                    },
                    {
                        "id": 5,
                        "title": "内存使用率",
                        "type": "gauge",
                        "targets": [{
                            "expr": "node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes"
                        }]
                    }
                ]
            }
        }
        
        return dashboard


# 主函数
def generate_deployment_config(app_type: str = "python") -> Dict:
    """生成部署配置"""
    generator = DeploymentGenerator()
    
    return {
        "dockerfile": generator.generate_dockerfile(app_type),
        "docker_compose": generator.generate_docker_compose([
            "backend", "frontend", "db", "redis", "monitoring"
        ]),
        "github_actions": generator.generate_github_actions("ci_cd"),
        "prometheus": generator.generate_prometheus_config(),
        "grafana_dashboard": generator.generate_grafana_dashboard()
    }


if __name__ == "__main__":
    import json
    config = generate_deployment_config()
    print(json.dumps({k: v[:100] + "..." for k, v in config.items()}, indent=2))
