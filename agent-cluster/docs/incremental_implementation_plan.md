# 📋 增量代码生成 - 实施计划

**开始日期**: 2026-04-08  
**预计完成**: 2026-04-10 (3 天)  
**负责人**: 小五

---

## 🎯 目标

实现增量代码生成，解决大代码量任务失败问题，**不影响现有功能**。

---

## 📅 时间安排

### Day 1 (2026-04-08): 核心函数实现

**上午 (2 小时)**:
- [ ] 阅读现有代码 (`incremental_generator.py`, `review_collector.py`)
- [ ] 设计 `_apply_feedback_to_code()` 实现方案
- [ ] 创建 Prompt 模板

**下午 (3 小时)**:
- [ ] 实现 `_apply_feedback_to_code()`
- [ ] 实现 `_create_incremental_modification_prompt()`
- [ ] 实现 `_extract_code_from_result()`
- [ ] 单元测试

**产出**:
- `utils/incremental_generator.py` 核心函数完成
- 单元测试通过

---

### Day 2 (2026-04-09): 集成到工作流

**上午 (2 小时)**:
- [ ] 修改 `agent_executor.py` 支持增量模式
- [ ] 添加 `existing_files` 参数
- [ ] 实现 `_execute_incremental_task()`

**下午 (3 小时)**:
- [ ] 修改 `orchestrator.py` 的 `_coding_phase()`
- [ ] 实现 `_execute_incremental_coding()`
- [ ] 实现 `_quick_review_phase()`
- [ ] 添加回滚逻辑

**产出**:
- `utils/agent_executor.py` 增量支持
- `orchestrator.py` 集成完成
- 集成测试通过

---

### Day 3 (2026-04-10): 测试与文档

**上午 (2 小时)**:
- [ ] 完整工作流测试
- [ ] 性能测试 (对比全量生成)
- [ ] 边界情况测试 (审查通过/不通过)

**下午 (2 小时)**:
- [ ] 编写使用文档
- [ ] 代码审查
- [ ] Git 提交
- [ ] 更新 MEMORY.md

**产出**:
- 测试报告
- 使用文档
- Git 提交记录

---

## 🔧 技术细节

### 1. `_apply_feedback_to_code()` 实现

```python
def _apply_feedback_to_code(self, code: str, feedback: Dict) -> str:
    """应用审查反馈到代码"""
    
    # 1. 分析代码风格
    style_analyzer = CodeStyleAnalyzer()
    style = style_analyzer.analyze_style(code)
    
    # 2. 构建增量修改 prompt
    prompt = self._create_incremental_modification_prompt(
        code=code,
        feedback=feedback,
        style=style
    )
    
    # 3. 调用 Agent (短超时)
    api = OpenClawAPI()
    result = api.spawn_agent(
        agent_id="codex",
        task=prompt,
        timeout_seconds=1800  # 30 分钟
    )
    
    # 4. 解析返回代码
    modified_code = self._extract_code_from_result(result)
    
    # 5. 确保风格一致
    modified_code = style_analyzer.ensure_style_consistency(
        new_code=modified_code,
        reference_code=code
    )
    
    return modified_code
```

### 2. Prompt 模板

```python
def _create_incremental_modification_prompt(
    self, code: str, feedback: Dict, style: Dict
) -> str:
    return f"""【增量代码修改任务】

你是一个专业的代码审查修复助手。请根据审查反馈修改以下代码。

## 原始代码

```{style.get('language', 'python')}
{code}
```

## 审查反馈

### 必须修复的问题 (Critical)
"""
    + "\n".join([f"- {i['description']}" for i in feedback['critical_issues']])
    + f"""

## 修改要求

1. **最小化变更原则**: 只修改必要的代码，保持其他部分不变
2. **代码风格一致**: 
   - 命名：{style.get('naming_convention', 'snake_case')}
   - 缩进：{style.get('indentation', {}).get('size', 4)}空格
3. **向后兼容**: 避免破坏性修改
4. **保留注释**: 保持现有注释

## 输出格式

直接返回修改后的完整代码，不要解释。
"""
```

### 3. Orchestrator 集成

