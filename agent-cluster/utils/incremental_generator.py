#!/usr/bin/env python3
"""
P3: 增量代码生成器
基于现有代码的增量修改，保持代码风格一致，最小化变更
"""

import json
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib


class IncrementalCodeGenerator:
    """
    P3: 增量代码生成器
    
    功能:
    - 代码差异分析
    - 增量修改策略
    - 代码合并逻辑
    - 代码风格保持
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace/agent-cluster"):
        self.workspace = Path(workspace).expanduser()
        self.code_history_dir = self.workspace / "code_history"
        self.code_history_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_code_diff(self, old_code: str, new_code: str, file_path: str = "") -> Dict:
        """
        分析代码差异
        
        Args:
            old_code: 旧代码
            new_code: 新代码
            file_path: 文件路径
        
        Returns:
            {
                "file_path": str,
                "diff_lines": [...],
                "added_lines": int,
                "removed_lines": int,
                "modified_functions": [...],
                "breaking_changes": [...],
                "risk_level": "low/medium/high"
            }
        """
        diff = list(difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        ))
        
        # 统计变更
        added_lines = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        # 识别修改的函数 (简单实现)
        modified_functions = []
        for i, line in enumerate(diff):
            if line.startswith('@@'):
                # 提取函数名 (简化实现)
                if i + 5 < len(diff):
                    context = ''.join(diff[i:i+10])
                    if 'def ' in context or 'function' in context:
                        modified_functions.append(f"function_{len(modified_functions)+1}")
        
        # 检测破坏性变更
        breaking_changes = []
        breaking_patterns = [
            ('def ', '函数定义变更'),
            ('class ', '类定义变更'),
            ('return ', '返回值变更'),
            ('async ', '异步变更'),
        ]
        
        for line in diff:
            if line.startswith('-'):
                for pattern, desc in breaking_patterns:
                    if pattern in line:
                        breaking_changes.append({
                            "type": desc,
                            "line": line.strip(),
                            "severity": "medium"
                        })
        
        # 评估风险等级
        total_changes = added_lines + removed_lines
        if total_changes > 50 or len(breaking_changes) > 5:
            risk_level = "high"
        elif total_changes > 20 or len(breaking_changes) > 2:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "file_path": file_path,
            "diff_lines": diff,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "modified_functions": modified_functions,
            "breaking_changes": breaking_changes,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_incremental_changes(self, workflow_id: str, original_task: str, 
                                     existing_files: List[Dict], feedback: Dict) -> List[Dict]:
        """
        生成增量代码变更
        
        Args:
            workflow_id: 工作流 ID
            original_task: 原始任务描述
            existing_files: 现有文件列表
            feedback: 审查反馈
        
        Returns:
            [
                {
                    "file_path": str,
                    "action": "modify/add/delete",
                    "old_content": str,
                    "new_content": str,
                    "reason": str,
                    "risk_level": str
                }
            ]
        """
        changes = []
        
        # 🔒 强烈建议：验证反馈质量
        print(f"\n📋 验证审查反馈质量...")
        quality = self.validate_feedback_quality(feedback)
        print(f"   关键问题数：{quality['critical_issues_count']}")
        print(f"   可操作数：{quality['actionable_count']}")
        print(f"   质量评估：{quality['recommendation']}")
        
        if not quality['usable']:
            print(f"   ⚠️ 反馈质量不足，跳过增量修改")
            return []
        
        # 1. 分析审查反馈，确定需要修改的文件
        files_to_modify = set()
        critical_issues = feedback.get('critical_issues', [])
        suggestions = feedback.get('suggestions', [])
        
        for issue in critical_issues + suggestions:
            if 'file' in issue:
                files_to_modify.add(issue['file'])
        
        # 2. 对每个需要修改的文件生成增量变更
        for file_info in existing_files:
            file_path = file_info.get('path', '')
            file_name = file_info.get('filename', '')
            
            # 检查是否需要修改
            needs_modification = any(file_name in f or file_path in f for f in files_to_modify)
            
            if needs_modification:
                # 生成修改后的代码
                old_content = file_info.get('content', '')
                new_content = self._apply_feedback_to_code(old_content, feedback, file_path)
                
                # 分析差异
                diff_result = self.analyze_code_diff(old_content, new_content, file_path)
                
                changes.append({
                    "file_path": file_path,
                    "action": "modify",
                    "old_content": old_content,
                    "new_content": new_content,
                    "reason": "审查反馈修复",
                    "risk_level": diff_result['risk_level'],
                    "diff_summary": {
                        "added_lines": diff_result['added_lines'],
                        "removed_lines": diff_result['removed_lines'],
                        "breaking_changes": len(diff_result['breaking_changes'])
                    }
                })
        
        # 3. 如果没有需要修改的文件，返回空列表
        if not changes:
            print(f"   ℹ️  无需增量修改 (审查已通过或无问题)")
        
        return changes
    
    def _apply_feedback_to_code(self, code: str, feedback: Dict, file_path: str = "") -> str:
        """
        应用审查反馈到代码 (MVP 实现)
        
        实现方案:
        1. 检查代码大小，处理 Token 限制
        2. 构建增量修改 prompt
        3. 调用 OpenClaw Agent
        4. 解析返回的修改后代码
        
        Args:
            code: 原始代码
            feedback: 审查反馈
            file_path: 文件路径 (可选)
        
        Returns:
            修改后的代码
        """
        # 🔒 必须实现 #1: Token 限制处理
        if len(code) > 8000:  # 大约 30KB，接近 token 限制
            print(f"   ⚠️ 文件较大 ({len(code)} 字符)，使用简化策略")
            # 大文件：只应用关键修改，不保证完整
            return self._apply_minimal_changes(code, feedback)
        
        # 1. 分析代码风格
        style_analyzer = CodeStyleAnalyzer()
        style = style_analyzer.analyze_style(code)
        
        # 2. 构建增量修改 prompt
        prompt = self._create_incremental_modification_prompt(
            code=code,
            feedback=feedback,
            style=style,
            file_path=file_path
        )
        
        # 3. 调用 Agent (使用短超时)
        try:
            from .openclaw_api import OpenClawAPI
            api = OpenClawAPI(str(self.workspace))
            
            print(f"   🤖 调用 Agent 进行增量修改...")
            result = api.spawn_agent(
                agent_id="codex",  # 使用 codex 进行代码修改
                task=prompt,
                timeout_seconds=1800  # 30 分钟
            )
            
            if result.get('success'):
                # 4. 解析返回的代码
                modified_code = self._extract_code_from_result(result)
                
                if modified_code:
                    print(f"   ✅ Agent 修改成功")
                    # 5. 确保风格一致 (简化实现)
                    return modified_code
                else:
                    print(f"   ⚠️ 未能解析返回的代码，保持原样")
            else:
                print(f"   ⚠️ Agent 调用失败：{result.get('error', 'unknown')}")
        
        except Exception as e:
            print(f"   ⚠️ 增量修改异常：{e}，保持原代码")
        
        # 失败时返回原代码
        return code
    
    def _apply_minimal_changes(self, code: str, feedback: Dict) -> str:
        """
        应用最小化变更 (针对大文件)
        
        策略:
        1. 只修改审查反馈中明确指出的问题
        2. 不保证代码风格完全一致
        3. 快速返回结果
        
        Args:
            code: 原始代码
            feedback: 审查反馈
        
        Returns:
            修改后的代码 (可能不完整)
        """
        # 简化实现：在代码中添加修复注释，提示人工修改
        fix_comments = "\n# 🔧 TODO: 需要修复以下问题:\n"
        
        for issue in feedback.get('critical_issues', []):
            fix_comments += f"# - {issue.get('description', '未描述')}\n"
        
        return code + fix_comments
    
    def _create_incremental_modification_prompt(
        self, code: str, feedback: Dict, style: Dict, file_path: str = ""
    ) -> str:
        """
        创建增量修改 prompt
        
        关键要素:
        1. 原始代码 (上下文)
        2. 审查反馈 (问题列表)
        3. 修改要求 (最小化变更)
        4. 风格约束 (保持一致)
        
        Args:
            code: 原始代码
            feedback: 审查反馈
            style: 代码风格
            file_path: 文件路径
        
        Returns:
            Prompt 文本
        """
        # 检测语言
        language = style.get('language', 'python')
        if file_path:
            ext_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.jsx': 'javascript',
                '.java': 'java',
                '.go': 'go',
            }
            ext = Path(file_path).suffix.lower()
            language = ext_map.get(ext, 'text')
        
        prompt = f"""【增量代码修改任务】

