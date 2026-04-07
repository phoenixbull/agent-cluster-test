#!/usr/bin/env python3
"""测试真实 Agent 调用"""

import sys
sys.path.insert(0, 'utils')

from openclaw_api import OpenClawAPI

api = OpenClawAPI()

print("=== P1: 真实 Agent 调用测试 ===\n")

# 测试 1: Codex 后端专家
print("测试 1: Codex 后端专家 - 创建用户登录 API")
result = api.spawn_agent_sync(
    agent_id='codex',
    task='用 Python Flask 创建一个用户登录 API，包含输入验证和密码加密',
    timeout_seconds=120
)
print(f"  成功：{result.get('success', False)}")
if result.get('success'):
    print(f"  输出预览：{result.get('output', '')[:200]}...")
else:
    print(f"  错误：{result.get('error', '未知')}")
print()

# 测试 2: Reviewer 审查
print("测试 2: Codex Reviewer - 代码审查")
result = api.spawn_agent_sync(
    agent_id='codex-reviewer',
    task='审查以下代码的安全问题：def login(username, password): query = f"SELECT * FROM users WHERE username=\'{username}\'"',
    timeout_seconds=120
)
print(f"  成功：{result.get('success', False)}")
if result.get('success'):
    print(f"  输出预览：{result.get('output', '')[:200]}...")
else:
    print(f"  错误：{result.get('error', '未知')}")
print()

print("=== 测试完成 ===")
