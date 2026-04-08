# 🔧 超时配置修复 - 短期方案

**日期**: 2026-04-08  
**问题**: P3 编码阶段超时时间不足，大代码量任务可能失败  
**修复类型**: 短期修复 (不影响现有功能)

---

## 📋 问题描述

### 原问题
P3 编码阶段，如果生成的代码比较多、耗时比较久：
1. 超时时间设置不一致
2. 大代码量任务可能在 5 分钟内无法完成
3. 超时参数没有正确传递到所有层级

### 风险
| 问题 | 影响 | 概率 |
|------|------|------|
| Token 限制 | Agent 输出被截断 | 🔴 高 |
| 超时 | 任务被强制终止 | 🔴 高 |
| 内存不足 | 会话崩溃 | 🟡 中 |
| 文件写入失败 | 部分文件丢失 | 🟡 中 |

---

## ✅ 修复内容

### 1. `utils/agent_executor.py`

**修改**:
- 默认超时从 `3600 秒` → `7200 秒` (2 小时)
- 添加超时日志输出
- 确保超时参数传递到 `spawn_agent`

```python
def execute_task(self, agent_id: str, task: str, output_dir: Path, 
                 timeout_seconds: int = 7200,  # 🔧 修改
                 use_real_agent: bool = True, workflow_id: str = None, 
                 use_incremental: bool = False) -> Dict:
    
    print(f"   ⏱️ 超时设置：{timeout_seconds}秒 ({timeout_seconds/60:.1f}分钟)")
    
    # 🔧 传递超时参数到底层
    result = self.openclaw.spawn_agent(
        agent_id=agent_id,
        task=task,
        timeout_seconds=timeout_seconds
    )
```

### 2. `utils/openclaw_api.py`

**修改**:
- `spawn_agent` 默认超时从 `300 秒` → `7200 秒` (2 小时)
- `spawn_agent_sync` 默认超时从 `120 秒` → `300 秒` (5 分钟)
- 增强超时日志输出
- 超时错误信息包含具体秒数

```python
def spawn_agent(self, agent_id: str, task: str, timeout_seconds: int = 7200) -> Dict:
    """
    Args:
        timeout_seconds: 超时时间 (默认 7200 秒=2 小时，支持大代码量任务)
    """
    print(f"   ⏱️ 超时：{timeout_seconds}秒 ({timeout_seconds/60:.1f}分钟)")
    print(f"   ⏳ 执行中 (最多等待 {timeout_seconds/60:.0f}分钟)...")
```

### 3. `orchestrator.py`

**修改**:
- P3 编码阶段调用超时从 `3600 秒` → `7200 秒`

```python
result = self.executor.execute_task(
    agent_id=agent_id,
    task=prompt,
    output_dir=output_dir,
    timeout_seconds=7200  # 🔧 2 小时，支持大型任务
)
```

---

## 📊 超时配置对比

| 组件 | 修复前 | 修复后 | 说明 |
|------|--------|--------|------|
| `agent_executor.execute_task` | 3600 秒 | **7200 秒** | P3 编码阶段 |
| `openclaw_api.spawn_agent` | 300 秒 | **7200 秒** | API 层默认 |
| `openclaw_api.spawn_agent_sync` | 120 秒 | **300 秒** | 同步模式 |
| `orchestrator._design_phase` | 1800 秒 | 1800 秒 | 设计阶段 (保持不变) |
| `orchestrator._coding_phase` | 3600 秒 | **7200 秒** | 编码阶段 |

---

## ✅ 测试验证

运行测试脚本:
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 test_timeout_config.py
```

**测试结果**:
```
✅ agent_executor 默认超时 = 7200 秒
✅ openclaw_api spawn_agent 默认超时 = 7200 秒
✅ openclaw_api spawn_agent_sync 默认超时 = 300 秒
✅ orchestrator 调用超时 = 7200 秒
✅ 日志输出增强
```

---

## 🔍 影响评估

### ✅ 向后兼容
- 所有修改都是**增加默认值**，不影响显式传递超时的调用
- 现有功能和服务**不受影响**
- 短任务仍然可以快速完成（不会等待 2 小时）

### ✅ 性能影响
- 无额外性能开销
- 仅增加日志输出（可忽略）

### ✅ 风险控制
- 已备份原始文件 (`*.bak`)
- 语法检查通过
- 测试验证通过

---

## 📝 备份文件

| 文件 | 备份路径 |
|------|---------|
| `utils/agent_executor.py` | `utils/agent_executor.py.bak` |
| `utils/openclaw_api.py` | `utils/openclaw_api.py.bak` |

恢复命令:
```bash
cp utils/agent_executor.py.bak utils/agent_executor.py
cp utils/openclaw_api.py.bak utils/openclaw_api.py
```

---

## 🚀 下一步计划

### 中期优化 (下次迭代)
1. 实现任务规模评估
2. 大任务自动拆分
3. 异步执行 + 进度轮询

### 长期规划
1. 支持增量代码生成
2. 断点续传机制
3. 分布式 Agent 集群

---

## 📞 问题反馈

如果遇到问题：
1. 检查日志中的超时设置
2. 查看 `logs/` 目录下的执行日志
3. 恢复备份文件

---

**修复完成时间**: 2026-04-08 09:00  
**测试通过时间**: 2026-04-08 09:10  
**修复状态**: ✅ 已完成
