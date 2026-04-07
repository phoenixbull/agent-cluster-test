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

### 第一阶段：清理会话（立即执行）

- [ ] 备份旧会话记录
- [ ] 清理 sessions 目录
- [ ] 重新测试电商项目
- [ ] 验证生成的代码

### 第二阶段：配置 GitHub（可选）

- [ ] 更新 cluster_config_v2.json
- [ ] 重启服务
- [ ] 验证 repo_dir 路径

### 第三阶段：代码逻辑修复（如需要）

- [ ] 修改 _collect_code_files 逻辑
- [ ] 添加会话验证
- [ ] 测试验证

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
