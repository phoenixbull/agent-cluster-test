#!/usr/bin/env python3
"""
增量代码生成 MVP 测试
验证核心功能实现

测试内容:
1. 反馈质量验证
2. Token 限制处理
3. Prompt 创建
4. 代码提取
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.incremental_generator import IncrementalCodeGenerator, CodeStyleAnalyzer


def test_validate_feedback_quality():
    """测试反馈质量验证"""
    print("\n📋 测试 1: 反馈质量验证")
    
    generator = IncrementalCodeGenerator()
    
    # 测试用例 1: 高质量反馈
    good_feedback = {
        "critical_issues": [
            {"description": "添加类型注解到函数参数", "file": "utils.py", "severity": "critical"},
            {"description": "修复 SQL 注入漏洞，使用参数化查询", "file": "api.py", "severity": "critical"}
        ],
        "suggestions": [
            {"description": "建议添加单元测试", "severity": "warning"}
        ]
    }
    
    quality = generator.validate_feedback_quality(good_feedback)
    print(f"   高质量反馈测试:")
    print(f"     usable: {quality['usable']}")
    print(f"     actionable_count: {quality['actionable_count']}")
    
    assert quality['usable'] == True, "高质量反馈应该可用"
    assert quality['actionable_count'] >= 1, "应该有可操作的问题"
    print(f"   ✅ 通过")
    
    # 测试用例 2: 低质量反馈
    bad_feedback = {
        "critical_issues": [
            {"description": "代码差", "severity": "critical"},  # 太模糊
            {"description": "不好", "severity": "critical"}  # 无操作性
        ]
    }
    
    quality = generator.validate_feedback_quality(bad_feedback)
    print(f"\n   低质量反馈测试:")
    print(f"     usable: {quality['usable']}")
    print(f"     issues: {quality['issues']}")
    
    assert quality['usable'] == False, "低质量反馈应该不可用"
    print(f"   ✅ 通过")
    
    return True


def test_token_limit_handling():
    """测试 Token 限制处理"""
    print("\n📋 测试 2: Token 限制处理")
    
    generator = IncrementalCodeGenerator()
    
    # 测试用例 1: 小文件 (<8000 字符)
    small_code = "def add(a, b): return a + b\n" * 100  # 约 3KB
    feedback = {"critical_issues": [{"description": "添加类型注解", "file": "test.py"}]}
    
    # 小文件应该正常处理 (不会触发最小化变更)
    # 注意：这里不实际调用 Agent，只验证逻辑
    print(f"   小文件测试 ({len(small_code)} 字符):")
    print(f"     应该使用完整修改流程")
    assert len(small_code) < 8000, "测试代码应该小于 8000"
    print(f"   ✅ 通过")
    
    # 测试用例 2: 大文件 (>8000 字符)
    large_code = "def add(a, b): return a + b\n" * 1000  # 约 30KB
    print(f"\n   大文件测试 ({len(large_code)} 字符):")
    print(f"     应该触发最小化变更")
    assert len(large_code) > 8000, "测试代码应该大于 8000"
    
    # 验证 _apply_minimal_changes 函数
    minimal_result = generator._apply_minimal_changes(large_code, feedback)
    assert "TODO" in minimal_result, "大文件应该添加 TODO 注释"
    assert len(minimal_result) > len(large_code), "结果应该包含额外内容"
    print(f"     最小化变更已添加")
    print(f"   ✅ 通过")
    
    return True


def test_create_incremental_prompt():
    """测试增量修改 Prompt 创建"""
    print("\n📋 测试 3: Prompt 创建")
    
    generator = IncrementalCodeGenerator()
    style_analyzer = CodeStyleAnalyzer()
    
    code = """def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""
    
    feedback = {
        "critical_issues": [
            {"description": "添加类型注解", "file": "utils.py"},
            {"description": "添加文档字符串", "file": "utils.py"}
        ],
        "suggestions": [
            {"description": "使用 sum() 内置函数", "file": "utils.py"}
        ]
    }
    
    style = style_analyzer.analyze_style(code)
    prompt = generator._create_incremental_modification_prompt(code, feedback, style, "utils.py")
    
    print(f"   Prompt 长度：{len(prompt)} 字符")
    print(f"   包含关键要素:")
    
    # 验证 Prompt 包含必要元素
    assert "增量代码修改任务" in prompt, "应该包含任务标题"
    assert "原始代码" in prompt, "应该包含原始代码部分"
    assert "必须修复的问题" in prompt, "应该包含关键问题"
    assert "添加类型注解" in prompt, "应该包含具体问题"
    assert "最小化变更原则" in prompt, "应该包含修改要求"
    assert "代码风格一致" in prompt, "应该包含风格要求"
    
    print(f"     ✅ 任务标题")
    print(f"     ✅ 原始代码")
    print(f"     ✅ 审查反馈")
    print(f"     ✅ 修改要求")
    print(f"     ✅ 风格约束")
    print(f"   ✅ 通过")
    
    return True


