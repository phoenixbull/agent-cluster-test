# 🚀 增量代码生成方案设计

**日期**: 2026-04-08  
**目标**: 彻底解决大代码量生成问题  
**原则**: 不影响现有功能流程

---

## 📋 现状分析

### 已有基础 ✅

| 组件 | 状态 | 说明 |
|------|------|------|
| `IncrementalCodeGenerator` | 🟡 框架完成 | 关键函数占位实现 |
| `ReviewCollector` | ✅ 完成 | 审查反馈收集 |
| `Phase5Reviewer` | ✅ 完成 | 3 个 Reviewer 审查 |
| `CodeReviewIntegration` | 🟡 部分完成 | 反馈应用逻辑待实现 |

### 当前工作流

```
P1 需求 → P2 设计 → P3 编码 (全量) → P4 测试 → P5 审查
                                              ↓
                                          审查通过？
                                              ↓
                                           是 → 完成
                                              ↓
                                           否 → ❌ 任务失败
```

**问题**: 审查不通过时，没有二次修改机会

---

## 🎯 目标工作流

### 增量代码生成工作流

```
P1 需求 → P2 设计 → P3 编码 (全量) → P4 测试 → P5 审查
                                              ↓
                                          审查通过？
                                              ↓
                                           是 → 完成
                                              ↓
                                           否
                                              ↓
                              ┌───────────────┴───────────────┐
                              ↓                               ↓
                    P3 增量修改 (二次)                   人工介入
                    - 只改问题文件                        - 复杂需求
                    - 最小化变更                          - 架构调整
                    - 1800 秒超时                         - 重新设计
                              ↓
                    P5 复审 (快速)
                    - 只审查变更
                    - 300 秒超时
                              ↓
                          审查通过？
                              ↓
                           是 → 完成
                              ↓
                           否 → 失败/人工
```

**核心改进**:
1. 审查不通过 → 自动触发增量修改
2. 只修改问题文件，不重新生成全部代码
3. 增量修改超时更短 (1800 秒 vs 7200 秒)

---

## 🔧 实施方案

### 阶段 1: 实现核心函数 (1-2 天)

#### 1.1 修改 `IncrementalCodeGenerator._apply_feedback_to_code()`

**当前状态**: 占位实现 (返回原代码)

**目标**: 调用 LLM 根据反馈修改代码

```python
def _apply_feedback_to_code(self, code: str, feedback: Dict) -> str:
    """
    应用审查反馈到代码
    
    实现方案:
    1. 构建增量修改 prompt
    2. 调用 OpenClaw Agent (codex 或 claude-code)
    3. 解析返回的修改后代码
    4. 保持代码风格一致
    """
    # 1. 分析代码风格
    style_analyzer = CodeStyleAnalyzer()
    style = style_analyzer.analyze_style(code)
    
    # 2. 构建增量修改 prompt
    prompt = self._create_incremental_modification_prompt(
        code=code,
        feedback=feedback,
        style=style
    )
    
    # 3. 调用 Agent (使用短超时)
    api = OpenClawAPI()
    result = api.spawn_agent(
        agent_id="codex",  # 或 claude-code
        task=prompt,
        timeout_seconds=1800  # 30 分钟，足够修改单个文件
    )
    
    # 4. 解析返回的代码
    modified_code = self._extract_code_from_result(result)
    
    # 5. 确保风格一致
    modified_code = style_analyzer.ensure_style_consistency(
        new_code=modified_code,
        reference_code=code
    )
    
    return modified_code
```

#### 1.2 新增 `_create_incremental_modification_prompt()`

```python
def _create_incremental_modification_prompt(
    self, code: str, feedback: Dict, style: Dict
) -> str:
    """
    创建增量修改 prompt
    
    关键要素:
    1. 原始代码 (上下文)
    2. 审查反馈 (问题列表)
    3. 修改要求 (最小化变更)
    4. 风格约束 (保持一致)
    """
    prompt = f"""【增量代码修改任务】

你是一个专业的代码审查修复助手。请根据审查反馈修改以下代码。

## 原始代码

```{style.get('language', 'python')}
{code}
```

## 审查反馈

### 必须修复的问题 (Critical)
"""
    
    for issue in feedback.get('critical_issues', []):
        prompt += f"- {issue['description']}\n"
        if 'file' in issue and issue['file']:
            prompt += f"  文件：{issue['file']}\n"
    
    prompt += "\n### 建议修复的问题 (Warning)\n"
    for issue in feedback.get('suggestions', []):
        prompt += f"- {issue['description']}\n"
    
    prompt += f"""

## 修改要求

1. **最小化变更原则**: 只修改必要的代码，保持其他部分不变
2. **代码风格一致**: 
   - 命名风格：{style.get('naming_convention', 'snake_case')}
   - 缩进：{style.get('indentation', {}).get('type', 'spaces')} ({style.get('indentation', {}).get('size', 4)})
   - 引号：{style.get('quote_style', 'double')}
3. **向后兼容**: 避免破坏性修改
4. **保留注释**: 保持现有注释和文档

## 输出格式

直接返回修改后的完整代码，不要解释。代码应该可以直接替换原始文件。
"""
    
    return prompt
```

