#!/usr/bin/env python3
"""
测试实际钉钉通知发送
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/agent-cluster')

from notifiers.dingtalk import ClusterNotifier

# 创建通知器
notifier = ClusterNotifier(
    dingtalk_webhook="https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea",
    dingtalk_secret="SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e"
)

# 测试 PR 就绪通知（这是实际使用的方法）
print("📱 发送 PR 就绪通知测试...")
result = notifier.notify_pr_ready({
    "id": "test-001",
    "description": "在线待办事项管理系统开发",
    "agent": "cluster"
}, {
    "pr_number": 12,
    "pr_url": "https://github.com/phoenixbull/agent-cluster-test/pull/12",
    "status": "ready",
    "has_screenshots": False
})
print(f"PR 就绪通知：{'✅ 成功' if result else '❌ 失败'}")

# 测试任务完成通知
print("\n📱 发送任务完成通知测试...")
result = notifier.notify_task_complete({
    "id": "test-002",
    "description": "Phase 1 需求分析完成",
    "agent": "product-manager"
}, {
    "status": "completed",
    "pr_number": 0,
    "execution_time": 120.5
})
print(f"任务完成通知：{'✅ 成功' if result else '❌ 失败'}")

# 测试需要人工介入通知
print("\n📱 发送人工介入通知测试...")
result = notifier.notify_human_intervention({
    "id": "test-003",
    "description": "Phase 4 测试失败",
    "agent": "tester"
}, {
    "status": "failed",
    "retry_count": 1
}, "测试覆盖率 75% < 80%，发现 2 个高危 Bug")
print(f"人工介入通知：{'✅ 成功' if result else '❌ 失败'}")

print("\n✅ 所有测试完成！请检查钉钉群消息。")