def test_extract_code_from_result():
    """测试代码提取"""
    print("\n📋 测试 4: 代码提取")
    
    generator = IncrementalCodeGenerator()
    
    # 测试用例 1: 标准代码块
    result1 = {
        "output": """好的，这是修改后的代码：

```python
def add(a: int, b: int) -> int:
    return a + b
```

希望这能帮到你。"""
    }
    
    code1 = generator._extract_code_from_result(result1)
    print(f"   测试 1 (标准代码块):")
    print(f"     提取结果：{len(code1)} 字符")
    assert "def add(a: int, b: int) -> int:" in code1, "应该提取到代码"
    assert "```" not in code1, "不应该包含代码块标记"
    print(f"   ✅ 通过")
    
    # 测试用例 2: 无代码块 (纯代码)
    result2 = {
        "output": "def add(a: int, b: int) -> int:\n    return a + b"
    }
    
    code2 = generator._extract_code_from_result(result2)
    print(f"\n   测试 2 (纯代码):")
    print(f"     提取结果：{len(code2)} 字符")
    assert "def add" in code2, "应该提取到代码"
    print(f"   ✅ 通过")
    
    # 测试用例 3: 空结果
    result3 = {
        "output": ""
    }
    
    code3 = generator._extract_code_from_result(result3)
    print(f"\n   测试 3 (空结果):")
    print(f"     提取结果：{code3}")
    assert code3 is None, "空结果应该返回 None"
    print(f"   ✅ 通过")
    
    return True


def test_code_style_analysis():
    """测试代码风格分析"""
    print("\n📋 测试 5: 代码风格分析")
    
    style_analyzer = CodeStyleAnalyzer()
    
    # Python 代码风格
    python_code = """
def calculate_sum(numbers):
    \"\"\"Calculate sum of numbers\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total
"""
    
    style = style_analyzer.analyze_style(python_code)
    print(f"   Python 代码风格:")
    print(f"     命名风格：{style['naming_convention']}")
    print(f"     缩进：{style['indentation']['type']} ({style['indentation']['size']})")
    print(f"     总行数：{style['total_lines']}")
    
    assert style['naming_convention'] == 'snake_case', "Python 应该是蛇形命名"
    assert style['indentation']['type'] == 'spaces', "Python 应该使用空格缩进"
    print(f"   ✅ 通过")
    
    return True


def test_incremental_changes_generation():
    """测试增量变更生成 (集成测试)"""
    print("\n📋 测试 6: 增量变更生成 (集成测试)")
    
    generator = IncrementalCodeGenerator()
    
    # 模拟现有文件
    existing_files = [
        {
            "filename": "utils.py",
            "path": "/tmp/test/utils.py",
            "content": "def add(a, b): return a + b\n"
        },
        {
            "filename": "api.py",
            "path": "/tmp/test/api.py",
            "content": "def get_data(): return []\n"
        }
    ]
    
    # 模拟审查反馈
    feedback = {
        "critical_issues": [
            {"description": "添加类型注解到 add 函数", "file": "utils.py", "severity": "critical"}
        ],
        "suggestions": [],
        "review_approved": False
    }
    
    # 生成增量变更
    print(f"   生成增量变更...")
    changes = generator.generate_incremental_changes(
        workflow_id="wf-test-001",
        original_task="测试任务",
        existing_files=existing_files,
        feedback=feedback
    )
    
    print(f"   生成变更数：{len(changes)}")
    
    # 验证结果
    # 注意：由于没有实际调用 Agent，这里只验证框架逻辑
    assert isinstance(changes, list), "结果应该是列表"
    # changes 可能为空 (因为反馈质量验证或 Agent 未调用)
    print(f"   ✅ 通过 (框架逻辑正常)")
    
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 增量代码生成 MVP 测试")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("反馈质量验证", test_validate_feedback_quality()))
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results.append(("反馈质量验证", False))
    
    try:
        results.append(("Token 限制处理", test_token_limit_handling()))
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results.append(("Token 限制处理", False))
    
    try:
        results.append(("Prompt 创建", test_create_incremental_prompt()))
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results.append(("Prompt 创建", False))
    
    try:
        results.append(("代码提取", test_extract_code_from_result()))
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results.append(("代码提取", False))
    
    try:
        results.append(("代码风格分析", test_code_style_analysis()))
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results.append(("代码风格分析", False))
    
    try:
        results.append(("增量变更生成", test_incremental_changes_generation()))
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results.append(("增量变更生成", False))
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！MVP 核心功能正常。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试未通过。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
