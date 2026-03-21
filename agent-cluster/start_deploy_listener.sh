#!/bin/bash
# 钉钉部署确认监听器启动脚本
# 支持轮询模式和回调模式

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置
MODE="${1:-callback}"  # 默认回调模式
PORT="${2:-8891}"
TOKEN="${3:-}"  # 可选

echo "============================================================"
echo "📱 钉钉部署确认监听器"
echo "============================================================"
echo ""
echo "模式：$MODE"
echo "端口：$PORT"
echo "工作目录：$SCRIPT_DIR"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 python3"
    exit 1
fi

echo "✅ Python 版本：$(python3 --version)"
echo ""

# 启动监听器
if [ "$MODE" = "callback" ]; then
    echo "🚀 启动回调模式..."
    echo ""
    echo "⚠️  需要在钉钉开放平台配置回调地址:"
    echo "   http://服务器 IP:$PORT/dingtalk/callback"
    echo ""
    echo "📝 配置步骤:"
    echo "   1. 访问 https://open.dingtalk.com"
    echo "   2. 创建企业自建应用"
    echo "   3. 添加权限：群会话消息"
    echo "   4. 配置事件订阅，回调地址填入上面的 URL"
    echo "   5. 复制 Token 并填入启动命令"
    echo ""
    echo "示例命令:"
    echo "   ./start_deploy_listener.sh callback 8891 your_token"
    echo ""
    
    if [ -n "$TOKEN" ]; then
        python3 deploy_listener.py --mode callback --port "$PORT" --token "$TOKEN"
    else
        python3 deploy_listener.py --mode callback --port "$PORT"
    fi
else
    echo "🚀 启动轮询模式..."
    echo ""
    echo "⚠️  轮询模式仅检查待确认部署，无法接收钉钉消息"
    echo "   如需实时接收消息，请使用回调模式"
    echo ""
    
    python3 deploy_listener.py --mode poll
fi