#### 1.3 修改 `AgentTaskExecutor.execute_task()` 支持增量模式

**当前**: 已有 `use_incremental` 参数，但逻辑不完整

**目标**: 完整的增量执行逻辑

```python
def execute_task(self, agent_id: str, task: str, output_dir: Path, 
                 timeout_seconds: int = 7200, use_real_agent: bool = True, 
                 workflow_id: str = None, use_incremental: bool = False,
                 existing_files: List[Dict] = None) -> Dict:
    """
    执行任务并收集代码
    
    新增参数:
    - existing_files: 现有文件列表 (增量修改时使用)
    """
    # P3: 如果有审查反馈且启用增量修改，生成增量变更
    if use_incremental and workflow_id and existing_files:
        print(f"\n📝 应用增量代码生成 (工作流：{workflow_id})")
        return self._execute_incremental_task(
            agent_id, task, output_dir, workflow_id, 
            existing_files, timeout_seconds
        )
    
    # ... 原有全量生成逻辑 ...
```

---

### 阶段 2: 集成到 Orchestrator (1 天)

#### 2.1 修改 `_coding_phase()` 支持增量修改

```python
def _coding_phase(self, tasks: List[Dict], design_result: Dict) -> Dict:
    """编码阶段 - 支持增量修改"""
    
    # 第一次：全量生成
    print("\n💻 第一次：全量代码生成")
    result = self._execute_coding_tasks(tasks, timeout=7200)
    
    # 执行审查
    print("\n🔍 执行代码审查")
    review_result = self._review_phase(result)
    
    # 审查不通过 → 增量修改
    if review_result.get('status') == 'rejected':
        print("\n🔄 审查未通过，触发增量修改")
        
        # 获取审查反馈
        feedback = self.review_collector.get_code_feedback(result['workflow_id'])
        
        # 增量修改 (只改问题文件)
        incremental_result = self._execute_incremental_coding(
            tasks=tasks,
            existing_files=result['code_files'],
            feedback=feedback,
            timeout=1800  # 30 分钟
        )
        
        # 合并结果
        result = self._merge_coding_results(result, incremental_result)
        
        # 复审 (快速)
        print("\n🔍 执行快速复审")
        review_result = self._quick_review_phase(
            result, 
            changed_files=incremental_result['changed_files']
        )
    
    return {
        **result,
        "review_status": review_result.get('status'),
        "incremental_applied": review_result.get('status') == 'rejected'
    }
```

#### 2.2 新增 `_execute_incremental_coding()` 方法

```python
def _execute_incremental_coding(
    self, tasks: List[Dict], existing_files: List[Dict], 
    feedback: Dict, timeout: int = 1800
) -> Dict:
    """
    执行增量代码修改
    
    特点:
    - 只修改问题文件
    - 超时更短 (1800 秒)
    - 并行执行 (独立文件)
    """
    print(f"\n🔧 开始增量修改...")
    print(f"   问题文件数：{len(feedback['files_to_modify'])}")
    print(f"   超时设置：{timeout}秒")
    
    changed_files = []
    
    # 对每个问题文件执行增量修改
    for file_info in existing_files:
        file_path = file_info.get('path', '')
        
        # 检查是否需要修改
        needs_modification = any(
            file_path in f or Path(file_path).name in f 
            for f in feedback['files_to_modify']
        )
        
        if needs_modification:
            print(f"\n   📝 修改文件：{file_path}")
            
            # 调用增量生成器
            generator = IncrementalCodeGenerator(str(self.workspace))
            
            modified_code = generator._apply_feedback_to_code(
                code=file_info.get('content', ''),
                feedback=feedback
            )
            
            # 保存修改
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_code)
            
            changed_files.append({
                "path": file_path,
                "action": "modified",
                "old_content": file_info.get('content', ''),
                "new_content": modified_code
            })
    
    return {
        "changed_files": changed_files,
        "total_modified": len(changed_files)
    }
```

#### 2.3 新增 `_quick_review_phase()` 方法

