#!/usr/bin/env python3
"""
Agent 集群管理器
基于 Datawhale OpenClaw+HelloAgents 架构实现

支持通过 OpenClaw API 启动子代理执行任务
"""

import json
import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess
import requests

# 集群根目录
CLUSTER_ROOT = Path(__file__).parent.absolute()
CONFIG_FILE = CLUSTER_ROOT / "cluster_config.json"
AGENTS_DIR = CLUSTER_ROOT / "agents"

# OpenClaw Gateway 配置
GATEWAY_URL = "ws://172.17.14.106:14065"
GATEWAY_TOKEN = "686803b591e9863514199d651a7893c4"

# 设置环境变量（供 subprocess 使用）
os.environ["OPENCLAW_GATEWAY_TOKEN"] = GATEWAY_TOKEN


class AgentConfig:
    """Agent 配置类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.id = config.get("id", "unknown")
        self.name = config.get("name", self.id)
        self.workspace = Path(config.get("workspace", f"~/.openclaw/workspace/agents/{self.id}")).expanduser()
        self.model = config.get("model", {})
        self.role = config.get("role", "specialist")
        self.skills = config.get("skills", [])
        self.mcp_servers = config.get("mcp_servers", [])
        self.enabled = config.get("enabled", True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "workspace": str(self.workspace),
            "model": self.model,
            "role": self.role,
            "skills": self.skills,
            "mcp_servers": self.mcp_servers,
            "enabled": self.enabled
        }


class SessionManager:
    """会话管理器 - 管理 Agent 的 sessions"""
    
    def __init__(self, agent_id: str, workspace: Path):
        self.agent_id = agent_id
        self.workspace = workspace
        self.sessions_dir = workspace / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(self, task: str = "") -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        session_file = self.sessions_dir / f"{session_id}.json"
        
        session_data = {
            "id": session_id,
            "agent_id": self.agent_id,
            "created_at": datetime.now().isoformat(),
            "task": task,
            "messages": [],
            "status": "active"
        }
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]):
        """更新会话数据"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            session_data.update(data)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def list_sessions(self, status: str = None) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            if status is None or session_data.get("status") == status:
                sessions.append(session_data)
        return sessions


