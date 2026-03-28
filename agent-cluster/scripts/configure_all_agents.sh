#!/bin/bash
# 批量配置所有工作流 Agent

set -e

echo "======================================================================"
echo "🔧 批量配置工作流 Agent"
echo "======================================================================"
echo ""

# Agent 配置映射表：agent_id:model
declare -A AGENTS=(
    # Phase 1: 需求分析
    ["product-manager"]="alibaba-cloud/qwen-plus"
    
    # Phase 2: 技术设计
    ["tech-lead"]="alibaba-cloud/qwen3.5-plus"
    ["designer"]="alibaba-cloud/qwen-vl-plus"
    
    # Phase 3: 编码实现
    ["claude-code"]="alibaba-cloud/qwen3.5-plus"
    ["mobile-ios"]="alibaba-cloud/qwen3.5-plus"
    ["mobile-android"]="alibaba-cloud/qwen3.5-plus"
    ["mobile-react-native"]="alibaba-cloud/qwen3.5-plus"
    ["mobile-flutter"]="alibaba-cloud/qwen3.5-plus"
    
    # Phase 4: 测试
    ["tester"]="alibaba-cloud/qwen-coder-plus"
    ["mobile-tester"]="alibaba-cloud/qwen-coder-plus"
)

# 遍历配置
for agent_id in "${!AGENTS[@]}"; do
    model="${AGENTS[$agent_id]}"
    
    echo "配置 $agent_id ($model)..."
    
    # 检查是否已存在
    if openclaw agents list 2>&1 | grep -q "^- $agent_id$"; then
        echo "  ⚠️  $agent_id 已存在，跳过"
    else
        # 创建 Agent
        openclaw agents add "$agent_id" \
            --model "$model" \
            --workspace "/home/admin/.openclaw/workspace/agent-cluster/agents/$agent_id" \
            --agent-dir "/home/admin/.openclaw/agents/$agent_id" \
            --non-interactive 2>&1 | tail -3
        
        echo "  ✅ $agent_id 配置完成"
    fi
    echo ""
done

echo "======================================================================"
echo "✅ 所有 Agent 配置完成！"
echo "======================================================================"
echo ""

# 显示最终配置
echo "📋 当前所有 Agent:"
openclaw agents list 2>&1 | grep -E "^-|^  (Workspace|Model):"
