# AI 产品开发智能体 - 项目隔离修复计划

**创建时间**: 2026-04-07 19:15  
**更新时间**: 2026-04-07 19:19  
**优先级**: 🔴 高  
**状态**: 第一阶段完成，待深入排查

---

## 📊 当前状态

### ✅ 已完成

| 任务 | 状态 | 说明 |
|------|------|------|
| output_dir 逻辑修复 | ✅ 完成 | orchestrator.py:730-755 |
| 飞书通知模块 | ✅ 完成 | notifier_sender.py |
| 飞书用户配置 | ✅ 完成 | cluster_config_v2.json |
| 代码提交 | ✅ 完成 | commit ea495f8 + 8864f16 + 6696540 |
| 记忆更新 | ✅ 完成 | MEMORY.md |
| 清理旧会话 | ✅ 完成 | 备份到 /tmp/old-sessions-backup/ |
| 重新测试 | ✅ 完成 | 新会话创建成功 |

### 📊 测试结果

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 项目识别 | ✅ 成功 | 电商项目 (关键词匹配) |
| 工作区设置 | ✅ 成功 | /home/admin/.openclaw/workspace/ecommerce-platform |
| output_dir 选择 | ✅ 成功 | 使用 GitHub 仓库目录 |
| 新会话创建 | ✅ 成功 | 906ab3cf (codex), 89ae0ed2 (claude-code) |
| 代码生成 | ❌ 失败 | 0 个代码文件 |
| 测试执行 | ❌ 跳过 | 无代码文件 |
| Review | ❌ 跳过 | 无代码文件 |

### 🔍 已知问题

| 问题 | 优先级 | 根因 |
|------|--------|------|
| OpenClaw Agent 未收到正确任务 | 🔴 高 | 收到默认提示而非任务描述 |
| 代码生成失败 | 🔴 高 | Agent 未执行实际任务 |
| GitHub 配置为空 | 🟡 中 | user/repo 未配置 |

### ⏳ 待实施

| 任务 | 优先级 | 预计时间 |
|------|--------|---------|
| 检查 OpenClaw Gateway 配置 | 🔴 高 | 15 分钟 |
| 验证 sessions_spawn API | 🔴 高 | 20 分钟 |
| 配置 GitHub user/repo | 🟡 中 | 5 分钟 |
| 修复测试执行逻辑 | 🟡 中 | 20 分钟 |

---

## 🔍 问题根因分析

### 问题 1: OpenClaw Agent 返回历史会话