你是一个专业的代码审查修复助手。请根据审查反馈修改以下代码。

## 原始代码

```{language}
{code}
```

## 审查反馈

### 必须修复的问题 (Critical)
"""
        
        critical_issues = feedback.get('critical_issues', [])
        if critical_issues:
            for i, issue in enumerate(critical_issues, 1):
                prompt += f"{i}. {issue.get('description', '未描述')}\n"
                if 'file' in issue and issue['file']:
                    prompt += f"   文件：{issue['file']}\n"
        else:
            prompt += "(无)\n"
        
        prompt += "\n### 建议修复的问题 (Warning)\n"
        suggestions = feedback.get('suggestions', [])
        if suggestions:
            for i, issue in enumerate(suggestions, 1):
                prompt += f"{i}. {issue.get('description', '未描述')}\n"
        else:
            prompt += "(无)\n"
        
        prompt += f"""

## 修改要求

1. **最小化变更原则**: 只修改必要的代码，保持其他部分不变
2. **代码风格一致**: 
   - 命名风格：{style.get('naming_convention', 'snake_case')}
   - 缩进：{style.get('indentation', {}).get('type', 'spaces')} ({style.get('indentation', {}).get('size', 4)})
   - 引号：{style.get('quote_style', 'double')}
3. **向后兼容**: 避免破坏性修改
4. **保留注释**: 保持现有注释和文档
5. **完整输出**: 返回修改后的完整代码，不要省略任何部分

