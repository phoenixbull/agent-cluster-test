#!/usr/bin/env python3
"""
GitHub API 集成模块
用于创建分支、提交代码、创建 PR、检查 CI 状态
"""

import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import base64


class GitHubAPI:
    """
    GitHub API 客户端
    
    功能:
    - Git 操作 (clone, branch, commit, push)
    - PR 创建和管理
    - CI 状态检查
    - Review 管理
    """
    
    def __init__(self, token: str, user: str, repo: str):
        """
        初始化 GitHub API
        
        Args:
            token: GitHub Personal Access Token
            user: GitHub 用户名
            repo: 仓库名
        """
        self.token = token
        self.user = user
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.repo_url = f"{user}/{repo}"
        self.clone_url = f"https://{token}@github.com/{user}/{repo}.git"
        
        # 本地仓库路径
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.repo_dir = self.workspace / repo
    
    def git_command(self, *args, cwd: Path = None) -> subprocess.CompletedProcess:
        """执行 Git 命令"""
        cmd = ["git"] + list(args)
        cwd = cwd or self.repo_dir
        
        # 设置认证信息
        env = {
            "GIT_ASKPASS": "echo",
            "GIT_USERNAME": self.user,
            "GIT_PASSWORD": self.token
        }
        
        # Python 3.6 兼容：使用 stdout/stderr 替代 capture_output
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env={**subprocess.os.environ, **env}
        )
        
        return result
    
    def ensure_repo_cloned(self) -> Path:
        """确保仓库已克隆"""
        if not self.repo_dir.exists():
            print(f"📦 克隆仓库：{self.repo_url}")
            self.repo_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Python 3.6 兼容
            result = subprocess.run(
                ["git", "clone", self.clone_url, str(self.repo_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            if result.returncode != 0:
                raise Exception(f"克隆仓库失败：{result.stderr}")
            
            print(f"   ✅ 仓库已克隆到：{self.repo_dir}")
        else:
            print(f"   ✅ 仓库已存在：{self.repo_dir}")
        
        return self.repo_dir
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> Dict:
        """
        创建新分支
        
        Args:
            branch_name: 新分支名
            base_branch: 基础分支
        
        Returns:
            分支信息
        """
        print(f"\n🌿 创建分支：{branch_name} (基于 {base_branch})")
        
        self.ensure_repo_cloned()
        
        # 切换到主分支并更新
        self.git_command("checkout", base_branch)
        self.git_command("pull", "origin", base_branch)
        
        # 创建新分支
        result = self.git_command("checkout", "-b", branch_name)
        
        if result.returncode != 0:
            raise Exception(f"创建分支失败：{result.stderr}")
        
        print(f"   ✅ 分支已创建：{branch_name}")
        
        return {
            "branch_name": branch_name,
            "base_branch": base_branch,
            "status": "created"
        }
    
    def commit_changes(self, message: str, files: List[str] = None) -> Dict:
        """
        提交更改
        
        Args:
            message: 提交信息
            files: 要提交的文件列表 (None 表示所有更改)
        
        Returns:
            提交信息
        """
        print(f"\n💾 提交更改：{message[:50]}...")
        
        if files:
            for file in files:
                self.git_command("add", file)
        else:
            self.git_command("add", "-A")
        
        # 检查是否有更改
        status_result = self.git_command("status", "--porcelain")
        if not status_result.stdout.strip():
            print("   ⚠️ 没有更改需要提交")
            return {"status": "no_changes"}
        
        result = self.git_command("commit", "-m", message)
        
        if result.returncode != 0:
            if "nothing to commit" in result.stderr:
                print("   ⚠️ 没有更改需要提交")
                return {"status": "no_changes"}
            raise Exception(f"提交失败：{result.stderr}")
        
        # 获取提交 hash
        hash_result = self.git_command("rev-parse", "HEAD")
        commit_hash = hash_result.stdout.strip()
        
        print(f"   ✅ 已提交：{commit_hash[:8]}")
        
        return {
            "status": "committed",
            "commit_hash": commit_hash,
            "message": message
        }
    
    def cleanup_merged_branch(self, branch_name: str) -> Dict:
        """清理已合并的分支"""
        try:
            print(f"\n🧹 清理已合并分支：{branch_name}")
            # 切换回 main
            self.git_command("checkout", "main")
            # 拉取最新
            self.git_command("pull", "origin", "main")
            # 删除本地分支
            self.git_command("branch", "-d", branch_name)
            # 删除远程分支
            self.git_command("push", "origin", "--delete", branch_name)
            print(f"   ✅ 分支已清理：{branch_name}")
            return {"success": True, "message": f"分支已清理：{branch_name}"}
        except Exception as e:
            print(f"   ⚠️ 清理失败：{e}")
            return {"success": False, "error": str(e)}
    
    def push_branch(self, branch_name: str) -> Dict:
        """
        推送分支到远程
        
        Args:
            branch_name: 分支名
        
        Returns:
            推送结果
        """
        print(f"\n📤 推送分支：{branch_name}")
        
        result = self.git_command(
            "push", "-u", "origin", branch_name,
            "--force-with-lease"
        )
        
        if result.returncode != 0:
            raise Exception(f"推送失败：{result.stderr}")
        
        print(f"   ✅ 分支已推送")
        
        return {
            "status": "pushed",
            "branch_name": branch_name
        }
    
    def create_pr(self, title: str, body: str, head: str, base: str = "main") -> Dict:
        """
        创建 Pull Request
        
        Args:
            title: PR 标题
            body: PR 描述
            head: 源分支
            base: 目标分支
        
        Returns:
            PR 信息
        """
        print(f"\n🔀 创建 Pull Request: {title[:50]}...")
        
        url = f"{self.api_base}/repos/{self.repo_url}/pulls"
        
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        result = self._api_request("POST", url, data)
        
        if result:
            print(f"   ✅ PR 已创建：#{result.get('number')}")
            print(f"   🔗 {result.get('html_url')}")
            
            return {
                "pr_number": result.get("number"),
                "pr_url": result.get("html_url"),
                "status": "created",
                "head": head,
                "base": base
            }
        else:
            raise Exception("创建 PR 失败")
    
    def get_pr_status(self, pr_number: int) -> Dict:
        """
        获取 PR 状态
        
        Args:
            pr_number: PR 编号
        
        Returns:
            PR 状态信息
        """
        url = f"{self.api_base}/repos/{self.repo_url}/pulls/{pr_number}"
        result = self._api_request("GET", url)
        
        if result:
            return {
                "pr_number": pr_number,
                "state": result.get("state"),
                "merged": result.get("merged"),
                "mergeable": result.get("mergeable"),
                "commits": result.get("commits"),
                "additions": result.get("additions"),
                "deletions": result.get("deletions")
            }
        return {}
    
    def check_ci_status(self, pr_number: int) -> Dict:
        """
        检查 CI 状态
        
        Args:
            pr_number: PR 编号
        
        Returns:
            CI 状态
        """
        print(f"\n🔍 检查 CI 状态 (PR #{pr_number})...")
        
        # 获取 PR 的 head sha
        pr_info = self.get_pr_status(pr_number)
        if not pr_info:
            return {"status": "unknown"}
        
        # 获取提交状态
        url = f"{self.api_base}/repos/{self.repo_url}/commits/{pr_info.get('head_sha')}/status"
        result = self._api_request("GET", url)
        
        if result:
            status = result.get("state", "unknown")
            print(f"   CI 状态：{status}")
            
            return {
                "status": status,
                "total_count": result.get("total_count"),
                "statuses": result.get("statuses", [])
            }
        
        return {"status": "unknown"}
    
    def get_pr_reviews(self, pr_number: int) -> Dict:
        """
        获取 PR 审查状态
        
        Args:
            pr_number: PR 编号
        
        Returns:
            审查结果
        """
        url = f"{self.api_base}/repos/{self.repo_url}/pulls/{pr_number}/reviews"
        result = self._api_request("GET", url)
        
        if result:
            approved = sum(1 for r in result if r.get("state") == "APPROVED")
            changes_requested = sum(1 for r in result if r.get("state") == "CHANGES_REQUESTED")
            
            return {
                "approved": approved,
                "changes_requested": changes_requested,
                "reviews": result
            }
        
        return {"approved": 0, "changes_requested": 0, "reviews": []}
    
    def _api_request(self, method: str, url: str, data: Dict = None) -> Optional[Dict]:
        """发送 GitHub API 请求"""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Agent-Cluster/2.0"
        }
        
        if data:
            data = json.dumps(data).encode('utf-8')
            headers["Content-Type"] = "application/json"
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"   ❌ API 请求失败：{e.code} {e.reason}")
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                print(f"      错误：{error_body.get('message', '')}")
            except:
                pass
            return None
        except Exception as e:
            print(f"   ❌ 请求异常：{e}")
            return None
    
    def generate_pr_body(self, requirement: str, tasks: List[Dict], results: Dict) -> str:
        """
        生成 PR 描述
        
        Args:
            requirement: 产品需求
            tasks: 任务列表
            results: 执行结果
        
        Returns:
            PR 描述 (Markdown)
        """
        return f"""## 🤖 自动生成

本 PR 由 Agent 集群 V2.0 自动生成。

### 📋 产品需求

{requirement}

### ✅ 完成的任务

""" + "\n".join([f"- [x] {task.get('description', '未知任务')}" for task in tasks]) + f"""

### 🧪 测试结果

- 单元测试：{results.get('tests_passed', 0)}/{results.get('tests_run', 0)} 通过
- 集成测试：{results.get('integration_tests', 'N/A')}
- AI Review: {results.get('review_status', 'pending')}

### 📝 审查清单

- [ ] 代码审查通过
- [ ] 测试全部通过
- [ ] 文档已更新
- [ ] 无破坏性变更

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent 集群**: V2.0
"""


# ========== 便捷函数 ==========

def create_github_client(config_path: str = "cluster_config.json") -> GitHubAPI:
    """从配置文件创建 GitHub 客户端"""
    config_file = Path(config_path).expanduser()
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    github_config = config.get("github", {})
    
    return GitHubAPI(
        token=github_config.get("token", ""),
        user=github_config.get("user", ""),
        repo=github_config.get("repo", "")
    )


# ========== 测试入口 ==========

def main():
    """测试函数"""
    import sys
    
    github = create_github_client()
    
    print("📊 GitHub API 测试")
    print("=" * 60)
    
    # 测试仓库克隆
    repo_dir = github.ensure_repo_cloned()
    
    # 测试创建分支
    branch_name = f"test/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    branch_info = github.create_branch(branch_name)
    print(f"分支信息：{json.dumps(branch_info, indent=2)}")
    
    # 测试获取 PR 列表
    print("\n📋 最近 PR:")
    url = f"{github.api_base}/repos/{github.repo_url}/pulls?state=all&per_page=5"
    result = github._api_request("GET", url)
    if result:
        for pr in result:
            print(f"  #{pr.get('number')}: {pr.get('title')} ({pr.get('state')})")


if __name__ == "__main__":
    main()
