#!/usr/bin/env python3
"""
钉钉通知测试脚本
"""

import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from notifiers.dingtalk import DingTalkNotifier, ClusterNotifier


def test_basic_message():
    """测试基本消息发送"""
    print("\n" + "="*60)
    print("测试 1: 发送基本文本消息")
    print("="*60)
    
    webhook = input("\n请输入钉钉机器人 Webhook URL: ")
    secret = input("请输入加签密钥 (可选，直接回车跳过): ")
    
    notifier = DingTalkNotifier(webhook, secret if secret else None)
    
    # 测试文本消息
    result = notifier.send_text(
        content="🤖 Agent 集群通知测试\n\n这是一条测试消息，如果您看到这条消息，说明钉钉通知功能正常工作！",
        at_all=False
    )
    
    if result:
        print("\n✅ 文本消息发送成功！")
    else:
        print("\n❌ 文本消息发送失败")
    
    return result, webhook, secret


def test_pr_ready_notification(webhook: str, secret: str):
    """测试 PR 就绪通知"""
    print("\n" + "="*60)
    print("测试 2: 发送 PR 就绪通知（人工 Review）")
    print("="*60)
    
    notifier = ClusterNotifier(webhook, secret)
    
    task = {
        "id": "test-pr-notification",
        "description": "测试钉钉通知功能",
        "agent": "codex",
        "branch": "test/dingtalk-notification"
    }
    
    result = {
        "pr_number": 999,
        "pr_url": "https://github.com/test/repo/pull/999",
        "status": "ready_for_merge",
        "ci_status": "success",
        "reviews": {"approved": 2},
        "execution_time": 120.5,
        "has_screenshots": False
    }
    
    success = notifier.notify_pr_ready(task, result)
    
    if success:
        print("\n✅ PR 就绪通知发送成功！")
    else:
        print("\n❌ PR 就绪通知发送失败")
    
    return success


def test_task_complete_notification(webhook: str, secret: str):
    """测试任务完成通知"""
    print("\n" + "="*60)
    print("测试 3: 发送任务完成通知")
    print("="*60)
    
    notifier = ClusterNotifier(webhook, secret)
    
    task = {
        "id": "feat-user-auth",
        "description": "实现用户登录功能",
        "agent": "codex",
        "branch": "feat/user-auth"
    }
    
    result = {
        "pr_number": 1000,
        "pr_url": "https://github.com/test/repo/pull/1000",
        "status": "completed",
        "ci_status": "success",
        "reviews": {"approved": 3},
        "execution_time": 1800.0,
        "has_screenshots": True
    }
    
    success = notifier.notify_task_complete(task, result)
    
    if success:
        print("\n✅ 任务完成通知发送成功！")
    else:
        print("\n❌ 任务完成通知发送失败")
    
    return success


def test_task_failed_notification(webhook: str, secret: str):
    """测试任务失败通知"""
    print("\n" + "="*60)
    print("测试 4: 发送任务失败通知（@所有人）")
    print("="*60)
    
    notifier = ClusterNotifier(webhook, secret)
    
    task = {
        "id": "bug-payment-error",
        "description": "修复支付模块 bug",
        "agent": "codex",
        "branch": "fix/payment-bug",
        "retry_count": 3
    }
    
    result = {
        "status": "failed",
        "ci_status": "failed",
        "ci_errors": ["单元测试失败：支付金额计算错误"],
        "execution_time": 3600.0
    }
    
    failure_reason = "CI 失败：单元测试未通过 - 支付金额计算错误"
    
    success = notifier.notify_task_failed(task, result, failure_reason)
    
    if success:
        print("\n✅ 任务失败通知发送成功！")
    else:
        print("\n❌ 任务失败通知发送失败")
    
    return success


def test_human_intervention_notification(webhook: str, secret: str):
    """测试人工介入通知"""
    print("\n" + "="*60)
    print("测试 5: 发送人工介入通知（@所有人）")
    print("="*60)
    
    notifier = ClusterNotifier(webhook, secret)
    
    task = {
        "id": "feat-complex-refactor",
        "description": "重构核心模块",
        "agent": "codex",
        "branch": "refactor/core",
        "retry_count": 3
    }
    
    result = {
        "status": "failed",
        "pr_created": False,
        "error": "代码复杂度太高，超出单次处理范围"
    }
    
    failure_reason = "多次重试失败：任务复杂度过高，需要人工拆解"
    
    success = notifier.notify_human_intervention(task, result, failure_reason)
    
    if success:
        print("\n✅ 人工介入通知发送成功！")
    else:
        print("\n❌ 人工介入通知发送失败")
    
    return success


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🤖 Agent 集群 - 钉钉通知测试")
    print("="*60)
    
    # 测试 1: 基本消息
    success, webhook, secret = test_basic_message()
    
    if not success:
        print("\n❌ 基本消息发送失败，请检查 Webhook URL 和网络连接")
        print("\n配置指南:")
        print("1. 钉钉群 → 群设置 → 智能群助手 → 添加机器人")
        print("2. 复制 Webhook URL")
        print("3. 重新运行测试")
        return False
    
    # 继续测试其他通知类型
    print("\n" + "="*60)
    print("继续测试其他通知类型？(y/n)")
    print("="*60)
    
    choice = input("\n请输入: ").strip().lower()
    
    if choice != 'y':
        print("\n✅ 测试完成")
        return True
    
    # 测试其他通知
    test_pr_ready_notification(webhook, secret)
    test_task_complete_notification(webhook, secret)
    test_task_failed_notification(webhook, secret)
    test_human_intervention_notification(webhook, secret)
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)
    print("\n请检查钉钉群是否收到以下消息:")
    print("1. ✅ 基本文本测试消息")
    print("2. 🎉 PR 就绪通知")
    print("3. ✅ 任务完成通知")
    print("4. ❌ 任务失败通知 (@所有人)")
    print("5. 🚨 人工介入通知 (@所有人)")
    print("\n如果所有消息都正常显示，说明钉钉通知功能配置成功！")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
