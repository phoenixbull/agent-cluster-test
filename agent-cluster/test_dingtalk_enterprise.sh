#!/bin/bash
# 钉钉企业应用通知测试脚本

set -e

echo "======================================"
echo "📧 钉钉企业应用通知测试"
echo "======================================"
echo ""

cd /home/admin/.openclaw/workspace/agent-cluster

# 测试 1: 语法检查
echo "1️⃣  语法检查..."
python3 -m py_compile notifiers/dingtalk.py
echo "   ✅ 语法检查通过"
echo ""

# 测试 2: 获取 Token
echo "2️⃣  测试获取访问令牌..."
python3 -c "
from notifiers.dingtalk import DingTalkNotifier
import json

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

notifier = DingTalkNotifier(config)
try:
    token = notifier._get_access_token()
    print(f'   ✅ 获取 Token 成功：{token[:20]}...')
except Exception as e:
    print(f'   ❌ 获取 Token 失败：{e}')
    exit(1)
"
echo ""

# 测试 3: 发送测试消息
echo "3️⃣  发送测试消息..."
python3 -c "
from notifiers.dingtalk import get_notifier
import json

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

notifier = get_notifier(config)

# 测试发送
success = notifier.dingtalk.send_markdown(
    ['admin'],
    '🧪 测试消息',
    '## 🧪 钉钉企业应用通知测试\\n\\n**时间**: 测试中\\n\\n这是一条测试消息。',
    at_all=False
)

if success:
    print('   ✅ 测试消息发送成功')
else:
    print('   ❌ 测试消息发送失败')
"
echo ""

echo "======================================"
echo "测试完成！"
echo "======================================"
echo ""
echo "📝 查看日志：tail -f logs/web_app.log"
echo ""
