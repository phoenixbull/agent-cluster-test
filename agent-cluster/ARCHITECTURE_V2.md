# Agent 集群系统 v2.0 - 基于 OpenClaw + Codex 架构优化

## 核心架构：双层系统

```
┌─────────────────────────────────────────────────────────────────┐
│                        编排层 (OpenClaw/Zoe)                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  业务上下文中心                                          │    │
│  │  - Obsidian 会议记录 (自动同步)                           │    │
│  │  - 客户数据/CRM                                          │    │
│  │  - 历史决策/成功失败案例                                  │    │
│  │  - 产品定位/设计原则                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  智能调度器                                              │    │
│  │  - 任务拆解与分配                                         │    │
│  │  - Agent 选择策略                                         │    │
│  │  - 动态 Prompt 生成                                        │    │
│  │  - 失败分析与重试                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐ ─────────────────┐ ┌─────────────────┐
│  Codex Agent    │ │  Claude Code    │ │   Gemini        │
│  (后端专家)     │ │  Agent (前端)   │ │   Agent (设计)  │
│                 │ │                 │ │                 │
│ • 后端逻辑      │ │ • 前端工作      │ │ • UI 设计        │
│ • 复杂 bug       │ │ • git 操作       │ │ • HTML/CSS     │
│ • 多文件重构     │ │ • 快速迭代      │ │ • 视觉规范     │
│ • 跨代码库推理   │ │                 │ │                 │
│ • 90% 任务        │ │                 │ │                 │
└────────────────┘ └────────────────┘ └────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub CI/CD + AI Reviewers                   │
│  Lint → typecheck → tests → e2e → AI reviewers x3                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   Cron Job     │
                    │  (每 10 分钟)    │
                    └───────┬────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
         ┌─────────┐                 ┌─────────┐
         │  Pass?  │──── No ────────►│ 重试/调整 │
         └────┬────┘                 └─────────┘
              │ Yes
              ▼
       ┌──────────────┐
       │Notify Telegram│
       └──────────────┘
```

## 模型映射（阿里云替代方案）

| 原文模型 | 阿里云替代 | 用途 | 配置 |
|----------|------------|------|------|
| GPT-5.3-Codex | **qwen-coder-plus** | 后端逻辑、复杂 bug、多文件重构 | temperature: 0.3 |
| Claude-Opus-4.5 | **qwen-plus** | 前端工作、git 操作、快速迭代 | temperature: 0.5 |
| Gemini | **qwen-vl-plus** | UI 设计、视觉规范、HTML/CSS | temperature: 0.6 |
| Zoe (Orchestrator) | **qwen-max** | 编排层、任务调度、上下文管理 | temperature: 0.7 |

## 优化后的 Agent 配置

### 1. 编排层 Agent (Zoe)

```json
{
  "id": "zoe",
  "name": "Zoe 编排者",
  "workspace": "~/.openclaw/workspace/zoe",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-max",
    "temperature": 0.7
  },
  "role": "orchestrator",
  "skills": [
    "task_decomposition",
    "agent_selection",
    "prompt_engineering",
    "failure_analysis",
    "context_management"
  ],
  "mcp_servers": ["obsidian", "memory", "database", "telegram"]
}
```

**核心能力**：
- 读取 Obsidian 会议记录（自动同步）
- 访问生产数据库（只读）获取客户配置
- 根据任务类型选择合适的 Agent
- 失败时分析原因并动态调整 prompt 重试
- 完成后通过 Telegram 通知

### 2. 执行层 Agent

#### Codex Agent (后端专家)
```json
{
  "id": "codex",
  "name": "Codex 后端专家",
  "workspace": "~/.openclaw/workspace/agents/codex",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-coder-plus",
    "temperature": 0.3
  },
  "role": "backend_specialist",
  "skills": [
    "backend_logic",
    "bug_fixing",
    "refactoring",
    "cross_file_reasoning",
    "api_design"
  ],
  "mcp_servers": ["filesystem", "github", "database"]
}
```

#### Claude Code Agent (前端专家)
```json
{
  "id": "claude-code",
  "name": "Claude Code 前端专家",
  "workspace": "~/.openclaw/workspace/agents/claude-code",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-plus",
    "temperature": 0.5
  },
  "role": "frontend_specialist",
  "skills": [
    "frontend_development",
    "git_operations",
    "component_development",
    "rapid_iteration"
  ],
  "mcp_servers": ["filesystem", "github"]
}
```

#### Gemini Agent (设计专家)
```json
{
  "id": "gemini",
  "name": "Gemini 设计专家",
  "workspace": "~/.openclaw/workspace/agents/gemini",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-vl-plus",
    "temperature": 0.6
  },
  "role": "design_specialist",
  "skills": [
    "ui_design",
    "visual_system",
    "html_css",
    "design_spec"
  ],
  "mcp_servers": ["figma", "excalidraw", "filesystem"]
}
```

