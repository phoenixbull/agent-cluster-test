#!/usr/bin/env python3
"""
项目路由器 - 根据需求识别项目
支持多项目隔离，每个项目有独立的工作区和 GitHub 仓库
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional


class ProjectRouter:
    """
    项目路由器
    
    功能:
    - 根据需求识别项目
    - 支持项目前缀标记 [项目名]
    - 支持关键词自动匹配
    - 提供项目配置
    """
    
    def __init__(self, config_path: str = "projects.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载项目配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # 返回默认配置
        return {
            "projects": {
                "default": {
                    "name": "默认项目",
                    "keywords": [],
                    "github": {
                        "user": "phoenixbull",
                        "repo": "agent-cluster-test",
                        "branch_prefix": "agent/"
                    },
                    "workspace": "~/.openclaw/workspace/agent-cluster-test"
                }
            }
        }
    
    def identify_project(self, requirement: str) -> str:
        """
        识别项目
        
        Args:
            requirement: 产品需求描述
        
        Returns:
            project_id: 项目 ID
        """
        print(f"\n🔍 识别项目...")
        
        # 1. 检查是否有项目前缀标记
        # 例如：[电商] 添加购物车功能
        prefix_match = re.match(r'\[([^\]]+)\]\s*(.+)', requirement)
        if prefix_match:
            prefix = prefix_match.group(1).lower()
            # 查找匹配的项目
            for project_id, config in self.config["projects"].items():
                if project_id.lower() == prefix or config["name"].lower() == prefix.lower():
                    project_name = config['name']
                    print(f"   📁 识别项目 (前缀): {project_name}")
                    return project_id
        
        # 2. 关键词匹配
        best_match = "default"
        best_score = 0
        
        for project_id, config in self.config["projects"].items():
            if project_id == "default":
                continue
            
            keywords = config.get("keywords", [])
            score = sum(1 for kw in keywords if kw in requirement)
            
            if score > best_score:
                best_score = score
                best_match = project_id
        
        if best_score > 0:
            project_name = self.config["projects"][best_match]["name"]
            print(f"   📁 识别项目 (关键词): {project_name} (匹配 {best_score} 个关键词)")
            return best_match
        
        # 3. 默认项目
        print(f"   📁 识别项目：默认项目 (无匹配)")
        return "default"
    
    def get_project_config(self, project_id: str) -> Dict:
        """获取项目配置"""
        return self.config["projects"].get(project_id, self.config["projects"]["default"])
    
    def get_github_config(self, project_id: str) -> Dict:
        """获取 GitHub 配置"""
        project = self.get_project_config(project_id)
        return project.get("github", self.config["projects"]["default"]["github"])
    
    def get_workspace(self, project_id: str) -> Path:
        """获取项目工作区"""
        project = self.get_project_config(project_id)
        workspace = project.get("workspace", "~/.openclaw/workspace/agent-cluster-test")
        return Path(workspace).expanduser()
    
    def get_repo_dir(self, project_id: str) -> Path:
        """获取 Git 仓库目录"""
        github_config = self.get_github_config(project_id)
        repo_name = github_config.get("repo", "agent-cluster-test")
        workspace = self.get_workspace(project_id)
        return workspace / repo_name
    
    def get_branch_prefix(self, project_id: str) -> str:
        """获取分支前缀"""
        github_config = self.get_github_config(project_id)
        return github_config.get("branch_prefix", "agent/")
    
    def list_projects(self) -> list:
        """列出所有项目"""
        return [
            {
                "id": project_id,
                "name": config["name"],
                "keywords": config.get("keywords", []),
                "repo": config.get("github", {}).get("repo", "unknown"),
                "workspace": config.get("workspace", "unknown")
            }
            for project_id, config in self.config["projects"].items()
        ]


# ========== 测试入口 ==========

def main():
    """测试函数"""
    router = ProjectRouter()
    
    print("📊 项目路由器测试")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        "[电商] 添加购物车功能",
        "[博客] 实现文章评论功能",
        "创建一个 CRM 客户管理功能",
        "实现购物车和订单管理",
        "添加文章发布和分类功能",
        "创建一个待办事项功能"
    ]
    
    for requirement in test_cases:
        print(f"\n需求：{requirement}")
        project_id = router.identify_project(requirement)
        config = router.get_project_config(project_id)
        github = router.get_github_config(project_id)
        
        print(f"  项目：{config['name']}")
        print(f"  仓库：{github['user']}/{github['repo']}")
        print(f"  分支前缀：{github['branch_prefix']}")
        print(f"  工作区：{router.get_workspace(project_id)}")
    
    # 列出所有项目
    print("\n" + "=" * 60)
    print("📋 所有项目配置:")
    for project in router.list_projects():
        print(f"\n  {project['id']}:")
        print(f"    名称：{project['name']}")
        print(f"    仓库：{project['repo']}")
        print(f"    关键词：{', '.join(project['keywords']) if project['keywords'] else '无'}")


if __name__ == "__main__":
    main()
