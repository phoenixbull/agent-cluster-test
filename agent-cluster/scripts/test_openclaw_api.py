#!/usr/bin/env python3
"""测试 OpenClaw API 真实调用"""

import sys
sys.path.insert(0, 'utils')

from openclaw_api import OpenClawAPI

api = OpenClawAPI()

print("=== 测试 OpenClaw API 真实调用 ===\n")

# 测试 1: 检查 CLI
print("测试 1: 检查 OpenClaw CLI")
print(f"CLI 路径：{api.openclaw_cli}")
print()

# 测试 2: 触发 Agent 执行
print("测试 2: 触发 Agent 执行")
result = api.spawn_agent(
    agent_id="codex",
    task="创建一个简单的 Python 函数，计算两个数的和",
    timeout_seconds=60
)

print(f"\n执行结果:")
print(f"  成功：{result.get('success', False)}")
print(f"  会话密钥：{result.get('session_key', 'N/A')}")
print(f"  输出：{result.get('output', 'N/A')[:200]}...")
print(f"  时间戳：{result.get('timestamp', 'N/A')}")

if result.get('mock'):
    print(f"  ⚠️  这是模拟结果 (CLI 不可用)")
else:
    print(f"  ✅ 这是真实执行结果")

print()

# 测试 3: 查询会话状态
print("测试 3: 查询会话状态")
session_key = result.get('session_key', '')
if session_key:
    status = api.get_session_status(session_key)
    print(f"  状态：{status.get('status', 'unknown')}")
else:
    print(f"  无会话密钥，跳过")

print("\n=== 测试完成 ===")
