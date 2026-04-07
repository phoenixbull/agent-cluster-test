#!/bin/bash
# Agent 集群 V2.1 健康检查脚本
# 用于心跳检查，正确识别 302 重定向为正常状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/health_check.log"

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_https() {
    # 检查 HTTPS 443 端口，接受 200 或 302 为正常
    local http_code=$(curl -sk -o /dev/null -w "%{http_code}" https://localhost:443 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
        log "✅ HTTPS (443) 正常 (HTTP: $http_code)"
        return 0
    else
        log "❌ HTTPS (443) 异常 (HTTP: $http_code)"
        return 1
    fi
}

check_web_service() {
    # 检查后端 Web 服务 8890 端口
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8890 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
        log "✅ Web 服务 (8890) 正常 (HTTP: $http_code)"
        return 0
    else
        log "❌ Web 服务 (8890) 异常 (HTTP: $http_code)"
        return 1
    fi
}

check_monitor() {
    # 检查监控脚本日志是否有错误
    if [ -f "$SCRIPT_DIR/monitor.log" ]; then
        local errors=$(tail -20 "$SCRIPT_DIR/monitor.log" | grep -iE "错误|ERROR|异常|FAIL" | wc -l)
        if [ "$errors" -gt 0 ]; then
            log "⚠️ 监控日志发现 $errors 条错误"
            return 1
        fi
    fi
    log "✅ 监控脚本无报错"
    return 0
}

check_nginx() {
    # 检查 nginx 服务状态
    if systemctl is-active --quiet nginx 2>/dev/null; then
        log "✅ nginx 服务运行中"
        return 0
    else
        log "❌ nginx 服务未运行"
        return 1
    fi
}

# 主逻辑
log "========== 健康检查开始 =========="

local_status=0

check_https || local_status=1
check_web_service || local_status=1
check_monitor || local_status=1
check_nginx || local_status=1

if [ $local_status -eq 0 ]; then
    log "🎉 所有检查项通过"
else
    log "⚠️ 部分检查项失败，需要关注"
fi

log "========== 健康检查结束 =========="

exit $local_status