## 输出格式

直接返回修改后的完整代码，包含在代码块中，不要解释。例如:

```{language}
[修改后的完整代码]
```
"""
        
        return prompt
    
    def _extract_code_from_result(self, result: Dict) -> Optional[str]:
        """
        从 Agent 返回结果中提取代码
        
        Args:
            result: Agent 返回结果
        
        Returns:
            提取的代码，如果提取失败返回 None
        """
        import re
        
        # 尝试从多个来源提取
        output = result.get('output', '')
        
        if not output:
            return None
        
        # 尝试提取代码块 (支持多种格式)
        patterns = [
            r'```[\w]*\n(.*?)```',  # ```python\n...\n```
            r'```\n(.*?)```',        # ```\n...\n```
        ]
        
        for pattern in patterns:
            code_blocks = re.findall(pattern, output, re.DOTALL)
            if code_blocks:
                return code_blocks[0].strip()
        
        # 如果没有代码块，检查是否是纯代码
        if output.strip() and not output.strip().startswith('{'):
            return output.strip()
        
        return None
    
    def validate_feedback_quality(self, feedback: Dict) -> Dict:
        """
        🔒 强烈建议：验证审查反馈质量
        
        检查反馈是否具体、可操作
        
        Args:
            feedback: 审查反馈
        
        Returns:
            {
                "usable": bool,
                "issues": [...],
                "recommendation": str
            }
        """
        usable = True
        quality_issues = []
        
        # 检查关键问题是否具体
        critical_issues = feedback.get('critical_issues', [])
        for issue in critical_issues:
            desc = issue.get('description', '')
            
            # 问题描述太短
            if len(desc) < 10:
                quality_issues.append(f"问题描述过于简单：{desc}")
                usable = False
            
            # 缺少文件信息
            if 'file' not in issue or not issue['file']:
                quality_issues.append(f"问题未指定文件：{desc}")
                # 不标记为不可用，但记录
            
            # 检查是否有可操作性
            actionable_keywords = ['添加', '修改', '删除', '修复', '使用', '替换', '移除', '实现']
            has_action = any(kw in desc.lower() for kw in actionable_keywords)
            if not has_action:
                quality_issues.append(f"问题缺乏可操作性：{desc}")
        
        # 检查是否有可操作的建议
        actionable_count = sum(
            1 for i in critical_issues
            if any(kw in i.get('description', '').lower() for kw in actionable_keywords)
        )
        
        if actionable_count == 0 and critical_issues:
            quality_issues.append("审查反馈缺乏可操作性")
            usable = False
        
        # 生成建议
        if usable:
            recommendation = f"反馈质量合格，可执行增量修改 ({len(critical_issues)} 个关键问题)"
        else:
            recommendation = "需要人工审查反馈质量"
        
        return {
            "usable": usable,
            "issues": quality_issues,
            "recommendation": recommendation,
            "critical_issues_count": len(critical_issues),
            "actionable_count": actionable_count
        }
    
    def save_code_history(self, workflow_id: str, file_path: str, 
                         old_content: str, new_content: str, changes: Dict):
        """
        保存代码变更历史
        
        Args:
            workflow_id: 工作流 ID
            file_path: 文件路径
            old_content: 旧代码
            new_content: 新代码
            changes: 变更摘要
        """
        history_file = self.code_history_dir / f"{workflow_id}_{Path(file_path).name}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        history_data = {
            "workflow_id": workflow_id,
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "old_hash": hashlib.md5(old_content.encode()).hexdigest(),
            "new_hash": hashlib.md5(new_content.encode()).hexdigest(),
            "changes": changes,
            "diff_lines": changes.get('diff_lines', [])
        }
        
        # 保存完整内容 (可选)
        if len(old_content) < 10000:
            history_data["old_content"] = old_content
        if len(new_content) < 10000:
            history_data["new_content"] = new_content
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 代码历史已保存：{history_file}")
    
    def merge_code_changes(self, base_code: str, new_code: str, file_path: str = "") -> Dict:
        """
        合并代码变更 (处理冲突)
        
        Args:
            base_code: 基础代码
            new_code: 新代码
            file_path: 文件路径
        
        Returns:
            {
                "success": bool,
                "merged_code": str,
                "conflicts": [...],
                "error": str or None
            }
        """
        result = {
            "success": True,
            "merged_code": "",
            "conflicts": [],
            "error": None
        }
        
        # 简化实现：直接使用新代码
        # 真实实现应该使用三向合并算法
        
        try:
            # 检测明显冲突 (占位实现)
            if "CONFLICT" in new_code or "<<<<<<" in new_code:
                result["success"] = False
                result["conflicts"].append({
                    "type": "merge_conflict",
                    "description": "检测到合并冲突标记"
                })
            else:
                result["merged_code"] = new_code
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def generate_change_summary(self, changes: List[Dict]) -> Dict:
        """
        生成变更摘要
        
        Args:
            changes: 变更列表
        
        Returns:
            {
                "total_files": int,
                "added_files": int,
                "modified_files": int,
                "deleted_files": int,
                "total_added_lines": int,
                "total_removed_lines": int,
                "risk_assessment": {...},
                "commit_message": str
            }
        """
        summary = {
            "total_files": len(changes),
            "added_files": 0,
            "modified_files": 0,
            "deleted_files": 0,
            "total_added_lines": 0,
            "total_removed_lines": 0,
            "risk_assessment": {
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "commit_message": ""
        }
        
        for change in changes:
            action = change.get('action', 'modify')
            if action == 'add':
                summary['added_files'] += 1
            elif action == 'modify':
                summary['modified_files'] += 1
            elif action == 'delete':
                summary['deleted_files'] += 1
            
            diff_summary = change.get('diff_summary', {})
            summary['total_added_lines'] += diff_summary.get('added_lines', 0)
            summary['total_removed_lines'] += diff_summary.get('removed_lines', 0)
            
            risk = change.get('risk_level', 'low')
            summary['risk_assessment'][risk] += 1
        
        # 生成提交消息
        if summary['modified_files'] > 0:
            summary['commit_message'] = f"fix: 根据审查反馈修改 {summary['modified_files']} 个文件"
        elif summary['added_files'] > 0:
            summary['commit_message'] = f"feat: 新增 {summary['added_files']} 个文件"
        else:
            summary['commit_message'] = "chore: 代码优化"
        
        return summary
    
    def create_incremental_prompt(self, original_task: str, changes: List[Dict], 
                                  feedback: Dict) -> str:
        """
        创建增量修改提示
        
        Args:
            original_task: 原始任务
            changes: 变更列表
            feedback: 审查反馈
        
        Returns:
            包含变更上下文的提示
        """
        prompt = f"""{original_task}

