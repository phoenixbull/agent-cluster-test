#!/usr/bin/env python3
"""测试飞书通知"""

from notifier_sender import send_to_feishu

result = send_to_feishu(
    'ou_8c9dae59c67ad5cede6a3711512c69e7',
    '**🧪 飞书通知测试**\n\n这是一条测试消息。\n\n- 发送时间：2026-04-07\n- 测试类型：飞书通知集成\n- 目标用户：老五\n\n---\n\n🤖 Agent 集群自动通知'
)
print(f'测试结果：{result}')