class SubAgent:
    """子代理类 - 用于并行执行任务"""
    
    def __init__(self, session_id: str, agent_id: str, task: str):
        self.session_id = session_id
        self.agent_id = agent_id
        self.task = task
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "task": self.task,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ProtocolManager:
    """协议管理器 - 管理 MCP/A2A/ANP 协议"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mcp_enabled = config.get("mcp", {}).get("enabled", True)
        self.a2a_enabled = config.get("a2a", {}).get("enabled", True)
        self.anp_enabled = config.get("anp", {}).get("enabled", False)
        
        self.mcp_servers = config.get("mcp", {}).get("servers", [])
        self.a2a_port = config.get("a2a", {}).get("port", 5000)
    
    async def initialize_mcp(self):
        """初始化 MCP 连接"""
        if not self.mcp_enabled:
            return
        
        print(f"🔌 初始化 MCP，连接 {len(self.mcp_servers)} 个服务器...")
        for server in self.mcp_servers:
            print(f"  - 连接 MCP 服务器：{server}")
            # 实际实现会在这里建立 MCP 连接
    
    async def initialize_a2a(self):
        """初始化 A2A 通信"""
        if not self.a2a_enabled:
            return
        
        print(f"🤝 初始化 A2A，监听端口 {self.a2a_port}...")
        # 实际实现会在这里启动 A2A 服务器
    
    async def discover_services(self):
        """ANP 服务发现"""
        if not self.anp_enabled:
            return []
        
        print("🔍 ANP 服务发现...")
        # 实际实现会在这里进行服务发现
        return []


class ClusterManager:
    """集群管理器 - 核心类"""
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or CONFIG_FILE
        self.config = self._load_config()
        self.agents: Dict[str, AgentConfig] = {}
        self.session_managers: Dict[str, SessionManager] = {}
        self.protocol_manager = ProtocolManager(self.config.get("protocols", {}))
        self.sub_agents: Dict[str, SubAgent] = {}
        self.running = False
        
        self._initialize_agents()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "cluster": {
                "name": "default-cluster",
                "mode": "supervisor",
                "max_parallel_agents": 5,
                "timeout_seconds": 300
            },
            "agents": [
                {
                    "id": "main",
                    "name": "主代理",
                    "workspace": "~/.openclaw/workspace",
                    "model": {"provider": "alibaba-cloud", "model": "qwen3.5-plus"},
                    "role": "supervisor",
                    "enabled": True
                }
            ],
            "protocols": {
                "mcp": {"enabled": True, "servers": ["filesystem"]},
                "a2a": {"enabled": True, "port": 5000},
                "anp": {"enabled": False}
            },
            "tools": {
                "builtin": ["search", "calculator"],
                "mcp": ["filesystem", "github"]
            }
        }
    
    def _initialize_agents(self):
        """初始化所有 Agent"""
        for agent_data in self.config.get("agents", []):
            agent = AgentConfig(agent_data)
            if agent.enabled:
                self.agents[agent.id] = agent
                self.session_managers[agent.id] = SessionManager(agent.id, agent.workspace)
                print(f"✅ 初始化 Agent: {agent.name} ({agent.id})")
    
    def save_config(self):
        """保存配置"""
        config_data = {
            "cluster": self.config.get("cluster", {}),
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "protocols": self.config.get("protocols", {}),
            "tools": self.config.get("tools", {})
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"💾 配置已保存到 {self.config_path}")
    
    # ========== Agent 管理 ==========
    
    def add_agent(self, agent_id: str, name: str = None, role: str = "specialist", 
                  model: str = "qwen3.5-plus", workspace: str = None):
        """添加新 Agent"""
        if agent_id in self.agents:
            print(f"❌ Agent '{agent_id}' 已存在")
            return False
        
        if workspace is None:
            workspace = f"~/.openclaw/workspace/agents/{agent_id}"
        
        agent_config = {
            "id": agent_id,
            "name": name or agent_id,
            "workspace": workspace,
            "model": {"provider": "alibaba-cloud", "model": model},
            "role": role,
            "skills": [],
            "mcp_servers": [],
            "enabled": True
        }
        
        agent = AgentConfig(agent_config)
        self.agents[agent_id] = agent
        self.session_managers[agent_id] = SessionManager(agent_id, agent.workspace)
        
        # 创建 Agent 工作目录
        agent.workspace.mkdir(parents=True, exist_ok=True)
        self._create_agent_soul_file(agent)
        
        self.config.setdefault("agents", []).append(agent_config)
        self.save_config()
        
        print(f"✅ 已添加 Agent: {agent.name} ({agent_id})")
        return True
    
    def _create_agent_soul_file(self, agent: AgentConfig):
        """创建 Agent 的 SOUL.md 文件"""
        soul_content = f"""# SOUL.md - {agent.name}

## 角色定位
你是 {agent.name}，在集群中担任 {agent.role} 角色。

## 核心职责
- 专注于你的专业领域
- 与其他 Agent 协作完成任务
- 保持高质量的输出

## 工作风格
- 专业、高效
- 善于沟通协作
- 主动汇报进度

## 协作协议
- 接收来自主代理 (main) 的任务委托
- 使用 A2A 协议与其他 Agent 通信
- 通过 MCP 协议调用工具

---
*此文件定义了你在集群中的人格和行为准则*
"""
        soul_file = agent.workspace / "SOUL.md"
        with open(soul_file, "w", encoding="utf-8") as f:
            f.write(soul_content)
        
        # 创建 IDENTITY.md
        identity_content = f"""# IDENTITY.md - {agent.name}

- **Name:** {agent.name}
- **ID:** {agent.id}
- **Role:** {agent.role}
- **Model:** {agent.model.get('model', 'qwen3.5-plus')}
- **Emoji:** 🤖