```python
def _quick_review_phase(self, coding_result: Dict, changed_files: List[Dict]) -> Dict:
    """
    快速复审 - 只审查变更文件
    
    特点:
    - 只审查变更文件
    - 超时更短 (300 秒)
    - 1 个 Reviewer 即可
    """
    print(f"\n⚡ 快速复审 (只审查 {len(changed_files)} 个变更文件)")
    
    # 只审查变更文件
    review_prompt = f"""【快速复审 - 只审查变更】

请审查以下代码变更：

"""
    
    for change in changed_files:
        review_prompt += f"\n## 文件：{change['path']}\n"
        review_prompt += f"\n### 变更前\n```diff\n{change['old_content']}\n```\n"
        review_prompt += f"\n### 变更后\n```diff\n{change['new_content']}\n```\n"
    
    # 调用单个 Reviewer (codex-reviewer)
    api = OpenClawAPI()
    result = api.spawn_agent(
        agent_id="codex-reviewer",
        task=review_prompt,
        timeout_seconds=300  # 5 分钟
    )
    
    return {
        "status": "approved" if result.get('success') else "rejected",
        "reviewer": "codex-reviewer",
        "changed_files_reviewed": len(changed_files)
    }
```

---

### 阶段 3: 测试验证 (1 天)

#### 3.1 单元测试

```python
# test_incremental_generation.py

def test_apply_feedback_to_code():
    """测试应用审查反馈到代码"""
    generator = IncrementalCodeGenerator()
    
    code = "def add(a, b): return a + b"
    feedback = {
        "critical_issues": [
            {"description": "添加类型注解", "file": "utils.py"}
        ]
    }
    
    modified = generator._apply_feedback_to_code(code, feedback)
    
    assert "def add(a: int, b: int) -> int:" in modified

def test_incremental_coding_phase():
    """测试增量编码阶段"""
    orchestrator = WorkflowOrchestrator()
    
    # 模拟审查不通过场景
    result = orchestrator._coding_phase(tasks, design_result)
    
    assert result['incremental_applied'] == True
    assert len(result['changed_files']) > 0
```

#### 3.2 集成测试

```bash
# 完整工作流测试
python3 test_full_workflow.py --scenario review-failed

# 预期输出:
# P1-P3: 全量生成 (7200 秒)
# P5: 审查不通过 (发现 3 个问题)
# P3: 增量修改 (1800 秒，修改 2 个文件)
# P5: 快速复审通过 (300 秒)
# ✅ 任务完成
```

---

## 📊 预期效果

### 性能对比

| 场景 | 当前方案 | 增量方案 | 提升 |
|------|---------|---------|------|
| **首次生成 200 文件** | 7200 秒 | 7200 秒 | - |
| **审查不通过 (修改 20 文件)** | ❌ 失败 | 1800 秒 | ✅ 挽救 |
| **总耗时 (含修改)** | - | 9000 秒 | - |
| **成功率** | ~60% | ~90% | +50% |

### 代码量对比

| 阶段 | 生成文件数 | 修改文件数 |
|------|-----------|-----------|
| P3 全量 | 200 | - |
| P3 增量 | - | 20 (10%) |
| **总计** | 200 | 20 |

**节省**: 避免重新生成 180 个无问题文件

---

## 🔒 风险控制

### 向后兼容

1. **默认关闭增量模式** - 需要显式启用
2. **现有流程不变** - 增量是可选扩展
3. **超时独立** - 增量修改超时不影响全量生成

### 回滚方案

如果增量修改失败：
```python
if incremental_result['status'] == 'failed':
    # 回滚到原始文件
    for change in incremental_result['changed_files']:
        with open(change['path'], 'w') as f:
            f.write(change['old_content'])
    
    # 标记任务失败
    result['status'] = 'failed'
    result['error'] = '增量修改失败，已回滚'
```

### 监控指标

```python
# 记录关键指标
metrics = {
    "full_generation_time": 7200,
    "incremental_generation_time": 1800,
    "files_modified": 20,
    "review_passed": True,
    "total_time": 9000
}
```

---

## 📝 实施清单

### 阶段 1: 核心函数 (1-2 天)

- [ ] 实现 `_apply_feedback_to_code()`
- [ ] 实现 `_create_incremental_modification_prompt()`
- [ ] 修改 `AgentTaskExecutor.execute_task()` 支持增量
- [ ] 添加代码风格保持一致性检查

### 阶段 2: 集成 (1 天)

- [ ] 修改 `_coding_phase()` 支持增量
- [ ] 实现 `_execute_incremental_coding()`
- [ ] 实现 `_quick_review_phase()`
- [ ] 添加回滚逻辑

### 阶段 3: 测试 (1 天)

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 文档更新

### 阶段 4: 上线 (0.5 天)

- [ ] 代码审查
- [ ] 灰度发布 (10% 任务)
- [ ] 监控指标
- [ ] 全量发布

---

## 🎯 成功标准

1. ✅ 审查不通过率降低 50%
2. ✅ 增量修改成功率 > 90%
3. ✅ 无现有功能回归
4. ✅ 平均任务耗时增加 < 20%

---

**下一步**: 开始实施阶段 1，预计 2 天完成核心功能。
