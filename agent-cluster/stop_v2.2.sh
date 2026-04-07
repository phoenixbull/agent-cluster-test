#!/bin/bash
# 停止 V2.2 服务脚本

set -e

echo "========================================"
echo "  停止 Agent 集群 V2.2 服务"
echo "========================================"
echo ""

# 停止 Web 服务
echo "🛑 停止 Web 服务..."
pkill -f "web_app_v2.py" || true
pkill -f "web_app.py" || true

# 停止监控脚本
echo "🛑 停止监控脚本..."
pkill -f "monitor.py" || true

# 停止部署监听器
echo "🛑 停止部署监听器..."
pkill -f "deploy_listener.py" || true

# 清理 tmux 会话（可选）
# tmux kill-session -t agent-cluster 2>/dev/null || true

echo ""
echo "✅ 所有服务已停止"
echo ""
echo "📋 下一步:"
echo "   1. 切换版本：./switch_version.sh switch 2.1"
echo "   2. 启动服务：./start_web.sh"
echo ""
