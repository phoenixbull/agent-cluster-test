# Agent 集群系统 v2.0

基于 OpenClaw + Codex/Claude Code 架构优化的多 Agent 协作系统。

**灵感来源**: [@elvissun 的 OpenClaw + Codex 实践](https://x.com/elvissun/status/2025920521871716562)

**核心成果**:
- 📈 单日最高 94 次提交（平均每天 50 次）
- ⚡ 30 分钟完成 7 个 PR
- 🎯 当天交付客户需求
- 💰 月成本约 ¥950 ($130)

## 核心架构：双层系统

```
┌─────────────────────────────────────────────────────────────────┐
│                    编排层 (OpenClaw/Zoe)                         │
│  • 持有所有业务上下文（客户数据、会议记录、历史决策）            │
│  • 根据任务类型选择合适的 Agent                                 │
│  • 失败时分析原因并动态调整 prompt 重试                          │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐ ─────────────────┐ ┌─────────────────┐
│  Codex Agent    │ │  Claude Code    │ │   Gemini        │
│  (后端专家)     │ │  Agent (前端)   │ │   Agent (设计)  │
│  qwen-coder-plus│ │  qwen-plus      │ │   qwen-vl-plus  │
└──────────────── └──────────────── └────────────────
                              │
                              ▼
                    GitHub CI/CD + AI Reviewers x3
                              │
                              ▼
                       Notify Telegram
```

## 快速开始

### 1. 初始化集群

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 cluster_manager.py init
```

### 2. 添加 Agent

```bash
# 编排层
python3 cluster_manager.py agent add zoe Zoe 编排者

# 执行层
python3 cluster_manager.py agent add codex Codex 后端专家
python3 cluster_manager.py agent add claude-code Claude Code 前端专家
python3 cluster_manager.py agent add gemini Gemini 设计专家
```

### 3. 启动集群

```bash
python3 cluster_manager.py start
```

### 4. 运行任务

```bash
# 并行执行多个任务
python3 cluster_manager.py parallel examples/full_pipeline_tasks.json

# 使用 Ralph Loop 执行（带学习机制）
python3 ralph_loop.py
```

### 5. 监控状态

```bash
# 查看集群状态
python3 cluster_manager.py status

# 查看子代理
python3 cluster_manager.py subagents list

# 运行监控脚本（每 10 分钟）
python3 monitor.py
```

## Agent 配置

### 编排层

| Agent | 模型 | 用途 | 温度 |
|-------|------|------|------|
| **Zoe** | qwen-max | 任务调度、上下文管理、Prompt 生成 | 0.7 |

### 执行层

| Agent | 模型 | 用途 | 温度 | 任务类型 |
|-------|------|------|------|----------|
| **Codex** | qwen-coder-plus | 后端逻辑、复杂 bug、多文件重构 | 0.3 | 90% 任务 |
| **Claude Code** | qwen-plus | 前端工作、git 操作、快速迭代 | 0.5 | 快速任务 |
| **Gemini** | qwen-vl-plus | UI 设计、视觉规范、HTML/CSS | 0.6 | 设计任务 |

### 审查层

| Reviewer | 模型 | 职责 | 权重 |
|----------|------|------|------|
| **Codex Reviewer** | qwen-coder-plus | 边界情况、逻辑错误、竞态条件 | 高（必需） |
| **Gemini Reviewer** | qwen-plus | 安全问题、扩展性、代码质量 | 中（必需） |
| **Claude Reviewer** | qwen-turbo | 基础检查（仅 critical） | 低（可选） |

## 核心机制

### 1. 改进版 Ralph Loop

**传统 Ralph Loop**: 从记忆检索 → 生成输出 → 评估 → 保存学习（但 prompt 静态）

**改进版**: 失败时分析原因并**动态调整 prompt**

```python
# ❌ 静态 prompt
"实现自定义模板功能"

# ✅ 动态 prompt
"""
停。客户要的是 X，不是 Y。

这是他们在会议里的原话：
"我们希望保存现有配置，而不是从头创建新的。"

重点做配置复用，不要做新建流程。

上下文：
- 客户：{customer_name}
- 业务场景：{business_context}
- 上次失败原因：{previous_failure_reason}
"""
```

### 2. Agent 选择策略

```python
# 根据任务类型自动选择
TASK_TYPE_MAPPING = {
    "backend_logic": "codex",      # 后端 → Codex
    "frontend": "claude-code",     # 前端 → Claude Code
    "ui_design": "gemini",         # 设计 → Gemini
    "bug_fix": "codex",            # Bug → Codex
    "documentation": "writer",     # 文档 → Writer
}
```

### 3. 自动化监控

- **频率**: 每 10 分钟检查一次
- **检查项**:
  - tmux 会话是否存活
  - PR 是否创建
  - CI 状态（lint/typecheck/tests/e2e）
  - AI Reviewer 审查状态

### 4. 完成定义

PR 算"完成"必须满足：
- ✅ PR 已创建
- ✅ CI 全绿（lint、typecheck、tests、e2e）
- ✅ Codex Reviewer 批准
- ✅ Gemini Reviewer 批准
- ✅ 有 UI 改动时附带截图

## 完整工作流

```
1. 客户需求 → Zoe 理解并拆解
   ↓
2. 创建 git worktree + tmux 会话
   ↓
3. 根据任务类型选择 Agent 并启动
   ↓
4. Agent 执行任务（后台运行）
   ↓
5. Cron 每 10 分钟监控状态
   ↓
6. Agent 创建 PR
   ↓
7. 3 个 AI Reviewer 自动审查
   ↓
8. CI 运行（lint → typecheck → tests → e2e）
   ↓
9. 全部通过后通知人工 Review
   ↓
10. 人工 Review（5-10 分钟）→ 合并
```

## 成本估算

| 项目 | 月成本 | 说明 |
|------|--------|------|
| qwen-max (编排层) | ¥200 | 上下文管理、任务调度 |
| qwen-coder-plus (执行层) | ¥500 | 90% 的代码任务 |
| qwen-plus (前端) | ¥150 | 前端快速迭代 |
| qwen-vl-plus (设计) | ¥100 | UI 设计生成 |
| **总计** | **~¥950 ($130)** | 比原文 $190 略低 |

**新手起步**: 仅使用 qwen-plus + qwen-coder-plus，约 ¥200/月 ($30)

## 内存优化

每个 Agent 需要独立的 worktree + node_modules，内存是主要瓶颈。

**优化策略**:
1. 共享 node_modules（软链接）
2. 限制并发 Agent 数量（默认 3 个）
3. 定期清理孤立的 worktree（每天）
4. 7 天前的任务记录自动删除

## 文件结构

```
agent-cluster/
├── README.md                    # 本文档
├── ARCHITECTURE_V2.md           # v2.0 架构设计
├── cluster_config_v2.json       # v2.0 配置文件
├── cluster_manager.py           # 集群管理器
├── ralph_loop.py                # Ralph Loop 实现
├── agent_selector.py            # Agent 选择策略
├── monitor.py                   # 监控脚本
├── web_app.py                   # 🆕 Web 界面应用
├── start_web.sh                 # 🆕 Web 服务启动脚本
├── protocols/
│   ├── mcp/
│   │   ├── README.md            # MCP 协议
│   │   ├── figma.md             # Figma MCP
│   │   └── design-tools.md      # 设计工具
│   └── a2a/
│       └── README.md            # A2A 协议
├── agents/
│   ├── codex/SOUL.md            # Codex 人格
│   ├── claude-code/SOUL.md      # Claude Code 人格
│   ├── gemini/SOUL.md           # Gemini 人格
│   └── designer/SOUL.md         # 设计专家人格
├── utils/
│   ├── project_router.py        # 🆕 项目路由器
│   ├── agent_executor.py        # Agent 执行器
│   ├── cost_tracker.py          # 🆕 成本跟踪器
│   ├── github_helper.py         # GitHub API 助手
│   ├── code_collector.py        # 代码收集器
│   └── openclaw_api.py          # OpenClaw API
├── examples/
│   ├── parallel_tasks.json      # 并行任务示例
│   └── full_pipeline_tasks.json # 完整工作流示例
└── memory/
    ├── templates.json           # 🆕 工作流模板库
    ├── cost_stats.json          # 🆕 成本统计数据
    └── workflow_state.json      # 工作流状态
```

## 参考资源

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [阿里云百炼模型平台](https://bailian.console.aliyun.com)
- [原文推文](https://x.com/elvissun/status/2025920521871716562)
- [Ralph Loop 原理](https://github.com/ralph-loop)

## 实施路线图

### ✅ 阶段 1：基础架构（已完成）
- [x] 部署 Zoe 编排层
- [x] 配置 3 个执行层 Agent
- [x] 设置 Obsidian 自动同步
- [x] 配置 Telegram 通知

### ✅ 阶段 2：工作流自动化（已完成）
- [x] 实现 Ralph Loop 重试机制
- [x] 配置 Cron 监控任务
- [x] 设置自动化 Code Review
- [x] 集成 CI/CD 流程

### ✅ 阶段 3：长期改进（已完成 - 2026-03-06）
- [x] 收集成功/失败模式
- [x] 优化 Agent 选择策略
- [x] 调整 Prompt 模板
- [x] 内存和性能优化
- [x] 🆕 Web 界面
- [x] 🆕 工作流模板库
- [x] 🆕 多项目支持
- [x] 🆕 成本统计

---

## 🆕 新功能

### Web 界面
访问 http://localhost:8889 使用可视化界面：
- 任务提交、工作流管理、模板库、成本统计

```bash
./start_web.sh  # 启动 Web 服务
```

### 工作流模板库
保存和复用常用需求模板：
```bash
cat memory/templates.json  # 查看预置模板
```

### 多项目支持
同时管理多个项目，自动隔离：
```bash
python3 orchestrator.py "[电商] 添加购物车功能"
python3 orchestrator.py "[博客] 实现文章评论功能"
```

### 成本统计
实时追踪 API 调用成本：
```bash
curl http://localhost:8889/api/costs
```

**详细文档**: 
- [QUICKSTART.md](QUICKSTART.md) - 完整使用指南
- [NEW_FEATURES_GUIDE.md](NEW_FEATURES_GUIDE.md) - 5 分钟快速上手
- [LONG_TERM_IMPROVEMENTS_COMPLETE.md](LONG_TERM_IMPROVEMENTS_COMPLETE.md) - 改进报告

---

*基于 @elvissun 的 OpenClaw + Codex 实践优化，适配阿里云模型*
*最后更新：2026-03-06*
