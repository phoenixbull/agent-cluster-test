# 🚀 Agent 集群自动化流水线设计

## 📋 理想工作流程

```
用户输入产品需求
       ↓
┌─────────────────────────────────────────────────────────────┐
│  1. 需求接收模块 (OpenClaw / 钉钉)                            │
│     - 接收产品需求描述                                        │
│     - 自动唤醒集群                                            │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  2. 需求分析 (Orchestrator - Zoe)                            │
│     - 解析需求，提取功能点                                    │
│     - 生成任务清单 (Task List)                                │
│     - 评估任务依赖关系                                        │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  3. UI/UX 设计 (Designer Agent - Gemini)                     │
│     - 生成线框图/原型                                         │
│     - 输出设计规范和 HTML/CSS 原型                              │
│     - 保存到 Git 分支                                          │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 编码实现 (并行)                                          │
│     ┌─────────────────┐    ┌─────────────────┐              │
│     │ 后端 (Codex)    │    │ 前端 (Claude)   │              │
│     │ - API 设计       │    │ - 组件开发      │              │
│     │ - 数据库         │    │ - 页面集成      │              │
│     │ - 业务逻辑       │    │ - 样式实现      │              │
│     └─────────────────┘    └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  5. 代码测试 (Codex + Claude)                                │
│     - 单元测试                                                │
│     - 集成测试                                                │
│     - 如果有问题 → 自动修复 → 重新测试 (循环)                   │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  6. AI Review (3 个 Reviewer Agent)                           │
│     - Codex Reviewer: 逻辑/边界情况                           │
│     - Gemini Reviewer: 安全/扩展性                            │
│     - Claude Reviewer: 基础检查                               │
│     - 必须全部通过才能继续                                    │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  7. 创建 Pull Request                                        │
│     - 创建功能分支                                            │
│     - 提交代码到 GitHub                                       │
│     - 创建 PR                                                 │
│     - 触发 CI/CD (GitHub Actions)                             │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  8. 钉钉通知 (ClusterNotifier)                               │
│     - 发送 PR 就绪通知                                        │
│     - 附 PR 链接、检查清单、AI Review 意见                        │
│     - @相关人员 Review                                        │
└─────────────────────────────────────────────────────────────┘
       ↓
人工 Review & 合并
```

---

## 🏗️ 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户接口层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  OpenClaw    │  │   钉钉机器人  │  │   Web 界面    │          │
│  │   (Webhook)  │  │   (Webhook)  │  │   (可选)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   编排层 (Orchestrator)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Zoe (主编排者)                                          │   │
│  │  - 需求解析                                              │   │
│  │  - 任务分解                                              │   │
│  │  - Agent 调度                                            │   │
│  │  - 流程控制                                              │   │
│  │  - 异常处理                                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Agent 执行层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Designer │  │  Codex   │  │  Claude  │  │ Research │       │
│  │ (Gemini) │  │ (Backend)│  │ (Frontend)│  │ (可选)   │       │
│  └──────────┘  └──────────┘  └──────────┘  ┌──────────┐       │
│                                              │ Reviewer │       │
│                                              │ (3 个)    │       │
│                                              └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   工具层 (MCP Servers)                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │GitHub  │ │ Git    │ │ 文件   │ │ 数据库  │ │ 钉钉   │       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                  │
│  │ Figma  │ │Excalid │ │ Memory │ │ Obsidian│                 │
│  └────────┘ └────────┘ └────────┘ └────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 文件结构

```
/home/admin/.openclaw/workspace/agent-cluster/
├── cluster_manager.py          # 集群管理器（启动/停止/状态）
├── orchestrator.py             # 🆕 编排器（核心流程控制）
├── workflow/
│   ├── __init__.py
│   ├── requirement_parser.py   # 🆕 需求解析器
│   ├── task_planner.py         # 🆕 任务规划器
│   ├── design_phase.py         # 🆕 设计阶段
│   ├── coding_phase.py         # 🆕 编码阶段
│   ├── testing_phase.py        # 🆕 测试阶段
│   ├── review_phase.py         # 🆕 Review 阶段
│   └── pr_phase.py             # 🆕 PR 创建
├── agents/
│   ├── orchestrator/           # 🆕 Zoe 编排者
│   ├── designer/
│   ├── codex/
│   ├── claude-code/
│   └── reviewers/
│       ├── codex-reviewer/
│       ├── gemini-reviewer/
│       └── claude-reviewer/
├── notifiers/
│   └── dingtalk.py             # 钉钉通知（已完成）
├── webhooks/
│   ├── __init__.py
│   ├── dingtalk_webhook.py     # 🆕 钉钉 webhook 接收
│   └── openclaw_webhook.py     # 🆕 OpenClaw webhook 接收
├── utils/
│   ├── github_helper.py        # 🆕 GitHub 操作辅助
│   ├── git_helper.py           # 🆕 Git 操作辅助
│   └── test_runner.py          # 🆕 测试运行器
├── config/
│   └── cluster_config.json
├── memory/                     # 🆕 流程状态存储
│   └── workflow_state.json
└── logs/                       # 🆕 运行日志
```