---
*这是你的身份标识*
"""
        identity_file = agent.workspace / "IDENTITY.md"
        with open(identity_file, "w", encoding="utf-8") as f:
            f.write(identity_content)
        
        # 创建 memory 目录
        (agent.workspace / "memory").mkdir(exist_ok=True)
        
        print(f"📝 已创建 {agent.name} 的人格文件")
    
    def remove_agent(self, agent_id: str):
        """移除 Agent"""
        if agent_id not in self.agents:
            print(f"❌ Agent '{agent_id}' 不存在")
            return False
        
        if agent_id == "main":
            print("❌ 不能移除主代理 (main)")
            return False
        
        del self.agents[agent_id]
        del self.session_managers[agent_id]
        
        self.config["agents"] = [a for a in self.config.get("agents", []) if a.get("id") != agent_id]
        self.save_config()
        
        print(f"✅ 已移除 Agent: {agent_id}")
        return True
    
    def list_agents(self):
        """列出所有 Agent"""
        print("\n" + "="*60)
        print("📋 Agent 列表")
        print("="*60)
        
        for agent_id, agent in self.agents.items():
            status = "🟢" if agent.enabled else "🔴"
            print(f"\n{status} {agent.name} ({agent_id})")
            print(f"   角色：{agent.role}")
            print(f"   模型：{agent.model.get('model', 'N/A')}")
            print(f"   工作区：{agent.workspace}")
            print(f"   技能：{', '.join(agent.skills) if agent.skills else '无'}")
        
        print("\n" + "="*60)
    
    # ========== 会话管理 ==========
    
    def create_session(self, agent_id: str, task: str = "") -> str:
        """为指定 Agent 创建会话"""
        if agent_id not in self.session_managers:
            print(f"❌ Agent '{agent_id}' 不存在")
            return None
        
        session_id = self.session_managers[agent_id].create_session(task)
        print(f"✅ 已创建会话：{session_id} (Agent: {agent_id})")
        return session_id
    
    def get_session(self, agent_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        if agent_id not in self.session_managers:
            return None
        return self.session_managers[agent_id].get_session(session_id)
    
    # ========== 子代理管理 ==========
    
    def spawn_sub_agent(self, agent_id: str, task: str) -> str:
        """生成子代理执行任务 - 通过 OpenClaw API"""
        # 1. 创建本地会话记录
        session_id = self.create_session(agent_id, task)
        if not session_id:
            return None
        
        # 2. 通过 OpenClaw API 启动子代理
        try:
            openclaw_session_id = self._call_openclaw_spawn(agent_id, task)
            if openclaw_session_id:
                session_id = openclaw_session_id
        except Exception as e:
            print(f"⚠️ OpenClaw API 调用失败：{e}，使用本地会话模式")
        
        # 3. 创建子代理对象
        sub_agent = SubAgent(session_id, agent_id, task)
        sub_agent.status = "running"
        self.sub_agents[session_id] = sub_agent
        
        print(f"🚀 生成子代理：{session_id} (Agent: {agent_id}, Task: {task[:50]}...)")
        return session_id
    
    def _call_openclaw_spawn(self, agent_id: str, task: str) -> Optional[str]:
        """通过 OpenClaw API 启动子代理 - 使用 Python 直接调用"""
        try:
            # 使用 orchestrator.py 中的 OpenClawAPI
            sys.path.insert(0, str(CLUSTER_ROOT))
            from utils.openclaw_api import OpenClawAPI
            
            api = OpenClawAPI(workspace=str(CLUSTER_ROOT.parent))
            result = api.spawn_agent(agent_id, task, timeout_seconds=3600)
            
            if result.get("status") == "success":
                session_id = result.get("session_id")
                if session_id:
                    return f"agent:{agent_id}:{session_id}"
            
            return None
        except Exception as e:
            print(f"⚠️ OpenClaw API 调用失败：{e}")
            return None
    
    def parallel_execute(self, tasks: List[Dict[str, str]]) -> Dict[str, Any]:
        """并行执行多个任务"""
        print(f"\n⚡ 并行执行 {len(tasks)} 个任务...")
        
        results = {}
        for i, task in enumerate(tasks):
            agent_id = task.get("agent", "main")
            task_desc = task.get("task", "")
            
            session_id = self.spawn_sub_agent(agent_id, task_desc)
            if session_id:
                results[session_id] = {
                    "agent_id": agent_id,
                    "task": task_desc,
                    "status": "pending"
                }
        
        print(f"📊 已生成 {len(results)} 个子代理")
        return results
    
    def list_sub_agents(self):
        """列出所有子代理"""
        print("\n" + "="*60)
        print("📋 子代理列表")
        print("="*60)
        
        if not self.sub_agents:
            print("暂无运行中的子代理")
            return
        
        for session_id, sub_agent in self.sub_agents.items():
            status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}.get(sub_agent.status, "❓")
            print(f"\n{status_icon} {session_id}")
            print(f"   Agent: {sub_agent.agent_id}")
            print(f"   任务：{sub_agent.task[:60]}...")
            print(f"   状态：{sub_agent.status}")
            print(f"   创建时间：{sub_agent.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*60)
    
    def stop_sub_agent(self, session_id: str):
        """停止子代理"""
        if session_id in self.sub_agents:
            sub_agent = self.sub_agents[session_id]
            sub_agent.status = "stopped"
            sub_agent.completed_at = datetime.now()
            
            # 更新会话状态
            if sub_agent.agent_id in self.session_managers:
                self.session_managers[sub_agent.agent_id].update_session(
                    session_id, {"status": "stopped"}
                )
            
            print(f"✅ 已停止子代理：{session_id}")
        else:
            print(f"❌ 子代理 '{session_id}' 不存在")
    
    def stop_all_sub_agents(self):
        """停止所有子代理"""
        count = 0
        for session_id in list(self.sub_agents.keys()):
            self.stop_sub_agent(session_id)
            count += 1
        print(f"✅ 已停止 {count} 个子代理")
    
    # ========== 集群控制 ==========
    
    async def start(self):
        """启动集群"""
        if self.running:
            print("⚠️ 集群已在运行中")
            return
        
        print("\n" + "="*60)
        print("🚀 启动 Agent 集群")
        print("="*60)
        
        # 初始化协议
        await self.protocol_manager.initialize_mcp()
        await self.protocol_manager.initialize_a2a()
        await self.protocol_manager.discover_services()
        
        self.running = True
        print(f"\n✅ 集群已启动，模式：{self.config['cluster']['mode']}")
        print(f"📊 活跃 Agent: {len(self.agents)}")
        print("="*60 + "\n")
    
    def stop(self):
        """停止集群"""
        if not self.running:
            print("⚠️ 集群未运行")
            return
        
        print("\n🛑 停止集群...")
        self.stop_all_sub_agents()
        self.running = False
        print("✅ 集群已停止\n")
    
    def status(self):
        """显示集群状态"""
        print("\n" + "="*60)
        print(f"📊 集群状态 - {self.config['cluster']['name']}")
        print("="*60)
        
        print(f"\n运行状态：{'🟢 运行中' if self.running else '🔴 已停止'}")
        print(f"协作模式：{self.config['cluster']['mode']}")
        print(f"活跃 Agent: {len(self.agents)}")
        print(f"子代理数：{len([s for s in self.sub_agents.values() if s.status in ['pending', 'running']])}")
        
        print("\nAgent 状态:")
        for agent_id, agent in self.agents.items():
            sessions = self.session_managers[agent_id].list_sessions(status="active")
            print(f"  - {agent.name}: {len(sessions)} 活跃会话")
        
        print("\n" + "="*60 + "\n")
    
    # ========== 协作模式 ==========
    
    def set_mode(self, mode: str):
        """设置协作模式"""
        valid_modes = ["supervisor", "router", "pipeline", "parallel"]
        if mode not in valid_modes:
            print(f"❌ 无效的模式，可选：{', '.join(valid_modes)}")
            return
        
        self.config["cluster"]["mode"] = mode
        self.save_config()
        print(f"✅ 协作模式已设置为：{mode}")


# ========== CLI 入口 ==========

def print_help():
    """打印帮助信息"""
    help_text = """
