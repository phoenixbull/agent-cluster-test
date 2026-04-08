#!/usr/bin/env python3
"""
自动化测试套件 - 主入口
运行所有测试: python3 tests/test_suite.py
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """运行所有测试"""
    test_dir = Path(__file__).parent
    
    # 运行所有测试
    args = [
        str(test_dir),
        "-v",  # 详细输出
        "--tb=short",  # 简短的 traceback
        "-x",  # 遇到第一个失败就停止
    ]
    
    return pytest.main(args)


def run_specific_test(test_file):
    """运行特定测试文件"""
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return 1
    
    return pytest.main([str(test_path), "-v"])


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    test_dir = Path(__file__).parent
    
    args = [
        str(test_dir),
        "-v",
        "--cov=utils",
        "--cov=metrics_collector",
        "--cov-report=html:htmlcov",
        "--cov-report=term"
    ]
    
    return pytest.main(args)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='运行测试套件')
    parser.add_argument('--test', '-t', help='运行特定测试文件 (如: test_incremental)')
    parser.add_argument('--cov', '-c', action='store_true', help='生成覆盖率报告')
    
    args = parser.parse_args()
    
    if args.cov:
        sys.exit(run_with_coverage())
    elif args.test:
        sys.exit(run_specific_test(args.test))
    else:
        sys.exit(run_all_tests())
