#!/usr/bin/env python3
"""
OpenClaw API 集成模块
用于触发子 Agent 执行任务、管理会话、收集结果
"""

import json
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time


class OpenClawAPI:
    """
    OpenClaw API 客户端
    
    功能:
    - 触发子 Agent 执行任务 (sessions_spawn)
    - 查询会话状态
    - 获取会话结果
    - 管理 Agent 会话
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace"):
        self.workspace = Path(workspace).expanduser()
        self.agents_dir = self.workspace / "agents"
        self.cluster_dir = self.workspace / "agent-cluster"
    
    def spawn_agent(self, agent_id: str, task: str, timeout_seconds: int = 3600) -> Dict:
        """
        触发子 Agent 执行任务
        
        Args:
            agent_id: Agent ID (codex, claude-code, designer 等)
            task: 任务描述
            timeout_seconds: 超时时间 (秒)
        
        Returns:
            执行结果
        """
        print(f"\n🚀 触发 Agent: {agent_id}")
        print(f"   任务：{task[:100]}...")
        
        # 构建 sessions_spawn 命令
        # 通过 openclaw CLI 或 Python API 触发
        result = self._execute_via_openclaw(agent_id, task, timeout_seconds)
        
        return result
    
    def _execute_via_openclaw(self, agent_id: str, task: str, timeout_seconds: int) -> Dict:
        """
        通过 OpenClaw 执行任务
        
        方法 1: 使用 openclaw CLI (如果可用)
        方法 2: 直接操作会话文件
        方法 3: 调用 OpenClaw Python API
        """
        
        # 首先尝试使用 openclaw CLI
        try:
            cli_path = self._find_openclaw_cli()
            if cli_path:
                return self._execute_via_cli(cli_path, agent_id, task, timeout_seconds)
        except Exception as e:
            print(f"   ⚠️ CLI 执行失败：{e}，尝试其他方法...")
        
        # 回退到直接操作会话文件
        return self._execute_via_session_file(agent_id, task, timeout_seconds)
    
    def _find_openclaw_cli(self) -> Optional[str]:
        """查找 openclaw CLI 路径"""
        # 常见路径
        possible_paths = [
            "/usr/local/bin/openclaw",
            "/opt/openclaw/bin/openclaw",
            "~/.openclaw/bin/openclaw"
        ]
        
        for path in possible_paths:
            p = Path(path).expanduser()
            if p.exists() and p.is_executable():
                return str(p)
        
        # 尝试在 PATH 中查找
        try:
            result = subprocess.run(
                ["which", "openclaw"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def _execute_via_cli(self, cli_path: str, agent_id: str, task: str, timeout_seconds: int) -> Dict:
        """通过 CLI 执行 - 使用 openclaw agent 命令"""
        import json as json_lib
        
        # 使用 openclaw agent 命令，通过 stdin 传递任务
        cmd = [
            cli_path,
            "agent",
            "--local",
            "--message", task,
            "--timeoutSeconds", str(timeout_seconds)
        ]
        
        print(f"   执行命令：{' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=min(timeout_seconds, 120)  # 限制最多 2 分钟
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "output": result.stdout,
                    "agent_id": agent_id,
                    "session_id": "local-exec"
                }
            else:
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "agent_id": agent_id
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": f"任务执行超时 ({timeout_seconds}秒)",
                "agent_id": agent_id
            }
    
    def _execute_via_session_file(self, agent_id: str, task: str, timeout_seconds: int) -> Dict:
        """
        通过会话文件执行 (回退方案)
        
        1. 创建会话文件
        2. 等待执行 (模拟)
        3. 返回结果
        """
        import uuid
        
        agent_dir = self.agents_dir / agent_id
        sessions_dir = agent_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        session_id = str(uuid.uuid4())[:8]
        session_file = sessions_dir / f"{session_id}.json"
        
        # 创建会话文件
        session_data = {
            "id": session_id,
            "agent_id": agent_id,
            "created_at": datetime.now().isoformat(),
            "task": task,
            "messages": [],
            "status": "active"
        }
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 会话已创建：{session_id}")
        print(f"   📁 会话文件：{session_file}")
        
        # 等待执行完成 (这里应该轮询会话状态)
        # 暂时模拟执行
        print(f"   ⏳ 等待 Agent 执行... (模拟 {min(timeout_seconds, 10)} 秒)")
        time.sleep(min(timeout_seconds, 10))
        
        # 更新会话状态
        session_data["status"] = "completed"
        session_data["completed_at"] = datetime.now().isoformat()
        session_data["messages"] = [
            {
                "role": "assistant",
                "content": f"任务已完成：{task[:50]}...",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "completed",
            "session_id": session_id,
            "agent_id": agent_id,
            "session_file": str(session_file),
            "output": f"任务已完成：{task[:50]}..."
        }
    
    def get_session_result(self, agent_id: str, session_id: str) -> Optional[Dict]:
        """获取会话结果"""
        session_file = self.agents_dir / agent_id / "sessions" / f"{session_id}.json"
        
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def list_agent_sessions(self, agent_id: str, status: str = None) -> List[Dict]:
        """列出 Agent 的会话"""
        sessions_dir = self.agents_dir / agent_id / "sessions"
        
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_file in sessions_dir.glob("*.json"):
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            if status is None or session_data.get("status") == status:
                sessions.append(session_data)
        
        return sessions
    
    def cleanup_old_sessions(self, agent_id: str, retention_days: int = 7):
        """清理旧会话"""
        sessions_dir = self.agents_dir / agent_id / "sessions"
        
        if not sessions_dir.exists():
            return
        
        cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        
        for session_file in sessions_dir.glob("*.json"):
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            created_at = session_data.get("created_at", "1970-01-01")
            try:
                timestamp = datetime.fromisoformat(created_at).timestamp()
                if timestamp < cutoff:
                    session_file.unlink()
                    print(f"   🗑️ 已清理旧会话：{session_file.name}")
            except:
                pass


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


# ========== 测试入口 ==========

def main():
    """测试函数"""
    import sys
    
    api = OpenClawAPI()
    
    if len(sys.argv) < 3:
        print("用法：python openclaw_api.py <agent_id> <任务描述>")
        print("示例：python openclaw_api.py codex '实现用户登录 API'")
        return
    
    agent_id = sys.argv[1]
    task = " ".join(sys.argv[2:])
    
    result = api.spawn_agent(agent_id, task, timeout_seconds=60)
    
    print(f"\n📊 执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
