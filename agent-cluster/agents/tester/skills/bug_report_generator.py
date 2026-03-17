#!/usr/bin/env python3
"""
Tester Agent - Bug 报告生成器
生成详细的 Bug 描述和修复提示词，帮助开发 Agent 准确修复
"""

import json
from typing import Dict, List, Optional
from datetime import datetime


class BugReportGenerator:
    """Bug 报告生成器"""
    
    def generate_bug_report(
        self,
        bug_type: str,
        severity: str,
        title: str,
        description: str,
        steps_to_reproduce: List[str],
        expected_behavior: str,
        actual_behavior: str,
        code_location: Optional[str] = None,
        error_message: Optional[str] = None,
        screenshot_url: Optional[str] = None
    ) -> Dict:
        """
        生成标准 Bug 报告
        
        Args:
            bug_type: Bug 类型 (functional/performance/security/ui)
            severity: 严重程度 (critical/major/minor)
            title: Bug 标题
            description: Bug 描述
            steps_to_reproduce: 重现步骤
            expected_behavior: 期望行为
            actual_behavior: 实际行为
            code_location: 代码位置
            error_message: 错误信息
            screenshot_url: 截图 URL
        
        Returns:
            Bug 报告字典
        """
        bug_id = f"BUG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "bug_id": bug_id,
            "bug_type": bug_type,
            "severity": severity,
            "title": title,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "expected_behavior": expected_behavior,
            "actual_behavior": actual_behavior,
            "code_location": code_location,
            "error_message": error_message,
            "screenshot_url": screenshot_url,
            "created_at": datetime.now().isoformat(),
            "status": "open"
        }
    
    def generate_fix_prompt(self, bug_report: Dict) -> str:
        """
        生成修复提示词
        
        Args:
            bug_report: Bug 报告
        
        Returns:
            修复提示词（Markdown 格式）
        """
        severity_emoji = {
            "critical": "🔴",
            "major": "🟡",
            "minor": "🟢"
        }
        
        bug_type_name = {
            "functional": "功能问题",
            "performance": "性能问题",
            "security": "安全问题",
            "ui": "界面问题"
        }
        
        prompt = f"""# 🔧 Bug 修复任务

## 📋 Bug 信息

**Bug ID**: `{bug_report['bug_id']}`
**严重程度**: {severity_emoji.get(bug_report['severity'], '⚪')} {bug_report['severity'].upper()}
**Bug 类型**: {bug_type_name.get(bug_report['bug_type'], '未知')}
**标题**: {bug_report['title']}

---

## 📝 Bug 描述

{bug_report['description']}

---

## 🔄 重现步骤

{self._format_steps(bug_report['steps_to_reproduce'])}

---

## ✅ 期望行为

{bug_report['expected_behavior']}

---

## ❌ 实际行为

{bug_report['actual_behavior']}

---

## 📍 代码位置

**文件**: `{bug_report.get('code_location', '未知')}`

**错误信息**:
```
{bug_report.get('error_message', '无')}
```

---

## 🛠️ 修复要求

### 必须完成

1. **修复 Bug** - 解决上述问题
2. **添加测试** - 为防止回归，添加对应的测试用例
3. **验证修复** - 确保重现步骤不再触发 Bug

### 修复建议

"""
        # 根据 Bug 类型添加修复建议
        if bug_report['bug_type'] == 'security':
            prompt += """
**安全相关修复建议**:
- 使用参数化查询防止 SQL 注入
- 对所有输入进行验证和转义
- 不要硬编码密钥，使用环境变量
- 实施适当的认证和授权检查
"""
        elif bug_report['bug_type'] == 'performance':
            prompt += """
**性能相关修复建议**:
- 添加数据库索引优化查询
- 使用缓存减少重复计算
- 优化循环和递归
- 避免 N+1 查询问题
"""
        elif bug_report['bug_type'] == 'functional':
            prompt += """
**功能相关修复建议**:
- 检查边界条件和异常情况
- 确保输入验证完整
- 验证业务逻辑正确性
- 添加错误处理
"""
        
        prompt += """
---

## 📤 提交要求

修复完成后，请:

1. ✅ 确认 Bug 已修复
2. ✅ 运行所有测试确保通过
3. ✅ 提交代码并附上修复说明
4. ✅ 标记 Bug 状态为 "Fixed"

---

**修复时限**: 30 分钟
**重试次数**: 1/3
"""
        
        return prompt
    
    def _format_steps(self, steps: List[str]) -> str:
        """格式化重现步骤"""
        if not steps:
            return "无"
        
        formatted = ""
        for i, step in enumerate(steps, 1):
            formatted += f"{i}. {step}\n"
        return formatted
    
    def generate_batch_fix_prompt(self, bug_reports: List[Dict], target_agent: str) -> str:
        """
        生成批量修复提示词
        
        Args:
            bug_reports: Bug 报告列表
            target_agent: 目标开发 Agent (codex/claude-code)
        
        Returns:
            批量修复提示词
        """
        prompt = f"""# 🔧 批量 Bug 修复任务

**目标 Agent**: {'后端专家 (Codex)' if target_agent == 'codex' else '前端专家 (Claude-Code)'}
**Bug 数量**: {len(bug_reports)} 个
**修复时限**: 30 分钟

---

## 📋 Bug 列表

"""
        # 按严重程度排序
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        sorted_bugs = sorted(bug_reports, key=lambda x: severity_order.get(x['severity'], 3))
        
        for i, bug in enumerate(sorted_bugs, 1):
            severity_emoji = {"critical": "🔴", "major": "🟡", "minor": "🟢"}
            prompt += f"""
### Bug {i}: {bug['title']}

- **ID**: `{bug['bug_id']}`
- **严重程度**: {severity_emoji.get(bug['severity'], '⚪')} {bug['severity'].upper()}
- **类型**: {bug['bug_type']}
- **位置**: `{bug.get('code_location', '未知')}`
- **描述**: {bug['description'][:100]}...

"""
        
        prompt += """
---

## 🛠️ 修复要求

### 优先级

1. **🔴 高危 Bug** - 必须立即修复
2. **🟡 中危 Bug** - 应该修复
3. **🟢 低危 Bug** - 建议修复

### 修复流程

1. 按优先级顺序修复 Bug
2. 每个 Bug 修复后运行相关测试
3. 所有 Bug 修复完成后运行全量测试
4. 提交代码并附上修复说明

---

## 📤 提交要求

修复完成后，请:

1. ✅ 确认所有 Bug 已修复
2. ✅ 运行全量测试确保通过
3. ✅ 提交代码并附上修复说明
4. ✅ 更新所有 Bug 状态为 "Fixed"

---

**修复时限**: 30 分钟
**重试次数**: 1/3
"""
        
        return prompt
    
    def generate_test_failure_report(self, test_results: Dict) -> str:
        """
        生成测试失败报告
        
        Args:
            test_results: 测试结果
        
        Returns:
            测试失败报告
        """
        failed_tests = test_results.get("failed_tests", [])
        
        report = """# 🧪 测试失败报告

## 📊 测试概览

**总测试数**: {total}
**通过**: {passed} ✅
**失败**: {failed} ❌
**跳过**: {skipped} ⏭️
**覆盖率**: {coverage}%

**状态**: ❌ 未通过质量门禁

---

## ❌ 失败的测试

""".format(
            total=test_results.get("total", 0),
            passed=test_results.get("passed", 0),
            failed=len(failed_tests),
            skipped=test_results.get("skipped", 0),
            coverage=test_results.get("coverage", 0)
        )
        
        for i, test in enumerate(failed_tests[:10], 1):  # 最多显示 10 个
            report += f"""
### 测试 {i}: {test.get('name', '未知')}

**错误信息**:
```
{test.get('error', '无错误信息')}
```

**期望**: {test.get('expected', '未知')}

**实际**: {test.get('actual', '未知')}

**代码位置**: `{test.get('location', '未知')}`

"""
        
        if len(failed_tests) > 10:
            report += f"\n... 还有 {len(failed_tests) - 10} 个失败的测试\n"
        
        report += """
---

## 🔧 修复建议

1. **分析失败原因** - 查看错误信息和堆栈
2. **修复代码** - 根据期望和实际行为差异修复
3. **运行测试** - 确保修复后测试通过
4. **添加测试** - 如有必要，添加额外测试覆盖边界情况

---

**修复时限**: 30 分钟
**重试次数**: 1/3
"""
        
        return report


# 主函数 - 供集群调用
def create_bug_fix_prompt(
    bug_reports: List[Dict],
    target_agent: str = "codex"
) -> str:
    """
    创建 Bug 修复提示词
    
    Args:
        bug_reports: Bug 报告列表
        target_agent: 目标 Agent
    
    Returns:
        修复提示词
    """
    generator = BugReportGenerator()
    
    if len(bug_reports) == 1:
        return generator.generate_fix_prompt(bug_reports[0])
    else:
        return generator.generate_batch_fix_prompt(bug_reports, target_agent)


if __name__ == "__main__":
    # 测试
    print("Bug 报告生成器测试")
