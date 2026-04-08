# 🔍 增量代码生成方案 - 风险评估与改进

**Review 日期**: 2026-04-08  
**Review 重点**: 识别设计缺陷和边界情况

---

## ⚠️ 发现的问题

### 问题 1: 单文件修改的 Token 限制 ❗🔴

**问题描述**:
```python
def _apply_feedback_to_code(self, code: str, feedback: Dict) -> str:
    # 如果文件很大 (比如 5000 行)，加上审查反馈，可能超过模型 token 限制
```

**风险**:
- 大文件 (>10KB 代码) + 多个审查问题 → Token 超限
- 模型可能截断输出，导致代码不完整

**影响范围**: 🔴 高 (常见于生成的主文件)

**改进方案**:
```python
def _apply_feedback_to_code(self, code: str, feedback: Dict, file_path: str) -> str:
    # 1. 检查代码大小
    if len(code) > 8000:  # 约 30KB，接近 token 限制
        # 2. 使用"函数级"修改策略
        return self._apply_function_level_changes(code, feedback)
    else:
        # 3. 正常处理
        return self._apply_full_file_changes(code, feedback)

def _apply_function_level_changes(self, code: str, feedback: Dict) -> str:
    """
    函数级增量修改 (针对大文件)
    
    策略:
    1. 识别需要修改的函数/类
    2. 只提取相关函数 + 上下文
    3. 修改后合并回原文件
    """
    # 使用 AST 分析识别需要修改的函数
    import ast
    tree = ast.parse(code)
    
    # 提取相关函数
    functions_to_modify = self._identify_functions_to_modify(tree, feedback)
    
    # 对每个函数单独修改
    for func in functions_to_modify:
        func_code = ast.unparse(func)  # Python 3.9+
        modified_func = self._modify_single_function(func_code, feedback)
        # 替换原函数
    
    return code
```

---

### 问题 2: 多文件依赖关系 ❗🟡

**问题描述**:
```python
# 当前设计：独立修改每个文件
for file_info in existing_files:
    if needs_modification(file_info):
        modified = _apply_feedback_to_code(file_info['content'], feedback)
```

**风险**:
- 文件 A 修改后，可能影响文件 B
- 单独修改每个文件，可能导致接口不一致

**例子**:
```
审查反馈："api.py 的函数签名需要添加参数"
→ 修改 api.py (添加参数)
→ 但 test_api.py 没有同步修改 → 测试失败
```

**影响范围**: 🟡 中 (多文件项目常见)

**改进方案**:
```python
def _execute_incremental_coding(self, ..., feedback: Dict) -> Dict:
    # 1. 分析文件依赖关系
    dependency_graph = self._build_dependency_graph(existing_files)
    
    # 2. 识别"影响范围"
    affected_files = self._analyze_impact_scope(
        feedback['files_to_modify'], 
        dependency_graph
    )
    
    # 3. 按依赖顺序修改
    for file_path in self._topological_sort(affected_files):
        # 修改时考虑依赖文件的变化
        modified = self._modify_with_context(file_path, feedback, affected_files)
```

**简化方案** (实施成本更低):
```python
# 在 Prompt 中提供相关文件的上下文
def _create_incremental_modification_prompt(...):
    prompt = f"""
## 相关文件 (供参考，不要修改)

### {related_file_1}
```python
{related_file_1_code[:2000]}  # 限制长度
```

### {related_file_2}
```python
{related_file_2_code[:2000]}
```

## 需要修改的文件

{target_file_code}
"""
```

---

### 问题 3: 增量修改失败的回滚 ❗🟡

**问题描述**:
```python
# 当前设计：修改后直接覆盖
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(modified_code)
```

**风险**:
- 如果修改后验证失败，原始代码已丢失
- 多个文件修改时，部分成功部分失败

**影响范围**: 🟡 中

**改进方案**:
```python
def _execute_incremental_coding(self, ...) -> Dict:
    backup_dir = self.workspace / "incremental_backup" / workflow_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    modified_files = []
    
    try:
        for file_info in existing_files:
            if needs_modification(file_info):
                # 1. 备份原始文件
                backup_path = backup_dir / Path(file_info['path']).name
                shutil.copy(file_info['path'], backup_path)
                
                # 2. 修改
                modified_code = _apply_feedback_to_code(...)
                
                # 3. 验证 (语法检查)
                if not self._validate_syntax(modified_code, file_info['path']):
                    raise Exception(f"语法验证失败：{file_info['path']}")
                
                # 4. 写入
                with open(file_info['path'], 'w') as f:
                    f.write(modified_code)
                
                modified_files.append(file_info['path'])
        
        return {"status": "success", "modified_files": modified_files}
        
    except Exception as e:
        # 5. 失败时回滚
        print(f"⚠️ 增量修改失败，回滚到原始文件...")
        for backup_file in backup_dir.glob("*"):
            original_path = Path(file_info['path']).parent / backup_file.name
            shutil.copy(backup_file, original_path)
        
        return {"status": "failed", "error": str(e), "rolled_back": True}
```

