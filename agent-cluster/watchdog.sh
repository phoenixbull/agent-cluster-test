#!/bin/bash
# Web 服务看门狗脚本

LOG_FILE="/home/admin/.openclaw/workspace/agent-cluster/logs/watchdog.log"
PORT=8889
WORKSPACE="/home/admin/.openclaw/workspace/agent-cluster"

# 检查端口是否监听
if ! netstat -tlnp 2>/dev/null | grep -q ":$PORT"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 端口 $PORT 未监听，尝试重启服务..." >> $LOG_FILE
    
    # 杀死旧进程
    pkill -f "web_app.py" 2>/dev/null
    sleep 1
    
    # 启动新进程
    cd $WORKSPACE
    python3 web_app.py --port $PORT >> $LOG_FILE 2>&1 &
    
    sleep 2
    
    # 验证是否启动成功
    if netstat -tlnp 2>/dev/null | grep -q ":$PORT"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 服务已重启" >> $LOG_FILE
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 服务重启失败" >> $LOG_FILE
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 服务运行正常" >> $LOG_FILE
fi