---

## 🔧 核心实现

### 1. 需求接收 (Webhook)

#### 钉钉 Webhook
```python
# webhooks/dingtalk_webhook.py
from flask import Flask, request
from orchestrator import Orchestrator

app = Flask(__name__)
orchestrator = Orchestrator()

@app.route('/webhook/dingtalk', methods=['POST'])
def receive_requirement():
    data = request.json
    
    # 解析钉钉消息
    if data.get('msgtype') == 'text':
        requirement = data['text']['content']
    elif data.get('msgtype') == 'markdown':
        requirement = extract_text_from_markdown(data['markdown']['text'])
    
    # 启动工作流
    workflow_id = orchestrator.start_workflow(requirement)
    
    # 回复确认
    return {
        "msgtype": "text",
        "text": {
            "content": f"✅ 需求已接收，工作流已启动\nID: {workflow_id}\n预计完成时间：60-90 分钟"
        }
    }
```

#### OpenClaw 会话触发
```python
# 通过 OpenClaw sessions_spawn 触发
{
  "action": "sessions_spawn",
  "agentId": "orchestrator",
  "task": "新产品需求：创建一个用户管理系统，包含登录、注册、权限管理功能"
}
```

---

### 2. 编排器 (Orchestrator)

```python
# orchestrator.py
class Orchestrator:
    def __init__(self):
        self.config = load_config()
        self.notifier = ClusterNotifier(...)
        self.workflow_state = {}
    
    def start_workflow(self, requirement: str) -> str:
        """启动完整工作流"""
        workflow_id = generate_id()
        
        # 1. 解析需求
        tasks = self.parse_requirement(requirement)
        
        # 2. 执行工作流
        asyncio.run(self.execute_workflow(workflow_id, tasks))
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, tasks: List[Dict]):
        """执行完整工作流"""
        try:
            # 阶段 1: UI 设计
            design_result = await self.design_phase(tasks)
            
            # 阶段 2: 编码实现（并行）
            coding_result = await self.coding_phase(tasks, design_result)
            
            # 阶段 3: 测试（循环直到通过）
            test_result = await self.testing_loop(coding_result)
            
            # 阶段 4: AI Review
            review_result = await self.review_phase(test_result)
            
            # 阶段 5: 创建 PR
            pr_info = await self.create_pr(review_result)
            
            # 阶段 6: 发送通知
            await self.notifier.notify_pr_ready(tasks, pr_info)
            
        except Exception as e:
            await self.notifier.notify_human_intervention(tasks, {'error': str(e)})
```

---

### 3. 测试循环 (自动修复)

```python
# workflow/testing_phase.py
async def testing_loop(code_result: Dict, max_retries: int = 3) -> Dict:
    """测试循环：测试 → 失败则修复 → 重测"""
    retries = 0
    
    while retries < max_retries:
        # 运行测试
        test_result = await run_tests(code_result)
        
        if test_result['passed']:
            print("✅ 测试通过")
            return test_result
        
        # 测试失败，分析错误
        errors = analyze_test_failures(test_result)
        
        # 调用 Codex 修复
        print(f"❌ 测试失败，正在修复 (尝试 {retries + 1}/{max_retries})...")
        code_result = await fix_bugs(code_result, errors)
        
        retries += 1
    
    # 超过最大重试次数
    raise Exception(f"测试失败，已重试 {max_retries} 次")
```

---

### 4. AI Review 阶段

```python
# workflow/review_phase.py
async def review_phase(code_result: Dict) -> Dict:
    """多 Agent 代码审查"""
    reviewers = [
        CodexReviewer(),    # 逻辑/边界
        GeminiReviewer(),   # 安全/扩展
        ClaudeReviewer()    # 基础检查
    ]
    
    reviews = []
    for reviewer in reviewers:
        review = await reviewer.review(code_result)
        reviews.append(review)
        
        if review['status'] == 'rejected' and review['severity'] == 'critical':
            # 有关键问题，需要修复
            return {'status': 'needs_fix', 'reviews': reviews}
    
    # 所有 Review 通过
    return {'status': 'approved', 'reviews': reviews}
```

