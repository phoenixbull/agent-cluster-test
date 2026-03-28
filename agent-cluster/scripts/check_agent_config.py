#!/usr/bin/env python3
"""检查 Agent 配置状态"""

import subprocess
import json
from pathlib import Path

print("=" * 70)
print("🔍 Agent 配置状态检查")
print("=" * 70)
print()

# 1. 获取已配置的 Agent
print("📋 已配置的 Agent (openclaw agents list):")
print("-" * 70)

result = subprocess.run(
    ["openclaw", "agents", "list"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True
)

configured_agents = {}
for line in result.stdout.split('\n'):
    if line.startswith('- '):
        parts = line[2:].split(' ')
        agent_id = parts[0]
        configured_agents[agent_id] = {"configured": True}
        print(f"  ✅ {agent_id}")

print()

# 2. 工作流中使用的 Agent
print("📝 工作流中使用的 Agent:")
print("-" * 70)

workflow_agents = {
    # Phase 1: 需求分析
    "product-manager": "产品需求分析",
    
    # Phase 2: 技术设计
    "tech-lead": "技术架构设计",
    "designer": "UI/UX 设计",
    
    # Phase 3: 编码实现
    "codex": "后端开发 (Python/Node.js)",
    "claude-code": "前端开发 (React/Vue)",
    "mobile-ios": "iOS 开发 (Swift)",
    "mobile-android": "Android 开发 (Kotlin)",
    "mobile-react-native": "React Native 开发",
    "mobile-flutter": "Flutter 开发",
    
    # Phase 4: 测试
    "tester": "Web/后端测试",
    "mobile-tester": "移动端测试",
    
    # Phase 5: 审查
    "codex-reviewer": "代码审查 (逻辑)",
    "gemini-reviewer": "代码审查 (安全)",
    "claude-reviewer": "代码审查 (基础)",
}

for agent_id, purpose in workflow_agents.items():
    status = "✅ 已配置" if agent_id in configured_agents else "❌ 未配置"
    print(f"  {status} {agent_id:25} - {purpose}")

print()

# 3. 统计
print("📊 统计:")
print("-" * 70)
total = len(workflow_agents)
configured = sum(1 for a in workflow_agents if a in configured_agents)
missing = total - configured

print(f"  工作流需要：{total} 个 Agent")
print(f"  已配置：{configured} 个 ({configured/total*100:.1f}%)")
print(f"  缺失：{missing} 个")

print()

# 4. 缺失的 Agent
if missing > 0:
    print("❌ 缺失的 Agent (需要配置):")
    print("-" * 70)
    for agent_id, purpose in workflow_agents.items():
        if agent_id not in configured_agents:
            print(f"  - {agent_id:25} ({purpose})")

print()

# 5. workspace/agents 目录检查
print("📁 workspace/agents 目录检查:")
print("-" * 70)

agents_dir = Path("/home/admin/.openclaw/workspace/agents")
if agents_dir.exists():
    dirs = [d.name for d in agents_dir.iterdir() if d.is_dir()]
    print(f"  目录数：{len(dirs)}")
    for d in sorted(dirs):
        in_workflow = "✅" if d in workflow_agents else "⚠️ "
        in_config = "✅" if d in configured_agents else "❌"
        print(f"    {in_workflow} {in_config} {d}")
else:
    print(f"  ❌ 目录不存在：{agents_dir}")

print()
print("=" * 70)
