# 🗂️ Agent 集群 V2.0 - 多项目隔离方案

**问题**: 当前所有任务都使用同一个 GitHub 仓库，无法区分不同项目

---

## 📊 当前架构的问题

### 现状
```
所有需求 → 同一个 orchestrator → 同一个 GitHub 仓库 (agent-cluster-test)
```

### 问题
1. ❌ **代码混在一起** - 不同项目的代码在同一个仓库
2. ❌ **工作区冲突** - 不同项目的文件在同一目录
3. ❌ **无法独立管理** - 不能单独配置每个项目的 CI/CD
4. ❌ **PR 混乱** - 所有 PR 都在一个仓库

---

## ✅ 解决方案：项目隔离架构

### 方案 1: 多仓库模式 (推荐)

```
需求 → 识别项目 → 选择对应配置 → 独立仓库
```

#### 架构图
```
┌─────────────────────────────────────────────────────────┐
│                   用户输入需求                            │
│  "为电商项目添加购物车功能"                               │
│  "为博客系统添加评论功能"                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              项目识别器 (Project Router)                  │
│  - 关键词匹配：电商/博客/CRM/...                         │
│  - 项目前缀识别：[电商]/[博客]/...                        │
│  - 默认项目：unknown                                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              项目配置选择                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  电商项目配置 │  │  博客项目配置 │  │  CRM 项目配置  │  │
│  │  repo: ecommerce│ │  repo: blog  │ │  repo: crm   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              独立工作流执行                               │
│  - 独立的工作区目录                                       │
│  - 独立的 Git 仓库                                         │
│  - 独立的 PR                                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 实现方案

### 1. 项目配置文件

创建 `projects.json` 配置多个项目：

```json
{
  "projects": {
    "ecommerce": {
      "name": "电商项目",
      "keywords": ["电商", "购物车", "商品", "订单", "支付"],
      "github": {
        "user": "phoenixbull",
        "repo": "ecommerce-platform",
        "branch_prefix": "feature/"
      },
      "workspace": "~/.openclaw/workspace/ecommerce",
      "agents": {
        "backend": "codex",
        "frontend": "claude-code",
        "design": "designer"
      }
    },
    "blog": {
      "name": "博客系统",
      "keywords": ["博客", "文章", "评论", "分类", "标签"],
      "github": {
        "user": "phoenixbull",
        "repo": "blog-system",
        "branch_prefix": "feature/"
      },
      "workspace": "~/.openclaw/workspace/blog",
      "agents": {
        "backend": "codex",
        "frontend": "claude-code"
      }
    },
    "default": {
      "name": "默认项目",
      "keywords": [],
      "github": {
        "user": "phoenixbull",
        "repo": "agent-cluster-test",
        "branch_prefix": "agent/"
      },
      "workspace": "~/.openclaw/workspace/agent-cluster-test",
      "agents": {
        "backend": "codex",
        "frontend": "claude-code"
      }
    }
  }
}
```

---

### 2. 项目识别器 (Project Router)

```python
# utils/project_router.py

import json
import re
from pathlib import Path
from typing import Dict, Optional