```python
def _coding_phase(self, tasks: List[Dict], design_result: Dict) -> Dict:
    # 第一次：全量生成
    result = self._execute_coding_tasks(tasks, timeout=7200)
    
    # 执行审查
    review_result = self._review_phase(result)
    
    # 审查不通过 → 增量修改
    if review_result['status'] == 'rejected':
        feedback = self.review_collector.get_code_feedback(result['workflow_id'])
        
        incremental_result = self._execute_incremental_coding(
            tasks=tasks,
            existing_files=result['code_files'],
            feedback=feedback,
            timeout=1800
        )
        
        # 合并结果
        result = self._merge_coding_results(result, incremental_result)
        
        # 快速复审
        review_result = self._quick_review_phase(result, incremental_result['changed_files'])
    
    return {**result, "review_status": review_result['status']}
```

---

## ✅ 验收标准

### 功能验收

- [ ] 审查通过时，不触发增量修改
- [ ] 审查不通过时，自动触发增量修改
- [ ] 增量修改只修改问题文件
- [ ] 快速复审只审查变更文件
- [ ] 回滚逻辑正常工作

### 性能验收

- [ ] 全量生成超时 = 7200 秒 (不变)
- [ ] 增量修改超时 = 1800 秒
- [ ] 快速复审超时 = 300 秒
- [ ] 增量修改文件数 < 20% 总文件数

### 质量验收

- [ ] 增量修改成功率 > 90%
- [ ] 代码风格一致性 > 95%
- [ ] 无现有功能回归
- [ ] 单元测试覆盖率 > 80%

---

## 📊 测试场景

### 场景 1: 审查通过 (无需增量)

```bash
python3 test_workflow.py --scenario review-passed

预期:
- P3 全量生成 (7200 秒)
- P5 审查通过
- ✅ 任务完成
- 增量修改未触发
```

### 场景 2: 审查不通过 → 增量修改成功

```bash
python3 test_workflow.py --scenario review-failed-fix-success

预期:
- P3 全量生成 (7200 秒)
- P5 审查不通过 (发现 3 个问题)
- P3 增量修改 (1800 秒，修改 2 个文件)
- P5 快速复审通过 (300 秒)
- ✅ 任务完成
```

### 场景 3: 审查不通过 → 增量修改失败

```bash
python3 test_workflow.py --scenario review-failed-fix-failed

预期:
- P3 全量生成 (7200 秒)
- P5 审查不通过
- P3 增量修改失败
- 🔄 回滚到原始文件
- ❌ 任务失败 (可人工介入)
```

---

## 🔒 风险控制

### 回滚方案

```python
def _execute_incremental_coding(self, ...):
    try:
        # 执行增量修改
        changes = self._apply_feedback(...)
        
        # 验证修改
        if not self._validate_changes(changes):
            raise Exception("修改验证失败")
        
        return {"status": "success", "changes": changes}
        
    except Exception as e:
        # 回滚
        for change in changes:
            with open(change['path'], 'w') as f:
                f.write(change['old_content'])
        
        return {"status": "failed", "error": str(e), "rolled_back": True}
```

### 监控指标

```python
# 记录到 metrics.json
{
    "workflow_id": "wf-xxx",
    "full_generation_time": 7200,
    "incremental_generation_time": 1800,
    "files_total": 200,
    "files_modified": 20,
    "review_passed": True,
    "total_time": 9300,
    "timestamp": "2026-04-10T10:00:00"
}
```

---

## 📝 交付物

1. **代码**:
   - `utils/incremental_generator.py` (增强)
   - `utils/agent_executor.py` (增量支持)
   - `orchestrator.py` (集成)

2. **测试**:
   - `test_incremental_generation.py`
   - `test_workflow.py` (集成测试)

3. **文档**:
   - `docs/incremental_code_generation_design.md`
   - `docs/incremental_implementation_plan.md` (本文档)
   - `docs/incremental_usage.md` (使用说明)

4. **Git 提交**:
   ```
   feat: 实现增量代码生成功能
   
   - 新增 _apply_feedback_to_code() 函数
   - 集成到 _coding_phase() 工作流
   - 支持审查不通过自动修复
   - 添加回滚机制
   - 测试覆盖率 85%
   
   Closes #123
   ```

---

## 🚀 下一步

**立即开始**: Day 1 - 核心函数实现

1. 打开 `utils/incremental_generator.py`
2. 实现 `_apply_feedback_to_code()`
3. 运行单元测试
4. 更新进度

---

**进度追踪**: 每次完成一个阶段，更新 MEMORY.md
