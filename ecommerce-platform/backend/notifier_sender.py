#!/usr/bin/env python3
"""
通知发送器 - 实际发送消息到飞书
通过 OpenClaw sessions_send API
"""

import json
import sys
from pathlib import Path

# 添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def send_to_feishu(user_id: str, message: str) -> bool:
    """
    发送消息到飞书
    
    Args:
        user_id: 飞书用户 ID (open_id)
        message: 消息内容 (Markdown)
    
    Returns:
        是否成功
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('feishu_notifier')
    
    try:
        import subprocess
        
        logger.info(f"📧 准备发送飞书消息到：{user_id}")
        logger.info(f"📝 消息内容：{message[:100]}...")
        
        # 使用 openclaw message send 命令
        cmd = [
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', f'user:{user_id}',
            '--message', message
        ]
        
        logger.info(f"🔧 执行命令：{' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        
        logger.info(f"📊 返回码：{result.returncode}")
        logger.info(f"📤 STDOUT: {result.stdout[:500] if result.stdout else '(空)'}")
        logger.info(f"📤 STDERR: {result.stderr[:500] if result.stderr else '(空)'}")
        
        if result.returncode == 0:
            logger.info(f"✅ 飞书消息已发送到：{user_id}")
            print(f"✅ 飞书消息已发送到：{user_id}")
            return True
        else:
            error_msg = result.stderr[:200] if result.stderr else '未知错误'
            logger.error(f"❌ 飞书发送失败：{error_msg}")
            print(f"❌ 飞书发送失败：{error_msg}")
            return False
        
    except subprocess.TimeoutExpired:
        logger.error("❌ 飞书发送超时 (30 秒)")
        print("❌ 飞书发送超时 (30 秒)")
        return False
    except Exception as e:
        logger.error(f"❌ 飞书发送异常：{e}")
        print(f"❌ 飞书发送异常：{e}")
        return False


def send_notification(channels: list, user_ids: dict, title: str, content: str) -> dict:
    """
    发送通知到多个渠道
    
    Args:
        channels: 渠道列表 ['feishu', 'dingtalk']
        user_ids: 用户 ID 字典 {'feishu': 'xxx', 'dingtalk': 'yyy'}
        title: 消息标题
        content: 消息内容
    
    Returns:
        发送结果字典
    """
    results = {}
    
    # 构建完整消息
    full_message = f"**{title}**\n\n{content}"
    
    print(f"\n📧 开始发送通知")
    print(f"   标题：{title}")
    print(f"   渠道：{channels}")
    print(f"   用户 ID: {user_ids}")
    
    for channel in channels:
        user_id = user_ids.get(channel)
        if not user_id:
            print(f"⚠️  跳过 {channel} - 未配置用户 ID")
            results[channel] = "skipped"
            continue
        
        print(f"\n   📤 发送到 {channel}...")
        
        if channel == "feishu":
            success = send_to_feishu(user_id, full_message)
        else:
            print(f"⚠️  未知渠道：{channel}")
            results[channel] = "unknown"
            continue
        
        results[channel] = "sent" if success else "failed"
        print(f"   结果：{results[channel]}")
    
    # 汇总结果
    print(f"\n📊 发送汇总:")
    for channel, status in results.items():
        icon = "✅" if status == "sent" else "⚠️" if status == "skipped" else "❌"
        print(f"   {icon} {channel}: {status}")
    
    return results


# 测试函数
if __name__ == "__main__":
    # 测试飞书通知
    test_user = "ou_8c9dae59c67ad5cede6a3711512c69e7"
    
    result = send_notification(
        channels=["feishu"],
        user_ids={"feishu": test_user},
        title="🧪 飞书通知测试",
        content="""
这是一条测试消息。

- 发送时间：2026-04-07
- 测试类型：飞书通知集成
- 目标用户：老五

---

🤖 Agent 集群自动通知
"""
    )
    
    print(f"\n测试结果：{result}")
