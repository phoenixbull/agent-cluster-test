#!/usr/bin/env python3
"""P1/P2: 真实 Agent 调用和 Phase 5 审查集成测试"""

import sys
sys.path.insert(0, 'utils')

from openclaw_api import OpenClawAPI
from phase5_reviewer import Phase5Reviewer

print("=" * 60)
print("P1/P2: 真实 Agent 调用和 Phase 5 审查集成测试")
print("=" * 60)
print()

# ========== P1: 真实 Agent 调用测试 ==========
print("【P1】真实 Agent 调用测试")
print("-" * 60)

api = OpenClawAPI()

# 测试 1: Codex 后端专家
print("\n1. Codex 后端专家 - 创建用户登录 API")
result = api.spawn_agent_sync(
    agent_id='codex',
    task='用 Python Flask 创建一个用户登录 API，包含输入验证和密码加密',
    timeout_seconds=120
)

print(f"   状态：{'✅ 成功' if result.get('success') else '❌ 失败'}")
if result.get('success'):
    output = result.get('output', '')
    print(f"   输出长度：{len(output)} 字符")
    print(f"   预览：{output[:150]}...")
else:
    print(f"   错误：{result.get('error', '未知')}")

# 测试 2: 异步模式
print("\n2. 异步模式测试")
result = api.spawn_agent(
    agent_id='codex',
    task='创建一个 Python 工具函数，用于生成 UUID',
    timeout_seconds=60
)
print(f"   状态：{'✅ 已触发' if result.get('success') else '❌ 失败'}")
print(f"   PID: {result.get('pid', 'N/A')}")
print(f"   会话：{result.get('session_key', 'N/A')}")

print("\n" + "=" * 60)
print("【P2】Phase 5 审查流程测试")
print("-" * 60)

# Phase 5 审查测试
reviewer = Phase5Reviewer()

# 模拟代码文件
test_code_files = [
    {
        "filename": "login_api.py",
        "language": "python",
        "content": """from flask import Flask, request, jsonify
import hashlib

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 简单验证
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 密码加密 (实际应该用 bcrypt)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # TODO: 查询数据库验证
    return jsonify({'message': '登录成功', 'user': username})

if __name__ == '__main__':
    app.run(debug=True)
"""
    }
]

print("\n3. 代码审查 - 登录 API 安全审查")
result = reviewer.execute_review(
    workflow_id="wf-login-review-001",
    code_files=test_code_files,
    pr_info={"title": "添加用户登录 API", "description": "Flask 登录接口实现"}
)

print(f"\n   审查状态：{'✅ 通过' if result['status'] == 'approved' else '❌ 拒绝'}")
print(f"   通过数：{result['approved_count']}/{len(result['reviews'])}")
print(f"   平均分数：{result['summary']['average_score']}")
print(f"   问题总数：{result['summary']['total_issues']}")
print(f"   严重问题：{result['summary']['critical_count']}")

# 显示每个 Reviewer 的结果
print("\n   Reviewer 详情:")
for review in result['reviews']:
    status = '✅' if review.get('status') == 'approved' else '❌'
    print(f"   - {review.get('reviewer_id', 'unknown')}: {status} (评分：{review.get('score', 0)})")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
