#!/usr/bin/env python3
"""
手动触发子代理任务执行
用于测试和调试
"""

import json
from pathlib import Path

# 加载任务
tasks_file = Path("test_tasks.json")
with open(tasks_file, "r", encoding="utf-8") as f:
    tasks = json.load(f)

print("📋 待执行任务:")
print("=" * 60)

for i, task in enumerate(tasks, 1):
    agent = task.get("agent", "main")
    task_desc = task.get("task", "")
    
    print(f"\n{i}. Agent: {agent}")
    print(f"   任务：{task_desc[:80]}...")
    print(f"   完整任务：{task_desc}")

print("\n" + "=" * 60)
print("\n💡 提示：这些任务需要通过 OpenClaw 的 sessions 系统来执行")
print("   当前会话文件已创建，等待任务执行触发")
print("\n📁 会话文件位置:")
print("   - ~/.openclaw/workspace/agents/codex/sessions/")
print("   - ~/.openclaw/workspace/agents/claude-code/sessions/")
print("   - ~/.openclaw/workspace/agents/designer/sessions/")
