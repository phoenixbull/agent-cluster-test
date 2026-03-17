#!/usr/bin/env python3
"""
测试钉钉通知流程
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from notifiers.dingtalk import ClusterNotifier

# 加载配置
config_file = Path(__file__).parent / "cluster_config_v2.json"
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 初始化通知器
notifier = ClusterNotifier(config)

print("=== 测试钉钉通知 ===\n")

# 测试 1: PR 就绪通知
print("1️⃣ 测试：PR 就绪通知")
try:
    notifier.notify_pr_ready(
        {
            "id": "wf-test-001",
            "description": "测试需求：创建一个用户登录系统",
            "agent": "cluster",
            "branch": "feature/wf-test-001"
        },
        {
            "pr_number": 42,
            "pr_url": "https://github.com/phoenixbull/agent-cluster-test/pull/42",
            "status": "created",
            "ci_status": "success",
            "reviews": {"approved": 3},
            "has_screenshots": False
        }
    )
    print("   ✅ 已发送\n")
except Exception as e:
    print(f"   ❌ 失败：{e}\n")

# 测试 2: 任务完成通知（无 PR）
print("2️⃣ 测试：任务完成通知（无 PR）")
try:
    notifier.notify_task_complete(
        {
            "id": "wf-test-002",
            "description": "测试需求：项目初始化",
            "agent": "cluster"
        },
        {
            "status": "completed",
            "pr_info": {"pr_number": 0, "message": "GitHub 未配置"},
            "execution_time": 45.5
        }
    )
    print("   ✅ 已发送\n")
except Exception as e:
    print(f"   ❌ 失败：{e}\n")

# 测试 3: 需要人工介入
print("3️⃣ 测试：需要人工介入通知")
try:
    notifier.notify_human_intervention(
        {
            "id": "wf-test-003",
            "description": "测试需求：失败测试",
            "agent": "cluster"
        },
        {"status": "failed"},
        "测试失败原因：模拟错误"
    )
    print("   ✅ 已发送\n")
except Exception as e:
    print(f"   ❌ 失败：{e}\n")

print("=== 所有测试完成 ===")
