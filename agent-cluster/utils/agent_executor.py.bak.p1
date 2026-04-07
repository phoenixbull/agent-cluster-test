#!/usr/bin/env python3
"""
Agent 任务执行器
触发 Agent 执行任务并收集生成的代码文件
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class AgentTaskExecutor:
    """
    Agent 任务执行器
    
    功能:
    - 触发 Agent 执行任务
    - 等待执行完成
    - 收集生成的代码
    - 保存为工程文件
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace"):
        self.workspace = Path(workspace).expanduser()
        self.agents_dir = self.workspace / "agents"
        self.current_project = "default"
    
    def set_project(self, project_id: str, project_config: Dict):
        """
        设置当前项目
        
        Args:
            project_id: 项目 ID
            project_config: 项目配置
        """
        self.current_project = project_id
        # 项目特定的工作区
        workspace_str = project_config.get("workspace", "~/.openclaw/workspace/agent-cluster-test")
        self.workspace = Path(workspace_str).expanduser()
        self.agents_dir = self.workspace / "agents"
        
        # 确保目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"   📁 设置项目工作区：{self.workspace}")
    
    def execute_task(self, agent_id: str, task: str, output_dir: Path, timeout_seconds: int = 3600) -> Dict:
        """
        执行任务并收集代码
        
        Args:
            agent_id: Agent ID
            task: 任务描述
            output_dir: 输出目录
            timeout_seconds: 超时时间
        
        Returns:
            执行结果
        """
        print(f"\n🚀 执行任务：{agent_id}")
        print(f"   任务：{task[:100]}...")
        
        # 1. 创建会话
        session_id = self._create_session(agent_id, task)
        print(f"   ✅ 会话已创建：{session_id}")
        
        # 2. 等待执行完成 (模拟真实 Agent 执行)
        print(f"   ⏳ 等待 Agent 执行...")
        execution_result = self._simulate_agent_execution(agent_id, task, session_id)
        
        # 3. 收集代码文件
        print(f"\n   📦 收集代码文件...")
        code_files = self._collect_code_files(session_id, output_dir, execution_result)
        
        # 4. 更新会话状态
        self._update_session(agent_id, session_id, code_files)
        
        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "completed",
            "code_files": code_files,
            "execution_result": execution_result
        }
    
    def _create_session(self, agent_id: str, task: str) -> str:
        """创建会话"""
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        sessions_dir = self.agents_dir / agent_id / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        session_file = sessions_dir / f"{session_id}.json"
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
        
        return session_id
    
    def _simulate_agent_execution(self, agent_id: str, task: str, session_id: str) -> Dict:
        """
        模拟 Agent 执行 (真实场景应该调用 OpenClaw API)
        
        这里根据任务类型生成示例代码
        """
        # 根据 Agent 类型和任务生成对应的代码
        if agent_id == "codex":
            return self._generate_backend_code(task)
        elif agent_id == "claude-code":
            return self._generate_frontend_code(task)
        elif agent_id == "designer":
            return self._generate_design_assets(task)
        else:
            return self._generate_generic_code(task)
    
    def _generate_backend_code(self, task: str) -> Dict:
        """生成后端代码"""
        task_lower = task.lower()
        
        # 根据任务关键词生成不同的代码
        if "待办" in task or "todo" in task_lower:
            return {
                "files": [
                    {
                        "filename": "todo_api.py",
                        "language": "python",
                        "content": self._get_todo_api_code()
                    },
                    {
                        "filename": "models.py",
                        "language": "python",
                        "content": self._get_todo_models_code()
                    }
                ]
            }
        elif "登录" in task or "login" in task_lower:
            return {
                "files": [
                    {
                        "filename": "auth_api.py",
                        "language": "python",
                        "content": self._get_auth_api_code()
                    },
                    {
                        "filename": "user_model.py",
                        "language": "python",
                        "content": self._get_user_model_code()
                    }
                ]
            }
        else:
            return {
                "files": [
                    {
                        "filename": "api.py",
                        "language": "python",
                        "content": self._get_generic_api_code(task)
                    }
                ]
            }
    
    def _generate_frontend_code(self, task: str) -> Dict:
        """生成前端代码"""
        task_lower = task.lower()
        
        if "待办" in task or "todo" in task_lower:
            return {
                "files": [
                    {
                        "filename": "TodoApp.jsx",
                        "language": "javascript",
                        "content": self._get_todo_component_code()
                    },
                    {
                        "filename": "TodoApp.css",
                        "language": "css",
                        "content": self._get_todo_styles_code()
                    }
                ]
            }
        elif "登录" in task or "login" in task_lower:
            return {
                "files": [
                    {
                        "filename": "LoginForm.jsx",
                        "language": "javascript",
                        "content": self._get_login_component_code()
                    },
                    {
                        "filename": "LoginForm.css",
                        "language": "css",
                        "content": self._get_login_styles_code()
                    }
                ]
            }
        else:
            return {
                "files": [
                    {
                        "filename": "App.jsx",
                        "language": "javascript",
                        "content": self._get_generic_component_code(task)
                    }
                ]
            }
    
    def _generate_design_assets(self, task: str) -> Dict:
        """生成设计资源"""
        return {
            "files": [
                {
                    "filename": "design_spec.md",
                    "language": "markdown",
                    "content": self._get_design_spec(task)
                }
            ]
        }
    
    def _generate_generic_code(self, task: str) -> Dict:
        """生成通用代码"""
        return {
            "files": [
                {
                    "filename": "main.py",
                    "language": "python",
                    "content": f"# Generated code for: {task}\n\ndef main():\n    print('Hello from generated code')\n\nif __name__ == '__main__':\n    main()\n"
                }
            ]
        }
    
    def _collect_code_files(self, session_id: str, output_dir: Path, execution_result: Dict) -> List[Dict]:
        """收集代码文件"""
        collected = []
        files = execution_result.get("files", [])
        
        for file_info in files:
            filename = file_info["filename"]
            content = file_info["content"]
            language = file_info.get("language", "text")
            
            # 创建子目录 (按语言)
            subdir_map = {
                "python": "backend",
                "javascript": "frontend",
                "css": "frontend",
                "html": "frontend",
                "typescript": "frontend"
            }
            subdir = subdir_map.get(language, "other")
            
            target_dir = output_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            file_path = target_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            collected.append({
                "filename": filename,
                "path": str(file_path),
                "language": language,
                "size": len(content),
                "subdir": subdir
            })
            
            print(f"      📝 保存：{subdir}/{filename} ({len(content)} 字节)")
        
        return collected
    
    def _update_session(self, agent_id: str, session_id: str, code_files: List[Dict]):
        """更新会话状态"""
        sessions_dir = self.agents_dir / agent_id / "sessions"
        session_file = sessions_dir / f"{session_id}.json"
        
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            session_data["status"] = "completed"
            session_data["completed_at"] = datetime.now().isoformat()
            session_data["code_files"] = code_files
            session_data["messages"] = [
                {
                    "role": "assistant",
                    "content": f"任务已完成，生成了 {len(code_files)} 个文件",
                    "timestamp": datetime.now().isoformat(),
                    "code_files": code_files
                }
            ]
            
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    # ========== 代码模板 ==========
    
    def _get_todo_api_code(self) -> str:
        return '''"""
待办事项 API 模块
提供待办事项的增删改查功能
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid


class TodoItem:
    """待办事项模型"""
    
    def __init__(self, title: str, description: str = "", completed: bool = False):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.completed = completed
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TodoAPI:
    """待办事项 API"""
    
    def __init__(self):
        self.todos: Dict[str, TodoItem] = {}
    
    def create_todo(self, title: str, description: str = "") -> TodoItem:
        """创建待办事项"""
        todo = TodoItem(title, description)
        self.todos[todo.id] = todo
        return todo
    
    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """获取待办事项"""
        return self.todos.get(todo_id)
    
    def list_todos(self, completed: Optional[bool] = None) -> List[TodoItem]:
        """列出待办事项"""
        todos = list(self.todos.values())
        if completed is not None:
            todos = [t for t in todos if t.completed == completed]
        return todos
    
    def update_todo(self, todo_id: str, title: str = None, 
                    description: str = None, completed: bool = None) -> Optional[TodoItem]:
        """更新待办事项"""
        todo = self.todos.get(todo_id)
        if not todo:
            return None
        
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if completed is not None:
            todo.completed = completed
        
        todo.updated_at = datetime.now()
        return todo
    
    def delete_todo(self, todo_id: str) -> bool:
        """删除待办事项"""
        if todo_id in self.todos:
            del self.todos[todo_id]
            return True
        return False
    
    def toggle_complete(self, todo_id: str) -> Optional[TodoItem]:
        """切换完成状态"""
        todo = self.todos.get(todo_id)
        if todo:
            todo.completed = not todo.completed
            todo.updated_at = datetime.now()
        return todo


# Flask REST API 示例
def create_flask_app():
    """创建 Flask 应用"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    api = TodoAPI()
    
    @app.route('/todos', methods=['POST'])
    def create():
        data = request.json
        todo = api.create_todo(data['title'], data.get('description', ''))
        return jsonify(todo.to_dict()), 201
    
    @app.route('/todos', methods=['GET'])
    def list_all():
        completed = request.args.get('completed')
        if completed is not None:
            completed = completed.lower() == 'true'
        todos = api.list_todos(completed)
        return jsonify([t.to_dict() for t in todos])
    
    @app.route('/todos/<todo_id>', methods=['GET'])
    def get(todo_id):
        todo = api.get_todo(todo_id)
        if not todo:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(todo.to_dict())
    
    @app.route('/todos/<todo_id>', methods=['PUT'])
    def update(todo_id):
        data = request.json
        todo = api.update_todo(
            todo_id,
            data.get('title'),
            data.get('description'),
            data.get('completed')
        )
        if not todo:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(todo.to_dict())
    
    @app.route('/todos/<todo_id>', methods=['DELETE'])
    def delete(todo_id):
        if api.delete_todo(todo_id):
            return '', 204
        return jsonify({'error': 'Not found'}), 404
    
    @app.route('/todos/<todo_id>/toggle', methods=['POST'])
    def toggle(todo_id):
        todo = api.toggle_complete(todo_id)
        if not todo:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(todo.to_dict())
    
    return app


if __name__ == '__main__':
    app = create_flask_app()
    app.run(debug=True, port=5000)
'''
    
    def _get_todo_models_code(self) -> str:
        return '''"""
待办事项数据模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Todo(Base):
    """待办事项数据库模型"""
    
    __tablename__ = 'todos'
    
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
'''
    
    def _get_todo_component_code(self) -> str:
        return '''import React, { useState, useEffect } from 'react';
import './TodoApp.css';

function TodoApp() {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');
  const [filter, setFilter] = useState('all');

  // 加载待办事项
  useEffect(() => {
    loadTodos();
  }, []);

  const loadTodos = async () => {
    try {
      const response = await fetch('/api/todos');
      const data = await response.json();
      setTodos(data);
    } catch (error) {
      console.error('Failed to load todos:', error);
    }
  };

  // 添加待办事项
  const addTodo = async (e) => {
    e.preventDefault();
    if (!newTodo.trim()) return;

    try {
      const response = await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTodo })
      });
      const todo = await response.json();
      setTodos([...todos, todo]);
      setNewTodo('');
    } catch (error) {
      console.error('Failed to add todo:', error);
    }
  };

  // 切换完成状态
  const toggleTodo = async (id) => {
    try {
      const response = await fetch(`/api/todos/${id}/toggle`, {
        method: 'POST'
      });
      const updated = await response.json();
      setTodos(todos.map(t => t.id === id ? updated : t));
    } catch (error) {
      console.error('Failed to toggle todo:', error);
    }
  };

  // 删除待办事项
  const deleteTodo = async (id) => {
    try {
      await fetch(`/api/todos/${id}`, { method: 'DELETE' });
      setTodos(todos.filter(t => t.id !== id));
    } catch (error) {
      console.error('Failed to delete todo:', error);
    }
  };

  // 过滤待办事项
  const filteredTodos = todos.filter(todo => {
    if (filter === 'active') return !todo.completed;
    if (filter === 'completed') return todo.completed;
    return true;
  });

  return (
    <div className="todo-app">
      <h1>待办事项</h1>
      
      <form onSubmit={addTodo} className="todo-form">
        <input
          type="text"
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          placeholder="添加新的待办事项..."
        />
        <button type="submit">添加</button>
      </form>

      <div className="filters">
        <button 
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          全部
        </button>
        <button 
          className={filter === 'active' ? 'active' : ''}
          onClick={() => setFilter('active')}
        >
          进行中
        </button>
        <button 
          className={filter === 'completed' ? 'active' : ''}
          onClick={() => setFilter('completed')}
        >
          已完成
        </button>
      </div>

      <ul className="todo-list">
        {filteredTodos.map(todo => (
          <li key={todo.id} className={todo.completed ? 'completed' : ''}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
            />
            <span className="todo-title">{todo.title}</span>
            <button onClick={() => deleteTodo(todo.id)} className="delete-btn">
              删除
            </button>
          </li>
        ))}
      </ul>

      <div className="stats">
        总计：{todos.length} | 
        已完成：{todos.filter(t => t.completed).length} | 
        进行中：{todos.filter(t => !t.completed).length}
      </div>
    </div>
  );
}

export default TodoApp;
'''
    
    def _get_todo_styles_code(self) -> str:
        return '''.todo-app {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
}

.todo-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.todo-form input {
  flex: 1;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.todo-form button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  justify-content: center;
}

.filters button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.filters button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.todo-list {
  list-style: none;
  padding: 0;
}

.todo-list li {
  display: flex;
  align-items: center;
  padding: 10px;
  border: 1px solid #ddd;
  margin-bottom: 8px;
  border-radius: 4px;
}

.todo-list li.completed {
  background: #f8f9fa;
}

.todo-list li.completed .todo-title {
  text-decoration: line-through;
  color: #999;
}

.todo-title {
  flex: 1;
  margin-left: 10px;
}

.delete-btn {
  padding: 5px 10px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.stats {
  margin-top: 20px;
  text-align: center;
  color: #666;
}
'''
    
    def _get_auth_api_code(self) -> str:
        return '''"""
用户认证 API 模块
提供登录、注册、密码找回功能
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
import hashlib
import secrets


class UserAuthAPI:
    """用户认证 API"""
    
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """密码哈希"""
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed, salt
    
    def register(self, username: str, email: str, password: str) -> Dict:
        """用户注册"""
        # 检查用户是否已存在
        if username in self.users:
            raise ValueError("用户名已存在")
        
        # 哈希密码
        hashed_password, salt = self._hash_password(password)
        
        # 创建用户
        user = {
            "id": secrets.token_hex(16),
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "salt": salt,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        self.users[username] = user
        return {"id": user["id"], "username": username}
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        user = self.users.get(username)
        if not user:
            raise ValueError("用户名或密码错误")
        
        # 验证密码
        hashed_password, _ = self._hash_password(password, user["salt"])
        if hashed_password != user["password_hash"]:
            raise ValueError("用户名或密码错误")
        
        # 创建会话
        session_token = secrets.token_hex(32)
        self.sessions[session_token] = {
            "user_id": user["id"],
            "username": username,
            "expires_at": datetime.now() + timedelta(days=7)
        }
        
        return {
            "token": session_token,
            "user": {"id": user["id"], "username": username},
            "expires_in": 604800
        }
    
    def logout(self, token: str) -> bool:
        """用户登出"""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False
    
    def reset_password(self, email: str) -> bool:
        """密码重置"""
        # 查找用户
        user = None
        for u in self.users.values():
            if u["email"] == email:
                user = u
                break
        
        if not user:
            return False
        
        # 生成重置令牌
        reset_token = secrets.token_hex(32)
        # TODO: 发送重置邮件
        
        return True
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证会话令牌"""
        session = self.sessions.get(token)
        if not session:
            return None
        
        if session["expires_at"] < datetime.now():
            del self.sessions[token]
            return None
        
        return session
'''
    
    def _get_user_model_code(self) -> str:
        return '''"""
用户数据模型
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """用户模型"""
    
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(64), nullable=False)
    salt = Column(String(32), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
'''
    
    def _get_login_component_code(self) -> str:
        return '''import React, { useState } from 'react';
import './LoginForm.css';

function LoginForm({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || '登录失败');
      }

      const data = await response.json();
      localStorage.setItem('token', data.token);
      
      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>用户登录</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label>用户名</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label>密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? '登录中...' : '登录'}
        </button>

        <div className="login-links">
          <a href="/register">注册账号</a>
          <a href="/forgot-password">忘记密码？</a>
        </div>
      </form>
    </div>
  );
}

export default LoginForm;
'''
    
    def _get_login_styles_code(self) -> str:
        return '''.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f5f5;
}

.login-form {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

.login-form h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.login-form button {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.login-form button:disabled {
  background: #ccc;
}

.error-message {
  background: #fee;
  color: #c00;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.login-links {
  margin-top: 20px;
  text-align: center;
}

.login-links a {
  color: #007bff;
  text-decoration: none;
  margin: 0 10px;
}
'''
    
    def _get_generic_api_code(self, task: str) -> str:
        return f'''"""
生成的 API 模块
任务：{task}
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({{"status": "ok"}})

# TODO: 实现具体业务逻辑

if __name__ == '__main__':
    app.run(debug=True)
'''
    
    def _get_generic_component_code(self, task: str) -> str:
        return f'''import React from 'react';

// 任务：{task}
function GeneratedComponent() {{
  return (
    <div className="generated-component">
      <h2>Generated Component</h2>
      <p>Task: {task}</p>
    </div>
  );
}}

export default GeneratedComponent;
'''
    
    def _get_design_spec(self, task: str) -> str:
        return f'''# 设计规范

## 任务
{task}

## 颜色方案
- 主色：#007bff
- 成功：#28a745
- 警告：#ffc107
- 危险：#dc3545

## 字体
- 主字体：-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
- 代码字体：'Courier New', monospace

## 间距
- 小：8px
- 中：16px
- 大：24px

## 组件
- 按钮：圆角 4px
- 输入框：圆角 4px，边框 1px
- 卡片：阴影 0 2px 10px rgba(0,0,0,0.1)
'''


# ========== 测试入口 ==========

def main():
    """测试函数"""
    executor = AgentTaskExecutor()
    
    output_dir = Path("/tmp/agent-test-output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试待办事项
    result = executor.execute_task(
        agent_id="codex",
        task="创建一个待办事项管理功能",
        output_dir=output_dir
    )
    
    print(f"\n✅ 执行完成")
    print(f"   文件数：{len(result['code_files'])}")
    for f in result['code_files']:
        print(f"   - {f['path']}")


if __name__ == "__main__":
    main()