---

### 问题 4: 快速复审的可靠性 ❗🟡

**问题描述**:
```python
def _quick_review_phase(self, coding_result: Dict, changed_files: List[Dict]) -> Dict:
    # 只审查变更文件，300 秒超时
    # 单个 Reviewer (codex-reviewer)
```

**风险**:
- 只审查变更，可能遗漏"变更引入的新问题"
- 单个 Reviewer，审查质量下降
- 300 秒可能不够 (变更复杂时)

**影响范围**: 🟡 中

**改进方案**:
```python
def _quick_review_phase(self, coding_result: Dict, changed_files: List[Dict]) -> Dict:
    # 方案 A: 保留 300 秒超时，但使用 2 个 Reviewer
    reviewers = ["codex-reviewer", "gemini-reviewer"]
    results = []
    
    for reviewer_id in reviewers:
        result = self._single_quick_review(reviewer_id, changed_files, timeout=300)
        results.append(result)
    
    # 至少 1 个通过即可
    approved = any(r['status'] == 'approved' for r in results)
    
    # 方案 B: 动态调整超时 (根据变更大小)
    total_changed_lines = sum(
        len(f['new_content'].splitlines()) - len(f['old_content'].splitlines())
        for f in changed_files
    )
    
    timeout = min(600, max(300, total_changed_lines * 10))  # 每行 10 秒，最多 10 分钟
    
    return {
        "status": "approved" if approved else "rejected",
        "timeout_used": timeout,
        "changed_lines": total_changed_lines
    }
```

---

### 问题 5: 无限循环风险 ❗🔴

**问题描述**:
```python
# 伪代码
while review_result['status'] == 'rejected':
    incremental_result = _execute_incremental_coding(...)
    review_result = _quick_review_phase(...)
    # 如果一直不通过，会无限循环
```

**风险**:
- 增量修改后仍然不通过 → 再次修改 → 再次不通过
- 可能陷入死循环

**影响范围**: 🔴 高

**改进方案**:
```python
def _coding_phase(self, tasks: List[Dict], design_result: Dict) -> Dict:
    # 第一次：全量生成
    result = self._execute_coding_tasks(tasks, timeout=7200)
    
    # 审查
    review_result = self._review_phase(result)
    
    # 增量修改循环 (最多 2 次)
    max_incremental_attempts = 2
    incremental_attempts = 0
    
    while review_result['status'] == 'rejected' and incremental_attempts < max_incremental_attempts:
        incremental_attempts += 1
        
        print(f"\n🔄 第 {incremental_attempts} 次增量修改...")
        
        feedback = self.review_collector.get_code_feedback(result['workflow_id'])
        
        # 检查是否是"相同问题" (避免重复修改)
        if incremental_attempts > 1:
            if self._is_same_issue(feedback, previous_feedback):
                print("⚠️ 检测到相同问题，停止自动修改，需要人工介入")
                break
        
        # 增量修改
        incremental_result = self._execute_incremental_coding(
            tasks=tasks,
            existing_files=result['code_files'],
            feedback=feedback,
            timeout=1800
        )
        
        if incremental_result['status'] == 'failed':
            print("❌ 增量修改失败")
            break
        
        # 合并结果
        result = self._merge_coding_results(result, incremental_result)
        previous_feedback = feedback
        
        # 快速复审
        review_result = self._quick_review_phase(result, incremental_result['changed_files'])
    
    # 最终检查
    if review_result['status'] == 'rejected':
        print(f"⚠️ {max_incremental_attempts} 次增量修改后仍未通过，需要人工介入")
        result['status'] = 'needs_human_intervention'
    
    return result
```

---

### 问题 6: 代码风格一致性的实现难度 ❗🟡

**问题描述**:
```python
def ensure_style_consistency(self, new_code: str, reference_code: str) -> str:
    # 当前：占位实现 (返回原代码)
    return new_code
```

**风险**:
- 真正实现需要代码格式化工具 (black, prettier)
- 不同语言的格式化工具不同
- 增加实施复杂度

**影响范围**: 🟡 中

**改进方案** (简化):
```python
def ensure_style_consistency(self, new_code: str, reference_code: str) -> str:
    """
    简化实现：使用标准格式化工具
    
    不追求完美，但求基本一致
    """
    import subprocess
    import tempfile
    
    # 检测语言
    language = self._detect_language(reference_code)
    
    if language == 'python':
        # 使用 black 格式化
        try:
            result = subprocess.run(
                ['black', '--quiet', '-'],
                input=new_code,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else new_code
        except:
            # black 未安装或失败，返回原代码
            return new_code
    
    elif language in ['javascript', 'typescript']:
        # 使用 prettier 格式化
        try:
            result = subprocess.run(
                ['prettier', '--parser', 'typescript' if language == 'typescript' else 'babel'],
                input=new_code,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else new_code
        except:
            return new_code
    
    else:
        # 未知语言，返回原代码
        return new_code
```

