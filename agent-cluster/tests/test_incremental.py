#!/usr/bin/env python3
"""
增量代码生成模块测试
测试核心功能和边界情况
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.incremental_generator import IncrementalCodeGenerator, CodeStyleAnalyzer


class TestIncrementalCodeGenerator:
    """增量代码生成器测试"""
    
    def test_init(self):
        """测试初始化"""
        gen = IncrementalCodeGenerator()
        assert gen.workspace.exists()
        assert gen.code_history_dir.exists()
    
    def test_extract_code_from_result_success(self):
        """测试代码提取 - 成功"""
        gen = IncrementalCodeGenerator()
        
        # 测试标准代码块
        result = {'output': '```python\ndef test(): pass\n```'}
        code = gen._extract_code_from_result(result)
        assert code is not None
        assert "def test(): pass" in code
        assert "```" not in code
    
    def test_extract_code_from_result_no_codeblock(self):
        """测试代码提取 - 无代码块"""
        gen = IncrementalCodeGenerator()
        
        # 纯代码
        result = {'output': 'def test(): pass'}
        code = gen._extract_code_from_result(result)
        assert code is not None
        assert "def test(): pass" in code
    
    def test_extract_code_from_result_empty(self):
        """测试代码提取 - 空结果"""
        gen = IncrementalCodeGenerator()
        
        result = {'output': ''}
        code = gen._extract_code_from_result(result)
        assert code is None
    
    def test_validate_feedback_quality_high(self, sample_feedback):
        """测试反馈质量验证 - 高质量"""
        gen = IncrementalCodeGenerator()
        
        quality = gen.validate_feedback_quality(sample_feedback)
        assert quality['usable'] == True
        assert quality['actionable_count'] >= 1
        assert len(quality['issues']) == 0
    
    def test_validate_feedback_quality_low(self, sample_feedback_low_quality):
        """测试反馈质量验证 - 低质量"""
        gen = IncrementalCodeGenerator()
        
        quality = gen.validate_feedback_quality(sample_feedback_low_quality)
        assert quality['usable'] == False
        assert len(quality['issues']) > 0
    
    def test_apply_minimal_changes(self):
        """测试最小化变更"""
        gen = IncrementalCodeGenerator()
        
        large_code = "x" * 10000
        feedback = {"critical_issues": [{"description": "添加类型注解"}]}
        
        result = gen._apply_minimal_changes(large_code, feedback)
        assert "TODO" in result
        assert "添加类型注解" in result
    
    def test_create_incremental_modification_prompt(self, sample_code, sample_feedback):
        """测试 Prompt 创建"""
        gen = IncrementalCodeGenerator()
        style_analyzer = CodeStyleAnalyzer()
        
        style = style_analyzer.analyze_style(sample_code)
        prompt = gen._create_incremental_modification_prompt(
            sample_code, sample_feedback, style, "test.py"
        )
        
        assert len(prompt) > 100
        assert "原始代码" in prompt
        assert "必须修复的问题" in prompt
        assert "添加类型注解" in prompt
    
    def test_analyze_code_diff(self, sample_code):
        """测试代码差异分析"""
        gen = IncrementalCodeGenerator()
        
        old_code = sample_code
        new_code = sample_code.replace("def add", "def add(a: int, b: int)")
        
        diff = gen.analyze_code_diff(old_code, new_code, "test.py")
        
        assert diff['file_path'] == "test.py"
        assert diff['added_lines'] > 0
        assert diff['risk_level'] in ['low', 'medium', 'high']


class TestCodeStyleAnalyzer:
    """代码风格分析器测试"""
    
    def test_analyze_style_python(self):
        """测试 Python 代码风格分析"""
        analyzer = CodeStyleAnalyzer()
        
        code = """
def calculate_sum(numbers):
    \"\"\"Calculate sum\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total
"""
        
        style = analyzer.analyze_style(code)
        
        # 验证返回的字段
        assert 'naming_convention' in style
        assert 'indentation' in style
        assert 'quote_style' in style
        assert 'total_lines' in style
        
        assert style['naming_convention'] == 'snake_case'
        assert style['indentation']['type'] == 'spaces'
        assert style['total_lines'] > 0
    
    def test_ensure_style_consistency_placeholder(self):
        """测试风格一致性 (占位实现)"""
        analyzer = CodeStyleAnalyzer()
        
        new_code = "def test(): pass"
        reference = "def ref(): pass"
        
        # 当前是占位实现，直接返回原代码
        result = analyzer.ensure_style_consistency(new_code, reference)
        assert result == new_code


class TestIntegration:
    """集成测试"""
    
    def test_full_incremental_flow(self, temp_workspace, sample_feedback):
        """测试完整增量流程"""
        gen = IncrementalCodeGenerator(str(temp_workspace))
        
        existing_files = [
            {
                "filename": "utils.py",
                "path": str(temp_workspace / "utils.py"),
                "content": "def add(a, b): return a + b\n"
            }
        ]
        
        # 生成增量变更
        changes = gen.generate_incremental_changes(
            workflow_id="wf-test",
            original_task="测试任务",
            existing_files=existing_files,
            feedback=sample_feedback
        )
        
        # 验证结果 (可能为空，因为不实际调用 Agent)
        assert isinstance(changes, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
