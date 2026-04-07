#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 集群 Web 界面
提供可视化的工作流管理、任务提交、状态监控功能
支持管理员登录验证
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import subprocess
import threading
import hashlib

# 项目根目录
BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"

# 确保目录存在
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# 认证配置文件
AUTH_CONFIG_FILE = MEMORY_DIR / "auth_config.json"
SESSIONS_FILE = MEMORY_DIR / "sessions.json"


class WebUIHandler(SimpleHTTPRequestHandler):
    """Web 界面请求处理器"""
    
    # 不需要认证的路径（注意：不包含 '/' 首页）
    PUBLIC_PATHS = ['/api/status', '/login', '/api/login', '/static/', '/favicon.ico']
    
    def __init__(self, *args, **kwargs):
        self.workflow_state = {}
        self.load_workflow_state()
        self.auth_config = self._load_auth_config()
        self.sessions = self._load_sessions()
        super().__init__(*args, **kwargs)
    
    def _load_auth_config(self) -> dict:
        """加载认证配置"""
        default_config = {
            "enabled": True,
            "username": "admin",
            "password_hash": hashlib.sha256("admin888".encode()).hexdigest(),
            "session_timeout_hours": 24
        }
        
        if AUTH_CONFIG_FILE.exists():
            try:
                with open(AUTH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("auth", default_config)
            except:
                pass
        
        return default_config
    
    def _load_sessions(self) -> dict:
        """加载会话"""
        if SESSIONS_FILE.exists():
            try:
                with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_sessions(self):
        """保存会话"""
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_client_ip(self) -> str:
        """获取客户端 IP"""
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0]
    
    def _check_auth(self) -> tuple:
        """
        检查认证状态
        
        Returns:
            (is_authenticated, token, redirect_needed)
        """
        # 如果认证未启用，直接通过
        if not self.auth_config.get("enabled", True):
            return True, None, False
        
        # 公开路径不需要认证
        for public_path in self.PUBLIC_PATHS:
            if self.path.startswith(public_path):
                return True, None, False
        
        # 从 Cookie 获取 token
        cookie = self.headers.get('Cookie', '')
        token = None
        for item in cookie.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                if key == 'auth_token':
                    token = value
                    break
        
        if not token:
            return False, None, True
        
        # 验证 token
        if token in self.sessions:
            session = self.sessions[token]
            # 检查是否过期
            import time
            timeout = self.auth_config.get("session_timeout_hours", 24) * 3600
            if time.time() - session.get("created_at", 0) < timeout:
                # 更新最后活动时间
                session["last_activity"] = time.time()
                self._save_sessions()
                return True, token, False
        
        return False, None, True
    
    def _generate_token(self) -> str:
        """生成会话 token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def load_workflow_state(self):
        """加载工作流状态"""
        state_file = MEMORY_DIR / "workflow_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    self.workflow_state = json.load(f)
            except:
                self.workflow_state = {}
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # 检查认证
        is_auth, token, need_redirect = self._check_auth()
        
        # 公开路径（注意：不包含 '/' 首页）
        if path in ['/login'] or path.startswith('/api/status') or path.startswith('/static/'):
            pass  # 公开路径，继续处理
        elif not is_auth and need_redirect:
            # 需要认证但未登录，重定向到登录页
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return
        
        query = urllib.parse.parse_qs(parsed_path.query)
        
        # API 端点
        if path == '/api/status':
            self.send_json_response(self.get_status())
        elif path == '/api/workflows':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_workflows())
        elif path == '/api/templates':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_templates())
        elif path == '/api/costs':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_costs())
        elif path == '/api/projects':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_projects())
        elif path == '/api/logout':
            self.handle_logout(token)
        elif path == '/login':
            self.send_html_page(self.get_login_page())
        elif path == '/':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_main_page())
        elif path == '/workflows':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_workflows_page())
        elif path == '/templates':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_templates_page())
        elif path == '/costs':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_costs_page())
        elif path == '/settings':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_settings_page())
        else:
            super().do_GET()
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except:
            data = {}
        
        # 登录 API 不需要认证
        if path == '/api/login':
            self.handle_login(data)
            return
        
        # 其他 API 需要认证
        is_auth, token, _ = self._check_auth()
        if not is_auth:
            self.send_json_response({"error": "未授权，请先登录"}, 401)
            return
        
        if path == '/api/submit':
            result = self.submit_task(data)
            self.send_json_response(result)
        elif path == '/api/template/save':
            result = self.save_template(data)
            self.send_json_response(result)
        elif path == '/api/template/delete':
            result = self.delete_template(data)
            self.send_json_response(result)
        elif path == '/api/logout':
            self.handle_logout(token)
        elif path == '/api/change-password':
            self.handle_change_password(data, token)
        else:
            self.send_error(404, "Not Found")
    
    def send_json_response(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html_page(self, html):
        """发送 HTML 页面"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_login(self, data):
        """处理登录请求"""
        import time
        
        username = data.get("username", "")
        password = data.get("password", "")
        client_ip = self._get_client_ip()
        
        # 验证用户名和密码
        stored_username = self.auth_config.get("username", "admin")
        stored_hash = self.auth_config.get("password_hash", "")
        
        if username != stored_username:
            self.send_json_response({
                "success": False,
                "error": "用户名或密码错误"
            })
            return
        
        if self._hash_password(password) != stored_hash:
            self.send_json_response({
                "success": False,
                "error": "用户名或密码错误"
            })
            return
        
        # 登录成功，生成 token
        token = self._generate_token()
        self.sessions[token] = {
            "username": username,
            "ip": client_ip,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        self._save_sessions()
        
        self.send_json_response({
            "success": True,
            "message": "登录成功",
            "token": token
        })
    
    def handle_logout(self, token):
        """处理登出请求"""
        if token and token in self.sessions:
            del self.sessions[token]
            self._save_sessions()
        
        self.send_response(302)
        self.send_header('Location', '/login')
        self.send_header('Set-Cookie', 'auth_token=; Path=/; Max-Age=0')
        self.end_headers()
    
    def handle_change_password(self, data, token):
        """处理修改密码请求"""
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")
        
        # 验证原密码
        stored_hash = self.auth_config.get("password_hash", "")
        if self._hash_password(old_password) != stored_hash:
            self.send_json_response({
                "success": False,
                "error": "原密码错误"
            })
            return
        
        # 验证新密码长度
        if len(new_password) < 6:
            self.send_json_response({
                "success": False,
                "error": "密码长度至少 6 位"
            })
            return
        
        # 更新密码
        self.auth_config["password_hash"] = self._hash_password(new_password)
        
        # 保存配置
        config_file = MEMORY_DIR / "auth_config.json"
        config = {"auth": self.auth_config}
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 使所有会话失效
        self.sessions = {}
        self._save_sessions()
        
        self.send_json_response({
            "success": True,
            "message": "密码修改成功，请重新登录"
        })
    
    def get_login_page(self):
        """获取登录页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - Agent 集群控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            border-radius: 16px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 28px;
            color: #333;
            margin-bottom: 10px;
        }
        .logo p {
            color: #666;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🤖 Agent 集群</h1>
            <p>管理员登录</p>
        </div>
        
        <div class="error-message" id="errorMessage"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" placeholder="请输入用户名" autocomplete="username" required>
            </div>
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" placeholder="请输入密码" autocomplete="current-password" required>
            </div>
            <button type="submit" class="btn" id="submitBtn">登录</button>
        </form>
        
        <div class="footer">
            Agent Cluster Console v2.0
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('submitBtn');
            const errorDiv = document.getElementById('errorMessage');
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            btn.disabled = true;
            btn.textContent = '登录中...';
            errorDiv.style.display = 'none';
            
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await res.json();
                
                if (data.success) {
                    // 设置 cookie
                    document.cookie = `auth_token=${data.token}; Path=/; Max-Age=${24*60*60}; SameSite=Strict`;
                    // 跳转到主页
                    window.location.href = '/';
                } else {
                    errorDiv.textContent = data.error || '登录失败';
                    errorDiv.style.display = 'block';
                    btn.disabled = false;
                    btn.textContent = '登录';
                }
            } catch (err) {
                errorDiv.textContent = '网络错误，请稍后重试';
                errorDiv.style.display = 'block';
                btn.disabled = false;
                btn.textContent = '登录';
            }
        });
    </script>
</body>
</html>
"""
    
    def get_status(self):
        """获取系统状态"""
        self.load_workflow_state()
        
        # 检查 orchestrator 是否运行
        orchestrator_running = False
        try:
            result = subprocess.run(['pgrep', '-f', 'orchestrator.py'], 
                                  capture_output=True, text=True, timeout=5)
            orchestrator_running = bool(result.stdout.strip())
        except:
            pass
        
        return {
            "status": "running" if orchestrator_running else "stopped",
            "timestamp": datetime.now().isoformat(),
            "active_workflows": self.workflow_state.get("active_count", 0),
            "completed_today": self.workflow_state.get("completed_today", 0),
            "failed_today": self.workflow_state.get("failed_today", 0)
        }
    
    def get_workflows(self):
        """获取工作流列表"""
        self.load_workflow_state()
        workflows_data = self.workflow_state.get("workflows", {})
        
        # 兼容字典和列表两种格式
        if isinstance(workflows_data, dict):
            # 字典格式：{workflow_id: workflow_data, ...}
            workflows = list(workflows_data.values())
        elif isinstance(workflows_data, list):
            # 列表格式：[workflow_data, ...]
            workflows = workflows_data
        else:
            workflows = []
        
        # 按时间排序
        workflows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {"workflows": workflows[-50:]}  # 返回最近 50 条
    
    def get_templates(self):
        """获取模板列表"""
        template_file = MEMORY_DIR / "templates.json"
        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                return {"templates": templates}
            except:
                pass
        return {"templates": []}
    
    def get_costs(self):
        """获取成本统计"""
        cost_file = MEMORY_DIR / "cost_stats.json"
        if cost_file.exists():
            try:
                with open(cost_file, 'r', encoding='utf-8') as f:
                    costs = json.load(f)
                return costs
            except:
                pass
        
        # 返回默认统计
        return {
            "today": {"total": 0, "workflows": 0},
            "week": {"total": 0, "workflows": 0},
            "month": {"total": 0, "workflows": 0},
            "by_model": {}
        }
    
    def get_projects(self):
        """获取项目列表"""
        projects_file = BASE_DIR / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file, 'r', encoding='utf-8') as f:
                    projects = json.load(f)
                return {"projects": projects}
            except:
                pass
        return {"projects": []}
    
    def submit_task(self, data):
        """提交任务"""
        requirement = data.get("requirement", "")
        project = data.get("project", "default")
        template = data.get("template", "")
        
        if not requirement:
            return {"success": False, "error": "需求内容不能为空"}
        
        # 构建命令
        cmd = f"cd {BASE_DIR} && python3 orchestrator.py \"{requirement}\""
        
        # 在后台执行
        try:
            subprocess.Popen(cmd, shell=True, 
                           stdout=open(LOGS_DIR / "web_submit.log", 'a'),
                           stderr=subprocess.STDOUT)
            
            return {
                "success": True,
                "message": "任务已提交，工作流已启动",
                "requirement": requirement,
                "project": project
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_template(self, data):
        """保存模板"""
        template_file = MEMORY_DIR / "templates.json"
        
        templates = []
        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            except:
                pass
        
        new_template = {
            "id": f"tpl_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": data.get("name", "未命名模板"),
            "description": data.get("description", ""),
            "requirement": data.get("requirement", ""),
            "project": data.get("project", "default"),
            "created_at": datetime.now().isoformat()
        }
        
        templates.append(new_template)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "template": new_template}
    
    def delete_template(self, data):
        """删除模板"""
        template_file = MEMORY_DIR / "templates.json"
        
        if not template_file.exists():
            return {"success": False, "error": "模板文件不存在"}
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            template_id = data.get("id")
            templates = [t for t in templates if t.get("id") != template_id]
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_main_page(self):
        """获取主页面"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent 集群控制台</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .nav {{ display: flex; gap: 20px; margin-top: 15px; }}
        .nav a {{ color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: background 0.3s; }}
        .nav a:hover {{ background: rgba(255,255,255,0.2); }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px; }}
        .status-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .card .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-top: 10px; }}
        .status.running {{ background: #d4edda; color: #155724; }}
        .status.stopped {{ background: #f8d7da; color: #721c24; }}
        .submit-form {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .submit-form h2 {{ margin-bottom: 20px; color: #333; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 8px; color: #555; font-weight: 500; }}
        .form-group textarea {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; min-height: 120px; }}
        .form-group select {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }}
        .btn {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s; }}
        .btn:hover {{ transform: translateY(-2px); }}
        .recent-workflows {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .recent-workflows h2 {{ margin-bottom: 20px; color: #333; }}
        .workflow-item {{ padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .workflow-item:last-child {{ border-bottom: none; }}
        .workflow-item .info {{ flex: 1; }}
        .workflow-item .title {{ font-weight: 500; color: #333; }}
        .workflow-item .meta {{ font-size: 12px; color: #999; margin-top: 5px; }}
        .workflow-item .status-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; }}
        .status-badge.completed {{ background: #d4edda; color: #155724; }}
        .status-badge.running {{ background: #cce5ff; color: #004085; }}
        .status-badge.failed {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Agent 集群控制台</h1>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings">⚙️ 设置</a>
            <a href="#" onclick="logout(); return false;" style="margin-left:auto;">🚪 登出</a>
        </div>
    </div>
    
    <div class="container">
        <div class="status-cards" id="statusCards">
            <div class="card">
                <h3>系统状态</h3>
                <div class="value" id="systemStatus">-</div>
                <span class="status" id="statusBadge">加载中...</span>
            </div>
            <div class="card">
                <h3>进行中的工作流</h3>
                <div class="value" id="activeWorkflows">-</div>
            </div>
            <div class="card">
                <h3>今日完成</h3>
                <div class="value" id="completedToday">-</div>
            </div>
            <div class="card">
                <h3>今日失败</h3>
                <div class="value" id="failedToday">-</div>
            </div>
        </div>
        
        <div class="submit-form">
            <h2>🚀 提交新任务</h2>
            <div class="form-group">
                <label>产品需求</label>
                <textarea id="requirement" placeholder="描述你想要实现的功能..."></textarea>
            </div>
            <div class="form-group">
                <label>选择项目</label>
                <select id="project">
                    <option value="default">默认项目</option>
                    <option value="ecommerce">电商项目</option>
                    <option value="blog">博客系统</option>
                    <option value="crm">CRM 系统</option>
                </select>
            </div>
            <button class="btn" onclick="submitTask()">提交任务</button>
        </div>
        
        <div class="recent-workflows">
            <h2>📋 最近工作流</h2>
            <div id="workflowList">加载中...</div>
        </div>
    </div>
    
    <script>
        async function loadStatus() {{
            try {{
                const res = await fetch('/api/status');
                const data = await res.json();
                
                document.getElementById('systemStatus').textContent = data.status === 'running' ? '运行中' : '已停止';
                document.getElementById('statusBadge').className = 'status ' + data.status;
                document.getElementById('statusBadge').textContent = data.status === 'running' ? '✅ 运行中' : '⏸️ 已停止';
                document.getElementById('activeWorkflows').textContent = data.active_workflows;
                document.getElementById('completedToday').textContent = data.completed_today;
                document.getElementById('failedToday').textContent = data.failed_today;
            }} catch (e) {{
                console.error('加载状态失败:', e);
            }}
        }}
        
        async function loadWorkflows() {{
            try {{
                const res = await fetch('/api/workflows');
                const data = await res.json();
                
                const list = document.getElementById('workflowList');
                if (data.workflows.length === 0) {{
                    list.innerHTML = '<p style="color:#999;text-align:center;padding:40px;">暂无工作流记录</p>';
                    return;
                }}
                
                list.innerHTML = data.workflows.slice(0, 10).map(wf => {{
                    const statusClass = wf.status === 'completed' ? 'completed' : wf.status === 'failed' ? 'failed' : 'running';
                    const statusText = wf.status === 'completed' ? '✅ 完成' : wf.status === 'failed' ? '❌ 失败' : '🔄 进行中';
                    return `
                        <div class="workflow-item">
                            <div class="info">
                                <div class="title">${{wf.requirement || '未命名任务'}}</div>
                                <div class="meta">${{wf.workflow_id}} · ${{wf.project || '默认项目'}} · ${{new Date(wf.created_at).toLocaleString('zh-CN')}}</div>
                            </div>
                            <span class="status-badge ${{statusClass}}">${{statusText}}</span>
                        </div>
                    `;
                }}).join('');
            }} catch (e) {{
                console.error('加载工作流失败:', e);
            }}
        }}
        
        async function submitTask() {{
            const requirement = document.getElementById('requirement').value.trim();
            const project = document.getElementById('project').value;
            
            if (!requirement) {{
                alert('请输入产品需求');
                return;
            }}
            
            try {{
                const res = await fetch('/api/submit', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ requirement, project }})
                }});
                const data = await res.json();
                
                if (data.success) {{
                    alert('✅ ' + data.message);
                    document.getElementById('requirement').value = '';
                    loadStatus();
                    loadWorkflows();
                }} else {{
                    alert('❌ ' + data.error);
                }}
            }} catch (e) {{
                alert('提交失败：' + e.message);
            }}
        }}
        
        // 登出功能
        async function logout() {{
            if (!confirm('确定要登出吗？')) return;
            
            try {{
                await fetch('/api/logout', {{ method: 'POST' }});
                // 清除 cookie
                document.cookie = 'auth_token=; Path=/; Max-Age=0';
                // 跳转到登录页
                window.location.href = '/login';
            }} catch (err) {{
                alert('登出失败：' + err.message);
            }}
        }}
        
        // 初始加载
        loadStatus();
        loadWorkflows();
        
        // 每 30 秒刷新状态
        setInterval(loadStatus, 30000);
    </script>
</body>
</html>
"""
    
    def get_workflows_page(self):
        """获取工作流页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工作流管理 - Agent 集群</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .nav { display: flex; gap: 20px; margin-top: 15px; }
        .nav a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; }
        .nav a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .content { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .filter-bar { display: flex; gap: 15px; margin-bottom: 20px; }
        .filter-bar select, .filter-bar input { padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
        .workflow-table { width: 100%; border-collapse: collapse; }
        .workflow-table th, .workflow-table td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        .workflow-table th { background: #f8f9fa; font-weight: 500; color: #666; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .status-badge.completed { background: #d4edda; color: #155724; }
        .status-badge.running { background: #cce5ff; color: #004085; }
        .status-badge.failed { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 工作流管理</h1>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings">⚙️ 设置</a>
            <a href="#" style="margin-left:auto;" onclick="logout(); return false;">🚪 登出</a>
        </div>
    </div>
    <div class="container">
        <div class="content">
            <div class="filter-bar">
                <select id="statusFilter"><option value="all">全部状态</option><option value="running">进行中</option><option value="completed">已完成</option><option value="failed">失败</option></select>
                <select id="projectFilter"><option value="all">全部项目</option><option value="default">默认项目</option><option value="ecommerce">电商项目</option><option value="blog">博客系统</option></select>
                <input type="text" id="searchInput" placeholder="搜索..." style="flex:1;">
            </div>
            <table class="workflow-table">
                <thead>
                    <tr><th>工作流 ID</th><th>需求</th><th>项目</th><th>状态</th><th>创建时间</th><th>耗时</th></tr>
                </thead>
                <tbody id="workflowTableBody"><tr><td colspan="6" style="text-align:center;color:#999;">加载中...</td></tr></tbody>
            </table>
        </div>
    </div>
    <script>
        async function loadWorkflows() {
            const res = await fetch('/api/workflows');
            const data = await res.json();
            const tbody = document.getElementById('workflowTableBody');
            tbody.innerHTML = data.workflows.map(wf => `
                <tr>
                    <td>${wf.workflow_id || '-'}</td>
                    <td>${wf.requirement || '未命名'}</td>
                    <td>${wf.project || '默认项目'}</td>
                    <td><span class="status-badge ${wf.status}">${wf.status}</span></td>
                    <td>${new Date(wf.created_at).toLocaleString('zh-CN')}</td>
                    <td>${wf.duration || '-'}</td>
                </tr>
            `).join('');
        }
        async function logout() {
            if (!confirm('确定要登出吗？')) return;
            try {
                await fetch('/api/logout', { method: 'POST' });
                document.cookie = 'auth_token=; Path=/; Max-Age=0';
                window.location.href = '/login';
            } catch (err) {
                alert('登出失败：' + err.message);
            }
        }
        loadWorkflows();
    </script>
</body>
</html>
"""
    
    def get_templates_page(self):
        """获取模板库页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模板库 - Agent 集群</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .nav { display: flex; gap: 20px; margin-top: 15px; }
        .nav a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; }
        .nav a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
        .template-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .template-card h3 { margin-bottom: 10px; color: #333; }
        .template-card p { color: #666; font-size: 14px; margin-bottom: 15px; line-height: 1.6; }
        .template-card .meta { font-size: 12px; color: #999; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #f44336; color: white; }
        .add-form { background: white; border-radius: 12px; padding: 24px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #555; }
        .form-group input, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 模板库</h1>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings">⚙️ 设置</a>
            <a href="#" style="margin-left:auto;" onclick="logout(); return false;">🚪 登出</a>
        </div>
    </div>
    <div class="container">
        <div class="add-form">
            <h2>➕ 新建模板</h2>
            <div class="form-group"><label>模板名称</label><input type="text" id="tplName" placeholder="例如：电商购物车功能"></div>
            <div class="form-group"><label>描述</label><input type="text" id="tplDesc" placeholder="简短描述模板用途"></div>
            <div class="form-group"><label>需求内容</label><textarea id="tplReq" rows="4" placeholder="详细的需求描述..."></textarea></div>
            <div class="form-group"><label>项目</label><select id="tplProject"><option value="default">默认项目</option><option value="ecommerce">电商项目</option><option value="blog">博客系统</option></select></div>
            <button class="btn btn-primary" onclick="saveTemplate()">保存模板</button>
        </div>
        <div class="template-grid" id="templateGrid">加载中...</div>
    </div>
    <script>
        async function loadTemplates() {
            const res = await fetch('/api/templates');
            const data = await res.json();
            const grid = document.getElementById('templateGrid');
            if (data.templates.length === 0) {
                grid.innerHTML = '<p style="color:#999;text-align:center;grid-column:1/-1;">暂无模板</p>';
                return;
            }
            grid.innerHTML = data.templates.map(tpl => `
                <div class="template-card">
                    <h3>${tpl.name}</h3>
                    <p>${tpl.description || tpl.requirement.substring(0, 100)}...</p>
                    <div class="meta">项目：${tpl.project} · 创建：${new Date(tpl.created_at).toLocaleString('zh-CN')}</div>
                    <div style="margin-top:15px;">
                        <button class="btn btn-primary" onclick="useTemplate('${tpl.requirement.replace(/"/g, "\\'")}')">使用</button>
                        <button class="btn btn-danger" onclick="deleteTemplate('${tpl.id}')" style="margin-left:10px;">删除</button>
                    </div>
                </div>
            `).join('');
        }
        async function saveTemplate() {
            const res = await fetch('/api/template/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: document.getElementById('tplName').value,
                    description: document.getElementById('tplDesc').value,
                    requirement: document.getElementById('tplReq').value,
                    project: document.getElementById('tplProject').value
                })
            });
            const data = await res.json();
            if (data.success) { alert('✅ 模板已保存'); loadTemplates(); }
            else { alert('❌ ' + data.error); }
        }
        async function deleteTemplate(id) {
            if (!confirm('确定删除此模板？')) return;
            const res = await fetch('/api/template/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id})
            });
            const data = await res.json();
            if (data.success) { alert('✅ 模板已删除'); loadTemplates(); }
        }
        function useTemplate(req) {
            localStorage.setItem('template_requirement', req);
            window.location.href = '/';
        }
        async function logout() {
            if (!confirm('确定要登出吗？')) return;
            try {
                await fetch('/api/logout', { method: 'POST' });
                document.cookie = 'auth_token=; Path=/; Max-Age=0';
                window.location.href = '/login';
            } catch (err) {
                alert('登出失败：' + err.message);
            }
        }
        loadTemplates();
    </script>
</body>
</html>
"""
    
    def get_costs_page(self):
        """获取成本统计页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>成本统计 - Agent 集群</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .nav { display: flex; gap: 20px; margin-top: 15px; }
        .nav a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; }
        .nav a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .cost-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .card .value { font-size: 28px; font-weight: bold; color: #333; }
        .card .sub { font-size: 12px; color: #999; margin-top: 5px; }
        .chart-container { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; color: #666; font-weight: 500; }
    </style>
</head>
<body>
    <div class="header">
        <h1>💰 成本统计</h1>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings">⚙️ 设置</a>
            <a href="#" style="margin-left:auto;" onclick="logout(); return false;">🚪 登出</a>
        </div>
    </div>
    <div class="container">
        <div class="cost-cards">
            <div class="card"><h3>今日成本</h3><div class="value" id="todayCost">¥0.00</div><div class="sub" id="todayWorkflows">0 个工作流</div></div>
            <div class="card"><h3>本周成本</h3><div class="value" id="weekCost">¥0.00</div><div class="sub" id="weekWorkflows">0 个工作流</div></div>
            <div class="card"><h3>本月成本</h3><div class="value" id="monthCost">¥0.00</div><div class="sub" id="monthWorkflows">0 个工作流</div></div>
            <div class="card"><h3>平均单次</h3><div class="value" id="avgCost">¥0.00</div><div class="sub">每工作流平均</div></div>
        </div>
        <div class="chart-container">
            <h2>按模型统计</h2>
            <table><thead><tr><th>模型</th><th>调用次数</th><th>Token 消耗</th><th>成本</th></tr></thead><tbody id="modelTable"><tr><td colspan="4" style="text-align:center;color:#999;">加载中...</td></tr></tbody></table>
        </div>
    </div>
    <script>
        async function loadCosts() {
            const res = await fetch('/api/costs');
            const data = await res.json();
            document.getElementById('todayCost').textContent = '¥' + (data.today?.total || 0).toFixed(2);
            document.getElementById('todayWorkflows').textContent = (data.today?.workflows || 0) + ' 个工作流';
            document.getElementById('weekCost').textContent = '¥' + (data.week?.total || 0).toFixed(2);
            document.getElementById('weekWorkflows').textContent = (data.week?.workflows || 0) + ' 个工作流';
            document.getElementById('monthCost').textContent = '¥' + (data.month?.total || 0).toFixed(2);
            document.getElementById('monthWorkflows').textContent = (data.month?.workflows || 0) + ' 个工作流';
            const avg = data.today?.workflows > 0 ? data.today.total / data.today.workflows : 0;
            document.getElementById('avgCost').textContent = '¥' + avg.toFixed(2);
            
            const tbody = document.getElementById('modelTable');
            const models = data.by_model || {};
            if (Object.keys(models).length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#999;">暂无数据</td></tr>';
            } else {
                tbody.innerHTML = Object.entries(models).map(([model, stats]) => `
                    <tr><td>${model}</td><td>${stats.calls || 0}</td><td>${stats.tokens || 0}</td><td>¥${(stats.cost || 0).toFixed(2)}</td></tr>
                `).join('');
            }
        }
        async function logout() {
            if (!confirm('确定要登出吗？')) return;
            try {
                await fetch('/api/logout', { method: 'POST' });
                document.cookie = 'auth_token=; Path=/; Max-Age=0';
                window.location.href = '/login';
            } catch (err) {
                alert('登出失败：' + err.message);
            }
        }
        loadCosts();
    </script>
</body>
</html>
"""
    
    def get_settings_page(self):
        """获取设置页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>设置 - Agent 集群</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .nav { display: flex; gap: 20px; margin-top: 15px; align-items: center; }
        .nav a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; }
        .nav a:hover { background: rgba(255,255,255,0.2); }
        .nav a.logout-btn { margin-left: auto; }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .content { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .setting-group { margin-bottom: 30px; }
        .setting-group h2 { margin-bottom: 15px; color: #333; }
        .setting-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #eee; }
        .setting-item label { color: #555; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #f44336; color: white; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        .form-group input { width: 100%; max-width: 400px; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .message { padding: 12px; border-radius: 8px; margin-bottom: 20px; display: none; }
        .message.success { background: #d4edda; color: #155724; }
        .message.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚙️ 设置</h1>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings">⚙️ 设置</a>
            <a href="#" class="logout-btn" onclick="logout(); return false;">🚪 登出</a>
        </div>
    </div>
    <div class="container">
        <div class="content">
            <h2>🔐 修改密码</h2>
            <div id="passwordMessage" class="message"></div>
            <div class="form-group">
                <label for="oldPassword">原密码</label>
                <input type="password" id="oldPassword" placeholder="请输入原密码">
            </div>
            <div class="form-group">
                <label for="newPassword">新密码</label>
                <input type="password" id="newPassword" placeholder="请输入新密码（至少 6 位）">
            </div>
            <div class="form-group">
                <label for="confirmPassword">确认新密码</label>
                <input type="password" id="confirmPassword" placeholder="请再次输入新密码">
            </div>
            <button class="btn btn-primary" onclick="changePassword()">修改密码</button>
        </div>
        
        <div class="content">
            <div class="setting-group">
                <h2>系统设置</h2>
                <div class="setting-item"><label>Web 服务端口</label><span>8889</span></div>
                <div class="setting-item"><label>工作区路径</label><span>/home/admin/.openclaw/workspace/agent-cluster</span></div>
            </div>
            <div class="setting-group">
                <h2>通知设置</h2>
                <div class="setting-item"><label>钉钉通知</label><span>✅ 已启用</span></div>
                <div class="setting-item"><label>通知事件</label><span>完成，失败，需要人工介入</span></div>
            </div>
            <div class="setting-group">
                <h2>项目配置</h2>
                <div class="setting-item"><label>项目数量</label><span>4</span></div>
                <div class="setting-item"><label>默认项目</label><span>agent-cluster-test</span></div>
            </div>
        </div>
    </div>
    
    <script>
        // 登出功能
        async function logout() {
            if (!confirm('确定要登出吗？')) return;
            try {
                await fetch('/api/logout', { method: 'POST' });
                document.cookie = 'auth_token=; Path=/; Max-Age=0';
                window.location.href = '/login';
            } catch (err) {
                alert('登出失败：' + err.message);
            }
        }
        
        // 修改密码功能
        async function changePassword() {
            const oldPassword = document.getElementById('oldPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const messageDiv = document.getElementById('passwordMessage');
            
            // 验证
            if (!oldPassword || !newPassword || !confirmPassword) {
                messageDiv.textContent = '请填写所有字段';
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
                return;
            }
            
            if (newPassword.length < 6) {
                messageDiv.textContent = '密码长度至少 6 位';
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
                return;
            }
            
            if (newPassword !== confirmPassword) {
                messageDiv.textContent = '两次输入的新密码不一致';
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
                return;
            }
            
            try {
                const res = await fetch('/api/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
                });
                
                const data = await res.json();
                
                if (data.success) {
                    messageDiv.textContent = data.message;
                    messageDiv.className = 'message success';
                    messageDiv.style.display = 'block';
                    // 清空表单
                    document.getElementById('oldPassword').value = '';
                    document.getElementById('newPassword').value = '';
                    document.getElementById('confirmPassword').value = '';
                    // 3 秒后跳转到登录页
                    setTimeout(() => {
                        logout();
                    }, 3000);
                } else {
                    messageDiv.textContent = data.error;
                    messageDiv.className = 'message error';
                    messageDiv.style.display = 'block';
                }
            } catch (err) {
                messageDiv.textContent = '网络错误：' + err.message;
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""


def get_host_ip():
    """获取本机 IP 地址"""
    import socket
    try:
        # 创建一个 UDP socket 来获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def run_server(host='', port=8889):
    """启动 Web 服务器"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, WebUIHandler)
    
    # 获取访问地址
    local_url = f"http://localhost:{port}"
    external_url = f"http://{get_host_ip()}:{port}"
    
    print(f"🌐 Web 界面已启动！")
    print(f"")
    print(f"   本地访问：{local_url}")
    print(f"   外网访问：{external_url}")
    print(f"")
    print(f"📁 工作目录：{BASE_DIR}")
    print(f"🔒 绑定地址：{'所有接口 (0.0.0.0)' if host == '' else host}")
    print(f"")
    print(f"按 Ctrl+C 停止服务")
    print(f"")
    httpd.serve_forever()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Agent 集群 Web 界面')
    parser.add_argument('--port', type=int, default=8889, help='Web 服务端口')
    parser.add_argument('--host', type=str, default='', help='绑定地址 (默认所有接口)')
    args = parser.parse_args()
    run_server(args.host, args.port)
