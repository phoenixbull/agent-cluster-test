#!/bin/bash
# Agent 集群版本切换脚本 - V2.2

set -e

WORKSPACE="/home/admin/.openclaw/workspace/agent-cluster"
cd "$WORKSPACE"

echo "========================================"
echo "  Agent 集群版本切换工具"
echo "========================================"
echo ""

# 检测当前版本
detect_current_version() {
    if [ -f "cluster_config_v2.2.json" ] && [ -L "cluster_config.json" ]; then
        LINK_TARGET=$(readlink cluster_config.json)
        if [[ "$LINK_TARGET" == *"v2.2"* ]]; then
            echo "2.2"
            return
        fi
    fi
    
    if [ -f "cluster_config_v2.json" ] && [ -f "cluster_config_v2.json.backup" ]; then
        # 检查配置内容
        if grep -q '"version": "2.2"' cluster_config.json 2>/dev/null; then
            echo "2.2"
        elif grep -q '"version": "2.0"' cluster_config.json 2>/dev/null; then
            echo "2.1"
        else
            echo "unknown"
        fi
    else
        echo "unknown"
    fi
}

# 切换到指定版本
switch_to_version() {
    local target_version=$1
    
    echo "🔄 切换到 V${target_version}..."
    echo ""
    
    case $target_version in
        "2.2")
            # 备份当前配置
            cp cluster_config.json cluster_config.json.active 2>/dev/null || true
            
            # 使用 V2.2 配置
            cp cluster_config_v2.2.json cluster_config.json
            
            echo "✅ 已切换到 V2.2"
            echo ""
            echo "📋 V2.2 新功能:"
            echo "   - 修复监控脚本空文件问题"
            echo "   - DevOps 多环境部署支持"
            echo "   - 一键回滚机制"
            echo "   - 项目任务看板"
            echo "   - 时间估算工具"
            ;;
        
        "2.1")
            # 备份当前配置
            cp cluster_config.json cluster_config.json.active 2>/dev/null || true
            
            # 恢复 V2.1 配置
            cp cluster_config_v2.json.backup cluster_config.json
            
            echo "✅ 已回滚到 V2.1"
            echo ""
            echo "📋 V2.1 功能:"
            echo "   - 10 个 Agent 协作"
            echo "   - 6 阶段开发流程"
            echo "   - 钉钉通知集成"
            echo "   - 质量门禁"
            ;;
        
        *)
            echo "❌ 未知版本：$target_version"
            echo "   可用版本：2.1, 2.2"
            exit 1
            ;;
    esac
    
    echo ""
    echo "⚠️  请重启服务使配置生效:"
    echo "   ./stop_v2.2.sh  # 停止当前服务"
    echo "   ./start_web.sh  # 启动服务"
    echo ""
}

# 显示帮助
show_help() {
    echo "用法：$0 [command] [version]"
    echo ""
    echo "命令:"
    echo "  status          显示当前版本状态"
    echo "  switch <ver>    切换到指定版本 (2.1 或 2.2)"
    echo "  list            列出可用版本"
    echo "  help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status       # 查看当前版本"
    echo "  $0 switch 2.2   # 切换到 V2.2"
    echo "  $0 switch 2.1   # 回滚到 V2.1"
    echo ""
}

# 列出可用版本
list_versions() {
    echo "可用版本:"
    echo ""
    
    if [ -f "cluster_config_v2.json.backup" ]; then
        echo "  V2.1  ✅ (生产就绪)"
        echo "       文件：cluster_config_v2.json.backup"
    fi
    
    if [ -f "cluster_config_v2.2.json" ]; then
        echo "  V2.2  🚧 (开发中)"
        echo "       文件：cluster_config_v2.2.json"
        echo "       新功能：多环境部署、自动回滚、项目管理"
    fi
    
    echo ""
}

# 主逻辑
case "${1:-status}" in
    "status")
        CURRENT=$(detect_current_version)
        echo "当前版本：V${CURRENT}"
        echo ""
        
        if [ "$CURRENT" == "2.2" ]; then
            echo "🟢 运行的是 V2.2 (最新版)"
        elif [ "$CURRENT" == "2.1" ]; then
            echo "🟡 运行的是 V2.1 (稳定版)"
        else
            echo "⚠️  版本状态未知"
        fi
        ;;
    
    "switch")
        if [ -z "$2" ]; then
            echo "❌ 请指定目标版本"
            echo "   用法：$0 switch <version>"
            echo "   示例：$0 switch 2.2"
            exit 1
        fi
        switch_to_version "$2"
        ;;
    
    "list")
        list_versions
        ;;
    
    "help"|"--help"|"-h")
        show_help
        ;;
    
    *)
        echo "❌ 未知命令：$1"
        show_help
        exit 1
        ;;
esac
