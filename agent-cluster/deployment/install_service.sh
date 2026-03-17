#!/bin/bash
# Agent Cluster systemd 服务安装脚本

set -e

SERVICE_NAME="agent-cluster"
SERVICE_FILE="$(dirname "$0")/agent-cluster.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🔧 安装 Agent Cluster systemd 服务..."

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 复制服务文件
cp "$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_NAME.service"
echo "✅ 服务文件已复制到 $SYSTEMD_DIR/$SERVICE_NAME.service"

# 重新加载 systemd
systemctl daemon-reload
echo "✅ systemd 配置已重载"

# 启用服务（开机自启）
systemctl enable $SERVICE_NAME
echo "✅ 服务已启用（开机自启）"

# 启动服务
systemctl start $SERVICE_NAME
echo "✅ 服务已启动"

# 显示状态
echo ""
echo "📊 服务状态:"
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "💡 常用命令:"
echo "  查看状态：sudo systemctl status $SERVICE_NAME"
echo "  启动服务：sudo systemctl start $SERVICE_NAME"
echo "  停止服务：sudo systemctl stop $SERVICE_NAME"
echo "  重启服务：sudo systemctl restart $SERVICE_NAME"
echo "  查看日志：sudo journalctl -u $SERVICE_NAME -f"
echo "  禁用自启：sudo systemctl disable $SERVICE_NAME"
