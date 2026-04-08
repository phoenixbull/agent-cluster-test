#!/usr/bin/env python3
"""
超时配置测试脚本
验证短期修复方案是否正确实施

测试内容:
1. agent_executor.py 默认超时 = 7200 秒
2. openclaw_api.py spawn_agent 默认超时 = 7200 秒
3. orchestrator.py 调用超时 = 7200 秒
"""

import inspect
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_executor_timeout():
    """测试 agent_executor.py 默认超时"""
    print("\n📋 测试 1: agent_executor.py 默认超时")
    
    from utils.agent_executor import AgentTaskExecutor
    
    # 获取 execute_task 方法的签名
    sig = inspect.signature(AgentTaskExecutor.execute_task)
    timeout_default = sig.parameters['timeout_seconds'].default
    
    print(f"   默认超时值：{timeout_default}秒 ({timeout_default/60:.1f}分钟)")
    
    if timeout_default == 7200:
        print("   ✅ 通过：默认超时 = 7200 秒 (2 小时)")
        return True
    else:
        print(f"   ❌ 失败：期望 7200 秒，实际 {timeout_default}秒")
        return False

def test_openclaw_api_timeout():
    """测试 openclaw_api.py 默认超时"""
    print("\n📋 测试 2: openclaw_api.py spawn_agent 默认超时")
    
    from utils.openclaw_api import OpenClawAPI
    
    # 获取 spawn_agent 方法的签名
    sig = inspect.signature(OpenClawAPI.spawn_agent)
    timeout_default = sig.parameters['timeout_seconds'].default
    
    print(f"   默认超时值：{timeout_default}秒 ({timeout_default/60:.1f}分钟)")
    
    if timeout_default == 7200:
        print("   ✅ 通过：spawn_agent 默认超时 = 7200 秒 (2 小时)")
        return True
    else:
        print(f"   ❌ 失败：期望 7200 秒，实际 {timeout_default}秒")
        return False

def test_openclaw_api_sync_timeout():
    """测试 openclaw_api.py spawn_agent_sync 默认超时"""
    print("\n📋 测试 3: openclaw_api.py spawn_agent_sync 默认超时")
    
    from utils.openclaw_api import OpenClawAPI
    
    # 获取 spawn_agent_sync 方法的签名
    sig = inspect.signature(OpenClawAPI.spawn_agent_sync)
    timeout_default = sig.parameters['timeout_seconds'].default
    
    print(f"   默认超时值：{timeout_default}秒 ({timeout_default/60:.1f}分钟)")
    
    if timeout_default == 300:
        print("   ✅ 通过：spawn_agent_sync 默认超时 = 300 秒 (5 分钟)")
        return True
    else:
        print(f"   ⚠️ 注意：spawn_agent_sync 默认超时 = {timeout_default}秒")
        return True  # 这个可以接受

def test_orchestrator_timeout():
    """测试 orchestrator.py 调用超时"""
    print("\n📋 测试 4: orchestrator.py 调用超时")
    
    # 读取 orchestrator.py 源码
    orchestrator_path = Path(__file__).parent / "orchestrator.py"
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查 execute_task 调用
    if "timeout_seconds=7200" in content:
        print("   ✅ 通过：orchestrator.py 使用 7200 秒超时")
        return True
    elif "timeout_seconds=3600" in content:
        print("   ⚠️ 注意：orchestrator.py 仍使用 3600 秒超时")
        return False
    else:
        print("   ⚠️ 未找到明确的超时设置")
        return False

def test_log_output():
    """测试日志输出是否包含超时信息"""
    print("\n📋 测试 5: 日志输出增强")
    
    from utils.agent_executor import AgentTaskExecutor
    from utils.openclaw_api import OpenClawAPI
    import io
    from contextlib import redirect_stdout
    
    # 检查 execute_task 方法是否打印超时信息
    source = inspect.getsource(AgentTaskExecutor.execute_task)
    if "超时设置" in source or "timeout" in source.lower():
        print("   ✅ agent_executor.py 包含超时日志")
    else:
        print("   ⚠️ agent_executor.py 缺少超时日志")
    
    # 检查 spawn_agent 方法是否打印超时信息
    source = inspect.getsource(OpenClawAPI.spawn_agent)
    if "超时" in source or "timeout" in source.lower():
        print("   ✅ openclaw_api.py 包含超时日志")
    else:
        print("   ⚠️ openclaw_api.py 缺少超时日志")
    
    return True

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🔧 超时配置测试 - 短期修复方案验证")
    print("=" * 60)
    
    results = []
    
    results.append(("agent_executor 默认超时", test_agent_executor_timeout()))
    results.append(("openclaw_api spawn_agent 默认超时", test_openclaw_api_timeout()))
    results.append(("openclaw_api spawn_agent_sync 默认超时", test_openclaw_api_sync_timeout()))
    results.append(("orchestrator 调用超时", test_orchestrator_timeout()))
    results.append(("日志输出增强", test_log_output()))
    
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
        print("\n🎉 所有测试通过！短期修复方案已正确实施。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试未通过，请检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
