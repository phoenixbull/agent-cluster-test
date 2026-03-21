#!/usr/bin/env python3
"""
钉钉群会话 ID 捕获工具

使用方法:
1. 运行此脚本：python3 capture_conversation_id.py
2. 在钉钉群里 @机器人 发送任意消息
3. 脚本会显示完整的消息信息，包括 conversationId
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("📱 钉钉群会话 ID 捕获工具")
print("=" * 60)
print()
print("📋 使用步骤:")
print("   1. 保持此脚本运行")
print("   2. 在钉钉群里 @机器人 发送任意消息")
print("   3. 查看下方输出的 conversationId")
print()
print("💡 提示：如果消息来自私聊，conversationType 会是 'single'")
print("         如果消息来自群聊，conversationType 会是 'group'")
print()
print("等待消息中... (按 Ctrl+C 退出)")
print("-" * 60)

# 读取最新的 OpenClaw 日志
import subprocess
import time

last_msg_id = None

while True:
    try:
        # 获取最新日志
        result = subprocess.run(
            ['openclaw', 'logs'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.split('\n')
        
        for line in lines[-50:]:  # 检查最后 50 行
            if 'Inbound' in line and 'dingtalk' in line.lower():
                # 解析日志
                if 'text=' in line:
                    # 提取消息内容
                    text_start = line.find('text="')
                    if text_start > 0:
                        text = line[text_start+6:text_start+50]
                        print(f"\n📨 收到消息：{text}...")
                        
                        # 提示用户查看完整日志
                        print("\n📋 请运行以下命令查看完整的 conversationId:")
                        print("   openclaw logs --max-bytes 100000 | grep -A 5 'Inbound' | tail -30")
                        print()
                        print("   或者查看网关日志文件:")
                        print("   cat /home/admin/.openclaw/gateway/logs/gateway.log | tail -50")
                        break
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  已退出")
        break
    except Exception as e:
        print(f"错误：{e}")
        time.sleep(2)
