#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 集群 Web 界面 V2.5 - FastAPI 异步版本
完整 6 阶段开发流程 | 10 个专业 Agent | 质量门禁 | 钉钉双向通知
性能优化：异步框架 | Redis 缓存 | Gzip 压缩
"""

import json
import os
import sys
import hashlib
import time
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess

# FastAPI 核心
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

# 安全模块
from utils.config_loader import config
from utils.auth import jwt_auth, require_auth, require_admin
from utils.rate_limiter import rate_limiter, get_client_ip
from utils.health_check import health_checker
from utils.database import get_database, init_database
from utils.backup_manager import get_backup_manager
from utils.checkpoint import get_checkpoint_manager, get_workflow_resumer

# 缓存
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# 初始化
BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"

MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# 初始化数据库
init_database()

# 创建 FastAPI 应用
app = FastAPI(
    title="Agent Cluster V2.5",
    description="完整 6 阶段开发流程 | 10 个专业 Agent | 质量门禁 | 钉钉双向通知",
    version="2.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Gzip 压缩
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 缓存管理器
class CacheManager:
    """Redis 缓存管理器"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = False
        
        if REDIS_AVAILABLE and config.redis_host:
            try:
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=int(config.redis_port),
                    password=config.redis_password if config.redis_password else None,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                self.cache_enabled = True
                print(f"✅ Redis 缓存已启用 ({config.redis_host}:{config.redis_port})")
            except Exception as e:
                print(f"⚠️ Redis 连接失败，使用内存缓存：{e}")
                self.cache_enabled = False
        
        # 内存缓存备用
        self.memory_cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self.cache_enabled and self.redis_client:
            try:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            except Exception:
                pass
        
        return self.memory_cache.get(key)
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """设置缓存"""
        if self.cache_enabled and self.redis_client:
            try:
                self.redis_client.setex(key, expire, json.dumps(value))
                return True
            except Exception:
                pass
        
        self.memory_cache[key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self.cache_enabled and self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception:
                pass
        
        self.memory_cache.pop(key, None)
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        count = 0
        
        if self.cache_enabled and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            except Exception:
                pass
        
        # 清理内存缓存
        keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(pattern.split('*')[0])]
        for k in keys_to_delete:
            del self.memory_cache[k]
            count += 1
        
        return count

cache_manager = CacheManager()


# Rate Limiting 依赖
async def check_rate_limit(request: Request):
    """Rate Limiting 检查"""
    client_ip = get_client_ip(dict(request.headers))
    allowed, remaining = rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        retry_after = rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁",
            headers={"Retry-After": str(retry_after)}
        )
    
    return remaining


# 认证依赖
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """获取当前用户"""
    # 从 Cookie 获取 Token
    token = request.cookies.get("auth_token")
    
    if not token:
        # 尝试从 Authorization 头获取
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        return None
    
    # 验证 Token
    payload = jwt_auth.verify_token(token)
    if not payload:
        return None
    
    # 更新会话活动
    db = get_database()
    db.update_session_activity(token)
    
    return payload


# ========== 公开 API ==========

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return health_checker.full_check()


