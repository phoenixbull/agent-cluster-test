#!/usr/bin/env python3
"""
测试钉钉 webhook 接口
模拟钉钉发送确认消息
"""

import requests
import json

# Webhook URL
url = "http://127.0.0.1:8890/api/dingtalk/callback"

# 测试消息
test_messages = [
    {
        "name": "确认部署",
        "data": {
            "text": {"content": "确认部署 wf-20260315-183840-b6bb"},
            "conversation_id": "test123",
            "sender_id": "user123"
        }
    },
    {
        "name": "确认",
        "data": {
            "text": {"content": "确认"},
            "conversation_id": "test123",
            "sender_id": "user123"
        }
    },
    {
        "name": "部署",
        "data": {
            "text": {"content": "部署"},
            "conversation_id": "test123",
            "sender_id": "user123"
        }
    },
    {
        "name": "取消部署",
        "data": {
            "text": {"content": "取消部署"},
            "conversation_id": "test123",
            "sender_id": "user123"
        }
    }
]

print("=== 测试钉钉 webhook 接口 ===\n")

for test in test_messages:
    print(f"测试：{test['name']}")
    print(f"消息：{test['data']['text']['content']}")
    
    try:
        response = requests.post(url, json=test['data'], timeout=10)
        result = response.json()
        
        print(f"状态码：{response.status_code}")
        print(f"响应：{result.get('text', {}).get('content', 'N/A')}")
        print()
    except Exception as e:
        print(f"❌ 错误：{e}")
        print()

print("=== 测试完成 ===")
