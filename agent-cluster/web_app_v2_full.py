#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 集群 Web 界面 V2.1
提供可视化的工作流管理、任务提交、状态监控功能
支持管理员登录验证、6 阶段流程展示、质量门禁监控
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
import time

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
CLUSTER_CONFIG = BASE_DIR / "cluster_config_v2.json"


class WebUIHandler(SimpleHTTPRequestHandler):
    """Web 界面请求处理器"""
    
    PUBLIC_PATHS = ['/api/status', '/login', '/api/login', '/static/', '/favicon.ico']
    
    def __init__(self, *args, **kwargs):
        self.workflow_state = {}
        self.load_workflow_state()
        self.auth_config = self._load_auth_config()
        self.sessions = self._load_sessions()
        self.cluster_config = self._load_cluster_config()
        super().__init__(*args, **kwargs)
    
    def _load_auth_config(self) -> dict:
        default_config = {
            "enabled": True,
            "username": "admin",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
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
        if SESSIONS_FILE.exists():
            try:
                with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_sessions(self):
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_client_ip(self) -> str:
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0]
    
    def _check_auth(self) -> tuple:
        if not self.auth_config.get("enabled", True):
            return True, None, False
        for public_path in self.PUBLIC_PATHS:
            if self.path.startswith(public_path):
                return True, None, False
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
        if token in self.sessions:
            session = self.sessions[token]
            timeout = self.auth_config.get("session_timeout_hours", 24) * 3600
            if time.time() - session.get("created_at", 0) < timeout:
                session["last_activity"] = time.time()
                self._save_sessions()
                return True, token, False
        return False, None, True
    
    def _generate_token(self) -> str:
        import secrets
        return secrets.token_urlsafe(32)
    
    def _load_cluster_config(self) -> dict:
        if CLUSTER_CONFIG.exists():
            try:
                with open(CLUSTER_CONFIG, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def load_workflow_state(self):
        state_file = MEMORY_DIR / "workflow_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    self.workflow_state = json.load(f)
            except:
                self.workflow_state = {}
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        is_auth, token, need_redirect = self._check_auth()
        
        if path in ['/login'] or path.startswith('/api/status') or path.startswith('/static/'):
            pass
        elif not is_auth and need_redirect:
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return
        
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/api/status':
            self.send_json_response(self.get_status())
        elif path == '/api/workflows':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_workflows())
        elif path == '/api/agents':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_agents())
        elif path == '/api/phases':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_phases())
        elif path == '/api/quality-gate':
            if not is_auth:
                self.send_json_response({"error": "未授权"}, 401)
                return
            self.send_json_response(self.get_quality_gate())
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
        elif path == '/agents':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_agents_page())
        elif path == '/phases':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_phases_page())
        elif path == '/quality':
            if not is_auth:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.send_html_page(self.get_quality_page())
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
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(post_data) if post_data else {}
        except:
            data = {}
        
        if path == '/api/login':
            self.handle_login(data)
            return
        
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
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html_page(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_login(self, data):
        username = data.get("username", "")
        password = data.get("password", "")
        client_ip = self._get_client_ip()
        stored_username = self.auth_config.get("username", "admin")
        stored_hash = self.auth_config.get("password_hash", "")
        
        if username != stored_username or self._hash_password(password) != stored_hash:
            self.send_json_response({"success": False, "error": "用户名或密码错误"})
            return
        
        token = self._generate_token()
        self.sessions[token] = {
            "username": username,
            "ip": client_ip,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        self._save_sessions()
        self.send_json_response({"success": True, "message": "登录成功", "token": token})
    
    def handle_logout(self, token):
        if token and token in self.sessions:
            del self.sessions[token]
            self._save_sessions()
        self.send_response(302)
        self.send_header('Location', '/login')
        self.send_header('Set-Cookie', 'auth_token=; Path=/; Max-Age=0')
        self.end_headers()
    
    def handle_change_password(self, data, token):
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")
        stored_hash = self.auth_config.get("password_hash", "")
        
        if self._hash_password(old_password) != stored_hash:
            self.send_json_response({"success": False, "error": "原密码错误"})
            return
        if len(new_password) < 6:
            self.send_json_response({"success": False, "error": "密码长度至少 6 位"})
            return
        
        self.auth_config["password_hash"] = self._hash_password(new_password)
        config_file = MEMORY_DIR / "auth_config.json"
        config = {"auth": self.auth_config}
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.sessions = {}
        self._save_sessions()
        self.send_json_response({"success": True, "message": "密码修改成功，请重新登录"})
    
    def get_status(self):
        self.load_workflow_state()
        orchestrator_running = False
        deploy_listener_running = False
        try:
            result = subprocess.run(['pgrep', '-f', 'orchestrator.py'], capture_output=True, text=True, timeout=5)
            orchestrator_running = bool(result.stdout.strip())
        except:
            pass
        try:
            result = subprocess.run(['pgrep', '-f', 'deploy_listener.py'], capture_output=True, text=True, timeout=5)
            deploy_listener_running = bool(result.stdout.strip())
        except:
            pass
        
        workflows_data = self.workflow_state.get("workflows", {})
        workflows = list(workflows_data.values()) if isinstance(workflows_data, dict) else workflows_data
        active = len([w for w in workflows if w.get("status") == "running"])
        completed = len([w for w in workflows if w.get("status") == "completed"])
        failed = len([w for w in workflows if w.get("status") == "failed"])
        
        return {
            "status": "running" if orchestrator_running else "stopped",
            "deploy_listener": "running" if deploy_listener_running else "stopped",
            "timestamp": datetime.now().isoformat(),
            "active_workflows": active,
            "completed_today": completed,
            "failed_today": failed,
            "total_workflows": len(workflows),
            "agents_ready": 10,
            "dingtalk_enabled": self.cluster_config.get("dingtalk", {}).get("webhook") is not None
        }
    
    def get_agents(self):
        agents = {
            "executors": [
                {"name": "Product Manager", "role": "产品经理", "phase": "Phase 1", "model": "qwen-max", "status": "ready"},
                {"name": "Tech Lead", "role": "技术负责人", "phase": "Phase 2", "model": "qwen-max", "status": "ready"},
                {"name": "Designer", "role": "设计师", "phase": "Phase 2", "model": "qwen-vl-plus", "status": "ready"},
                {"name": "DevOps", "role": "运维工程师", "phase": "Phase 2/6", "model": "qwen-plus", "status": "ready"},
                {"name": "Codex", "role": "后端专家", "phase": "Phase 3", "model": "qwen-coder-plus", "status": "ready"},
                {"name": "Claude-Code", "role": "前端专家", "phase": "Phase 3", "model": "kimi-k2.5", "status": "ready"},
                {"name": "Tester", "role": "测试工程师", "phase": "Phase 4", "model": "qwen-coder-plus", "status": "ready"}
            ],
            "reviewers": [
                {"name": "Codex Reviewer", "role": "逻辑审查", "phase": "Phase 5", "model": "glm-4.7", "status": "ready"},
                {"name": "Gemini Reviewer", "role": "安全审查", "phase": "Phase 5", "model": "qwen-plus", "status": "ready"},
                {"name": "Claude Reviewer", "role": "基础审查", "phase": "Phase 5", "model": "MiniMax-M2.5", "status": "ready"}
            ]
        }
        return agents
    
    def get_phases(self):
        phases = [
            {"id": 1, "name": "需求分析", "agents": ["Product Manager"], "outputs": ["PRD 文档", "用户故事", "验收标准"]},
            {"id": 2, "name": "技术设计", "agents": ["Tech Lead", "Designer", "DevOps"], "outputs": ["架构文档", "UI 设计", "部署配置"]},
            {"id": 3, "name": "开发实现", "agents": ["Codex", "Claude-Code"], "outputs": ["后端代码", "前端代码"]},
            {"id": 4, "name": "测试验证", "agents": ["Tester"], "outputs": ["测试报告", "Bug 列表"], "quality_gate": True},
            {"id": 5, "name": "代码审查", "agents": ["Codex Reviewer", "Gemini Reviewer", "Claude Reviewer"], "outputs": ["审查报告"], "quality_gate": True},
            {"id": 6, "name": "部署上线", "agents": ["DevOps"], "outputs": ["运行中的系统"], "require_confirmation": True}
        ]
        return {"phases": phases}
    
    def get_quality_gate(self):
        config = self.cluster_config.get("quality_gate", {})
        return {
            "phase_4": {
                "enabled": True,
                "min_coverage": config.get("phase_4", {}).get("min_coverage", 80),
                "max_critical_bugs": 0,
                "max_medium_bugs": 3
            },
            "phase_5": {
                "enabled": True,
                "min_review_score": config.get("phase_5", {}).get("min_review_score", 80),
                "required_approvals": 3
            },
            "deployment": {
                "require_confirmation": True,
                "confirmation_timeout_minutes": 30
            }
        }
    
    def get_workflows(self):
        self.load_workflow_state()
        workflows_data = self.workflow_state.get("workflows", {})
        workflows = list(workflows_data.values()) if isinstance(workflows_data, dict) else workflows_data
        workflows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"workflows": workflows[-50:]}
    
    def get_templates(self):
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
        cost_file = MEMORY_DIR / "cost_stats.json"
        if cost_file.exists():
            try:
                with open(cost_file, 'r', encoding='utf-8') as f:
                    costs = json.load(f)
                return costs
            except:
                pass
        return {"today": {"total": 0, "workflows": 0}, "week": {"total": 0, "workflows": 0}, "month": {"total": 0, "workflows": 0}, "by_model": {}}
    
    def get_projects(self):
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
        requirement = data.get("requirement", "")
        project = data.get("project", "default")
        template = data.get("template", "")
        
        if not requirement:
            return {"success": False, "error": "需求内容不能为空"}
        
        cmd = f"cd {BASE_DIR} && python3 orchestrator.py \"{requirement}\""
        try:
            subprocess.Popen(cmd, shell=True, stdout=open(LOGS_DIR / "web_submit.log", 'a'), stderr=subprocess.STDOUT)
            return {"success": True, "message": "任务已提交，工作流已启动", "requirement": requirement, "project": project}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_template(self, data):
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
    def get_login_page(self):
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - Agent 集群 V2.1</title>
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
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 28px; color: #333; margin-bottom: 10px; }
        .logo p { color: #666; font-size: 14px; }
        .logo .version { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; display: inline-block; margin-top: 8px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        .form-group input { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .error-message { background: #fee; color: #c33; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; display: none; }
        .footer { text-align: center; margin-top: 20px; color: #999; font-size: 12px; }
        .features { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .features h4 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .features ul { list-style: none; }
        .features li { color: #888; font-size: 12px; padding: 4px 0; }
        .features li:before { content: "✅ "; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🤖 Agent 集群</h1>
            <p>智能协作开发系统</p>
            <span class="version">V2.1</span>
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
        <div class="features">
            <h4>📊 系统特性</h4>
            <ul>
                <li>完整 6 阶段开发流程</li>
                <li>10 个专业 Agent 协作</li>
                <li>质量门禁自动审查</li>
                <li>钉钉双向通知</li>
            </ul>
        </div>
        <div class="footer">Agent Cluster Console v2.1</div>
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
                    document.cookie = `auth_token=${data.token}; Path=/; Max-Age=${24*60*60}; SameSite=Strict`;
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

    def get_main_page(self):
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent 集群 V2.1 控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
        .header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .header h1 { font-size: 24px; }
        .header .version { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .nav { display: flex; gap: 15px; flex-wrap: wrap; }
        .nav a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: background 0.3s; font-size: 14px; }
        .nav a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1600px; margin: 0 auto; padding: 30px; }
        .status-bar { background: white; border-radius: 12px; padding: 20px; margin-bottom: 30px; display: flex; gap: 30px; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .status-item { display: flex; align-items: center; gap: 10px; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-dot.green { background: #10b981; }
        .status-dot.red { background: #ef4444; }
        .status-dot.yellow { background: #f59e0b; }
        .status-label { color: #666; font-size: 14px; }
        .status-value { font-weight: 600; color: #333; }
        .status-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); }
        .card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .card .value { font-size: 32px; font-weight: bold; color: #333; }
        .card .sub { font-size: 12px; color: #999; margin-top: 8px; }
        .card .icon { font-size: 24px; margin-bottom: 10px; }
        .section { background: white; border-radius: 12px; padding: 24px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .section h2 { margin-bottom: 20px; color: #333; font-size: 18px; }
        .phase-timeline { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; }
        .phase-card { min-width: 200px; background: #f8f9fa; border-radius: 12px; padding: 20px; border-left: 4px solid #667eea; }
        .phase-card h4 { color: #333; margin-bottom: 8px; font-size: 16px; }
        .phase-card p { color: #666; font-size: 13px; margin-bottom: 10px; }
        .phase-card .agents { display: flex; flex-wrap: wrap; gap: 5px; }
        .phase-card .agent-tag { background: #e0e7ff; color: #4f46e5; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
        .phase-card .quality-gate { background: #fef3c7; color: #d97706; padding: 3px 8px; border-radius: 4px; font-size: 11px; margin-top: 8px; display: inline-block; }
        .submit-form { background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; padding: 30px; margin-bottom: 30px; }
        .submit-form h2 { margin-bottom: 20px; color: #333; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        .form-group textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; min-height: 120px; font-family: inherit; }
        .form-group textarea:focus { outline: none; border-color: #667eea; }
        .form-group select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .agent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
        .agent-card { background: #f8f9fa; border-radius: 10px; padding: 16px; display: flex; align-items: center; gap: 15px; }
        .agent-avatar { width: 48px; height: 48px; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
        .agent-info { flex: 1; }
        .agent-info h4 { color: #333; font-size: 14px; margin-bottom: 4px; }
        .agent-info p { color: #666; font-size: 12px; }
        .agent-info .model { color: #999; font-size: 11px; margin-top: 4px; }
        .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
        .status-badge.ready { background: #d1fae5; color: #065f46; }
        .status-badge.busy { background: #fef3c7; color: #92400e; }
        .workflow-list { max-height: 400px; overflow-y: auto; }
        .workflow-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .workflow-item:last-child { border-bottom: none; }
        .workflow-item .info { flex: 1; }
        .workflow-item .title { font-weight: 500; color: #333; font-size: 14px; }
        .workflow-item .meta { font-size: 12px; color: #999; margin-top: 5px; }
        .workflow-item .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .status-badge.completed { background: #d1fae5; color: #065f46; }
        .status-badge.running { background: #dbeafe; color: #1e40af; }
        .status-badge.failed { background: #fee2e2; color: #991b1b; }
        .quick-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .quick-action { background: white; border: 2px solid #e0e0e0; border-radius: 10px; padding: 16px; text-align: center; cursor: pointer; transition: all 0.2s; text-decoration: none; color: #333; }
        .quick-action:hover { border-color: #667eea; background: #f0f4ff; }
        .quick-action .icon { font-size: 28px; margin-bottom: 8px; }
        .quick-action .label { font-size: 13px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-top">
            <h1>🤖 Agent 集群控制台</h1>
            <span class="version">V2.1</span>
        </div>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/phases">🔄 开发流程</a>
            <a href="/agents">🤖 Agent 阵容</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/quality">🚦 质量门禁</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings" style="margin-left:auto;">⚙️ 设置</a>
            <a href="#" onclick="logout(); return false;">🚪 登出</a>
        </div>
    </div>
    
    <div class="container">
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot green" id="clusterStatusDot"></span>
                <span class="status-label">集群状态:</span>
                <span class="status-value" id="clusterStatus">-</span>
            </div>
            <div class="status-item">
                <span class="status-dot green" id="deployStatusDot"></span>
                <span class="status-label">部署监听:</span>
                <span class="status-value" id="deployStatus">-</span>
            </div>
            <div class="status-item">
                <span class="status-dot green" id="dingtalkStatusDot"></span>
                <span class="status-label">钉钉通知:</span>
                <span class="status-value" id="dingtalkStatus">-</span>
            </div>
            <div class="status-item" style="margin-left:auto; color:#999; font-size:13px;" id="lastUpdate"></div>
        </div>
        
        <div class="status-cards">
            <div class="card">
                <div class="icon">🔄</div>
                <h3>进行中的工作流</h3>
                <div class="value" id="activeWorkflows">-</div>
                <div class="sub">当前正在执行</div>
            </div>
            <div class="card">
                <div class="icon">✅</div>
                <h3>今日完成</h3>
                <div class="value" id="completedToday">-</div>
                <div class="sub">成功完成的工作流</div>
            </div>
            <div class="card">
                <div class="icon">❌</div>
                <h3>今日失败</h3>
                <div class="value" id="failedToday">-</div>
                <div class="sub">需要关注</div>
            </div>
            <div class="card">
                <div class="icon">🤖</div>
                <h3>就绪 Agent</h3>
                <div class="value" id="agentsReady">-</div>
                <div class="sub">共 10 个 Agent</div>
            </div>
        </div>
        
        <div class="submit-form">
            <h2>🚀 提交新任务</h2>
            <div class="form-group">
                <label>产品需求描述</label>
                <textarea id="requirement" placeholder="详细描述你想要实现的功能，例如：创建一个电商网站的购物车功能，支持添加商品、修改数量、删除商品、结算等功能..."></textarea>
            </div>
            <div class="form-group">
                <label>选择项目</label>
                <select id="project">
                    <option value="default">默认项目</option>
                    <option value="ecommerce">电商项目</option>
                    <option value="blog">博客系统</option>
                    <option value="crm">CRM 系统</option>
                    <option value="saas">SaaS 平台</option>
                </select>
            </div>
            <button class="btn" onclick="submitTask()">🚀 启动工作流</button>
        </div>
        
        <div class="section">
            <h2>🔄 完整开发流程（6 阶段）</h2>
            <div class="phase-timeline" id="phaseTimeline">
                <div class="phase-card">
                    <h4>Phase 1: 需求分析</h4>
                    <p>Product Manager</p>
                    <div class="agents">
                        <span class="agent-tag">PRD 文档</span>
                        <span class="agent-tag">用户故事</span>
                    </div>
                </div>
                <div class="phase-card">
                    <h4>Phase 2: 技术设计</h4>
                    <p>Tech Lead + Designer + DevOps</p>
                    <div class="agents">
                        <span class="agent-tag">架构设计</span>
                        <span class="agent-tag">UI 设计</span>
                        <span class="agent-tag">部署配置</span>
                    </div>
                </div>
                <div class="phase-card">
                    <h4>Phase 3: 开发实现</h4>
                    <p>Codex + Claude-Code</p>
                    <div class="agents">
                        <span class="agent-tag">后端代码</span>
                        <span class="agent-tag">前端代码</span>
                    </div>
                </div>
                <div class="phase-card">
                    <h4>Phase 4: 测试验证</h4>
                    <p>Tester</p>
                    <div class="agents">
                        <span class="agent-tag">单元测试</span>
                        <span class="agent-tag">集成测试</span>
                    </div>
                    <span class="quality-gate">🚦 质量门禁</span>
                </div>
                <div class="phase-card">
                    <h4>Phase 5: 代码审查</h4>
                    <p>3 Reviewers</p>
                    <div class="agents">
                        <span class="agent-tag">逻辑审查</span>
                        <span class="agent-tag">安全审查</span>
                    </div>
                    <span class="quality-gate">🚦 质量门禁</span>
                </div>
                <div class="phase-card">
                    <h4>Phase 6: 部署上线</h4>
                    <p>DevOps</p>
                    <div class="agents">
                        <span class="agent-tag">Docker</span>
                        <span class="agent-tag">CI/CD</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🤖 Agent 阵容（10 个）</h2>
            <div class="agent-grid" id="agentGrid">
                <div style="color:#999;text-align:center;padding:40px;grid-column:1/-1;">加载中...</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 最近工作流</h2>
            <div class="workflow-list" id="workflowList">
                <div style="color:#999;text-align:center;padding:40px;">加载中...</div>
            </div>
            <div style="text-align:center;margin-top:20px;">
                <a href="/workflows" style="color:#667eea;text-decoration:none;">查看全部 →</a>
            </div>
        </div>
        
        <div class="section">
            <h2>⚡ 快捷操作</h2>
            <div class="quick-actions">
                <a href="/phases" class="quick-action">
                    <div class="icon">🔄</div>
                    <div class="label">查看流程</div>
                </a>
                <a href="/agents" class="quick-action">
                    <div class="icon">🤖</div>
                    <div class="label">Agent 状态</div>
                </a>
                <a href="/quality" class="quick-action">
                    <div class="icon">🚦</div>
                    <div class="label">质量门禁</div>
                </a>
                <a href="/templates" class="quick-action">
                    <div class="icon">📝</div>
                    <div class="label">模板库</div>
                </a>
                <a href="/costs" class="quick-action">
                    <div class="icon">💰</div>
                    <div class="label">成本统计</div>
                </a>
            </div>
        </div>
    </div>
    
    <script>
        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                document.getElementById('clusterStatus').textContent = data.status === 'running' ? '运行中' : '已停止';
                document.getElementById('clusterStatusDot').className = 'status-dot ' + (data.status === 'running' ? 'green' : 'red');
                
                document.getElementById('deployStatus').textContent = data.deploy_listener === 'running' ? '监听中' : '已停止';
                document.getElementById('deployStatusDot').className = 'status-dot ' + (data.deploy_listener === 'running' ? 'green' : 'yellow');
                
                document.getElementById('dingtalkStatus').textContent = data.dingtalk_enabled ? '已启用' : '未配置';
                document.getElementById('dingtalkStatusDot').className = 'status-dot ' + (data.dingtalk_enabled ? 'green' : 'yellow');
                
                document.getElementById('activeWorkflows').textContent = data.active_workflows;
                document.getElementById('completedToday').textContent = data.completed_today;
                document.getElementById('failedToday').textContent = data.failed_today;
                document.getElementById('agentsReady').textContent = data.agents_ready;
                document.getElementById('lastUpdate').textContent = '最后更新：' + new Date(data.timestamp).toLocaleString('zh-CN');
            } catch (e) {
                console.error('加载状态失败:', e);
            }
        }
        
        async function loadAgents() {
            try {
                const res = await fetch('/api/agents');
                const data = await res.json();
                const grid = document.getElementById('agentGrid');
                
                const allAgents = [...data.executors, ...data.reviewers];
                grid.innerHTML = allAgents.map(agent => {
                    const avatar = agent.name.split(' ').map(w => w[0]).join('').substring(0, 2);
                    return `
                        <div class="agent-card">
                            <div class="agent-avatar">${avatar}</div>
                            <div class="agent-info" style="flex:1;">
                                <h4>${agent.name}</h4>
                                <p>${agent.role} · ${agent.phase}</p>
                                <div class="model">${agent.model}</div>
                            </div>
                            <span class="status-badge ready">就绪</span>
                        </div>
                    `;
                }).join('');
            } catch (e) {
                console.error('加载 Agent 失败:', e);
            }
        }
        
        async function loadWorkflows() {
            try {
                const res = await fetch('/api/workflows');
                const data = await res.json();
                const list = document.getElementById('workflowList');
                
                if (data.workflows.length === 0) {
                    list.innerHTML = '<div style="color:#999;text-align:center;padding:40px;">暂无工作流记录</div>';
                    return;
                }
                
                list.innerHTML = data.workflows.slice(0, 10).map(wf => {
                    const statusClass = wf.status === 'completed' ? 'completed' : wf.status === 'failed' ? 'failed' : 'running';
                    const statusText = wf.status === 'completed' ? '✅ 完成' : wf.status === 'failed' ? '❌ 失败' : '🔄 进行中';
                    return `
                        <div class="workflow-item">
                            <div class="info">
                                <div class="title">${wf.requirement || '未命名任务'}</div>
                                <div class="meta">${wf.workflow_id || '-'} · ${wf.project || '默认项目'} · ${new Date(wf.created_at).toLocaleString('zh-CN')}</div>
                            </div>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                    `;
                }).join('');
            } catch (e) {
                console.error('加载工作流失败:', e);
            }
        }
        
        async function submitTask() {
            const requirement = document.getElementById('requirement').value.trim();
            const project = document.getElementById('project').value;
            
            if (!requirement) {
                alert('请输入产品需求');
                return;
            }
            
            if (!confirm('确定要启动工作流吗？\\n\\n这将启动完整的 6 阶段开发流程，预计需要 10-30 分钟。')) {
                return;
            }
            
            try {
                const res = await fetch('/api/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ requirement, project })
                });
                const data = await res.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                    document.getElementById('requirement').value = '';
                    loadStatus();
                    loadWorkflows();
                } else {
                    alert('❌ ' + data.error);
                }
            } catch (e) {
                alert('提交失败：' + e.message);
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
        
        loadStatus();
        loadAgents();
        loadWorkflows();
        setInterval(loadStatus, 30000);
    </script>
</body>
</html>
"""
# 继续添加剩余页面方法...