@app.get("/api/status")
async def get_status(rate_limit_remaining: int = Depends(check_rate_limit)):
    """获取集群状态"""
    # 尝试从缓存获取
    cached = await cache_manager.get("status:cluster")
    if cached:
        return cached
    
    # 获取实时状态
    try:
        orch = bool(subprocess.run(
            ['pgrep', '-f', 'orchestrator.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=5
        ).stdout.strip())
        
        deploy = bool(subprocess.run(
            ['pgrep', '-f', 'deploy_listener.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=5
        ).stdout.strip())
        
        db = get_database()
        workflows = db.get_workflows(limit=1000)
        
        result = {
            "status": "running" if orch else "stopped",
            "deploy_listener": "running" if deploy else "stopped",
            "timestamp": datetime.now().isoformat(),
            "active_workflows": len([w for w in workflows if w.get("status") == "running"]),
            "completed_today": len([w for w in workflows if w.get("status") == "completed"]),
            "failed_today": len([w for w in workflows if w.get("status") == "failed"]),
            "agents_ready": 10,
            "version": "2.5.0"
        }
        
        # 缓存 30 秒
        await cache_manager.set("status:cluster", result, expire=30)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents")
async def get_agents():
    """获取 Agent 阵容"""
    cached = await cache_manager.get("agents:list")
    if cached:
        return cached
    
    # 从配置加载
    cluster_config = config.cluster_config
    agents = cluster_config.get('agents', [])
    reviewers = cluster_config.get('reviewers', [])
    
    result = {
        "executors": agents,
        "reviewers": reviewers
    }
    
    await cache_manager.set("agents:list", result, expire=300)
    return result


@app.get("/api/phases")
async def get_phases():
    """获取开发流程"""
    cached = await cache_manager.get("phases:list")
    if cached:
        return cached
    
    phases = [
        {"id": 1, "name": "Phase 1: 需求分析", "desc": "理解产品需求，明确功能范围", "agents": ["Product Manager"]},
        {"id": 2, "name": "Phase 2: 技术设计", "desc": "系统架构设计，UI/UX 设计，部署规划", "agents": ["Tech Lead", "Designer", "DevOps"]},
        {"id": 3, "name": "Phase 3: 开发实现", "desc": "前后端代码开发", "agents": ["Codex", "Claude-Code"]},
        {"id": 4, "name": "Phase 4: 测试验证", "desc": "单元测试，集成测试，E2E 测试", "agents": ["Tester"], "quality_gate": True},
        {"id": 5, "name": "Phase 5: 代码审查", "desc": "多层代码审查", "agents": ["Codex Reviewer", "Gemini Reviewer", "Claude Reviewer"], "quality_gate": True},
        {"id": 6, "name": "Phase 6: 部署上线", "desc": "部署到生产环境", "agents": ["DevOps"], "confirm": True}
    ]
    
    await cache_manager.set("phases:list", phases, expire=300)
    return {"phases": phases}


# ========== 认证 API ==========

@app.post("/api/login")
async def login(request: Request, data: Dict[str, str]):
    """用户登录"""
    username = data.get("username", "")
    password = data.get("password", "")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    
    # 尝试 JWT 认证
    user = jwt_auth.authenticate(username, password)
    
    # 兼容旧版
    if not user:
        auth_config_file = MEMORY_DIR / "auth_config.json"
        if auth_config_file.exists():
            try:
                with open(auth_config_file) as f:
                    auth_config = json.load(f).get("auth", {})
                
                if username == auth_config.get("username") and \
                   hashlib.sha256(password.encode()).hexdigest() == auth_config.get("password_hash"):
                    user = {
                        'username': username,
                        'user_id': hashlib.md5(username.encode()).hexdigest(),
                        'role': 'admin'
                    }
            except Exception:
                pass
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 创建 Token
    access_token = jwt_auth.create_token(username, user['user_id'], refresh=False)
    refresh_token = jwt_auth.create_token(username, user['user_id'], refresh=True)
    
    # 保存会话
    db = get_database()
    db.create_session(access_token, username, user['user_id'], get_client_ip(dict(request.headers)), user.get('role', 'user'))
    
    response = JSONResponse({
        "success": True,
        "token": access_token,
        "refresh_token": refresh_token,
        "expires_in": config.jwt_expiration * 3600,
        "user": {"username": username, "role": user.get('role', 'user')}
    })
    
    response.set_cookie(
        key="auth_token",
        value=access_token,
        max_age=config.jwt_expiration * 3600,
        httponly=True,
        samesite="lax"
    )
    
    return response


@app.post("/api/logout")
async def logout(request: Request, user: Dict = Depends(get_current_user)):
    """用户登出"""
    token = request.cookies.get("auth_token")
    
    if token:
        jwt_auth.logout(token)
        db = get_database()
        db.delete_session(token)
        await cache_manager.delete(f"session:{token}")
    
    response = RedirectResponse(url="/login")
    response.delete_cookie("auth_token")
    return response


# ========== 工作流 API ==========

@app.get("/api/workflows")
async def get_workflows(
    status: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 100,
    user: Dict = Depends(get_current_user)
):
    """获取工作流列表"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    db = get_database()
    workflows = db.get_workflows(status=status, project=project, limit=limit)
    
    return {"workflows": workflows}


@app.post("/api/submit")
async def submit_task(
    request: Request,
    data: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """提交新任务"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    requirement = data.get("requirement", "")
    project = data.get("project", "default")
    
    if not requirement:
        raise HTTPException(status_code=400, detail="需求不能为空")
    
    workflow_id = f"wf_{int(time.time())}"
    
    db = get_database()
    success = db.create_workflow(workflow_id, requirement, project)
    
    if not success:
        raise HTTPException(status_code=500, detail="创建工作流失败")
    
    # 清除缓存
    await cache_manager.clear_pattern("workflows:*")
    await cache_manager.clear_pattern("status:*")
    
    return {
        "success": True,
        "workflow_id": workflow_id,
        "message": "任务已提交，开始执行"
    }


# ========== 成本 API ==========

@app.get("/api/costs")
async def get_costs(days: int = 30, user: Dict = Depends(get_current_user)):
    """获取成本统计"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    # 尝试从缓存获取
    cache_key = f"costs:{days}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    db = get_database()
    stats = db.get_cost_stats(days=days)
    
    # 按时间分组统计
    result = {
        "today": {"total": 0, "workflows": 0},
        "week": {"total": 0, "workflows": 0},
        "month": {"total": stats.get('total_cost', 0), "workflows": stats.get('total_calls', 0)},
        "by_model": stats.get('by_model', {})
    }
    
    # 缓存 5 分钟
    await cache_manager.set(cache_key, result, expire=300)
    
    return result


# ========== Bug API ==========

@app.get("/api/bugs")
async def get_bugs(
    status: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 100,
    user: Dict = Depends(get_current_user)
):
    """获取 Bug 列表"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    db = get_database()
    bugs = db.get_bugs(status=status, project=project, limit=limit)
    
    return {"bugs": bugs}


@app.post("/api/bugs/submit")
async def submit_bug(
    request: Request,
    data: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """提交 Bug"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    title = data.get("title", "")
    priority = data.get("priority", "medium")
    description = data.get("description", "")
    project = data.get("project", "default")
    files = data.get("files", "")
    
    if not title or not description:
        raise HTTPException(status_code=400, detail="标题和描述不能为空")
    
    bug_id = f"bug_{int(time.time())}"
    
    db = get_database()
    success = db.create_bug(bug_id, title, description, priority, project, files)
    
    if not success:
        raise HTTPException(status_code=500, detail="创建 Bug 失败")
    
    # 清除缓存
    await cache_manager.clear_pattern("bugs:*")
    
    return {
        "success": True,
        "bug_id": bug_id,
        "message": "Bug 已提交，启动修复流程"
    }


# ========== 模板 API ==========

@app.get("/api/templates")
async def get_templates(user: Dict = Depends(get_current_user)):
    """获取模板列表"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    templates_file = MEMORY_DIR / "templates.json"
    if templates_file.exists():
        with open(templates_file, encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    return {"templates": []}


@app.post("/api/template/save")
async def save_template(
    data: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """保存模板"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    templates_file = MEMORY_DIR / "templates.json"
    
    templates = []
    if templates_file.exists():
        with open(templates_file, encoding='utf-8') as f:
            data_file = json.load(f)
            templates = data_file.get("templates", [])
    
    new_template = {
        "id": f"tpl_{int(time.time())}",
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "requirement": data.get("requirement", ""),
        "project": data.get("project", "default"),
        "created_at": datetime.now().isoformat()
    }
    
    templates.append(new_template)
    
    with open(templates_file, 'w', encoding='utf-8') as f:
        json.dump({"templates": templates}, f, ensure_ascii=False, indent=2)
    
    return {"success": True, "message": "模板已保存"}


@app.post("/api/template/delete")
async def delete_template(
    data: Dict[str, str],
    user: Dict = Depends(get_current_user)
):
    """删除模板"""
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    templates_file = MEMORY_DIR / "templates.json"
    
    if templates_file.exists():
        with open(templates_file, encoding='utf-8') as f:
            data_file = json.load(f)
            templates = data_file.get("templates", [])
        
        templates = [t for t in templates if t.get("id") != data.get("id")]
        
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump({"templates": templates}, f, ensure_ascii=False, indent=2)
    
    return {"success": True, "message": "模板已删除"}


# ========== 静态文件 ==========

# 挂载静态文件目录
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ========== HTML 页面路由 ==========

@app.get("/", response_class=HTMLResponse)
async def index(user: Dict = Depends(get_current_user)):
    """主页"""
    if not user:
        return RedirectResponse(url="/login")
    
    return get_main_page()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """登录页"""
    return get_login_page()


# ========== HTML 页面生成 ==========

def get_login_page():
    """生成登录页面"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - Agent 集群 V2.5</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
        .login-container{background:white;border-radius:16px;padding:40px;width:100%;max-width:400px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
        .logo{text-align:center;margin-bottom:30px}
        .logo h1{font-size:28px;color:#333;margin-bottom:10px}
        .logo .version{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:4px 12px;border-radius:20px;font-size:12px;display:inline-block;margin-top:8px}
        .form-group{margin-bottom:20px}
        .form-group label{display:block;margin-bottom:8px;color:#555;font-weight:500}
        .form-group input{width:100%;padding:12px 16px;border:2px solid #e0e0e0;border-radius:8px;font-size:14px;transition:border-color 0.3s}
        .form-group input:focus{outline:none;border-color:#667eea}
        .btn{width:100%;padding:14px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:transform 0.2s,box-shadow 0.2s}
        .btn:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(102,126,234,0.4)}
        .error-message{background:#fee;color:#c33;padding:12px;border-radius:8px;margin-bottom:20px;font-size:14px;display:none}
        .footer{text-align:center;margin-top:20px;color:#999;font-size:12px}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🤖 Agent 集群</h1>
            <p>智能协作开发系统</p>
            <span class="version">V2.5</span>
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
        <div class="footer">Agent Cluster Console v2.5 - FastAPI</div>
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
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                const data = await res.json();
                
                if (data.success) {
                    document.cookie = `auth_token=${data.token};Path=/;Max-Age=${data.expires_in};SameSite=Lax`;
                    window.location.href = '/';
                } else {
                    errorDiv.textContent = data.detail || '登录失败';
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
</html>"""


def get_main_page():
    """生成主页"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent 集群 V2.5</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}
        .header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}
        .nav{display:flex;gap:15px;margin-top:15px}
        .nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}
        .nav a:hover{background:rgba(255,255,255,0.1)}
        .container{max-width:1400px;margin:0 auto;padding:30px}
        .content{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:30px}
        h1{font-size:24px;margin-bottom:20px}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px}
        .stat-card{background:#f8f9fa;border-radius:8px;padding:20px;text-align:center}
        .stat-value{font-size:32px;font-weight:bold;color:#667eea}
        .stat-label{color:#666;margin-top:8px}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Agent 集群 V2.5</h1>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/agents">🤖 Agent</a>
            <a href="/phases">🔄 流程</a>
            <a href="/bugs">🐛 Bug</a>
            <a href="/templates">📝 模板</a>
            <a href="/costs">💰 成本</a>
            <a href="#" onclick="logout()">🚪 登出</a>
        </div>
    </div>
    <div class="container">
        <div class="content">
            <h2>📊 集群状态</h2>
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="status">-</div>
                    <div class="stat-label">集群状态</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="active">-</div>
                    <div class="stat-label">活跃工作流</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="completed">-</div>
                    <div class="stat-label">今日完成</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="agents">-</div>
                    <div class="stat-label">就绪 Agent</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        async function loadStats() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('status').textContent = data.status === 'running' ? '运行中' : '已停止';
                document.getElementById('active').textContent = data.active_workflows || 0;
                document.getElementById('completed').textContent = data.completed_today || 0;
                document.getElementById('agents').textContent = data.agents_ready || 0;
            } catch (e) {
                console.error(e);
            }
        }
        
        function logout() {
            fetch('/api/logout', {method: 'POST'}).then(() => {
                window.location.href = '/login';
            });
        }
        
        loadStats();
        setInterval(loadStats, 30000);
    </script>
</body>
</html>"""


# ========== 启动命令 ==========

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Agent Cluster V2.5 - FastAPI 异步版本              ║
╠═══════════════════════════════════════════════════════════╣
║  📊 性能优化：异步框架 | Redis 缓存 | Gzip 压缩              ║
║  🔗 API 文档：http://localhost:8890/docs                   ║
║  📖 ReDoc: http://localhost:8890/redoc                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        workers=1  # 开发环境单进程，生产环境可用 gunicorn -k uvicorn.workers.UvicornWorker
    )
