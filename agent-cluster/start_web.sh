#!/bin/bash
# Agent 集群 Web 界面启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 默认端口
PORT=${1:-8889}
HOST=${2:-""}

# 获取本机 IP
HOST_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "获取 IP 失败")

echo "🚀 启动 Agent 集群 Web 界面..."
echo "📁 工作目录：$SCRIPT_DIR"
echo ""
echo "🌐 访问地址:"
echo "   本地访问：http://localhost:$PORT"
echo "   外网访问：http://$HOST_IP:$PORT"
echo ""
echo "🔒 绑定地址：所有网络接口 (0.0.0.0)"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动 Web 服务 (绑定所有接口)
python3 web_app.py --port "$PORT" --host "$HOST"
