#!/bin/bash
# 钉钉回调测试脚本
# 用于测试钉钉消息接收功能

set -e

WEB_URL="http://localhost:8890/api/dingtalk/callback"
TOKEN="openclaw_callback_token_2026"

echo "======================================"
echo "📱 钉钉回调测试脚本"
echo "======================================"
echo ""

# 测试 1: GET 回调验证
echo "1️⃣  测试回调验证（GET）..."
TIMESTAMP=$(date +%s000)
NONCE=$(openssl rand -hex 16)
SIGNATURE=$(echo -en "${TIMESTAMP}\n${NONCE}\n${TOKEN}" | openssl dgst -sha256 -hmac "${TOKEN}" | awk '{print $2}')

GET_URL="${WEB_URL}?signature=${SIGNATURE}&timestamp=${TIMESTAMP}&nonce=${NONCE}&echostr=TEST_ECHOSTR"

echo "   URL: ${GET_URL}"
RESPONSE=$(curl -s -w "\n%{http_code}" "${GET_URL}" || echo "FAILED")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 回调验证成功 (HTTP $HTTP_CODE)"
    echo "   返回：$BODY"
else
    echo "   ❌ 回调验证失败 (HTTP $HTTP_CODE)"
    echo "   响应：$BODY"
fi

echo ""

# 测试 2: POST 消息
echo "2️⃣  测试消息接收（POST）..."

# 创建测试消息
TEST_DATA='{
  "msgtype": "text",
  "text": {
    "content": "部署"
  },
  "senderId": "test_user_001",
  "senderNick": "测试用户",
  "conversationId": "test_conv_001",
  "timestamp": "'"$(date -Iseconds)"'"
}'

# 计算签名
TIMESTAMP=$(date +%s000)
NONCE=$(openssl rand -hex 16)
SIGNATURE=$(echo -en "${TIMESTAMP}\n${NONCE}\n${TOKEN}" | openssl dgst -sha256 -hmac "${TOKEN}" | awk '{print $2}')

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-ding-signature: ${SIGNATURE}" \
  -H "x-ding-timestamp: ${TIMESTAMP}" \
  -H "x-ding-nonce: ${NONCE}" \
  -d "${TEST_DATA}" \
  "${WEB_URL}" || echo "FAILED")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 消息接收成功 (HTTP $HTTP_CODE)"
    echo "   响应：$BODY"
else
    echo "   ❌ 消息接收失败 (HTTP $HTTP_CODE)"
    echo "   响应：$BODY"
fi

echo ""

# 测试 3: 无效签名
echo "3️⃣  测试签名验证（应失败）..."

INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-ding-signature: invalid_signature" \
  -H "x-ding-timestamp: ${TIMESTAMP}" \
  -H "x-ding-nonce: ${NONCE}" \
  -d "${TEST_DATA}" \
  "${WEB_URL}" || echo "FAILED")

INVALID_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)

if [ "$INVALID_CODE" = "403" ]; then
    echo "   ✅ 签名验证正确拒绝 (HTTP $INVALID_CODE)"
else
    echo "   ⚠️  签名验证未生效 (HTTP $INVALID_CODE)"
fi

echo ""
echo "======================================"
echo "测试完成！"
echo "======================================"
echo ""
echo "📝 查看日志：tail -f logs/web_app.log"
echo ""
