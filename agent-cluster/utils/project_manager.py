#!/usr/bin/env python3
"""
项目管理器 - V2.2 增强版
支持任务看板、进度追踪、时间估算
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import fcntl


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = "critical"  # 🔴 紧急重要
    HIGH = "high"          # 🟠 重要
    MEDIUM = "medium"      # 🟡 普通
    LOW = "low"            # 🟢 低优先级


class TaskStatus(Enum):
    """任务状态"""
    BACKLOG = "backlog"      # 待办
    TODO = "todo"            # 准备做
    IN_PROGRESS = "in_progress"  # 进行中
    REVIEW = "review"        # 审查中
    DONE = "done"            # 已完成
    BLOCKED = "blocked"      # 被阻塞


class PhaseStatus(Enum):
    """阶段状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ProjectManager:
    """项目管理器（看板 + 进度追踪）"""
    
    def __init__(self, state_path: str = None):
        if state_path:
            self.state_path = Path(state_path)
        else:
            self.state_path = Path("~/.openclaw/workspace/agent-cluster/memory/project_state.json").expanduser()
        
        # 确保目录存在
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_state_file()
    
    def _ensure_state_file(self):
        """确保状态文件存在"""
        if not self.state_path.exists():
            self._write_state(self._default_state())
    
    def _default_state(self) -> Dict:
        """默认状态结构"""
        return {
            "version": "2.2",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "projects": {},
            "tasks": [],
            "phases": {
                "1_requirement": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                "2_design": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                "3_development": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                "4_testing": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                "5_review": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                "6_deployment": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0}
            }
        }
    
    def _read_state(self) -> Dict:
        """读取状态（带共享锁）"""
        with open(self.state_path, 'r', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _write_state(self, data: Dict):
        """写入状态（带排他锁）"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.state_path, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def create_project(self, project_id: str, name: str, 
                      description: str = "", owner: str = "") -> bool:
        """创建新项目"""
        try:
            state = self._read_state()
            
            if project_id in state.get("projects", {}):
                print(f"⚠️ 项目 {project_id} 已存在")
                return False
            
            project = {
                "id": project_id,
                "name": name,
                "description": description,
                "owner": owner,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "phases": {
                    "1_requirement": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                    "2_design": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                    "3_development": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                    "4_testing": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                    "5_review": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0},
                    "6_deployment": {"status": PhaseStatus.NOT_STARTED.value, "progress": 0}
                },
                "stats": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "blocked_tasks": 0
                }
            }
            
            if "projects" not in state:
                state["projects"] = {}
            state["projects"][project_id] = project
            state["tasks"] = []
            
            self._write_state(state)
            print(f"✅ 项目 {name} 已创建")
            return True
            
        except Exception as e:
            print(f"❌ 创建项目失败：{e}")
            return False
    
    def add_task(self, task_id: str, title: str, description: str = "",
                phase: str = "3_development", priority: str = "medium",
                assignee: str = None, estimated_hours: float = None,
                project_id: str = None) -> bool:
        """添加任务"""
        try:
            state = self._read_state()
            
            # 检查任务是否已存在
            for task in state.get("tasks", []):
                if task.get("id") == task_id:
                    print(f"⚠️ 任务 {task_id} 已存在")
                    return False
            
            task = {
                "id": task_id,
                "title": title,
                "description": description,
                "phase": phase,
                "status": TaskStatus.BACKLOG.value,
                "priority": priority,
                "assignee": assignee,
                "estimated_hours": estimated_hours,
                "actual_hours": 0,
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "blocked_by": None,
                "dependencies": [],
                "tags": []
            }
            
            if "tasks" not in state:
                state["tasks"] = []
            state["tasks"].append(task)
            
            # 更新项目统计
            if project_id and project_id in state.get("projects", {}):
                state["projects"][project_id]["stats"]["total_tasks"] += 1
            
            self._write_state(state)
            print(f"✅ 任务 {title} 已添加")
            return True
            
        except Exception as e:
            print(f"❌ 添加任务失败：{e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, 
                          updates: Dict = None) -> bool:
        """更新任务状态"""
        try:
            state = self._read_state()
            
            for task in state.get("tasks", []):
                if task.get("id") == task_id:
                    old_status = task.get("status")
                    task["status"] = status
                    
                    # 更新时间戳
                    if status == TaskStatus.IN_PROGRESS.value and not task.get("started_at"):
                        task["started_at"] = datetime.now().isoformat()
                    elif status == TaskStatus.DONE.value:
                        task["completed_at"] = datetime.now().isoformat()
                    
                    # 应用其他更新
                    if updates:
                        task.update(updates)
                    
                    # 更新项目统计
                    if task.get("project_id"):
                        project = state["projects"].get(task["project_id"])
                        if project:
                            if status == TaskStatus.DONE.value and old_status != TaskStatus.DONE.value:
                                project["stats"]["completed_tasks"] += 1
                            elif status == TaskStatus.BLOCKED.value and old_status != TaskStatus.BLOCKED.value:
                                project["stats"]["blocked_tasks"] += 1
                    
                    self._write_state(state)
                    print(f"✅ 任务 {task_id} 状态更新为 {status}")
                    return True
            
            print(f"⚠️ 未找到任务 {task_id}")
            return False
            
        except Exception as e:
            print(f"❌ 更新任务状态失败：{e}")
            return False
    
    def get_kanban_board(self, project_id: str = None) -> Dict:
        """获取看板数据"""
        state = self._read_state()
        tasks = state.get("tasks", [])
        
        # 按项目筛选
        if project_id:
            tasks = [t for t in tasks if t.get("project_id") == project_id]
        
        # 按状态分组
        board = {
            "backlog": [],
            "todo": [],
            "in_progress": [],
            "review": [],
            "done": [],
            "blocked": []
        }
        
        for task in tasks:
            status = task.get("status", "backlog")
            if status in board:
                board[status].append({
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "priority": task.get("priority"),
                    "assignee": task.get("assignee"),
                    "phase": task.get("phase"),
                    "estimated_hours": task.get("estimated_hours")
                })
        
        return board
    
    def get_progress(self, project_id: str = None) -> Dict:
        """获取项目进度"""
        state = self._read_state()
        
        if project_id:
            project = state.get("projects", {}).get(project_id)
            if not project:
                return {"error": "项目不存在"}
            
            phases = project.get("phases", {})
        else:
            phases = state.get("phases", {})
        
        # 计算总体进度
        total_progress = sum(p.get("progress", 0) for p in phases.values()) / len(phases) if phases else 0
        
        return {
            "overall_progress": round(total_progress, 2),
            "phases": {
                name: {
                    "status": phase.get("status"),
                    "progress": phase.get("progress")
                }
                for name, phase in phases.items()
            },
            "completed_phases": sum(1 for p in phases.values() if p.get("status") == PhaseStatus.COMPLETED.value),
            "total_phases": len(phases)
        }
    
    def get_task_stats(self, project_id: str = None) -> Dict:
        """获取任务统计"""
        state = self._read_state()
        tasks = state.get("tasks", [])
        
        if project_id:
            tasks = [t for t in tasks if t.get("project_id") == project_id]
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == TaskStatus.DONE.value)
        in_progress = sum(1 for t in tasks if t.get("status") == TaskStatus.IN_PROGRESS.value)
        blocked = sum(1 for t in tasks if t.get("status") == TaskStatus.BLOCKED.value)
        backlog = sum(1 for t in tasks if t.get("status") == TaskStatus.BACKLOG.value)
        
        # 估算时间统计
        estimated_total = sum(t.get("estimated_hours", 0) or 0 for t in tasks)
        estimated_remaining = sum(
            t.get("estimated_hours", 0) or 0 
            for t in tasks 
            if t.get("status") not in [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]
        )
        
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "blocked_tasks": blocked,
            "backlog_tasks": backlog,
            "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
            "estimated_total_hours": estimated_total,
            "estimated_remaining_hours": estimated_remaining
        }
    
    def get_phase_tasks(self, phase: str) -> List[Dict]:
        """获取指定阶段的任务"""
        state = self._read_state()
        return [
            t for t in state.get("tasks", [])
            if t.get("phase") == phase
        ]
    
    def update_phase_progress(self, phase: str, progress: int, 
                             status: str = None) -> bool:
        """更新阶段进度"""
        try:
            state = self._read_state()
            
            # 更新全局阶段
            if phase in state.get("phases", {}):
                state["phases"][phase]["progress"] = progress
                if status:
                    state["phases"][phase]["status"] = status
            
            # 更新所有项目的阶段
            for project in state.get("projects", {}).values():
                if phase in project.get("phases", {}):
                    project["phases"][phase]["progress"] = progress
                    if status:
                        project["phases"][phase]["status"] = status
            
            self._write_state(state)
            print(f"✅ 阶段 {phase} 进度更新为 {progress}%")
            return True
            
        except Exception as e:
            print(f"❌ 更新阶段进度失败：{e}")
            return False
    
    def list_projects(self) -> List[Dict]:
        """列出所有项目"""
        state = self._read_state()
        projects = list(state.get("projects", {}).values())
        
        # 添加实时统计
        for project in projects:
            stats = self.get_task_stats(project.get("id"))
            project["current_stats"] = stats
        
        return projects
    
    def get_project_detail(self, project_id: str) -> Optional[Dict]:
        """获取项目详情"""
        state = self._read_state()
        project = state.get("projects", {}).get(project_id)
        
        if not project:
            return None
        
        # 添加任务列表和统计
        project["tasks"] = [
            t for t in state.get("tasks", [])
            if t.get("project_id") == project_id
        ]
        project["stats"] = self.get_task_stats(project_id)
        project["progress"] = self.get_progress(project_id)
        
        return project


# 便捷函数
def get_project_manager() -> ProjectManager:
    """获取项目管理器实例"""
    return ProjectManager()


if __name__ == "__main__":
    # 测试
    manager = ProjectManager()
    print("项目列表:", len(manager.list_projects()))
    print("任务统计:", manager.get_task_stats())
