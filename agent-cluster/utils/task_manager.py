#!/usr/bin/env python3
"""
任务管理器 - V2.2 增强版
提供任务注册、状态追踪、自动恢复功能
"""

import json
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskManager:
    """任务管理器（支持文件锁防止并发冲突）"""
    
    def __init__(self, tasks_path: str = None):
        if tasks_path:
            self.tasks_path = Path(tasks_path)
        else:
            self.tasks_path = Path("~/.openclaw/workspace/agent-cluster/tasks.json").expanduser()
        
        # 确保目录存在
        self.tasks_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认结构
        self._ensure_valid_file()
    
    def _ensure_valid_file(self):
        """确保任务文件有效（处理空文件、损坏文件）"""
        if not self.tasks_path.exists():
            self._write_default()
            return
        
        # 检查空文件
        if self.tasks_path.stat().st_size == 0:
            self._write_default()
            return
        
        # 验证 JSON 格式
        try:
            with open(self.tasks_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    self._write_default()
        except (json.JSONDecodeError, Exception):
            self._write_default()
    
    def _write_default(self):
        """写入默认任务结构"""
        default_data = {
            "version": "2.2",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "running": [],
            "completed": [],
            "failed": [],
            "cancelled": [],
            "stats": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0
            }
        }
        self._write_raw(default_data)
    
    def _read_with_lock(self) -> Dict:
        """读取任务文件（带共享锁）"""
        with open(self.tasks_path, 'r', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _write_with_lock(self, data: Dict):
        """写入任务文件（带排他锁）"""
        data["last_updated"] = datetime.now().isoformat()
        self._write_raw(data)
    
    def _write_raw(self, data: Dict):
        """原始写入（带锁）"""
        with open(self.tasks_path, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def register_task(self, task_id: str, task_data: Dict) -> bool:
        """注册新任务"""
        try:
            data = self._read_with_lock()
            
            # 检查是否已存在
            for task in data.get("running", []):
                if task.get("id") == task_id:
                    print(f"⚠️ 任务 {task_id} 已存在")
                    return False
            
            # 添加任务
            task_entry = {
                "id": task_id,
                "status": TaskStatus.PENDING.value,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                **task_data
            }
            data["running"].append(task_entry)
            data["stats"]["total_tasks"] = data["stats"].get("total_tasks", 0) + 1
            
            self._write_with_lock(data)
            print(f"✅ 任务 {task_id} 已注册")
            return True
            
        except Exception as e:
            print(f"❌ 注册任务失败：{e}")
            return False
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          updates: Dict = None) -> bool:
        """更新任务状态"""
        try:
            data = self._read_with_lock()
            updated = False
            
            # 在 running 中查找
            for i, task in enumerate(data.get("running", [])):
                if task.get("id") == task_id:
                    task["status"] = status.value
                    
                    if status == TaskStatus.RUNNING and not task.get("started_at"):
                        task["started_at"] = datetime.now().isoformat()
                    elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        task["completed_at"] = datetime.now().isoformat()
                    
                    if updates:
                        task.update(updates)
                    
                    updated = True
                    
                    # 移动到对应列表
                    if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        data["running"].pop(i)
                        list_name = status.value + "s" if status.value != "cancelled" else "cancelled"
                        if list_name not in data:
                            data[list_name] = []
                        data[list_name].append(task)
                        
                        # 更新统计
                        if status == TaskStatus.COMPLETED:
                            data["stats"]["completed_tasks"] = data["stats"].get("completed_tasks", 0) + 1
                        elif status == TaskStatus.FAILED:
                            data["stats"]["failed_tasks"] = data["stats"].get("failed_tasks", 0) + 1
                    
                    break
            
            if updated:
                self._write_with_lock(data)
                print(f"✅ 任务 {task_id} 状态更新为 {status.value}")
                return True
            else:
                print(f"⚠️ 未找到任务 {task_id}")
                return False
                
        except Exception as e:
            print(f"❌ 更新任务状态失败：{e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        try:
            data = self._read_with_lock()
            
            # 在所有列表中查找
            for list_name in ["running", "completed", "failed", "cancelled"]:
                for task in data.get(list_name, []):
                    if task.get("id") == task_id:
                        return task
            
            return None
            
        except Exception as e:
            print(f"❌ 获取任务失败：{e}")
            return None
    
    def get_running_tasks(self) -> List[Dict]:
        """获取所有运行中的任务"""
        try:
            data = self._read_with_lock()
            return data.get("running", [])
        except Exception as e:
            print(f"❌ 获取运行任务失败：{e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取任务统计"""
        try:
            data = self._read_with_lock()
            return data.get("stats", {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0
            })
        except Exception as e:
            print(f"❌ 获取统计失败：{e}")
            return {}
    
    def cleanup_old_tasks(self, days: int = 7) -> int:
        """清理旧任务（保留最近 N 天）"""
        try:
            data = self._read_with_lock()
            cleaned = 0
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for list_name in ["completed", "failed", "cancelled"]:
                original_count = len(data.get(list_name, []))
                data[list_name] = [
                    task for task in data.get(list_name, [])
                    if task.get("completed_at") and 
                    datetime.fromisoformat(task["completed_at"]).timestamp() > cutoff
                ]
                cleaned += original_count - len(data[list_name])
            
            if cleaned > 0:
                self._write_with_lock(data)
                print(f"✅ 清理了 {cleaned} 个旧任务")
            
            return cleaned
            
        except Exception as e:
            print(f"❌ 清理任务失败：{e}")
            return 0


# 便捷函数
def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager()


if __name__ == "__main__":
    # 测试
    manager = TaskManager()
    print("任务文件路径:", manager.tasks_path)
    print("当前统计:", manager.get_stats())
    print("运行中任务:", len(manager.get_running_tasks()))