🤖 Agent 集群管理器

用法：python cluster_manager.py <命令> [参数]

命令:
  init                    初始化集群
  start                   启动集群
  stop                    停止集群
  status                  显示集群状态
  
  agent add <id> [name]   添加 Agent
  agent remove <id>       移除 Agent
  agent list              列出所有 Agent
  
  session create <id>     创建会话
  session list <id>       列出会话
  
  subagents list          列出子代理
  subagents stop <id>     停止子代理
  subagents stop all      停止所有子代理
  
  mode set <mode>         设置协作模式 (supervisor/router/pipeline/parallel)
  mode get                获取当前模式
  
  parallel <tasks.json>   并行执行任务 (JSON 文件)
  
  help                    显示此帮助信息

示例:
  python cluster_manager.py init
  python cluster_manager.py agent add coder 代码专家
  python cluster_manager.py mode set supervisor
  python cluster_manager.py start
"""
    print(help_text)


async def main_async():
    """异步主函数"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    cluster = ClusterManager()
    command = sys.argv[1]
    
    if command == "init":
        print("🔧 初始化集群...")
        cluster.save_config()
        print("✅ 集群初始化完成")
    
    elif command == "start":
        await cluster.start()
    
    elif command == "stop":
        cluster.stop()
    
    elif command == "status":
        cluster.status()
    
    elif command == "agent":
        if len(sys.argv) < 3:
            print("❌ 请指定子命令：add/remove/list")
            return
        
        sub_command = sys.argv[2]
        if sub_command == "add":
            if len(sys.argv) < 4:
                print("❌ 请指定 Agent ID")
                return
            agent_id = sys.argv[3]
            agent_name = sys.argv[4] if len(sys.argv) > 4 else None
            cluster.add_agent(agent_id, agent_name)
        elif sub_command == "remove":
            if len(sys.argv) < 4:
                print("❌ 请指定 Agent ID")
                return
            cluster.remove_agent(sys.argv[3])
        elif sub_command == "list":
            cluster.list_agents()
    
    elif command == "session":
        if len(sys.argv) < 3:
            print("❌ 请指定子命令：create/list")
            return
        
        sub_command = sys.argv[2]
        if sub_command == "create":
            if len(sys.argv) < 4:
                print("❌ 请指定 Agent ID")
                return
            cluster.create_session(sys.argv[3])
        elif sub_command == "list":
            if len(sys.argv) < 4:
                print("❌ 请指定 Agent ID")
                return
            agent_id = sys.argv[3]
            if agent_id in cluster.session_managers:
                sessions = cluster.session_managers[agent_id].list_sessions()
                print(f"\n📋 {agent_id} 的会话:")
                for s in sessions:
                    print(f"  - {s['id']}: {s.get('task', 'N/A')[:50]} ({s['status']})")
    
    elif command == "subagents":
        if len(sys.argv) < 3:
            print("❌ 请指定子命令：list/stop")
            return
        
        sub_command = sys.argv[2]
        if sub_command == "list":
            cluster.list_sub_agents()
        elif sub_command == "stop":
            if len(sys.argv) < 4:
                print("❌ 请指定子代理 ID 或 'all'")
                return
            if sys.argv[3] == "all":
                cluster.stop_all_sub_agents()
            else:
                cluster.stop_sub_agent(sys.argv[3])
    
    elif command == "mode":
        if len(sys.argv) < 3:
            print("❌ 请指定子命令：set/get")
            return
        
        sub_command = sys.argv[2]
        if sub_command == "set":
            if len(sys.argv) < 4:
                print("❌ 请指定模式：supervisor/router/pipeline/parallel")
                return
            cluster.set_mode(sys.argv[3])
        elif sub_command == "get":
            print(f"当前模式：{cluster.config['cluster']['mode']}")
    
    elif command == "parallel":
        if len(sys.argv) < 3:
            print("❌ 请指定任务 JSON 文件")
            return
        
        tasks_file = Path(sys.argv[2])
        if tasks_file.exists():
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            cluster.parallel_execute(tasks)
        else:
            print(f"❌ 文件不存在：{tasks_file}")
    
    elif command == "help":
        print_help()
    
    else:
        print(f"❌ 未知命令：{command}")
        print_help()


