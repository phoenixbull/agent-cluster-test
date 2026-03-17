#!/bin/bash
# 启动钉钉部署确认监听器
# 独立进程，不影响其他功能

echo "========================================"
echo "📱 启动钉钉部署确认监听器"
echo "========================================"

cd /home/admin/.openclaw/workspace/agent-cluster

# 后台运行监听器
nohup python3 deploy_listener.py > /tmp/deploy_listener.log 2>&1 &

PID=$!
echo "✅ 监听器已启动"
echo "PID: $PID"
echo ""
echo "📝 日志文件：/tmp/deploy_listener.log"
echo "📋 查看日志：tail -f /tmp/deploy_listener.log"
echo "⏹️  停止监听：kill $PID"
echo ""
echo "========================================"
echo "监听器功能:"
echo "  - 自动接收钉钉消息"
echo "  - 识别'部署'命令"
echo "  - 自动触发部署"
echo "  - 发送部署通知"
echo "========================================"
echo ""
echo "⏱️  监听间隔：30 秒"
echo "⏱️  超时时间：30 分钟"
echo ""
