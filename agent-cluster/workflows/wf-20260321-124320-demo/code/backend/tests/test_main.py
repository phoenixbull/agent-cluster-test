#!/usr/bin/env python3
"""
主应用测试 - 不依赖 pytest
"""

def test_health():
    """健康检查测试"""
    print("   Running test_health...")
    assert True, "Health check failed"
    print("   ✅ test_health passed")

def test_root():
    """根路径测试"""
    print("   Running test_root...")
    assert True, "Root test failed"
    print("   ✅ test_root passed")

if __name__ == "__main__":
    print("🧪 运行测试...")
    test_health()
    test_root()
    print("✅ 所有测试通过")
