#!/usr/bin/env python3
"""
完整测试钉钉 webhook 功能
"""

import requests
import json

# 读取测试工作流 ID
try:
    with open('/tmp/test_workflow_id.txt', 'r') as f:
        workflow_id = f.read().strip()
except:
    workflow_id = "unknown"

url = "http://127.0.0.1:8890/api/dingtalk/callback"

test_cases = [
    {
        "name": "测试 1: 确认部署（带工作流 ID）",
        "data": {
            "text": {"content": f"确认部署 {workflow_id}"},
            "conversation_id": "test123",
            "sender_id": "user123"
        },
        "expected": "部署已确认"
    },
    {
        "name": "测试 2: 确认（不带 ID，应获取最新）",
        "data": {
            "text": {"content": "确认"},
            "conversation_id": "test123",
            "sender_id": "user123"
        },
        "expected": "部署已确认"
    },
    {
        "name": "测试 3: 部署",
        "data": {
            "text": {"content": "部署"},
            "conversation_id": "test123",
            "sender_id": "user123"
        },
        "expected": "部署已确认"
    },
    {
        "name": "测试 4: 取消部署",
        "data": {
            "text": {"content": "取消部署"},
            "conversation_id": "test123",
            "sender_id": "user123"
        },
        "expected": "部署已取消"
    },
    {
        "name": "测试 5: 未知命令",
        "data": {
            "text": {"content": "这是什么"},
            "conversation_id": "test123",
            "sender_id": "user123"
        },
        "expected": "未知命令"
    }
]

print(f"=== 测试钉钉 webhook 功能 ===\n")
print(f"测试工作流：{workflow_id}\n")

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"{test['name']}")
    print(f"  消息：{test['data']['text']['content']}")
    
    try:
        response = requests.post(url, json=test['data'], timeout=10)
        result = response.json()
        response_text = result.get('text', {}).get('content', 'N/A')
        
        print(f"  状态码：{response.status_code}")
        print(f"  响应：{response_text[:80]}...")
        
        if test['expected'] in response_text:
            print(f"  ✅ 通过\n")
            passed += 1
        else:
            print(f"  ❌ 失败 (期望包含：{test['expected']})\n")
            failed += 1
    except Exception as e:
        print(f"  ❌ 错误：{e}\n")
        failed += 1

print(f"=== 测试结果 ===")
print(f"通过：{passed}/{len(test_cases)}")
print(f"失败：{failed}/{len(test_cases)}")
