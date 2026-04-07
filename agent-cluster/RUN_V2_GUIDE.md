# 🚀 Agent 集群 V2.0 完整运行指南

## 前置检查

### 1. 检查配置

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 检查配置文件
python3 -c "
import json
with open('cluster_config.json') as f:
    config = json.load(f)
    print('✅ 配置文件加载成功')
    print(f'集群模式：{config[\"cluster\"][\"mode\"]}')
    print(f'Agent 数量：{len(config[\"agents\"])}')
    print(f'钉钉通知：{\"✅ 已启用\" if config[\"notifications\"][\"dingtalk\"][\"enabled\"] else \"❌ 未启用\"}')
"
```

### 2. 检查依赖

```bash
# 检查 Python 版本
python3 --version

# 检查必要模块
python3 -c "
from notifiers.dingtalk import ClusterNotifier
print('✅ 钉钉通知模块 OK')

import cluster_manager
print('✅ 集群管理器 OK')

import ralph_loop
print('✅ Ralph Loop 模块 OK')

import agent_selector
print('✅ Agent 选择器 OK')

import monitor
print('✅ 监控模块 OK')
"
```

---

## 第一步：启动集群

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 启动集群
python3 cluster_manager.py start
```

**预期输出**:
```
============================================================
🚀 启动 Agent 集群
============================================================
🔌 初始化 MCP，连接 8 个服务器...
  - 连接 MCP 服务器：obsidian
  - 连接 MCP 服务器：memory
  - 连接 MCP 服务器：filesystem
  - ...
🤝 初始化 A2A，监听端口 5000...

✅ 集群已启动，模式：orchestrator
📊 活跃 Agent: 3
============================================================
```

---

## 第二步：查看集群状态

```bash
# 查看 Agent 列表
python3 cluster_manager.py agent list

# 查看集群状态
python3 cluster_manager.py status
```

**预期输出**:
```
🟢 Codex 后端专家 (codex)
   角色：backend_specialist
   模型：qwen-coder-plus
   技能：backend_logic, bug_fixing, refactoring...

🟢 Claude Code 前端专家 (claude-code)
   角色：frontend_specialist
   模型：qwen-plus
   技能：frontend_development, git_operations...

🟢 设计专家 (Gemini) (designer)
   角色：design_specialist
   模型：qwen-vl-plus
   技能：ui_design, wireframe, prototype...
```

---

## 第三步：运行测试任务

### 方案 A: 并行执行多个任务

```bash
# 运行完整工作流示例
python3 cluster_manager.py parallel examples/full_pipeline_tasks.json
```

**任务内容**:
1. researcher → 调研设计趋势
2. writer → 撰写需求文档
3. designer → 输出 UI 设计稿
4. coder → 评估技术可行性
5. main → 汇总生成项目报告

### 方案 B: 运行 Ralph Loop 测试

```bash
# 运行 Ralph Loop 测试（带学习机制）
python3 ralph_loop.py
```

### 方案 C: 自定义任务

创建任务文件 `test_task.json`:
```json
{
  "tasks": [
    {
      "agent": "codex",
      "task": "创建一个简单的 Python 计算器模块，支持加减乘除"
    },
    {
      "agent": "claude-code",
      "task": "创建一个 HTML 登录页面，使用 Tailwind CSS 样式"
    },
    {
      "agent": "designer",
      "task": "设计一个移动端首页的线框图"
    }
  ]
}
```

然后运行:
```bash
python3 cluster_manager.py parallel test_task.json
```

---

## 第四步：监控任务执行

### 查看子代理状态

```bash
# 查看运行中的子代理
python3 cluster_manager.py subagents list
```

### 运行监控脚本

```bash
# 手动运行监控
python3 monitor.py
```

### 设置自动监控（Cron）

```bash
# 编辑 crontab
crontab -e

# 添加每 10 分钟执行一次
*/10 * * * * cd /home/admin/.openclaw/workspace/agent-cluster && python3 monitor.py
```

---

## 第五步：查看钉钉通知

当任务完成或需要 Review 时，钉钉群会收到通知：

### PR 就绪通知
```
🎉 PR 已就绪，可以 Review！

任务：创建 Python 计算器模块
Agent: codex
PR: #123

✅ CI 全绿
✅ Codex Reviewer 批准
✅ Gemini Reviewer 批准
```

### 任务失败通知（@所有人）
```
❌ 任务失败

任务：创建 HTML 登录页面
问题：CI 失败：TypeScript 类型错误
重试次数：3/3

⚠️ 需要人工介入。
```

---

## 第六步：人工 Review

收到钉钉通知后：

1. 点击 PR 链接
2. 查看 AI Reviewer 的评论
3. 检查 CI 状态
4. 查看 UI 截图（如有）
5. 合并 PR

**平均 Review 时间**: 5-10 分钟

---

## 完整流程示例

### 1. 启动集群
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 cluster_manager.py start
```

### 2. 创建测试任务
```bash
cat > test_tasks.json << 'EOF'
[
  {
    "agent": "codex",
    "task": "实现一个用户认证模块，包含登录、注册、密码重置功能"
  },
  {
    "agent": "claude-code",
    "task": "创建用户认证的前端页面，包含登录表单和注册表单"
  },
  {
    "agent": "designer",
    "task": "设计用户认证页面的 UI，输出线框图和配色方案"
  }
]
EOF
```

### 3. 执行任务
```bash
python3 cluster_manager.py parallel test_tasks.json
```

### 4. 查看进度
```bash
# 查看子代理
python3 cluster_manager.py subagents list

# 运行监控
python3 monitor.py
```

### 5. 等待钉钉通知
- 任务完成时会收到通知
- PR 就绪时会收到 Review 通知
- 任务失败时会收到介入通知

### 6. Review 并合并
- 点击钉钉通知中的 PR 链接
- 查看 AI Review 意见
- 合并 PR

---

## 快速测试（一行命令）

```bash
cd /home/admin/.openclaw/workspace/agent-cluster && \
python3 cluster_manager.py start && \
python3 cluster_manager.py parallel examples/full_pipeline_tasks.json && \
python3 cluster_manager.py subagents list
```

---

## 常见问题

### Q1: Agent 启动失败
```bash
# 检查配置
python3 cluster_manager.py status

# 重新初始化
python3 cluster_manager.py init
```

### Q2: 收不到钉钉通知
```bash
# 测试钉钉通知
python3 -c "
from notifiers.dingtalk import ClusterNotifier
n = ClusterNotifier(
    'https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea',
    'SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e'
)
n.notify_pr_ready(
    {'id': 'test', 'description': '测试', 'agent': 'codex'},
    {'pr_number': 1, 'status': 'ready', 'ci_status': 'success', 'reviews': {'approved': 2}}
)
print('测试通知已发送')
"
```

### Q3: 任务一直运行
```bash
# 查看子代理状态
python3 cluster_manager.py subagents list

# 停止所有子代理
python3 cluster_manager.py subagents stop all

# 查看监控日志
python3 monitor.py
```

---

## 预期效果

### 效率指标
- **任务完成时间**: 1-2 小时/任务
- **人工投入**: 5-10 分钟/任务（仅 Review）
- **AI 完成率**: 85-95%
- **人工介入率**: 5-15%

### 输出成果
- ✅ 自动生成的代码
- ✅ 自动创建的 PR
- ✅ 自动运行的测试
- ✅ 自动审查的代码
- ✅ 钉钉通知提醒

---

**准备好了吗？让我们开始运行！** 🚀