#### Code Reviewers (3 个)
```json
{
  "reviewers": [
    {
      "id": "codex-reviewer",
      "name": "Codex 审查者",
      "model": "qwen-coder-plus",
      "focus": "边界情况、逻辑错误、竞态条件",
      "weight": "high"
    },
    {
      "id": "gemini-reviewer",
      "name": "Gemini 审查者",
      "model": "qwen-plus",
      "focus": "安全问题、扩展性、代码质量",
      "weight": "medium"
    },
    {
      "id": "claude-reviewer",
      "name": "Claude 审查者",
      "model": "qwen-turbo",
      "focus": "基础检查（仅 critical 问题）",
      "weight": "low"
    }
  ]
}
```

## Agent 选择策略

```python
AGENT_SELECTION_RULES = {
    # 后端任务 → Codex
    "backend_logic": "codex",
    "bug_fix": "codex",
    "refactoring": "codex",
    "api_design": "codex",
    "database": "codex",
    
    # 前端任务 → Claude Code
    "frontend": "claude-code",
    "ui_component": "claude-code",
    "git_operation": "claude-code",
    "quick_fix": "claude-code",
    
    # 设计任务 → Gemini
    "ui_design": "gemini",
    "visual": "gemini",
    "html_css": "gemini",
    "design_spec": "gemini",
    
    # 复杂任务 → 多 Agent 协作
    "full_feature": ["gemini", "claude-code", "codex"],
    "new_page": ["gemini", "claude-code"],
}
```

## 改进版 Ralph Loop

### 静态 Prompt vs 动态 Prompt

```python
# ❌ 坏例子（静态 prompt）
prompt = "实现自定义模板功能"

# ✅ 好例子（动态调整）
prompt = """
停。客户要的是 X，不是 Y。

这是他们在会议里的原话：
"我们希望保存现有配置，而不是从头创建新的。"

重点做配置复用，不要做新建流程。

上下文：
- 客户：{customer_name}
- 业务场景：{business_context}
- 上次失败原因：{previous_failure_reason}
- 成功模式：{success_pattern}
"""
```

### 失败重试机制

```python
class RalphLoop:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.memory = MemorySystem()
        self.max_retries = 3
    
    def execute_with_learning(self, task):
        for attempt in range(self.max_retries):
            # 1. 从记忆检索相关上下文
            context = self.memory.retrieve(task)
            
            # 2. 生成动态 prompt
            prompt = self.orchestrator.generate_prompt(task, context, attempt)
            
            # 3. 执行 Agent
            result = self.execute_agent(task, prompt)
            
            # 4. 评估结果
            if self.evaluate(result):
                # 5. 保存成功模式
                self.memory.save_success(task, prompt, result)
                return result
            else:
                # 6. 分析失败原因
                failure_reason = self.analyze_failure(result)
                
                # 7. 调整 prompt 重试
                self.memory.save_failure(task, prompt, failure_reason)
                continue
        
        # 所有重试失败，通知人工介入
        self.notify_human(task, result)
        return None
    
    def analyze_failure(self, result):
        """分析失败原因，用于调整下一次 prompt"""
        if result.ci_failed:
            return f"CI 失败：{result.ci_errors}"
        if result.review_rejected:
            return f"审查拒绝：{result.review_comments}"
        if result.timeout:
            return "执行超时，可能需要拆解任务"
        return "未知错误"
```

## 完整工作流实现

### 步骤 1：客户需求 → Zoe 理解并拆解

```python
async def handle_customer_request(customer_id, request_description):
    # 1. 从 Obsidian 读取会议记录
    meeting_notes = await obsidian.get_notes(customer_id)
    
    # 2. 从数据库获取客户配置
    customer_config = await database.get_config(customer_id)
    
    # 3. Zoe 理解并拆解需求
    task_breakdown = await zoe.decompose_task(
        request=request_description,
        context={
            "meeting_notes": meeting_notes,
            "customer_config": customer_config,
            "history": await memory.get_similar_tasks(request_description)
        }
    )
    
    # 4. 如果有管理员权限，立即处理客户问题
    if task_breakdown.requires_unblock:
        await admin_api.unblock_customer(customer_id)
    
    return task_breakdown
```

### 步骤 2：创建隔离环境并启动 Agent

```python
async def start_agent_task(task):
    # 1. 创建 git worktree（隔离分支）
    worktree_path = f"../{task.id}"
    await exec(f"git worktree add {worktree_path} -b {task.branch}")
    
    # 2. 创建 tmux 会话（可中途干预）
    session_name = f"{task.agent}-{task.id}"
    await exec(f"""
        tmux new-session -d -s "{session_name}" \\
            -c "{worktree_path}" \\
            "{task.agent_script}"
    """)
    
    # 3. 记录任务状态
    await task_registry.save({
        "id": task.id,
        "tmux_session": session_name,
        "agent": task.agent,
        "worktree": task.id,
        "branch": task.branch,
        "started_at": datetime.now(),
        "status": "running"
    })
    
    return session_name
```

### 步骤 3：自动监控（每 10 分钟）

