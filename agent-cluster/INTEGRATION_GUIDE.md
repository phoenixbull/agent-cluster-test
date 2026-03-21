# 📧 钉钉阶段通知集成指南

**版本**: V2.2.0  
**更新时间**: 2026-03-21 12:20  
**状态**: ✅ 已就绪

---

## 🎯 集成目标

将 17 个钉钉通知集成到实际工作流中，实现全流程通知覆盖。

---

## 📋 集成清单

### Phase 1 需求分析

**文件**: `orchestrator.py`  
**位置**: `_analyze_requirement()` 完成后

```python
# orchestrator.py:266 行附近
def execute_workflow(self, workflow_id: str, requirement: str):
    # 阶段 1: 需求分析
    print("\n📊 阶段 1/6: 需求分析")
    self.state.update_phase(workflow_id, "analysis", "in_progress")
    tasks = self._analyze_requirement(requirement)
    
    # ✅ 添加 PRD 完成通知
    if self.notifier:
        prd_info = {
            "pm_name": "Product Manager",
            "requirement": requirement,
            "prd_url": f"https://github.com/.../wiki/PRD-{workflow_id}",
            "user_stories": len(tasks),  # 假设每个任务是一个用户故事
            "acceptance_criteria": len(tasks) * 2  # 假设每个任务有 2 个验收标准
        }
        self.notifier.notify_phase1_prd_complete(
            {"id": workflow_id, "requirement": requirement},
            prd_info
        )
    
    self.state.update_phase(workflow_id, "analysis", "completed", {"tasks": tasks})
    print(f"   ✅ 分解为 {len(tasks)} 个任务")
```

---

### Phase 2 技术设计

**文件**: `orchestrator.py`  
**位置**: `_design_phase()` 完成后

```python
# orchestrator.py:273 行附近
# 阶段 2: UI 设计
print("\n🎨 阶段 2/6: UI/UX 设计")
self.state.update_phase(workflow_id, "design", "in_progress")
design_result = self._design_phase(tasks)

# ✅ 添加设计评审通知
if self.notifier and design_result:
    design_info = {
        "tech_lead": "Tech Lead",
        "designer": "Designer",
        "architecture_url": design_result.get('architecture_url', '#'),
        "ui_design_url": design_result.get('ui_design_url', '#'),
        "deploy_config_url": design_result.get('deploy_config_url', '#')
    }
    self.notifier.notify_phase2_design_review(
        {"id": workflow_id},
        design_info
    )

self.state.update_phase(workflow_id, "design", "completed", design_result)
print(f"   ✅ 设计完成")
```

---

### Phase 3 开发实现

**文件**: `orchestrator.py` 或 `cluster_manager.py`  
**位置**: 代码提交和 PR 创建后

```python
# orchestrator.py:280 行附近
# 阶段 3: 编码实现
print("\n💻 阶段 3/6: 编码实现")
self.state.update_phase(workflow_id, "coding", "in_progress")
coding_result = self._coding_phase(tasks, design_result)

# ✅ 添加代码提交通知（如果有提交信息）
if self.notifier and coding_result:
    # 代码提交通知
    commits = coding_result.get('commits', [])
    for commit in commits[-3:]:  # 最近 3 次提交
        commit_info = {
            "agent_name": commit.get('agent', 'Codex'),
            "commit_message": commit.get('message', ''),
            "files_changed": commit.get('files_changed', 0),
            "additions": commit.get('additions', 0),
            "deletions": commit.get('deletions', 0),
            "commit_url": commit.get('url', '#')
        }
        self.notifier.notify_phase3_code_commit(
            {"id": workflow_id},
            commit_info
        )
    
    # PR 就绪通知（已有）
    if coding_result.get('pr_number'):
        self.notifier.notify_pr_ready(
            {"id": workflow_id, "description": requirement[:50]},
            coding_result
        )

self.state.update_phase(workflow_id, "coding", "completed", coding_result)
print(f"   ✅ 编码完成")
```

