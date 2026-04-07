#!/bin/bash
# 快速部署脚本

set -e

echo "========================================"
echo "Agent Cluster 快速部署"
echo "========================================"
echo ""

# 1. 检查环境
echo "=== 1. 检查环境 ==="
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

if ! command -v docker &> /dev/null; then
    echo "⚠️ Docker 未安装（部署功能将不可用）"
fi

# 2. 安装依赖
echo -e "\n=== 2. 安装依赖 ==="
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ requirements.txt 不存在"
    exit 1
fi

# 3. 配置环境变量
echo -e "\n=== 3. 配置环境变量 ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo "⚠️ 请编辑 .env 文件填入实际配置"
else
    echo "✅ .env 文件已存在"
fi

# 4. 选择启动方式
echo -e "\n=== 4. 选择启动方式 ==="
echo "1. 直接启动（同步版本）"
echo "2. 异步版本（需要 fastapi）"
echo "3. 看门狗模式"
echo "4. systemd 服务"
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        echo "启动同步版本..."
        python3 web_app_v2.py --port 8890 &
        ;;
    2)
        echo "启动异步版本..."
        python3 web_app_async.py &
        ;;
    3)
        echo "启动看门狗模式..."
        python3 deployment/watchdog.py web_app_v2.py 8890 &
        ;;
    4)
        echo "配置 systemd 服务..."
        if [ -f deployment/agent-cluster.service ]; then
            sudo cp deployment/agent-cluster.service /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable agent-cluster
            sudo systemctl start agent-cluster
            echo "✅ systemd 服务已启动"
            sudo systemctl status agent-cluster
        else
            echo "❌ service 文件不存在"
            exit 1
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 5. 验证
echo -e "\n=== 5. 验证服务 ==="
sleep 5
if curl -s http://localhost:8890/api/health | grep -q "healthy"; then
    echo "✅ 服务运行正常"
    echo "访问地址：http://localhost:8890"
else
    echo "⚠️ 服务可能未正常启动，请检查日志"
fi

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