def main():
    """主函数"""
    # Python 3.6 兼容性：使用 get_event_loop 替代 asyncio.run()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main_async())
    finally:
        loop.close()


if __name__ == "__main__":
    main()


    def check_deploy_confirmations(self):
        """检查待确认的部署"""
        state = self.state.load()
        now = datetime.now()
        
        for wf_id, wf in state.get("workflows", {}).items():
            if wf.get("deployment_status") == "waiting_confirmation":
                phase = wf.get("phases", {}).get("deployment", {})
                notified_at = phase.get("notified_at")
                timeout = phase.get("confirmation_timeout", 30 * 60)
                
                if notified_at:
                    notified_time = datetime.fromisoformat(notified_at)
                    elapsed = (now - notified_time).total_seconds()
                    
                    if elapsed > timeout:
                        self.cancel_deployment(wf_id, "超时未确认")
                    else:
                        remaining = int(timeout - elapsed)
                        print(f"⏳ 等待部署确认：{wf_id} (剩余 {remaining}秒)")
    
    def confirm_deployment(self, workflow_id: str):
        """确认部署"""
        state = self.state.load()
        if workflow_id in state["workflows"]:
            wf = state["workflows"][workflow_id]
            pr_info = wf.get("result", {}).get("pr_info", {})
            
            print(f"🚀 执行部署：{workflow_id}")
            
            deploy_result = {
                "status": "deployed",
                "deployed_at": datetime.now().isoformat(),
                "environment": "production",
                "pr_info": pr_info
            }
            
            if hasattr(self, 'notifier') and self.notifier:
                self.notifier.send_deploy_complete(
                    {"id": workflow_id, "description": wf.get("description", "N/A")},
                    deploy_result
                )
            
            print(f"✅ 部署完成：{workflow_id}")
    
    def cancel_deployment(self, workflow_id: str, reason: str = "用户取消"):
        """取消部署"""
        state = self.state.load()
        if workflow_id in state["workflows"]:
            wf = state["workflows"][workflow_id]
            
            print(f"❌ 取消部署：{workflow_id} (原因：{reason})")
            
            if hasattr(self, 'notifier') and self.notifier:
                self.notifier.send_deploy_cancelled(
                    {"id": workflow_id, "description": wf.get("description", "N/A")},
                    reason
                )
            
            print(f"✅ 部署已取消：{workflow_id}")