**现象**:
- Agent 会话记录 (`cae8dde6-....jsonl`) 包含 4 月 2 日的旧对话
- 不是今天 ([2026-04-07](file:///home/admin/.openclaw/workspace/agent-cluster/agents/devops/rollback.py#L119-L119)) 的电商需求
- 代码收集逻辑复制旧文件到新目录

**影响**:
- 生成的代码是历史测试代码
- 不是电商购物车功能
- 测试和 Review 跳过

**根因**:
```python
# utils/agent_executor.py:586
def _collect_code_files(self, session_id: str, output_dir: Path, execution_result: Dict):
    files = execution_result.get("files", [])
    
    for file_info in files:
        source_path = file_info.get("path", "")
        
        # ❌ 问题：从会话记录读取的路径是历史的
        if source_path and Path(source_path).exists():
            # 复制到 output_dir（目录对了，但内容是旧的）
```

---

### 问题 2: GitHub 配置为空

**现象**:
```json
{
  "github": {
    "user": "",
    "repo": ""
  }
}
```

**影响**:
- `self.github.repo_dir` = `/home/admin/.openclaw/workspace/`
- 不是有效的项目目录

**当前绕过方案**:
- output_dir 优先级逻辑使用 ProjectRouter workspace

---

## 🛠️ 修复方案

### 方案 A: 清理旧会话记录（推荐优先）

**步骤**:
```bash
# 1. 备份旧会话
cd /home/admin/.openclaw/agents/codex/sessions/
mkdir -p /tmp/old-sessions-backup
mv *.jsonl /tmp/old-sessions-backup/
mv sessions.json /tmp/old-sessions-backup/

# 2. 重新测试
cd /home/admin/.openclaw/workspace/agent-cluster
python3 orchestrator.py "[电商] 添加购物车功能"

# 3. 验证新生成的代码
ls -la /home/admin/.openclaw/workspace/ecommerce-platform/backend/
find . -name "*cart*" -o -name "*shopping*"
```

**预期结果**:
- Agent 生成新的电商代码
- 包含购物车相关功能
- 测试和 Review 正常执行

---

### 方案 B: 配置 GitHub user/repo

**步骤**:
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 << 'EOF'
import json

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)

config['github']['user'] = 'phoenixbull'
config['github']['repo'] = 'agent-cluster-test'

with open('cluster_config_v2.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('✅ GitHub 配置已更新')
EOF

# 重启服务
sudo systemctl restart agent-cluster
```

**预期结果**:
- `self.github.repo_dir` = `/home/admin/.openclaw/workspace/agent-cluster-test`
- 代码保存到有效的 GitHub 仓库目录

---

### 方案 C: 修复代码收集逻辑

**修改**: `utils/agent_executor.py:586`

```python
def _collect_code_files(self, session_id: str, output_dir: Path, execution_result: Dict):
    """收集代码文件 - 优先使用新生成的代码"""
    collected = []
    files = execution_result.get("files", [])
    
    # 🆕 检查是否有新生成的代码（通过 session_id 判断）
    session_file = self.sessions_dir / f"{session_id}.json"
    if session_file.exists():
        # 优先使用当前会话的文件
        files = self._extract_files_from_session(session_file)
    
    for file_info in files:
        # ... 原有逻辑
```

---

## 📋 实施计划

### 第一阶段：清理会话（✅ 已完成）

- [x] 备份旧会话记录 (`/tmp/old-sessions-backup/`)
- [x] 清理 sessions 目录
- [x] 重新测试电商项目
- [x] 验证 output_dir 修复

**测试结果**:
- ✅ 项目识别：电商项目 (关键词匹配)
- ✅ 工作区设置：`/home/admin/.openclaw/workspace/ecommerce-platform`
- ✅ output_dir 选择：使用 GitHub 仓库目录
- ✅ 新会话创建：`906ab3cf` (codex), `89ae0ed2` (claude-code)
- ❌ 代码生成：0 个代码文件
- ❌ 测试执行：跳过 (无代码)
- ❌ Review: 跳过 (无代码)

---

### 第二阶段：Gateway 诊断（✅ 已完成）

**诊断结果**:

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Gateway 进程 | ✅ 正常 | PID 609337 |
| Gateway 端口 | ✅ 正常 | 14065 |
| RPC probe | ✅ 正常 | ok |
| 日志文件 | ✅ 正常 | `/tmp/openclaw/openclaw-2026-04-07.log` |

**发现的问题**:

| 问题 | 优先级 | 说明 |
|------|--------|------|
| Agent 收到错误消息 | 🔴 高 | 收到默认提示而非任务描述 |
| sessions.json 覆盖 | 🟡 中 | 清理时会话状态丢失 |
| 模型配置问题 | 🟡 中 | `bailian/glm-5` 不可用 |

**根因分析**:

1. `openclaw agent --message` 命令格式可能不正确
2. Gateway 可能使用了缓存的默认消息
3. sessions.json 状态不正确

---

### 第三阶段：Agent bootstrap 诊断（✅ 已完成 - 2026-04-07 19:32）

**诊断过程**:

| 步骤 | 操作 | 结果 |
|------|------|------|
| 1 | 测试 openclaw CLI | ✅ CLI 正常 (v2026.4.1) |
| 2 | 测试 agent 命令 | ✅ Gateway 响应正常 |
| 3 | 完成 IDENTITY.md | ✅ 已配置 |
| 4 | 完成 USER.md | ✅ 已配置 |
| 5 | 删除 BOOTSTRAP.md | ✅ 已删除 |
| 6 | 清理 sessions.json | ✅ 已备份并清理 |
| 7 | 测试 Agent 调用 | ⚠️ 能识别用户，但仍在 bootstrap 循环 |

**诊断结果**:

| 检查项 | 状态 | 说明 |
|--------|------|------|
| openclaw CLI | ✅ 正常 | 版本 2026.4.1 |
| Gateway 进程 | ✅ 正常 | PID 609337 |
| Gateway 端口 | ✅ 正常 | 14065 |
| RPC probe | ✅ 正常 | ok |
| Agent 消息识别 | ✅ 正常 | 能识别用户"老五" |
| bootstrap 配置 | ✅ 完成 | IDENTITY.md + USER.md |
| **任务执行** | ❌ **失败** | **Agent 进入 bootstrap 循环** |

**根因分析**:

Agent 的 system prompt 包含 bootstrap 检查逻辑：
1. 检查 BOOTSTRAP.md 是否存在
2. 检查 IDENTITY.md/USER.md 是否填写
3. 检查会话历史是否有上下文
4. **如果都没有，持续询问用户任务**

即使删除了 BOOTSTRAP.md，Agent 仍会检查会话历史，发现没有上下文后继续询问。

---

### 第四阶段：openclaw_api 修改（✅ 已完成 - 2026-04-07 19:39）

**修改内容**:

| 文件 | 修改 | 说明 |
|------|------|------|
| `utils/openclaw_api.py` | spawn_agent | 使用明确任务描述 + 新 session-id |

**修改后测试**:

| 测试项 | 结果 | 说明 |
|--------|------|------|
| CLI 调用 | ✅ 正常 | status: ok |
| bootstrap 绕过 | ✅ **部分成功** | Agent 不再询问 bootstrap |
| **工具调用** | ❌ **失败** | **Agent 不调用 write/edit/exec 工具** |

**最新诊断 (19:41)**:

Agent 能正常对话，但**不执行工具调用**：
- 回复文本正常 ✅
- **不调用工具创建/修改文件** ❌
- 只返回建议，不执行实际操作 ❌

**可能原因**:
1. Agent 工具调用逻辑需要特定触发条件
2. Agent 配置问题
3. 系统 prompt 缺少工具调用指导

**下一步建议**:
1. 检查 Agent 配置 (agents/codex/ 目录)
2. 检查系统 prompt 中的工具调用指导
3. 或考虑使用其他 Agent 调用方式

---

### 第四阶段：重新测试验证（⏳ 待执行）

- [ ] 修复 Agent 消息传递
- [ ] 配置 GitHub user/repo
- [ ] 重新测试电商项目
- [ ] 验证代码生成
- [ ] 验证测试执行
- [ ] 验证 Review
- [ ] 验证质量门禁

---

## ✅ 验收标准

- [ ] 项目识别正确（电商项目）
- [ ] 工作区设置正确（/home/admin/.openclaw/workspace/ecommerce-platform）
- [ ] 生成新的电商代码（包含购物车功能）
- [ ] 测试实际运行（pytest 执行）
- [ ] Review 正常执行（有代码文件）
- [ ] 质量门禁通过（覆盖率 > 0%）

---

## 📝 备注

- output_dir 修复已验证成功
- 项目隔离目录创建成功
- 主要问题是 OpenClaw Agent 返回历史会话
- 优先清理会话记录
