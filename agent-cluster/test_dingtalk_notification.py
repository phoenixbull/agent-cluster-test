#!/usr/bin/env python3
"""
测试钉钉通知发送
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/agent-cluster')

from notifiers.dingtalk import ClusterNotifier

# 创建通知器
notifier = ClusterNotifier(
    dingtalk_webhook="https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea",
    dingtalk_secret="SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e"
)

# 发送测试通知
print("📱 发送 Phase 完成通知测试...")
result = notifier.notify_phase_complete({
    "phase": "Phase 1",
    "name": "需求分析",
    "output": ["PRD 文档", "用户故事", "验收标准"]
})
print(f"Phase 完成通知：{'✅ 成功' if result else '❌ 失败'}")

print("\n📱 发送 PR 就绪通知测试...")
result = notifier.notify_pr_ready({
    "id": "test-001",
    "description": "测试任务",
    "agent": "cluster"
}, {
    "pr_number": 12,
    "pr_url": "https://github.com/test/pull/12",
    "status": "ready"
})
print(f"PR 就绪通知：{'✅ 成功' if result else '❌ 失败'}")

print("\n📱 发送部署确认通知测试...")
result = notifier.notify_deploy_confirmation({
    "project_name": "测试项目",
    "version": "v1.0.0",
    "environment": "production"
}, {
    "test_summary": {"passed": True, "coverage": 96},
    "review_summary": {"approved": True, "score": 90}
})
print(f"部署确认通知：{'✅ 成功' if result else '❌ 失败'}")

print("\n✅ 所有测试完成！请检查钉钉群消息。")
