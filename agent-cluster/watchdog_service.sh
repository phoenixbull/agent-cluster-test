#!/bin/bash
# AI 产品开发智能体服务守护脚本

SERVICE_NAME="web_app_v2.py"
PORT=8890
LOG_DIR="/home/admin/.openclaw/workspace/agent-cluster/logs"
RESTART_COUNT=0
MAX_RESTART=5

while true; do
    # 检查服务是否运行
    if ! pgrep -f "$SERVICE_NAME" > /dev/null; then
        RESTART_COUNT=$((RESTART_COUNT + 1))
        echo "[$(date)] 服务已停止，尝试重启 (第$RESTART_COUNT 次)" >> $LOG_DIR/watchdog_service.log
        
        if [ $RESTART_COUNT -le $MAX_RESTART ]; then
            # 启动服务
            cd /home/admin/.openclaw/workspace/agent-cluster
            nohup python3 $SERVICE_NAME --host 0.0.0.0 --port $PORT > $LOG_DIR/web_app_v2.log 2>&1 &
            sleep 5
            
            # 检查启动是否成功
            if pgrep -f "$SERVICE_NAME" > /dev/null; then
                echo "[$(date)] 服务重启成功" >> $LOG_DIR/watchdog_service.log
                RESTART_COUNT=0
            else
                echo "[$(date)] 服务重启失败" >> $LOG_DIR/watchdog_service.log
            fi
        else
            echo "[$(date)] 重启次数过多，停止尝试" >> $LOG_DIR/watchdog_service.log
            exit 1
        fi
    fi
    
    # 每 30 秒检查一次
    sleep 30
done
