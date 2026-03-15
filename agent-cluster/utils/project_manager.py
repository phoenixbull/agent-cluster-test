#!/usr/bin/env python3
"""项目管理器 - 支持看板、进度追踪"""
import json
from datetime import datetime
from pathlib import Path
from enum import Enum

class TaskStatus(Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

class ProjectManager:
    def __init__(self, state_path=None):
        self.state_path = Path(state_path) if state_path else Path("~/.openclaw/workspace/agent-cluster/memory/project_state.json").expanduser()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._write_state({"version": "2.2", "projects": {}, "tasks": []})
    
    def _read_state(self):
        with open(self.state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_state(self, data):
        data["last_updated"] = datetime.now().isoformat()
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_project(self, project_id, name, description=""):
        state = self._read_state()
        if project_id in state.get("projects", {}):
            return False
        state["projects"][project_id] = {
            "id": project_id, "name": name, "description": description,
            "created_at": datetime.now().isoformat(), "status": "active"
        }
        self._write_state(state)
        return True
    
    def add_task(self, task_id, title, phase="3_development", priority="medium", estimated_hours=0, project_id=None):
        state = self._read_state()
        for t in state.get("tasks", []):
            if t.get("id") == task_id:
                return False
        task = {
            "id": task_id, "title": title, "phase": phase, "priority": priority,
            "estimated_hours": estimated_hours, "project_id": project_id or "default",
            "status": TaskStatus.BACKLOG.value, "created_at": datetime.now().isoformat()
        }
        state["tasks"].append(task)
        self._write_state(state)
        return True
    
    def update_task_status(self, task_id, status):
        state = self._read_state()
        for task in state.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = status
                self._write_state(state)
                return True
        return False
    
    def list_projects(self):
        state = self._read_state()
        return list(state.get("projects", {}).values())
    
    def get_task_stats(self):
        state = self._read_state()
        tasks = state.get("tasks", [])
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == TaskStatus.DONE.value)
        return {"total_tasks": total, "completed_tasks": completed, "completion_rate": round(completed/total*100, 2) if total else 0}
    
    def get_progress(self):
        return {"overall_progress": self.get_task_stats().get("completion_rate", 0)}
    
    def get_kanban_board(self, project_id=None):
        state = self._read_state()
        tasks = state.get("tasks", [])
        if project_id:
            tasks = [t for t in tasks if t.get("project_id") == project_id]
        board = {"backlog": [], "todo": [], "in_progress": [], "review": [], "done": []}
        for task in tasks:
            status = task.get("status", "backlog")
            if status in board:
                board[status].append(task)
        return board
    
    def get_project_detail(self, project_id):
        state = self._read_state()
        project = state.get("projects", {}).get(project_id)
        if not project:
            return None
        project["tasks"] = [t for t in state.get("tasks", []) if t.get("project_id") == project_id]
        project["stats"] = self.get_task_stats()
        project["progress"] = self.get_progress()
        return project

def get_project_manager():
    return ProjectManager()
