#!/bin/bash
# Agent Cluster 开机自启脚本
# 部署方法:
# 1. cp /home/admin/.openclaw/workspace/agent-cluster/deployment/startup.sh /usr/local/bin/agent-cluster-start
# 2. chmod +x /usr/local/bin/agent-cluster-start
# 3. 添加到 crontab: @reboot /usr/local/bin/agent-cluster-start

# 等待网络就绪
sleep 10

# 停止可能存在的旧进程
pkill -f "web_app_v2.py" 2>/dev/null
pkill -f "dingtalk_notifier.py" 2>/dev/null
sleep 2

# 启动 Web 服务
cd /home/admin/.openclaw/workspace/agent-cluster
nohup python3 web_app_v2.py --port 8890 > logs/web_app_v2.log 2>&1 &
echo "✅ Agent Cluster Web 服务已启动"

# 等待 Web 服务启动
sleep 5

# 启动钉钉通知服务
cd /home/admin/.openclaw/workspace/agent-cluster/monitoring
nohup python3 dingtalk_notifier.py > dingtalk_notifier.log 2>&1 &
echo "✅ 钉钉通知服务已启动"

# 验证服务
sleep 3
curl -s http://localhost:8890/health > /dev/null && echo "✅ 健康检查通过" || echo "⚠️ 健康检查失败"
