"""
SQLite 数据库模块
提供工作流、部署、Bug 等数据的持久化存储
"""

import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from .config_loader import config


class Database:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            # 从配置获取
            db_url = config.database_url.replace('sqlite:///', '')
            self.db_path = Path(db_path) if db_path else Path(db_url)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 工作流表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT UNIQUE NOT NULL,
                    requirement TEXT,
                    project TEXT DEFAULT 'default',
                    status TEXT NOT NULL DEFAULT 'pending',
                    phase INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    cost REAL DEFAULT 0,
                    error_message TEXT,
                    metadata TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at)')
            
            # 部署表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deployment_id TEXT UNIQUE NOT NULL,
                    workflow_id TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    metadata TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deployments_workflow ON deployments(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status)')
            
            # Bug 表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bug_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT NOT NULL DEFAULT 'new',
                    project TEXT DEFAULT 'default',
                    files TEXT,
                    workflow_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bugs_status ON bugs(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bugs_priority ON bugs(priority)')
            
            # 成本记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT,
                    agent_id TEXT,
                    model TEXT,
                    tokens_in INTEGER,
                    tokens_out INTEGER,
                    cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_workflow ON cost_records(workflow_id)')
            
            # 会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    user_id TEXT,
                    ip TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
    
    # ========== 工作流 CRUD ==========
    
    def create_workflow(self, workflow_id: str, requirement: str, project: str = 'default') -> bool:
        """创建工作流"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO workflows (workflow_id, requirement, project, status, phase)
                    VALUES (?, ?, ?, 'pending', 0)
                ''', (workflow_id, requirement, project))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workflows WHERE workflow_id = ?', (workflow_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_workflow_status(self, workflow_id: str, status: str, phase: int = None, error_message: str = None) -> bool:
        """更新工作流状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if phase is not None:
                cursor.execute('''
                    UPDATE workflows 
                    SET status = ?, phase = ?, updated_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE workflow_id = ?
                ''', (status, phase, error_message, workflow_id))
            else:
                cursor.execute('''
                    UPDATE workflows 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE workflow_id = ?
                ''', (status, error_message, workflow_id))
            return cursor.rowcount > 0
    
    def complete_workflow(self, workflow_id: str, cost: float = 0, metadata: Dict = None) -> bool:
        """完成工作流"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE workflows 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP, 
                    updated_at = CURRENT_TIMESTAMP, cost = ?, metadata = ?
                WHERE workflow_id = ?
            ''', (cost, json.dumps(metadata) if metadata else None, workflow_id))
            return cursor.rowcount > 0
    
    def get_workflows(self, status: str = None, project: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取工作流列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM workflows WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            if project:
                query += ' AND project = ?'
                params.append(project)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workflows WHERE workflow_id = ?', (workflow_id,))
            return cursor.rowcount > 0
    
    # ========== 部署 CRUD ==========
    
    def create_deployment(self, deployment_id: str, workflow_id: str, environment: str) -> bool:
        """创建部署记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO deployments (deployment_id, workflow_id, environment, status)
                    VALUES (?, ?, ?, 'pending')
                ''', (deployment_id, workflow_id, environment))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def update_deployment_status(self, deployment_id: str, status: str, error_message: str = None) -> bool:
        """更新部署状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status == 'running':
                cursor.execute('''
                    UPDATE deployments 
                    SET status = ?, started_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE deployment_id = ?
                ''', (status, error_message, deployment_id))
            elif status in ('completed', 'failed', 'cancelled'):
                cursor.execute('''
                    UPDATE deployments 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE deployment_id = ?
                ''', (status, error_message, deployment_id))
            else:
                cursor.execute('''
                    UPDATE deployments 
                    SET status = ?, error_message = ?
                    WHERE deployment_id = ?
                ''', (status, error_message, deployment_id))
            return cursor.rowcount > 0
    
    def get_deployments(self, workflow_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取部署列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM deployments WHERE 1=1'
            params = []
            
            if workflow_id:
                query += ' AND workflow_id = ?'
                params.append(workflow_id)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== Bug CRUD ==========
    
    def create_bug(self, bug_id: str, title: str, description: str, priority: str = 'medium', 
                   project: str = 'default', files: str = None) -> bool:
        """创建 Bug 记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO bugs (bug_id, title, description, priority, project, files, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'new')
                ''', (bug_id, title, description, priority, project, files))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def update_bug_status(self, bug_id: str, status: str, workflow_id: str = None) -> bool:
        """更新 Bug 状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status == 'resolved':
                cursor.execute('''
                    UPDATE bugs 
                    SET status = ?, workflow_id = ?, resolved_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE bug_id = ?
                ''', (status, workflow_id, bug_id))
            else:
                cursor.execute('''
                    UPDATE bugs 
                    SET status = ?, workflow_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE bug_id = ?
                ''', (status, workflow_id, bug_id))
            return cursor.rowcount > 0
    
    def get_bugs(self, status: str = None, project: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取 Bug 列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM bugs WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            if project:
                query += ' AND project = ?'
                params.append(project)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== 成本记录 ==========
    
    def add_cost_record(self, workflow_id: str, agent_id: str, model: str, 
                       tokens_in: int, tokens_out: int, cost: float) -> bool:
        """添加成本记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cost_records (workflow_id, agent_id, model, tokens_in, tokens_out, cost)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (workflow_id, agent_id, model, tokens_in, tokens_out, cost))
            return True
    
    def get_cost_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取成本统计"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总成本
            cursor.execute('''
                SELECT SUM(cost) as total, COUNT(*) as count
                FROM cost_records
                WHERE created_at >= datetime('now', '-' || ? || ' days')
            ''', (days,))
            row = cursor.fetchone()
            
            # 按模型统计
            cursor.execute('''
                SELECT model, SUM(cost) as cost, SUM(tokens_in + tokens_out) as tokens, COUNT(*) as calls
                FROM cost_records
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY model
            ''', (days,))
            by_model = {row['model']: {'cost': row['cost'] or 0, 'tokens': row['tokens'] or 0, 'calls': row['calls'] or 0} 
                       for row in cursor.fetchall()}
            
            return {
                'total_cost': row['total'] or 0,
                'total_calls': row['count'] or 0,
                'by_model': by_model
            }
    
    # ========== 会话管理 ==========
    
    def create_session(self, token: str, username: str, user_id: str = None, 
                      ip: str = None, role: str = 'user') -> bool:
        """创建会话"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO sessions (token, username, user_id, ip, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (token, username, user_id, ip, role))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sessions WHERE token = ?', (token,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_session_activity(self, token: str) -> bool:
        """更新会话活动时间"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sessions 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE token = ?
            ''', (token,))
            return cursor.rowcount > 0
    
    def delete_session(self, token: str) -> bool:
        """删除会话"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
            return cursor.rowcount > 0
    
    def cleanup_expired_sessions(self, expiration_hours: int = 24) -> int:
        """清理过期会话"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM sessions 
                WHERE last_activity < datetime('now', '-' || ? || ' hours')
            ''', (expiration_hours,))
            return cursor.rowcount


# 全局数据库实例
db = None


def get_database() -> Database:
    """获取数据库实例"""
    global db
    if db is None:
        db = Database()
    return db


def init_database():
    """初始化数据库"""
    global db
    db = Database()
    return db
