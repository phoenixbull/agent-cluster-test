"""
pytest 配置文件
测试配置和共享 fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_workspace():
    """临时工作空间"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_code():
    """示例代码"""
    return """
def add(a, b):
    \"\"\"Add two numbers\"\"\"
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""


@pytest.fixture
def sample_feedback():
    """示例审查反馈 - 高质量"""
    return {
        "critical_issues": [
            {"description": "添加类型注解到函数参数", "file": "utils.py", "severity": "critical"},
            {"description": "修复 SQL 注入漏洞，使用参数化查询", "file": "api.py", "severity": "critical"}
        ],
        "suggestions": [
            {"description": "建议添加单元测试", "severity": "warning"}
        ],
        "review_approved": False
    }


@pytest.fixture
def sample_feedback_low_quality():
    """示例审查反馈 - 低质量"""
    return {
        "critical_issues": [
            {"description": "代码差", "severity": "critical"},
            {"description": "不好", "severity": "critical"}
        ]
    }


@pytest.fixture
def sample_workflow_result():
    """示例工作流结果"""
    return {
        "workflow_id": "wf-test-001",
        "status": "completed",
        "review_status": "approved",
        "total_files": 150,
        "incremental_attempts": 1,
        "code_files": [
            {"path": "/tmp/test/utils.py", "content": "def add(a, b): return a + b"},
            {"path": "/tmp/test/api.py", "content": "def get_data(): return []"}
        ]
    }