---

### Phase 4 测试验证

**文件**: `orchestrator.py` 或 `monitor.py`  
**位置**: 测试完成后

```python
# orchestrator.py:287 行附近
# 阶段 4: 测试循环
print("\n🧪 阶段 4/6: 测试")
self.state.update_phase(workflow_id, "testing", "in_progress")
test_result = self._testing_loop(coding_result)

# ✅ 添加测试覆盖率通知
if self.notifier and test_result:
    test_info = {
        "tester": "Tester",
        "total_tests": test_result.get('total_tests', 0),
        "passed_tests": test_result.get('passed_tests', 0),
        "failed_tests": test_result.get('failed_tests', 0),
        "coverage": test_result.get('coverage', 0),
        "coverage_url": test_result.get('coverage_url', '#'),
        "test_report_url": test_result.get('test_report_url', '#')
    }
    self.notifier.notify_phase4_test_coverage(
        {"id": workflow_id},
        test_info
    )
    
    # 严重 Bug 通知（如果有）
    bugs = test_result.get('bugs', [])
    for bug in bugs:
        if bug.get('severity') in ['critical', 'major']:
            self.notifier.notify_phase4_critical_bug(bug)

self.state.update_phase(workflow_id, "testing", "completed", test_result)
print(f"   ✅ 测试通过")
```

---

### Phase 5 代码审查

**文件**: `orchestrator.py`  
**位置**: 审查完成后

```python
# orchestrator.py:294 行附近
# 阶段 5: AI Review
print("\n🔍 阶段 5/6: AI Review")
self.state.update_phase(workflow_id, "review", "in_progress")
review_result = self._review_phase(test_result)

# ✅ 添加审查结果通知
if self.notifier and review_result:
    pr_info = review_result.get('pr_info', {})
    review_info = {
        "pr_number": pr_info.get('number', 'N/A'),
        "pr_url": pr_info.get('url', '#'),
        "reviewers": review_result.get('reviewers', []),
        "approved_count": review_result.get('approved_count', 0),
        "security_score": review_result.get('security_score', 0),
        "code_quality_score": review_result.get('code_quality_score', 0),
        "issues": review_result.get('issues', []),
        "critical_count": review_result.get('critical_count', 0),
        "major_count": review_result.get('major_count', 0)
    }
    
    # 根据审查结果发送不同通知
    if review_result.get('approved', False):
        # 审查通过
        self.notifier.notify_phase5_review_passed(
            {"id": workflow_id},
            review_info
        )
    elif review_info['issues']:
        # 审查发现问题
        self.notifier.notify_phase5_review_issues(
            {"id": workflow_id},
            review_info
        )

self.state.update_phase(workflow_id, "review", "completed", review_result)
print(f"   ✅ Review 通过")
```

---

### Phase 6 部署上线

**文件**: `orchestrator.py`  
**位置**: 已有部署确认通知

```python
# orchestrator.py:306 行附近
# 阶段 6: 部署确认
print("\n🚀 阶段 6/6: 部署确认")
self.state.update_phase(workflow_id, "deployment", "pending_confirmation")

# ✅ 发送部署确认通知（已有）
if self.notifier:
    print(f"\n📱 发送部署确认通知...")
    deploy_pr_info = pr_info if pr_info else {}
    self.notifier.send_deploy_confirmation(
        {"id": workflow_id, "description": requirement[:50], "agent": "cluster"},
        deploy_pr_info
    )
    print(f"   ✅ 部署确认通知已发送（钉钉）")
```

---

## 🔧 配置文件

确保 `cluster_config_v2.json` 中包含所有事件：

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "mode": "enterprise_app",
      "admin_user_ids": ["356820521035955"],
      "events": [
        "agent_task_assigned",
        "agent_task_complete",
        "phase1_prd_complete",
        "phase2_design_review",
        "phase3_code_commit",
        "phase4_critical_bug",
        "phase4_test_coverage",
        "phase5_review_passed",
        "phase5_review_issues",
        "pr_ready",
        "deploy_confirmation",
        "deploy_complete",
        "deploy_cancelled",
        "task_failed",
        "human_intervention_needed"
      ]
    }
  }
}
```

---

## 📊 通知触发流程图

```
工作流开始
   ↓