---

### 问题 7: 审查反馈的质量依赖 ❗🟡

**问题描述**:
```python
# 增量修改的质量依赖于审查反馈的质量
feedback = self.review_collector.get_code_feedback(workflow_id)
modified_code = _apply_feedback_to_code(code, feedback)
```

**风险**:
- 如果审查反馈模糊 ("代码质量差")，无法指导修改
- 如果审查反馈错误，会导致"错误修改"

**影响范围**: 🟡 中

**改进方案**:
```python
def _validate_feedback_quality(self, feedback: Dict) -> Dict:
    """
    验证审查反馈质量
    
    返回: {"usable": bool, "issues": [...], "suggestions": [...]}
    """
    usable = True
    issues = []
    
    # 检查关键问题是否具体
    for issue in feedback['critical_issues']:
        if len(issue.get('description', '')) < 10:
            issues.append(f"问题描述过于简单：{issue}")
            usable = False
        
        if 'file' not in issue:
            issues.append(f"问题未指定文件：{issue}")
            # 不标记为不可用，但记录
    
    # 检查是否有可操作的建议
    actionable_count = sum(
        1 for i in feedback['critical_issues'] 
        if any(kw in i.get('description', '').lower() for kw in ['添加', '修改', '删除', '修复'])
    )
    
    if actionable_count == 0:
        issues.append("审查反馈缺乏可操作性")
        usable = False
    
    return {
        "usable": usable,
        "issues": issues,
        "recommendation": "反馈质量高，可执行增量修改" if usable else "需要人工审查反馈"
    }

# 使用
feedback_quality = self._validate_feedback_quality(feedback)
if not feedback_quality['usable']:
    print("⚠️ 审查反馈质量不足，跳过增量修改")
    return {"status": "skipped", "reason": "反馈质量不足"}
```

---

## 📊 问题汇总

| 问题 | 严重程度 | 影响范围 | 解决成本 | 是否阻塞 |
|------|---------|---------|---------|---------|
| **1. Token 限制** | 🔴 高 | 大文件 | 🟢 低 | ❌ 否 (可规避) |
| **2. 多文件依赖** | 🟡 中 | 多文件项目 | 🟡 中 | ❌ 否 (可简化) |
| **3. 回滚机制** | 🟡 中 | 所有场景 | 🟢 低 | ⚠️ 建议实现 |
| **4. 快速复审** | 🟡 中 | 复审质量 | 🟢 低 | ❌ 否 (可调整) |
| **5. 无限循环** | 🔴 高 | 审查不通过 | 🟢 低 | ✅ **必须实现** |
| **6. 代码风格** | 🟡 中 | 代码质量 | 🟡 中 | ❌ 否 (可简化) |
| **7. 反馈质量** | 🟡 中 | 修改效果 | 🟢 低 | ⚠️ 建议实现 |

---

## ✅ 改进建议

### 必须实现 (阻塞性)

1. **无限循环防护** - 限制增量修改次数 (2 次)
2. **相同问题检测** - 避免重复修改

### 强烈建议 (高价值)

3. **回滚机制** - 修改失败时恢复原始文件
4. **反馈质量验证** - 确保反馈可操作

### 可选实现 (锦上添花)

5. **Token 限制处理** - 大文件函数级修改
6. **多文件依赖** - 提供相关文件上下文
7. **代码格式化** - 使用 black/prettier

---

## 🎯 调整后的实施计划

### Day 1: 核心函数 + 必须实现

- [ ] `_apply_feedback_to_code()` 基础实现
- [ ] `_create_incremental_modification_prompt()`
- [ ] **无限循环防护** (新增)
- [ ] 单元测试

### Day 2: 集成 + 强烈建议

- [ ] 修改 `agent_executor.py`
- [ ] 修改 `orchestrator.py`
- [ ] **回滚机制** (新增)
- [ ] **反馈质量验证** (新增)
- [ ] 集成测试

### Day 3: 测试 + 可选优化

- [ ] 完整工作流测试
- [ ] 性能测试
- [ ] 可选：代码格式化集成
- [ ] 文档更新

---

## 💡 关键决策

**问题**: 是否等所有问题都解决再实施？

**答案**: ❌ 不

**理由**:
1. 必须实现的问题 (#1, #5) 成本低 (1-2 小时)
2. 其他问题可以迭代优化
3. 先实现 MVP，再逐步完善

**MVP 范围**:
- ✅ 基础增量修改
- ✅ 无限循环防护
- ✅ 回滚机制
- ⏸️ 多文件依赖 (V2)
- ⏸️ 代码格式化 (V2)

---

**结论**: 设计方案整体可行，需要补充 2 个必须实现的功能，其他可以迭代优化。
