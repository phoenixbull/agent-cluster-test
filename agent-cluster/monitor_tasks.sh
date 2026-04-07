#!/bin/bash
# Agent 集群任务监控脚本
# 每 10 分钟检查一次任务状态，有问题时发送钉钉通知

LOG_FILE="/home/admin/.openclaw/workspace/agent-cluster/monitor_tasks.log"
SESSIONS_FILE="/home/admin/.openclaw/workspace/agent-cluster/memory/sessions.json"
DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea"
DINGTALK_SECRET="SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

send_dingtalk() {
    local title="$1"
    local content="$2"
    local at_all="$3"
    
    # 生成签名
    timestamp=$(date +%s000)
    sign=$(echo -n "${timestamp}\n${DINGTALK_SECRET}" | openssl dgst -sha256 -hmac "${DINGTALK_SECRET}" -binary | base64)
    
    if [ "$at_all" = "true" ]; then
        at_json='"isAll": true,'
    else
        at_json='"isAll": false,'
    fi
    
    curl "$DINGTALK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
            \"msgtype\": \"markdown\",
            \"markdown\": {
                \"title\": \"$title\",
                \"text\": \"$content\"
            },
            \"at\": {
                $at_json
                \"isAll\": false
            }
        }" >> /dev/null 2>&1
    
    log "钉钉通知已发送：$title"
}

check_tasks() {
    log "开始检查任务状态..."
    
    # 检查 sessions.json 是否存在
    if [ ! -f "$SESSIONS_FILE" ]; then
        log "错误：sessions.json 不存在"
        send_dingtalk "⚠️ Agent 集群监控告警" "## Agent 集群监控告警\n\n**问题**: 任务状态文件不存在\n\n**文件**: $SESSIONS_FILE\n\n**建议**: 检查集群是否正常运行" "true"
        return 1
    fi
    
    # 解析任务状态（简单检查）
    if ! python3 -c "import json; json.load(open('$SESSIONS_FILE'))" 2>/dev/null; then
        log "错误：sessions.json 格式错误"
        send_dingtalk "⚠️ Agent 集群监控告警" "## Agent 集群监控告警\n\n**问题**: 任务状态文件格式错误\n\n**文件**: $SESSIONS_FILE\n\n**建议**: 检查 JSON 格式" "true"
        return 1
    fi
    
    # 检查任务状态
    status=$(python3 -c "
import json
with open('$SESSIONS_FILE') as f:
    data = json.load(f)
    sessions = data.get('active_sessions', [])
    failed = [s for s in sessions if s.get('status') == 'failed']
    running = [s for s in sessions if s.get('status') == 'running']
    completed = [s for s in sessions if s.get('status') == 'completed']
    print(f'{len(running)},{len(failed)},{len(completed)}')
" 2>/dev/null)
    
    if [ -z "$status" ]; then
        log "错误：无法解析任务状态"
        send_dingtalk "⚠️ Agent 集群监控告警" "## Agent 集群监控告警\n\n**问题**: 无法解析任务状态\n\n**建议**: 手动检查集群状态" "true"
        return 1
    fi
    
    running=$(echo "$status" | cut -d',' -f1)
    failed=$(echo "$status" | cut -d',' -f2)
    completed=$(echo "$status" | cut -d',' -f3)
    
    log "任务状态：运行中=$running, 失败=$failed, 完成=$completed"
    
    # 如果有失败任务，发送通知
    if [ "$failed" -gt 0 ]; then
        send_dingtalk "🔴 Agent 集群任务失败" "## 🔴 Agent 集群任务失败\n\n**失败任务数**: $failed\n**运行中**: $running\n**已完成**: $completed\n\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\n\n**建议**: 立即检查集群日志" "true"
    elif [ "$running" -eq 0 ] && [ "$completed" -gt 0 ]; then
        send_dingtalk "✅ Agent 集群任务完成" "## ✅ Agent 集群任务完成\n\n**所有任务已完成**\n\n**完成数**: $completed\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\n\n**PR 地址**: https://github.com/phoenixbull/agent-cluster-test/pulls" "false"
    else
        log "任务正常进行中：$running 个运行中，$completed 个已完成"
    fi
    
    return 0
}

# 主程序
log "========== 监控检查开始 =========="
check_tasks
log "========== 监控检查结束 =========="
