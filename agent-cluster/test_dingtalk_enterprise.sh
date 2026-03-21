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
    print(f'   有效期至：{notifier.token_expires_at}')
except Exception as e:
    print(f'   ❌ 获取 Token 失败：{e}')
    exit(1)
"
echo ""

# 测试 3: 发送测试消息（需要配置正确的 userId）
echo "3️⃣  测试发送消息..."
python3 << 'PYTHON'
from notifiers.dingtalk import DingTalkNotifier
import json

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

notifier = DingTalkNotifier(config)

# 获取配置的 admin_user_ids
admin_ids = config.get('admin_user_ids', [])

if not admin_ids:
    print('   ⚠️  未配置 admin_user_ids，跳过个人消息测试')
    print('   💡 提示：请在 cluster_config_v2.json 中配置正确的钉钉用户 ID')
    print('   示例："admin_user_ids": ["your-dingtalk-user-id"]')
    print()
    print('   获取用户 ID 的方法:')
    print('   1. 钉钉管理后台 → 通讯录 → 找到用户 → 复制 userId')
    print('   2. 或通过 API: GET /v1.0/users/{unionId}')
else:
    print(f'   使用用户 ID: {admin_ids}')
    success = notifier.dingtalk.send_markdown(
        admin_ids,
        '🧪 测试消息',
        '## 🧪 钉钉企业应用通知测试\n\n**时间**: 测试中\n\n这是一条测试消息。',
        at_all=False
    )
    if success:
        print('   ✅ 测试消息发送成功')
    else:
        print('   ❌ 测试消息发送失败')
        print('   可能原因:')
        print('   1. userId 不正确（需要用钉钉 userId，不是用户名）')
        print('   2. 用户不在应用可见范围内')
        print('   3. 用户已被禁用')
PYTHON
echo ""

# 测试 4: 群消息测试（如果配置了群 ID）
echo "4️⃣  测试群消息..."
python3 << 'PYTHON'
from notifiers.dingtalk import DingTalkNotifier
import json

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

notifier = DingTalkNotifier(config)
group_id = config.get('deploy_group_conversation_id', '')

if not group_id:
    print('   ⚠️  未配置 deploy_group_conversation_id，跳过群消息测试')
    print('   💡 提示：如需发送群消息，请配置群会话 ID')
    print()
    print('   获取群会话 ID 的方法:')
    print('   1. 在钉钉群 @机器人 发送任意消息')
    print('   2. 查看 OpenClaw 日志：openclaw logs | grep dingtalk')
    print('   3. 找到 conversationId 字段（格式：cid_xxxxxx）')
else:
    print(f'   使用群 ID: {group_id}')
    success = notifier.dingtalk.send_to_group(
        group_id,
        '🧪 群消息测试',
        '## 🧪 钉钉群消息测试\n\n**时间**: 测试中\n\n这是一条群消息测试。',
        at_all=False
    )
    if success:
        print('   ✅ 群消息发送成功')
    else:
        print('   ❌ 群消息发送失败')
PYTHON
echo ""

echo "======================================"
echo "测试完成！"
echo "======================================"
echo ""
echo "📝 下一步:"
echo "   1. 配置正确的 admin_user_ids 或 deploy_group_conversation_id"
echo "   2. 重启 Web 服务：pkill -f web_app_v2.py && python3 web_app_v2.py --port 8890 &"
echo "   3. 查看日志：tail -f logs/web_app.log"
echo ""
