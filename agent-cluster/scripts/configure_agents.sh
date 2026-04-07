#!/bin/bash
# 配置 OpenClaw Agent 脚本

set -e

echo "=== 配置 OpenClaw Agent ==="
echo ""

# 1. 查看已配置的 Agent
echo "📋 当前已配置的 Agent:"
openclaw agents list
echo ""

# 2. 配置 Codex 后端专家 Agent
echo "🔧 配置 Codex 后端专家 Agent..."
openclaw agents add codex \
  --model alibaba-cloud/qwen-coder-plus \
  --workspace ~/.openclaw/workspace/agent-cluster/agents/codex \
  --agent-dir ~/.openclaw/agents/codex \
  --non-interactive || echo "⚠️  codex Agent 可能已存在"
echo ""

# 3. 配置 Reviewer Agent
echo "🔧 配置 Codex Reviewer Agent..."
openclaw agents add codex-reviewer \
  --model alibaba-cloud/qwen-plus \
  --workspace ~/.openclaw/workspace/agent-cluster/agents/codex-reviewer \
  --agent-dir ~/.openclaw/agents/codex-reviewer \
  --non-interactive || echo "⚠️  codex-reviewer Agent 可能已存在"
echo ""

# 4. 配置 Gemini Reviewer Agent
echo "🔧 配置 Gemini Reviewer Agent..."
openclaw agents add gemini-reviewer \
  --model alibaba-cloud/qwen-plus \
  --workspace ~/.openclaw/workspace/agent-cluster/agents/gemini-reviewer \
  --agent-dir ~/.openclaw/agents/gemini-reviewer \
  --non-interactive || echo "⚠️  gemini-reviewer Agent 可能已存在"
echo ""

# 5. 配置 Claude Reviewer Agent
echo "🔧 配置 Claude Reviewer Agent..."
openclaw agents add claude-reviewer \
  --model alibaba-cloud/qwen-turbo \
  --workspace ~/.openclaw/workspace/agent-cluster/agents/claude-reviewer \
  --agent-dir ~/.openclaw/agents/claude-reviewer \
  --non-interactive || echo "⚠️  claude-reviewer Agent 可能已存在"
echo ""

# 6. 列出所有 Agent
echo "✅ 配置完成！当前所有 Agent:"
openclaw agents list
echo ""

echo "=== Agent 配置完成 ==="
