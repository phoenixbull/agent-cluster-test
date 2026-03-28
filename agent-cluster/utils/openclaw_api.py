#!/usr/bin/env python3
"""
OpenClaw API 集成模块
用于触发子 Agent 执行任务、管理会话、收集结果

P1 优化：实现真实 OpenClaw sessions_spawn 调用
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time


class OpenClawAPI:
    """
    OpenClaw API 客户端
    
    功能:
    - 触发子 Agent 执行任务 (openclaw agent 命令)
    - 查询会话状态
    - 获取会话结果
    - 管理 Agent 会话
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace"):
        self.workspace = Path(workspace).expanduser()
        self.agents_dir = self.workspace / "agents"
        self.cluster_dir = self.workspace / "agent-cluster"
        self.openclaw_cli = self._find_openclaw_cli()
    
    def _find_openclaw_cli(self) -> Optional[str]:
        """查找 openclaw CLI 路径"""
        # 尝试在 PATH 中查找
        try:
            result = subprocess.run(
                ["which", "openclaw"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"   ✅ OpenClaw CLI 已找到：{result.stdout.strip()}")
                return result.stdout.strip()
        except:
            pass
        
        # 常见路径
        possible_paths = [
            "/usr/bin/openclaw",
            "/usr/local/bin/openclaw",
            "/opt/openclaw/bin/openclaw"
        ]
        
        for path in possible_paths:
            p = Path(path).expanduser()
            if p.exists() and os.access(str(p), os.X_OK):
                print(f"   ✅ OpenClaw CLI 已找到：{p}")
                return str(p)
        
        print(f"   ⚠️ OpenClaw CLI 未找到")
        return None
    
    def spawn_agent(self, agent_id: str, task: str, timeout_seconds: int = 3600) -> Dict:
        """
        触发子 Agent 执行任务
        
        Args:
            agent_id: Agent ID
            task: 任务描述
            timeout_seconds: 超时时间 (秒)
        
        Returns:
            执行结果
        """
        print(f"\n🚀 触发 Agent: {agent_id}")
        print(f"   任务：{task[:100]}...")
        print(f"   超时：{timeout_seconds}秒")
        
        if not self.openclaw_cli:
            print(f"   ⚠️ OpenClaw CLI 不可用，回退到模拟执行")
            return self._create_mock_result(agent_id, task)
        
        return self._execute_via_cli(agent_id, task, timeout_seconds)
    
    def _execute_via_cli(self, agent_id: str, task: str, timeout_seconds: int) -> Dict:
        """通过 OpenClaw CLI 执行任务"""
        try:
            cmd = [
                self.openclaw_cli,
                "agent",
                "--agent", agent_id,
                "--message", task,
                "--json"
            ]
            
            print(f"   🚀 执行命令：openclaw agent --agent {agent_id}...")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=timeout_seconds,
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    print(f"   ✅ Agent 执行成功")
                    return {
                        "success": True,
                        "session_key": output.get('session_key', f'session-{datetime.now().strftime("%Y%m%d-%H%M%S")}'),
                        "output": output.get('output', ''),
                        "messages": output.get('messages', []),
                        "agent_id": agent_id,
                        "task": task,
                        "timestamp": datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    print(f"   ⚠️ 输出解析失败，使用原始输出")
                    return {
                        "success": True,
                        "session_key": f'session-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                        "output": result.stdout,
                        "messages": [{"role": "assistant", "content": result.stdout}],
                        "agent_id": agent_id,
                        "task": task,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                print(f"   ❌ Agent 执行失败：{result.stderr[:200]}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "output": result.stdout,
                    "agent_id": agent_id,
                    "task": task,
                    "timestamp": datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ Agent 执行超时 ({timeout_seconds}秒)")
            return {
                "success": False,
                "error": f"Agent 执行超时 ({timeout_seconds}秒)",
                "agent_id": agent_id,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"   ❌ Agent 执行异常：{e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_mock_result(self, agent_id: str, task: str) -> Dict:
        """创建模拟结果 (当 CLI 不可用时)"""
        return {
            "success": True,
            "session_key": f'mock-session-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            "output": f"[模拟执行] Agent {agent_id} 已处理任务：{task[:50]}...",
            "messages": [
                {"role": "user", "content": task},
                {"role": "assistant", "content": f"[模拟] 任务已处理"}
            ],
            "agent_id": agent_id,
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    def get_session_status(self, session_key: str) -> Dict:
        """查询会话状态"""
        if not self.openclaw_cli:
            return {"status": "unknown", "error": "OpenClaw CLI 不可用"}
        
        try:
            cmd = [self.openclaw_cli, "sessions", "--json"]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
            
            if result.returncode == 0:
                sessions = json.loads(result.stdout)
                for session in sessions:
                    if session.get('id') == session_key or session_key in session.get('id', ''):
                        return {"status": "found", "session": session}
                return {"status": "not_found", "session_key": session_key}
            else:
                return {"status": "error", "error": result.stderr}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_session_result(self, agent_id: str, session_id: str) -> Optional[Dict]:
        """获取会话结果"""
        session_file = self.agents_dir / agent_id / "sessions" / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, "r", encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_agent_sessions(self, agent_id: str, status: str = None) -> List[Dict]:
        """列出 Agent 的会话"""
        sessions_dir = self.agents_dir / agent_id / "sessions"
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_file in sessions_dir.glob("*.json"):
            with open(session_file, "r", encoding='utf-8') as f:
                session_data = json.load(f)
            if status is None or session_data.get("status") == status:
                sessions.append(session_data)
        return sessions


# ========== 便捷函数 ==========

def spawn_codex(task: str, timeout: int = 3600) -> Dict:
    """触发 Codex 后端专家"""
    api = OpenClawAPI()
    return api.spawn_agent("codex", task, timeout)


def spawn_claude(task: str, timeout: int = 3600) -> Dict:
    """触发 Claude Code 前端专家"""
    api = OpenClawAPI()
    return api.spawn_agent("claude-code", task, timeout)


def spawn_designer(task: str, timeout: int = 3600) -> Dict:
    """触发设计师 Agent"""
    api = OpenClawAPI()
    return api.spawn_agent("designer", task, timeout)


if __name__ == "__main__":
    import sys
    
    api = OpenClawAPI()
    
    if len(sys.argv) < 3:
        print("用法：python openclaw_api.py <agent_id> <任务描述>")
        print("示例：python openclaw_api.py codex '实现用户登录 API'")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    task = " ".join(sys.argv[2:])
    
    result = api.spawn_agent(agent_id, task, timeout_seconds=60)
    print(f"\n📊 执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