```python
async def monitor_agents():
    """Cron 任务：每 10 分钟检查所有 Agent 状态"""
    tasks = await task_registry.get_running_tasks()
    
    for task in tasks:
        # 1. 检查 tmux 会话是否存活
        session_alive = await exec(f"tmux has-session -t {task.tmux_session}")
        
        # 2. 检查是否有新 PR
        pr = await github.get_pr(task.branch)
        
        # 3. 检查 CI 状态
        ci_status = await github.get_ci_status(pr.number) if pr else None
        
        # 4. 判断是否需要干预
        if not session_alive and ci_status != "success":
            # 任务失败，触发 Ralph Loop 重试
            if task.retry_count < 3:
                await ralph_loop.retry(task)
            else:
                await notify_human(task, "多次重试失败")
        
        # 5. 检查是否完成
        if ci_status == "success" and await all_reviews_approved(pr):
            await notify_human(task, "PR 已就绪，可以 Review")
```

### 步骤 4-7：自动化 Code Review + CI

```python
REVIEW_REQUIREMENTS = {
    "required": [
        "pr_created",
        "ci_passed",  # lint, typecheck, tests, e2e
        "codex_reviewer_approved",
        "gemini_reviewer_approved",
        "screenshots_attached"  # 如果有 UI 改动
    ],
    "optional": [
        "claude_reviewer_approved"  # 仅关注 critical 问题
    ]
}

async def all_reviews_approved(pr):
    reviews = await github.get_reviews(pr.number)
    
    # Codex Reviewer 必须通过
    if not reviews.get("codex", {}).get("approved"):
        return False
    
    # Gemini Reviewer 必须通过
    if not reviews.get("gemini", {}).get("approved"):
        return False
    
    # Claude Reviewer 仅关注 critical
    if reviews.get("claude", {}).get("critical_issues"):
        return False
    
    # 检查 CI
    ci = await github.get_ci_status(pr.number)
    if ci != "success":
        return False
    
    # 检查截图（如果有 UI 改动）
    if pr.has_ui_changes and not pr.has_screenshots:
        return False
    
    return True
```

## 成本估算

| 项目 | 月成本 | 说明 |
|------|--------|------|
| qwen-max (编排层) | ¥200 | 主要消耗在上下文管理 |
| qwen-coder-plus (执行层) | ¥500 | 90% 的代码任务 |
| qwen-plus (前端) | ¥150 | 前端快速迭代 |
| qwen-vl-plus (设计) | ¥100 | UI 设计生成 |
| **总计** | **~¥950 ($130)** | 比原文 $190 略低 |

**新手起步**：仅使用 qwen-plus + qwen-coder-plus，约 ¥200/月 ($30)

## 内存优化策略

原文提到瓶颈是 RAM（每个 Agent 需要独立的 worktree + node_modules）。

### 优化方案

```python
# 1. 共享 node_modules
SHARED_NODE_MODULES = "~/.openclaw/shared/node_modules"

async def setup_worktree(task):
    worktree_path = f"../{task.id}"
    await exec(f"git worktree add {worktree_path} -b {task.branch}")
    
    # 使用软链接共享 node_modules
    await exec(f"ln -s {SHARED_NODE_MODULES} {worktree_path}/node_modules")
    
    # 仅安装特定于项目的依赖
    await exec(f"cd {worktree_path} && pnpm install --prefer-offline")

# 2. 限制并发 Agent 数量
MAX_CONCURRENT_AGENTS = 3  # 根据 RAM 调整

# 3. 任务队列
task_queue = asyncio.Queue(maxsize=MAX_CONCURRENT_AGENTS)

# 4. 定期清理
async def cleanup():
    # 每天清理孤立的 worktree
    await exec("git worktree prune")
    
    # 清理 7 天前的任务记录
    await task_registry.delete_old(days=7)
```

## 实施路线图

### 阶段 1：基础架构（1 周）
- [ ] 部署 Zoe 编排层
- [ ] 配置 3 个执行层 Agent
- [ ] 设置 Obsidian 自动同步
- [ ] 配置 Telegram 通知

### 阶段 2：工作流自动化（1 周）
- [ ] 实现 Ralph Loop 重试机制
- [ ] 配置 Cron 监控任务
- [ ] 设置自动化 Code Review
- [ ] 集成 CI/CD 流程

### 阶段 3：优化迭代（持续）
- [ ] 收集成功/失败模式
- [ ] 优化 Agent 选择策略
- [ ] 调整 Prompt 模板
- [ ] 内存和性能优化

## 关键成功因素

1. **上下文分离**：编排层持有业务上下文，执行层只拿最小必要信息
2. **动态 Prompt**：失败时分析原因并调整 prompt，不是简单重试
3. **多 Reviewer**：3 个 AI 审查者，各有侧重
4. **完成定义**：PR + CI + Review + 截图，全部满足才算完成
5. **人工介入点**：只在关键节点（最终 Review）需要人工

## 参考资源

- [OpenClaw 文档](https://docs.openclaw.ai)
- [Ralph Loop 原理解析](https://github.com/ralph-loop)
- [阿里云百炼模型平台](https://bailian.console.aliyun.com)
