#!/bin/bash
# 测试 Agent 任务通知

set -e

echo "======================================"
echo "📧 Agent 任务通知测试"
echo "======================================"
echo ""

cd /home/admin/.openclaw/workspace/agent-cluster

# 测试 1: 语法检查
echo "1️⃣  语法检查..."
python3 -m py_compile cluster_manager.py
python3 -m py_compile notifiers/dingtalk.py
echo "   ✅ 语法检查通过"
echo ""

# 测试 2: 测试任务分配通知
echo "2️⃣  测试任务分配通知..."
python3 << 'PYTHON'
import json
from notifiers.dingtalk import get_notifier, reset_notifier

reset_notifier()

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

notifier = get_notifier(config)

# 模拟任务分配
task_info = {
    "id": "test-task-001",
    "description": "实现用户登录功能",
    "agent": "codex",
    "type": "backend_development",
    "phase": "3_development",
    "priority": "high",
    "created_at": "2026-03-21 11:45:00"
}

agent_info = {
    "name": "Codex 后端专家",
    "role": "backend_specialist"
}

print("发送任务分配通知...")
success = notifier.notify_agent_task_assigned(task_info, agent_info)
print(f"结果：{'✅ 成功' if success else '❌ 失败'}")
PYTHON
echo ""

# 测试 3: 测试任务完成通知
echo "3️⃣  测试任务完成通知..."
python3 << 'PYTHON'
import json
from notifiers.dingtalk import get_notifier, reset_notifier
from datetime import datetime

reset_notifier()

with open('cluster_config_v2.json', 'r') as f:
    config = json.load(f)['notifications']['dingtalk']

notifier = get_notifier(config)

# 模拟任务完成
task_info = {
    "id": "test-task-001",
    "description": "实现用户登录功能",
    "agent": "codex",
    "type": "backend_development",
    "phase": "3_development",
    "created_at": "2026-03-21 11:45:00"
}

result_info = {
    "status": "completed",
    "execution_time": 125.5,
    "deliverables": [
        {"name": "login.py", "path": "src/auth/login.py"},
        {"name": "test_login.py", "path": "tests/test_login.py"}
    ]
}

agent_info = {
    "name": "Codex 后端专家",
    "role": "backend_specialist"
}

print("发送任务完成通知...")
success = notifier.notify_agent_task_complete(task_info, result_info, agent_info)
print(f"结果：{'✅ 成功' if success else '❌ 失败'}")
PYTHON
echo ""

echo "======================================"
echo "测试完成！"
echo "======================================"
echo ""
echo "📝 检查钉钉消息:"
echo "   1. 任务分配通知 - 📥 Agent 接受新任务"
echo "   2. 任务完成通知 - ✅ Agent 完成任务"
echo ""