class ProjectRouter:
    """项目路由器 - 根据需求识别项目"""
    
    def __init__(self, config_path: str = "projects.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载项目配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"projects": {"default": self._default_project()}}
    
    def _default_project(self) -> Dict:
        """默认项目配置"""
        return {
            "name": "默认项目",
            "keywords": [],
            "github": {
                "user": "phoenixbull",
                "repo": "agent-cluster-test",
                "branch_prefix": "agent/"
            },
            "workspace": "~/.openclaw/workspace/agent-cluster-test"
        }
    
    def identify_project(self, requirement: str) -> str:
        """
        识别项目
        
        Args:
            requirement: 产品需求描述
        
        Returns:
            project_id: 项目 ID
        """
        # 1. 检查是否有项目前缀标记
        # 例如：[电商] 添加购物车功能
        prefix_match = re.match(r'\[([^\]]+)\]\s*(.+)', requirement)
        if prefix_match:
            prefix = prefix_match.group(1).lower()
            # 查找匹配的项目
            for project_id, config in self.config["projects"].items():
                if project_id.lower() == prefix or config["name"].lower() == prefix.lower():
                    print(f"   📁 识别项目 (前缀): {config['name']}")
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
        return self.config["projects"].get(project_id, self._default_project())
    
    def get_github_config(self, project_id: str) -> Dict:
        """获取 GitHub 配置"""
        project = self.get_project_config(project_id)
        return project.get("github", self._default_project()["github"])
    
    def get_workspace(self, project_id: str) -> Path:
        """获取项目工作区"""
        project = self.get_project_config(project_id)
        workspace = project.get("workspace", "~/.openclaw/workspace/agent-cluster-test")
        return Path(workspace).expanduser()
```

---

### 3. 更新 Orchestrator 支持多项目

```python
# orchestrator.py (修改部分)

from utils.project_router import ProjectRouter

class Orchestrator:
    def __init__(self, config_path: str = "cluster_config.json"):
        # ... 现有代码 ...
        
        # 添加项目路由器
        self.project_router = ProjectRouter()
        self.current_project = "default"
    
    def receive_requirement(self, requirement: str, source: str = "manual") -> str:
        """接收产品需求"""
        print(f"\n📥 接收到产品需求 (来源：{source})")
        print(f"   需求：{requirement[:100]}...")
        
        # 🆕 识别项目
        self.current_project = self.project_router.identify_project(requirement)
        project_config = self.project_router.get_project_config(self.current_project)
        print(f"   📁 项目：{project_config['name']}")
        
        # 🆕 初始化项目特定的 GitHub 客户端
        github_config = self.project_router.get_github_config(self.current_project)
        self.github = GitHubAPI(
            token=github_config.get("token", self.config.get("github", {}).get("token")),
            user=github_config.get("user"),
            repo=github_config.get("repo")
        )
        
        # 创建工作流
        workflow_id = self.state.create_workflow(requirement)
        
        # 🆕 在工作流中记录项目信息
        self.state.update_workflow_project(workflow_id, self.current_project)
        
        # ... 继续执行工作流 ...
```

---

### 4. 工作区隔离

```python
# utils/agent_executor.py (修改部分)

class AgentTaskExecutor:
    def __init__(self, workspace: str = "~/.openclaw/workspace"):
        self.workspace = Path(workspace).expanduser()
        # 🆕 支持项目子目录
        self.current_project = "default"
    
    def set_project(self, project_id: str, project_config: Dict):
        """设置当前项目"""
        self.current_project = project_id
        # 项目特定的工作区
        self.workspace = Path(project_config.get("workspace")).expanduser()
        self.agents_dir = self.workspace / "agents"
        
        # 确保目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
```

---

### 5. 分支命名隔离

```python
# orchestrator.py (修改部分)

def _create_pr(self, workflow_id: str, requirement: str, review_result: Dict) -> Dict:
    # 🆕 使用项目特定的分支前缀
    github_config = self.project_router.get_github_config(self.current_project)
    branch_prefix = github_config.get("branch_prefix", "agent/")
    
    # 分支名：项目前缀 + 工作流 ID
    branch_name = f"{branch_prefix}{workflow_id}"
    
    # 例如:
    # - feature/wf-20260305-150000-xxx (电商项目)
    # - feature/wf-20260305-150001-xxx (博客项目)
    # - agent/wf-20260305-150002-xxx (默认项目)
```

---

## 📋 使用方式

### 方式 1: 项目前缀标记

```bash
# 电商项目
python3 orchestrator.py "[电商] 添加购物车功能"

# 博客系统
python3 orchestrator.py "[博客] 添加文章评论功能"

# CRM 系统
python3 orchestrator.py "[CRM] 添加客户管理功能"

# 默认项目 (无前缀)
python3 orchestrator.py "创建一个待办事项功能"
```

### 方式 2: 关键词自动识别

```bash
# 自动识别为电商项目 (包含"购物车"关键词)
python3 orchestrator.py "实现购物车功能，支持添加商品和结算"

# 自动识别为博客项目 (包含"文章"关键词)
python3 orchestrator.py "实现文章发布和分类功能"
```

---

## 📊 项目隔离效果

### 目录结构
```
~/.openclaw/workspace/
├── ecommerce/              # 电商项目工作区
│   ├── agents/
│   │   ├── codex/sessions/
│   │   └── claude-code/sessions/
│   └── ecommerce-platform/ # Git 仓库
│       ├── backend/
│       ├── frontend/
│       └── .git
│
├── blog/                   # 博客项目工作区
│   ├── agents/
│   └── blog-system/        # Git 仓库
│       ├── backend/
│       └── frontend/
│
└── agent-cluster-test/     # 默认项目工作区
    └── ...
```

### GitHub 仓库
```
https://github.com/phoenixbull/ecommerce-platform
  ├── feature/wf-20260305-150000-xxx (电商 PR)
  └── feature/wf-20260305-150001-xxx

https://github.com/phoenixbull/blog-system
  ├── feature/wf-20260305-150002-xxx (博客 PR)
  └── feature/wf-20260305-150003-xxx

https://github.com/phoenixbull/agent-cluster-test
  └── agent/wf-20260305-150004-xxx (默认 PR)
```

---

## 🎯 实现步骤

### Phase 1: 基础支持 (本周)
- [ ] 创建 `projects.json` 配置文件
- [ ] 实现 `ProjectRouter` 项目识别器
- [ ] 更新 `Orchestrator` 支持多项目
- [ ] 测试项目识别功能

### Phase 2: 工作区隔离 (下周)
- [ ] 实现项目特定工作区
- [ ] 实现项目特定 GitHub 客户端
- [ ] 实现分支命名隔离
- [ ] 测试完整流程

### Phase 3: 高级功能 (后续)
- [ ] 项目间代码复用
- [ ] 跨项目依赖管理
- [ ] 项目模板系统
- [ ] 项目权限管理

---

## 🔗 相关文件

- `utils/project_router.py` - 项目识别器 (待创建)
- `projects.json` - 项目配置 (待创建)
- `orchestrator.py` - 编排器 (需更新)
- `utils/agent_executor.py` - Agent 执行器 (需更新)

---

**设计完成时间**: 2026-03-05  
**版本**: v2.0  
**状态**: 设计完成，待实现