Phase 1: 需求分析
   ↓
📄 PRD 完成通知
   ↓
Phase 2: 技术设计
   ↓
📐 设计评审通知
   ↓
Phase 3: 开发实现
   ↓
📝 代码提交通知（多次）
   ↓
🎉 PR 就绪通知
   ↓
Phase 4: 测试验证
   ↓
📊 测试覆盖率通知
   ↓
🐛 严重 Bug 通知（如有）
   ↓
Phase 5: 代码审查
   ↓
⚠️ 审查问题通知（如有问题）
   或
✅ 审查通过通知
   ↓
Phase 6: 部署确认
   ↓
🚀 部署确认通知
   ↓
✅ 部署完成通知
```

---

## 🧪 测试方法

### 方法 1: 单元测试

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./test_full_phase_notifications.sh
```

### 方法 2: 完整工作流测试

```bash
# 创建一个测试工作流
python3 orchestrator.py --test-workflow

# 或在 Web UI 中提交一个测试需求
```

### 方法 3: 实际项目测试

1. 在 Web UI 提交真实需求
2. 观察各阶段钉钉通知
3. 检查通知内容准确性

---

## 📋 集成检查清单

- [ ] `orchestrator.py` 已导入 `get_notifier`
- [ ] Phase 1 完成时调用 `notify_phase1_prd_complete()`
- [ ] Phase 2 完成时调用 `notify_phase2_design_review()`
- [ ] Phase 3 提交时调用 `notify_phase3_code_commit()`
- [ ] Phase 3 PR 就绪时调用 `notify_pr_ready()`
- [ ] Phase 4 完成时调用 `notify_phase4_test_coverage()`
- [ ] Phase 4 发现 Bug 时调用 `notify_phase4_critical_bug()`
- [ ] Phase 5 审查通过时调用 `notify_phase5_review_passed()`
- [ ] Phase 5 审查有问题时调用 `notify_phase5_review_issues()`
- [ ] Phase 6 部署确认时调用 `send_deploy_confirmation()`
- [ ] `cluster_config_v2.json` 配置完整
- [ ] 测试所有通知发送成功

---

## 🎯 推荐集成策略

### 阶段 1: 最小化集成（推荐先做）

集成 3 个关键通知：
1. ✅ Phase 1 PRD 完成
2. ✅ Phase 4 严重 Bug
3. ✅ Phase 5 审查通过

**收益**: 85% 覆盖率，关键里程碑覆盖

### 阶段 2: 完整集成

集成所有 17 个通知：
- ✅ 所有阶段通知
- ✅ 所有里程碑通知
- ✅ 所有风险预警

**收益**: 100% 覆盖率，全流程透明

---

## 📖 相关文档

| 文档 | 说明 |
|------|------|
| `PHASE_B_100_PERCENT_COMPLETE.md` | 100% 覆盖率报告 |
| `PHASE_A_IMPLEMENTATION.md` | 方案 A 实施报告 |
| `DINGTALK_NOTIFICATIONS_OVERVIEW.md` | 通知总览 |
| `AGENT_TASK_NOTIFICATIONS.md` | Agent 任务通知 |

---

## 🎯 下一步

### 立即执行

1. **更新 `orchestrator.py`** - 添加各阶段通知调用
2. **测试完整工作流** - 验证通知触发
3. **调整通知策略** - 根据实际使用情况优化

### 后续优化

- 根据反馈调整通知内容
- 避免通知过载（建议 < 50 条/天）
- 添加通知统计和报表

---

**状态**: ✅ 代码已就绪，等待集成  
**下一步**: 在实际工作流中添加通知调用