【增量修改要求】

请根据以下审查反馈进行**最小化修改**：

"""
        
        # 添加关键问题
        critical_issues = feedback.get('critical_issues', [])
        if critical_issues:
            prompt += "### 必须修复的问题\n"
            for i, issue in enumerate(critical_issues, 1):
                prompt += f"{i}. {issue.get('description', '未描述')}\n"
                if 'file' in issue:
                    prompt += f"   文件：{issue['file']}\n"
            prompt += "\n"
        
        # 添加变更摘要
        summary = self.generate_change_summary(changes)
        prompt += f"### 变更摘要\n"
        prompt += f"- 修改文件数：{summary['modified_files']}\n"
        prompt += f"- 新增行数：{summary['total_added_lines']}\n"
        prompt += f"- 删除行数：{summary['total_removed_lines']}\n"
        prompt += f"- 风险等级：高={summary['risk_assessment']['high']}, "
        prompt += f"中={summary['risk_assessment']['medium']}, "
        prompt += f"低={summary['risk_assessment']['low']}\n"
        
        prompt += "\n### 修改原则\n"
        prompt += "1. **最小化变更** - 只修改必要的代码\n"
        prompt += "2. **保持风格** - 与现有代码风格一致\n"
        prompt += "3. **向后兼容** - 避免破坏性修改\n"
        prompt += "4. **保留注释** - 保持现有注释和文档\n"
        
        return prompt


class CodeStyleAnalyzer:
    """
    代码风格分析器
    用于保持增量修改时的代码风格一致
    """
    
    def __init__(self):
        self.style_patterns = {
            'naming': {
                'snake_case': True,
                'camelCase': False,
                'PascalCase': False
            },
            'indentation': {
                'spaces': 4,
                'tabs': False
            },
            'quotes': {
                'single': False,
                'double': True
            }
        }
    
    def analyze_style(self, code: str) -> Dict:
        """
        分析代码风格
        
        Args:
            code: 代码内容
        
        Returns:
            {
                "naming_convention": str,
                "indentation": str,
                "quote_style": str,
                "line_length": int,
                "docstring_style": str
            }
        """
        lines = code.split('\n')
        
        # 分析命名风格
        naming_style = self._detect_naming_style(code)
        
        # 分析缩进
        indent_style = self._detect_indent_style(lines)
        
        # 分析引号
        quote_style = self._detect_quote_style(code)
        
        # 分析行长度
        max_line_length = max(len(line) for line in lines) if lines else 0
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        
        return {
            "naming_convention": naming_style,
            "indentation": indent_style,
            "quote_style": quote_style,
            "max_line_length": max_line_length,
            "avg_line_length": round(avg_line_length, 1),
            "total_lines": len(lines)
        }
    
    def _detect_naming_style(self, code: str) -> str:
        """检测命名风格"""
        import re
        
        # 检测蛇形命名
        snake_case = len(re.findall(r'def [a-z]+_[a-z]+', code))
        # 检测驼峰命名
        camel_case = len(re.findall(r'def [a-z]+[A-Z]', code))
        
        return "snake_case" if snake_case >= camel_case else "camelCase"
    
    def _detect_indent_style(self, lines: List[str]) -> Dict:
        """检测缩进风格"""
        spaces_count = 0
        tabs_count = 0
        
        for line in lines:
            if line.startswith('    '):
                spaces_count += 1
            elif line.startswith('\t'):
                tabs_count += 1
        
        return {
            "type": "spaces" if spaces_count >= tabs_count else "tabs",
            "size": 4 if spaces_count >= tabs_count else 1
        }
    
    def _detect_quote_style(self, code: str) -> str:
        """检测引号风格"""
        single_quotes = code.count("'")
        double_quotes = code.count('"')
        
        return "single" if single_quotes >= double_quotes else "double"
    
    def ensure_style_consistency(self, new_code: str, reference_code: str) -> str:
        """
        确保新代码风格与参考代码一致
        
        TODO: 实现真实的代码风格转换
        当前为占位实现
        """
        # 占位实现：返回原代码
        # 真实实现应该使用代码格式化工具 (black, prettier 等)
        return new_code


if __name__ == "__main__":
    # 测试增量代码生成器
    generator = IncrementalCodeGenerator()
    style_analyzer = CodeStyleAnalyzer()
    
    print("=== P3: 增量代码生成器测试 ===\n")
    
    # 测试代码差异分析
    old_code = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    
    new_code = """def add(a, b):
    \"\"\"Add two numbers\"\"\"
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""
    
    diff_result = generator.analyze_code_diff(old_code, new_code, "math_utils.py")
    print(f"代码差异分析:")
    print(f"  新增行数：{diff_result['added_lines']}")
    print(f"  删除行数：{diff_result['removed_lines']}")
    print(f"  风险等级：{diff_result['risk_level']}")
    print(f"  破坏性变更：{len(diff_result['breaking_changes'])}")
    print()
    
    # 测试代码风格分析
    style_result = style_analyzer.analyze_style(new_code)
    print(f"代码风格分析:")
    print(f"  命名风格：{style_result['naming_convention']}")
    print(f"  缩进：{style_result['indentation']['type']} ({style_result['indentation']['size']})")
    print(f"  引号：{style_result['quote_style']}")
    print(f"  总行数：{style_result['total_lines']}")
    print()
    
    # 测试变更摘要
    changes = [
        {
            "file_path": "backend/utils.py",
            "action": "modify",
            "risk_level": "low",
            "diff_summary": {"added_lines": 5, "removed_lines": 2}
        },
        {
            "file_path": "backend/api.py",
            "action": "modify",
            "risk_level": "medium",
            "diff_summary": {"added_lines": 10, "removed_lines": 5}
        }
    ]
    
    summary = generator.generate_change_summary(changes)
    print(f"变更摘要:")
    print(f"  总文件数：{summary['total_files']}")
    print(f"  修改文件数：{summary['modified_files']}")
    print(f"  新增行数：{summary['total_added_lines']}")
    print(f"  删除行数：{summary['total_removed_lines']}")
    print(f"  提交消息：{summary['commit_message']}")
