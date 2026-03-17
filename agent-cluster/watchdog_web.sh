#!/bin/bash
# Agent 集群 V2.1 Web 服务看门狗
# 检查 Web 服务是否正常，异常时自动重启

# 不使用 set -e，避免命令失败导致脚本提前退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/watchdog_web.log"
PORT=8890
MAX_RESTART_ATTEMPTS=3
RESTART_COOLDOWN=60  # 重启冷却时间 (秒)

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_web_service() {
    # 检查进程是否存在 (宽松匹配)
    if ! pgrep -f "web_app_v2.py" > /dev/null 2>&1; then
        log "⚠️ 检查失败：进程不存在"
        return 1
    fi
    
    # 检查 HTTP 响应
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "000" ] || [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
        log "⚠️ 检查失败：HTTP 状态异常 ($HTTP_CODE)"
        return 1
    fi
    
    return 0
}

restart_web_service() {
    log "🔄 尝试重启 Web 服务..."
    
    # 停止所有旧进程 (更彻底)
    pkill -9 -f "web_app_v2.py" 2>/dev/null || true
    sleep 3
    
    # 启动新进程 (绑定所有接口)
    cd "$SCRIPT_DIR"
    nohup python3 web_app_v2.py --host 0.0.0.0 --port $PORT >> logs/web_app_v2.1.log 2>&1 &
    local new_pid=$!
    
    sleep 5
    
    # 验证启动是否成功 (检查进程和 HTTP 响应)
    if pgrep -f "web_app_v2.py" > /dev/null 2>&1; then
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
        if [ "$http_code" != "000" ] && [ "$http_code" != "502" ] && [ "$http_code" != "503" ]; then
            log "✅ Web 服务重启成功 (PID: $new_pid, HTTP: $http_code)"
            return 0
        fi
    fi
    
    log "❌ Web 服务重启失败 (HTTP: $http_code)"
    return 1
}

# 主逻辑
log "========== Web 服务健康检查开始 =========="

if check_web_service; then
    log "✅ Web 服务正常 (端口: $PORT)"
    exit 0
else
    log "⚠️ Web 服务异常，开始恢复..."
    
    # 记录重启时间到临时文件，防止频繁重启
    RESTART_RECORD="/tmp/web_watchdog_last_restart"
    CURRENT_TIME=$(date +%s)
    
    if [ -f "$RESTART_RECORD" ]; then
        LAST_RESTART=$(cat "$RESTART_RECORD")
        TIME_DIFF=$((CURRENT_TIME - LAST_RESTART))
        
        if [ $TIME_DIFF -lt $RESTART_COOLDOWN ]; then
            log "⏳ 距离上次重启仅 ${TIME_DIFF}秒，等待冷却期 (${RESTART_COOLDOWN}秒)"
            exit 1
        fi
    fi
    
    # 执行重启
    if restart_web_service; then
        echo "$CURRENT_TIME" > "$RESTART_RECORD"
        log "🎉 服务已恢复"
    else
        log "🚨 服务重启失败，需要人工介入"
        # 这里可以添加钉钉通知
    fi
fi

log "========== Web 服务健康检查结束 =========="
