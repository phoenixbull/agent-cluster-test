#!/usr/bin/env python3
"""
OpenClaw API 集成模块 - 简化版本
直接通过 subprocess 调用 openclaw agent 命令
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import time


class OpenClawAPI:
    """OpenClaw API 客户端 - 简化版"""
    
    def __init__(self, workspace: str = "~/.openclaw/workspace"):
        self.workspace = Path(workspace).expanduser()
        self.openclaw_cli = self._find_openclaw_cli()
    
    def _find_openclaw_cli(self) -> Optional[str]:
        """查找 openclaw CLI 路径"""
        try:
            result = subprocess.run(
                ["which", "openclaw"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=5
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                print(f"   ✅ OpenClaw CLI: {path}")
                return path
        except:
            pass
        return None
    
    def spawn_agent(self, agent_id: str, task: str, timeout_seconds: int = 300) -> Dict:
        """
        触发 Agent 执行任务
        
        使用 openclaw agent 命令，异步执行不等待结果
        """
        print(f"\n🚀 触发 Agent: {agent_id}")
        print(f"   任务：{task[:80]}...")
        
        if not self.openclaw_cli:
            return self._mock_result(agent_id, task)
        
        # 异步执行，不等待结果
        session_key = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            # 后台执行命令
            cmd = [
                self.openclaw_cli,
                "agent",
                "--agent", agent_id,
                "--message", task
            ]
            
            # 使用 Popen 异步执行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=str(self.workspace)
            )
            
            print(f"   ✅ Agent 已触发 (PID: {process.pid})")
            print(f"   ⏳ 执行中... (后台运行)")
            
            return {
                "success": True,
                "session_key": session_key,
                "pid": process.pid,
                "agent_id": agent_id,
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "async": True
            }
            
        except Exception as e:
            print(f"   ❌ 触发失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
    
    def spawn_agent_sync(self, agent_id: str, task: str, timeout_seconds: int = 120) -> Dict:
        """
        同步触发 Agent 并等待结果 (短时间任务)
        """
        print(f"\n🚀 触发 Agent: {agent_id} (同步模式)")
        print(f"   任务：{task[:80]}...")
        
        if not self.openclaw_cli:
            return self._mock_result(agent_id, task)
        
        try:
            cmd = [
                self.openclaw_cli,
                "agent",
                "--agent", agent_id,
                "--message", task,
                "--json"
            ]
            
            print(f"   ⏳ 执行中...")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=timeout_seconds,
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"   ✅ 执行完成")
                
                # 尝试解析 JSON
                try:
                    json_output = json.loads(output)
                    return {
                        "success": True,
                        "session_key": json_output.get('session_key', f'session-{datetime.now().strftime("%Y%m%d-%H%M%S")}'),
                        "output": json_output.get('output', output),
                        "messages": json_output.get('messages', []),
                        "agent_id": agent_id,
                        "task": task,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return {
                        "success": True,
                        "session_key": f'session-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                        "output": output,
                        "messages": [{"role": "assistant", "content": output}],
                        "agent_id": agent_id,
                        "task": task,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                error_msg = result.stderr[:200] if result.stderr else "未知错误"
                print(f"   ❌ 执行失败：{error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "output": result.stdout,
                    "agent_id": agent_id,
                    "task": task,
                    "timestamp": datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ 执行超时 ({timeout_seconds}秒)")
            return {
                "success": False,
                "error": f"执行超时 ({timeout_seconds}秒)",
                "agent_id": agent_id,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"   ❌ 执行异常：{e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
    
    def _mock_result(self, agent_id: str, task: str) -> Dict:
        """模拟结果"""
        return {
            "success": True,
            "session_key": f'mock-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            "output": f"[模拟] Agent {agent_id} 已处理",
            "messages": [{"role": "assistant", "content": "[模拟] 任务完成"}],
            "agent_id": agent_id,
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }


# 便捷函数
def spawn_codex(task: str, timeout: int = 300) -> Dict:
    api = OpenClawAPI()
    return api.spawn_agent("main", task, timeout)


def spawn_reviewer(task: str, timeout: int = 300) -> Dict:
    api = OpenClawAPI()
    return api.spawn_agent("main", task, timeout)


if __name__ == "__main__":
    import sys
    
    api = OpenClawAPI()
    
    if len(sys.argv) < 2:
        print("用法：python openclaw_api.py <任务描述>")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    print("=== 异步模式 ===")
    result = api.spawn_agent("main", task, timeout_seconds=60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 同步模式 ===")
    result = api.spawn_agent_sync("main", task, timeout_seconds=60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