---

### 5. PR 创建

```python
# workflow/pr_phase.py
async def create_pr(review_result: Dict) -> Dict:
    """创建 Pull Request"""
    # 1. 创建分支
    branch_name = f"feature/auto-{generate_id()}"
    await git.create_branch(branch_name)
    
    # 2. 提交代码
    await git.commit_all("feat: auto-generated implementation")
    
    # 3. 推送到 GitHub
    await git.push(branch_name)
    
    # 4. 创建 PR
    pr = await github.create_pr(
        title=f"feat: auto-generated implementation",
        body=generate_pr_body(review_result),
        head=branch_name,
        base="main"
    )
    
    # 5. 触发 CI
    await github.trigger_ci(pr['number'])
    
    return {
        'pr_number': pr['number'],
        'pr_url': pr['html_url'],
        'status': 'ready_for_review'
    }
```

---

## 📱 钉钉交互示例

### 用户发送需求
```
创建一个电商小程序的购物车功能，包括：
1. 添加商品到购物车
2. 修改商品数量
3. 删除商品
4. 计算总价
5. 结算功能
```

### 集群自动回复
```
✅ 需求已接收，工作流已启动

📋 任务清单:
1. UI 设计 - 购物车页面线框图
2. 后端 - 购物车 API (增删改查)
3. 前端 - 购物车组件
4. 测试 - 单元测试 + 集成测试

⏱️ 预计完成时间：60-90 分钟

完成后会收到钉钉通知。
```

### 完成后通知
```
## 🎉 PR 已就绪，可以 Review！

**需求**: 电商小程序购物车功能

**PR**: #42

---

### ✅ 检查清单

- ✅ UI 设计完成
- ✅ 后端 API 实现 (5 个接口)
- ✅ 前端组件实现
- ✅ 单元测试通过 (23/23)
- ✅ 集成测试通过
- ✅ AI Review 通过 (3/3)
- ✅ CI 全绿

---

🔗 https://github.com/xxx/pull/42

⏱️ Review 预计需要 10-15 分钟
```

---

## 🚀 启动方式

### 方式 1: 钉钉机器人
1. 在钉钉群@Agent 集群助手
2. 发送产品需求
3. 自动触发工作流

### 方式 2: OpenClaw 会话
```bash
# 通过 OpenClaw 发送消息
sessions_spawn --agentId orchestrator --task "创建用户管理系统..."
```

### 方式 3: Web 界面 (可选)
简单的 Web 表单，提交后调用 webhook

---

## ⚙️ 配置项

```json
{
  "workflow": {
    "auto_start": true,
    "max_retries": 3,
    "timeout_hours": 4,
    "parallel_agents": 3
  },
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "notify_on": ["start", "complete", "failed", "human_needed"]
    }
  },
  "review": {
    "required_reviewers": 2,
    "auto_merge": false,
    "require_ci": true
  }
}
```

---

## 📊 状态追踪

工作流状态存储在 `memory/workflow_state.json`:
```json
{
  "workflow_id": "wf-20260305-001",
  "status": "coding",
  "requirement": "创建购物车功能...",
  "phases": {
    "design": {"status": "completed", "result": {...}},
    "coding": {"status": "in_progress", "progress": 60},
    "testing": {"status": "pending"},
    "review": {"status": "pending"},
    "pr": {"status": "pending"}
  },
  "started_at": "2026-03-05T09:00:00",
  "estimated_complete": "2026-03-05T10:30:00"
}
```

---

## 🎯 下一步实现计划

### Phase 1: 核心框架 (本周)
- [ ] 创建 orchestrator.py
- [ ] 实现需求解析器
- [ ] 实现任务规划器
- [ ] 集成钉钉 webhook 接收

### Phase 2: 工作流阶段 (下周)
- [ ] 设计阶段实现
- [ ] 编码阶段实现
- [ ] 测试循环实现
- [ ] Review 阶段实现
- [ ] PR 创建实现

### Phase 3: 完善优化 (后续)
- [ ] Web 界面
- [ ] 进度查询命令
- [ ] 人工介入接口
- [ ] 工作流模板

---

**设计完成时间**: 2026-03-05  
**版本**: v1.0  
**状态**: 设计完成，待实现
