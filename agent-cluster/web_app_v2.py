#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 集群 Web 界面 V2.3.0
完整 6 阶段开发流程 | 10 个专业 Agent | 质量门禁 | 钉钉双向通知
安全增强：JWT 认证 | Rate Limiting | 健康检查
智能增强：智能重试 | 指标监控 | Dashboard 可视化
修复：Python 3.6 兼容性 (subprocess.capture_output)
"""

import json, os, sys, hashlib, time, secrets, logging
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse, subprocess
from typing import Tuple, Dict, Optional, List, Any

# ============== 统一日志配置 ==============
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# 配置主日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOGS_DIR / "web_app_v2.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("Agent 集群 Web 服务启动 (V2.3.0)")
logger.info("=" * 50)

# 安全模块导入
from utils.config_loader import config
from utils.auth import jwt_auth, require_auth, require_admin
from utils.rate_limiter import rate_limiter, get_client_ip
from utils.health_check import health_checker
from utils.database import get_database, init_database
from utils.backup_manager import get_backup_manager
from utils.checkpoint import get_checkpoint_manager, get_workflow_resumer
from utils.deploy_executor import get_deploy_executor
from utils.k8s_deploy import get_k8s_deploy_executor
from utils.metrics import get_prometheus_metrics
from utils.metrics_collector import get_metrics_collector

# 钉钉消息接收模块（可选）
try:
    from notifiers.dingtalk_receiver import DingTalkMessageHandler
    from notifiers.dingtalk import ClusterNotifier
    DINGTALK_RECEIVER_AVAILABLE = True
except ImportError:
    DINGTALK_RECEIVER_AVAILABLE = False
    print("⚠️  dingtalk_receiver 未安装，钉钉回调功能不可用")

# 初始化数据库
init_database()

# 初始化部署执行器
deploy_executor = get_deploy_executor()
k8s_executor = get_k8s_deploy_executor()

BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

AUTH_CONFIG_FILE = MEMORY_DIR / "auth_config.json"
SESSIONS_FILE = MEMORY_DIR / "sessions.json"
CLUSTER_CONFIG = BASE_DIR / "cluster_config_v2.json"

# Rate Limiting 配置
RATE_LIMIT_REQUESTS = 1000  # 临时提高限制用于测试
RATE_LIMIT_WINDOW = 60

class WebUIHandler(SimpleHTTPRequestHandler):
    PUBLIC_PATHS = ['/api/status', '/api/agents', '/api/phases', '/login', '/api/login', '/health', '/api/health/v24', '/static/']
    
    def __init__(self, *args, **kwargs):
        self.workflow_state = self._load_workflow_state()
        self.auth_config = self._load_auth_config()
        self.sessions = self._load_sessions()
        self.cluster_config = self._load_cluster_config()
        self.dingtalk_config = self._load_dingtalk_config()
        super().__init__(*args, **kwargs)
    
    def _load_dingtalk_config(self):
        """加载钉钉配置"""
        default = {
            "callback_token": "openclaw_callback_token_2026",
            "webhook": "",
            "secret": ""
        }
        if CLUSTER_CONFIG.exists():
            try:
                cfg = self.cluster_config.get("notifications", {}).get("dingtalk", {})
                default["webhook"] = cfg.get("webhook", "")
                default["secret"] = cfg.get("secret", "")
            except: pass
        return default
    
    def _load_auth_config(self):
        default = {"enabled": True, "username": "admin", "password_hash": hashlib.sha256("admin123".encode()).hexdigest(), "session_timeout_hours": 24}
        if AUTH_CONFIG_FILE.exists():
            try:
                with open(AUTH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f).get("auth", default)
            except: pass
        return default
    
    def _load_sessions(self):
        if SESSIONS_FILE.exists():
            try:
                with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}
    
    def _save_sessions(self):
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)
    
    def _load_workflow_state(self):
        state_file = MEMORY_DIR / "workflow_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}
    
    def _load_cluster_config(self):
        if CLUSTER_CONFIG.exists():
            try:
                with open(CLUSTER_CONFIG, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}
    
    def _hash_password(self, password): return hashlib.sha256(password.encode()).hexdigest()
    def _generate_token(self): return secrets.token_urlsafe(32)
    
    def _check_auth(self):
        if not self.auth_config.get("enabled", True): return True, None, False
        for p in self.PUBLIC_PATHS:
            if self.path.startswith(p): return True, None, False
        cookie = self.headers.get('Cookie', '')
        token = None
        for item in cookie.split(';'):
            if '=' in item:
                k, v = item.strip().split('=', 1)
                if k == 'auth_token': token = v; break
        if not token: return False, None, True
        if token in self.sessions:
            s = self.sessions[token]
            if time.time() - s.get("created_at", 0) < self.auth_config.get("session_timeout_hours", 24) * 3600:
                s["last_activity"] = time.time()
                self._save_sessions()
                return True, token, False
        return False, None, True
    
    def _get_client_ip(self):
        """获取客户端 IP（支持代理）"""
        return get_client_ip(dict(self.headers))
    
    def _check_rate_limit(self) -> Tuple[bool, int]:
        """检查速率限制"""
        client_id = self._get_client_ip()
        return rate_limiter.is_allowed(client_id)
    
    def _send_rate_limit_response(self, retry_after):
        # type: (int) -> None
        """发送速率限制响应"""
        self.send_response(429)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Retry-After', str(retry_after))
        self.send_header('X-RateLimit-Limit', str(RATE_LIMIT_REQUESTS))
        self.send_header('X-RateLimit-Remaining', '0')
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': '请求过于频繁',
            'retry_after': retry_after
        }).encode())
    
    def do_GET(self):
        """处理 GET 请求（带 Rate Limiting）"""
        path = urllib.parse.urlparse(self.path).path
        
        # 钉钉回调验证（公开端点，无需认证）
        if path == '/api/dingtalk/callback':
            self.handle_dingtalk_callback_verify()
            return
        
        # 检查速率限制（公开 API 也需要）
        allowed, remaining = self._check_rate_limit()
        if not allowed:
            retry_after = rate_limiter.get_retry_after(self._get_client_ip())
            self._send_rate_limit_response(retry_after)
            return
        
        is_auth, token, _ = self._check_auth()
        
        if not is_auth and not any(path.startswith(p) for p in self.PUBLIC_PATHS):
            self.send_response(302); self.send_header('Location', '/login'); self.end_headers(); return
        
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_checker.full_check()).encode())
            return
        elif path == '/api/health/v24':
            # v2.4 版本健康检查端点（简化版）
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "version": "v2.4.0",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "codename": "稳定性增强版"
            }).encode())
            return
        elif path == '/metrics/prometheus':
            # Prometheus 指标端点 (修改路径避免冲突)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(get_prometheus_metrics().encode())
            return
        elif path == '/api/status': self.send_json(self.get_status())
        elif path == '/api/agents': self.send_json(self.get_agents())
        elif path == '/api/phases': self.send_json(self.get_phases())
        elif path == '/api/quality-gate': self.send_json(self.get_quality_gate())
        elif path == '/api/workflows' and is_auth: self.send_json(self.get_workflows())
        elif path == '/api/templates' and is_auth: self.send_json(self.get_templates())
        elif path == '/api/costs' and is_auth: self.send_json(self.get_costs())
        elif path == '/api/projects' and is_auth: self.send_json(self.get_projects())
        elif path == '/login': self.send_html(self.get_login_page())
        # 指标 API 路由 (GET) - 需要认证
        elif is_auth and path == '/api/metrics/summary': self.send_json(self.get_metrics_summary())
        elif is_auth and path == '/api/metrics/agents': self.send_json(self.get_metrics_agents())
        elif is_auth and path == '/api/metrics/tasks': self.send_json(self.get_metrics_tasks())
        elif is_auth and path == '/api/metrics/failures': self.send_json(self.get_metrics_failures())
        elif is_auth and path == '/api/metrics/report': self.send_json(self.get_metrics_report())
        elif is_auth and path == '/': 
            if not is_auth: self.send_response(302); self.send_header('Location', '/login'); self.end_headers(); return
            self.send_html(self.get_main_page())
        elif path == '/workflows' and is_auth: self.send_html(self.get_workflows_page())
        elif path == '/history' and is_auth: self.send_html(self.get_history_page())
        elif path == '/agents' and is_auth: self.send_html(self.get_agents_page())
        elif path == '/phases' and is_auth: self.send_html(self.get_phases_page())
        elif path == '/quality' and is_auth: self.send_html(self.get_quality_page())
        elif path == '/bugs' and is_auth: self.send_html(self.get_bugs_page())
        elif path == '/deployments' and is_auth: self.send_html(self.get_deployments_page())
        elif path == '/templates' and is_auth: self.send_html(self.get_templates_page())
        elif path == '/costs' and is_auth: self.send_html(self.get_costs_page())
        elif path == '/monitoring' and is_auth: self.send_html(self.get_monitoring_page())
        elif path == '/metrics' and is_auth: self.send_html(self.get_metrics_dashboard())
        elif path == '/metrics.html' and is_auth: self.send_html(self.get_metrics_dashboard())
        elif path == '/settings' and is_auth: self.send_html(self.get_settings_page())
        else: super().do_GET()
    
    def do_POST(self):
        """处理 POST 请求（带 Rate Limiting）"""
        path = urllib.parse.urlparse(self.path).path
        
        # 钉钉回调消息（公开端点，无需认证）
        if path == '/api/dingtalk/callback':
            self.handle_dingtalk_callback_message()
            return
        
        # 检查速率限制
        allowed, remaining = self._check_rate_limit()
        if not allowed:
            retry_after = rate_limiter.get_retry_after(self._get_client_ip())
            self._send_rate_limit_response(retry_after)
            return
        
        cl = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(cl).decode('utf-8')) if cl else {}
        
        # 登录接口使用新的 JWT 认证
        if path == '/api/login': self.handle_login_jwt(data); return
        
        # 需求检查和成本估算不需要认证（提交前预检）
        if path == '/api/requirement/check': self.send_json(self.check_requirement(data)); return
        if path == '/api/cost/estimate': self.send_json(self.estimate_cost(data)); return
        
        is_auth, token, _ = self._check_auth()
        if not is_auth: self.send_json({"error": "未授权"}, 401); return
        
        if path == '/api/submit': self.send_json(self.submit_task(data))
        elif path == '/api/workflows': self.send_json(self.get_workflows(data))
        elif path == '/api/task/history': self.send_json(self.get_task_history(data))
        elif path == '/api/task/archive': self.send_json({"success": self._archive_completed_task(data.get('task_id', ''))})
        elif path == '/api/task/logs': self.send_json(self.get_task_logs(data))
        elif path == '/api/task/retry-history': self.send_json(self.get_task_retry_history(data))
        elif path == '/api/system/load': self.send_json(self.get_system_load())
        elif path == '/api/deploy/execute': self.send_json(self.execute_deploy(data))
        elif path == '/api/deploy/stop': self.send_json(self.stop_deploy(data))
        elif path == '/api/deploy/status': self.send_json(self.get_deploy_status(data))
        elif path == '/api/bugs/submit': self.send_json(self.submit_bug(data))
        elif path == '/api/bugs' and is_auth: self.send_json(self.get_bugs())
        elif path == '/api/template/save': self.send_json(self.save_template(data))
        elif path == '/api/template/delete': self.send_json(self.delete_template(data))
        elif path == '/api/logout': self.handle_logout_jwt(token)
        elif path == '/api/change-password': self.handle_change_password_jwt(data, token)
        # 指标 API 路由
        elif path == '/api/metrics/summary': self.send_json(self.get_metrics_summary())
        elif path == '/api/metrics/agents': self.send_json(self.get_metrics_agents())
        elif path == '/api/metrics/tasks': self.send_json(self.get_metrics_tasks())
        elif path == '/api/metrics/failures': self.send_json(self.get_metrics_failures())
        elif path == '/api/metrics/report': self.send_json(self.get_metrics_report())
        else: self.send_error(404)
    
    def send_json(self, data, status=200):
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html(self, html):
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_login_jwt(self, data):
        """JWT 登录处理（兼容旧版 auth_config）"""
        try:
            username = data.get("username", "")
            password = data.get("password", "")
            
            if not username or not password:
                self.send_json({"success": False, "error": "用户名和密码不能为空"}, 400)
                return
            
            # 尝试旧版 auth_config 兼容（优先）
            if username == self.auth_config.get("username") and self._hash_password(password) == self.auth_config.get("password_hash"):
                user = {
                    'username': username,
                    'user_id': hashlib.md5(username.encode()).hexdigest(),
                    'role': 'admin'
                }
            else:
                # 尝试新的 JWT 认证
                user = jwt_auth.authenticate(username, password)
            
            if not user:
                self.send_json({"success": False, "error": "用户名或密码错误"}, 401)
                return
            
            # 创建访问 Token
            access_token = jwt_auth.create_token(username, user['user_id'], refresh=False)
            
            # 记录会话
            self.sessions[access_token] = {
                "username": username,
                "ip": self._get_client_ip(),
                "created_at": time.time(),
                "last_activity": time.time(),
                "user_id": user['user_id'],
                "role": user.get('role', 'user')
            }
            self._save_sessions()
            
            self.send_json({
                "success": True,
                "token": access_token,
                "expires_in": config.jwt_expiration * 3600,
                "user": {"username": username, "role": user.get('role', 'user')}
            })
        except Exception as e:
            print(f"登录错误：{e}")
            self.send_json({"success": False, "error": str(e)}, 500)
    
    def handle_logout_jwt(self, token):
        """JWT 登出处理"""
        # 将 Token 加入黑名单
        jwt_auth.logout(token)
        
        # 删除本地会话
        if token in self.sessions:
            del self.sessions[token]
            self._save_sessions()
        
        self.send_response(302)
        self.send_header('Location', '/login')
        self.send_header('Set-Cookie', 'auth_token=; Path=/; Max-Age=0')
        self.end_headers()
    
    def handle_change_password_jwt(self, data, token):
        """JWT 修改密码处理"""
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")
        
        # 获取当前用户
        payload = jwt_auth.verify_token(token)
        if not payload:
            self.send_json({"success": False, "error": "Token 无效"}, 401)
            return
        
        username = payload.get('username')
        
        # 修改密码
        success, message = jwt_auth.change_password(username, old_password, new_password)
        if not success:
            self.send_json({"success": False, "error": message})
            return
        
        # 使所有现有 Token 失效
        jwt_auth.logout(token)
        self.sessions = {}
        self._save_sessions()
        
        self.send_json({"success": True, "message": "密码已修改，请重新登录"})
    
    def handle_login(self, data):
        """兼容旧版登录（调用 JWT 版本）"""
        self.handle_login_jwt(data)
    
    def handle_logout(self, token):
        """兼容旧版登出（调用 JWT 版本）"""
        self.handle_logout_jwt(token)
    
    def handle_change_password(self, data, token):
        """兼容旧版修改密码（调用 JWT 版本）"""
        self.handle_change_password_jwt(data, token)
    
    def handle_dingtalk_callback_verify(self):
        """处理钉钉回调验证（GET 请求）"""
        if not DINGTALK_RECEIVER_AVAILABLE:
            self.send_json({"error": "钉钉接收模块未安装"}, 503)
            return
        
        try:
            # 解析查询参数
            query_string = self.path.split('?')[1] if '?' in self.path else ''
            params = urllib.parse.parse_qs(query_string)
            
            signature = params.get('signature', [''])[0]
            timestamp = params.get('timestamp', [''])[0]
            nonce = params.get('nonce', [''])[0]
            echostr = params.get('echostr', [''])[0]
            
            # 验证签名
            if self._verify_dingtalk_signature(signature, timestamp, nonce):
                print(f"✅ 钉钉回调验证成功 (timestamp={timestamp})")
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                # 直接返回 echostr（钉钉要求）
                self.wfile.write(echostr.encode())
            else:
                print(f"❌ 钉钉回调验证失败")
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "签名验证失败"}).encode())
        except Exception as e:
            print(f"❌ 钉钉回调验证异常：{e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def handle_dingtalk_callback_message(self):
        """处理钉钉消息回调（POST 请求）"""
        if not DINGTALK_RECEIVER_AVAILABLE:
            self.send_json({"error": "钉钉接收模块未安装"}, 503)
            return
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # 验证签名
            signature = self.headers.get('x-ding-signature', '')
            timestamp = self.headers.get('x-ding-timestamp', '')
            nonce = self.headers.get('x-ding-nonce', '')
            
            if not self._verify_dingtalk_signature(signature, timestamp, nonce):
                print(f"❌ 钉钉消息签名验证失败")
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "签名验证失败"}).encode())
                return
            
            # 解析消息
            message = self._parse_dingtalk_message(data)
            if message:
                print(f"📱 收到钉钉消息：{message['content']} (from {message['user']})")
                
                # 处理消息（部署确认等）
                self._process_dingtalk_message(message)
                
                # 返回成功
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "无法解析消息"}).encode())
                
        except Exception as e:
            print(f"❌ 处理钉钉消息失败：{e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def _verify_dingtalk_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """验证钉钉签名"""
        # 开发环境：如果签名为空，跳过验证
        if not signature and not timestamp and not nonce:
            return True
        
        callback_token = self.dingtalk_config.get("callback_token", "openclaw_callback_token_2026")
        
        try:
            # 计算签名
            sign_str = f"{timestamp}\n{nonce}\n{callback_token}"
            expected = hmac.new(
                callback_token.encode(),
                sign_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature == expected
        except Exception as e:
            print(f"⚠️ 签名验证异常：{e}")
            return False
    
    def _parse_dingtalk_message(self, data: Dict) -> Optional[Dict]:
        """解析钉钉消息"""
        try:
            msg_type = data.get('msgtype', 'text')
            
            if msg_type == 'text':
                content = data.get('text', {}).get('content', '')
            elif msg_type == 'markdown':
                content = data.get('markdown', {}).get('text', '')
            else:
                content = str(data)
            
            # 提取用户信息
            sender_id = data.get('senderId', 'unknown')
            sender_nick = data.get('senderNick', '钉钉用户')
            
            return {
                'content': content,
                'user': sender_nick,
                'user_id': sender_id,
                'msg_type': msg_type,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'conversation_id': data.get('conversationId', ''),
                'chatbot_user_id': data.get('chatbotUserId', '')
            }
        except Exception as e:
            print(f"⚠️ 解析钉钉消息失败：{e}")
            return None
    
    def _process_dingtalk_message(self, message: Dict):
        """处理钉钉消息"""
        content = message['content'].lower().strip()
        user = message['user']
        
        # 部署确认命令
        if any(kw in content for kw in ["部署", "确认", "deploy", "approve", "yes"]):
            print(f"✅ 收到部署确认：{user}")
            self._handle_deploy_confirm(user, message)
        elif any(kw in content for kw in ["取消", "cancel", "reject", "no"]):
            print(f"❌ 收到部署取消：{user}")
            self._handle_deploy_cancel(user, message)
        else:
            print(f"ℹ️ 未知命令：{content}")
    
    def _handle_deploy_confirm(self, user: str, message: Dict):
        """处理部署确认"""
        try:
            # 获取待确认的部署
            wf_state = self._load_workflow_state()
            pending = wf_state.get("pending_deployments", {})
            
            if not pending:
                print("⚠️ 没有待确认的部署")
                return
            
            # 获取最新的待确认部署
            deploy_id = list(pending.keys())[0]
            deploy_info = pending[deploy_id]
            
            # 发送确认通知
            webhook = self.dingtalk_config.get("webhook", "")
            secret = self.dingtalk_config.get("secret", "")
            
            if webhook:
                notifier = ClusterNotifier(webhook, secret)
                notifier.dingtalk.send_markdown(
                    "🚀 部署已确认",
                    f"""## 🚀 部署已确认

**确认人**: {user}
**部署 ID**: {deploy_id}
**项目**: {deploy_info.get('project_name', 'N/A')}
**版本**: {deploy_info.get('version', 'N/A')}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

正在执行部署，预计 5 分钟内完成...

---

🤖 Agent 集群自动部署
"""
                )
            
            # 更新部署状态
            pending[deploy_id]['status'] = 'confirmed'
            pending[deploy_id]['confirmed_by'] = user
            pending[deploy_id]['confirmed_at'] = datetime.now().isoformat()
            
            # 保存状态
            wf_state["pending_deployments"] = pending
            self.workflow_state = wf_state
            self._save_workflow_state(wf_state)
            
            print(f"✅ 部署 {deploy_id} 已确认，开始执行...")
            
            # TODO: 触发实际部署逻辑
            # self.execute_deploy(deploy_info)
            
        except Exception as e:
            print(f"❌ 处理部署确认失败：{e}")
    
    def _handle_deploy_cancel(self, user: str, message: Dict):
        """处理部署取消"""
        try:
            wf_state = self._load_workflow_state()
            pending = wf_state.get("pending_deployments", {})
            
            if not pending:
                print("⚠️ 没有待确认的部署")
                return
            
            deploy_id = list(pending.keys())[0]
            deploy_info = pending[deploy_id]
            
            webhook = self.dingtalk_config.get("webhook", "")
            secret = self.dingtalk_config.get("secret", "")
            
            if webhook:
                notifier = ClusterNotifier(webhook, secret)
                notifier.dingtalk.send_markdown(
                    "❌ 部署已取消",
                    f"""## ❌ 部署已取消

**取消人**: {user}
**部署 ID**: {deploy_id}
**项目**: {deploy_info.get('project_name', 'N/A')}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

部署已取消。如需重新部署，请重新触发流程。

---

🤖 Agent 集群自动部署
"""
                )
            
            # 更新状态
            pending[deploy_id]['status'] = 'cancelled'
            pending[deploy_id]['cancelled_by'] = user
            pending[deploy_id]['cancelled_at'] = datetime.now().isoformat()
            
            wf_state["pending_deployments"] = pending
            self.workflow_state = wf_state
            self._save_workflow_state(wf_state)
            
            print(f"❌ 部署 {deploy_id} 已取消")
            
        except Exception as e:
            print(f"❌ 处理部署取消失败：{e}")
    
    def _save_workflow_state(self, state):
        """保存工作流状态"""
        state_file = MEMORY_DIR / "workflow_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def get_health(self):
        """健康检查端点"""
        try:
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'agent-cluster',
                'version': '2.2.0'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_status(self):
        orch = bool(subprocess.run(['pgrep', '-f', 'orchestrator.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5).stdout.strip())
        deploy = bool(subprocess.run(['pgrep', '-f', 'deploy_listener.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5).stdout.strip())
        wf = self.workflow_state.get("workflows", {})
        wfl = list(wf.values()) if isinstance(wf, dict) else wf
        return {"status": "running" if orch else "stopped", "deploy_listener": "running" if deploy else "stopped",
                "timestamp": datetime.now().isoformat(), "active_workflows": len([w for w in wfl if w.get("status")=="running"]),
                "completed_today": len([w for w in wfl if w.get("status")=="completed"]),
                "failed_today": len([w for w in wfl if w.get("status")=="failed"]),
                "agents_ready": 10, "dingtalk_enabled": self.cluster_config.get("dingtalk", {}).get("webhook") is not None}
    
    def get_agents(self):
        return {"executors": [
            {"name": "Product Manager", "role": "产品经理", "phase": "Phase 1", "model": "qwen-max"},
            {"name": "Tech Lead", "role": "技术负责人", "phase": "Phase 2", "model": "qwen-max"},
            {"name": "Designer", "role": "设计师", "phase": "Phase 2", "model": "qwen-vl-plus"},
            {"name": "DevOps", "role": "运维工程师", "phase": "Phase 2/6", "model": "qwen-plus"},
            {"name": "Codex", "role": "后端专家", "phase": "Phase 3", "model": "qwen-coder-plus"},
            {"name": "Claude-Code", "role": "前端专家", "phase": "Phase 3", "model": "kimi-k2.5"},
            {"name": "Tester", "role": "测试工程师", "phase": "Phase 4", "model": "qwen-coder-plus"}],
            "reviewers": [
            {"name": "Codex Reviewer", "role": "逻辑审查", "phase": "Phase 5", "model": "glm-4.7"},
            {"name": "Gemini Reviewer", "role": "安全审查", "phase": "Phase 5", "model": "qwen-plus"},
            {"name": "Claude Reviewer", "role": "基础审查", "phase": "Phase 5", "model": "MiniMax-M2.5"}]}
    
    def get_phases(self):
        return {"phases": [
            {"id": 1, "name": "需求分析", "agents": ["Product Manager"], "outputs": ["PRD 文档", "用户故事", "验收标准"]},
            {"id": 2, "name": "技术设计", "agents": ["Tech Lead", "Designer", "DevOps"], "outputs": ["架构文档", "UI 设计", "部署配置"]},
            {"id": 3, "name": "开发实现", "agents": ["Codex", "Claude-Code"], "outputs": ["后端代码", "前端代码"]},
            {"id": 4, "name": "测试验证", "agents": ["Tester"], "outputs": ["测试报告", "Bug 列表"], "quality_gate": True},
            {"id": 5, "name": "代码审查", "agents": ["Codex Reviewer", "Gemini Reviewer", "Claude Reviewer"], "outputs": ["审查报告"], "quality_gate": True},
            {"id": 6, "name": "部署上线", "agents": ["DevOps"], "outputs": ["运行中的系统"], "require_confirmation": True}]}
    
    def get_quality_gate(self):
        cfg = self.cluster_config.get("quality_gate", {})
        return {"phase_4": {"enabled": True, "min_coverage": cfg.get("phase_4", {}).get("min_coverage", 80), "max_critical_bugs": 0},
                "phase_5": {"enabled": True, "min_review_score": cfg.get("phase_5", {}).get("min_review_score", 80), "required_approvals": 3},
                "deployment": {"require_confirmation": True, "confirmation_timeout_minutes": 30}}
    
    def get_workflows(self):
        wf = self.workflow_state.get("workflows", {})
        wfl = list(wf.values()) if isinstance(wf, dict) else wf
        wfl.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"workflows": wfl[-50:]}
    
    def get_templates(self):
        tf = MEMORY_DIR / "templates.json"
        if tf.exists():
            try:
                with open(tf, 'r', encoding='utf-8') as f: return {"templates": json.load(f)}
            except: pass
        return {"templates": []}
    
    def get_costs(self):
        cf = MEMORY_DIR / "cost_stats.json"
        if cf.exists():
            try:
                with open(cf, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return {"today": {"total": 0}, "week": {"total": 0}, "month": {"total": 0}, "by_model": {}}
    
    def get_projects(self):
        pf = BASE_DIR / "projects.json"
        if pf.exists():
            try:
                with open(pf, 'r', encoding='utf-8') as f: return {"projects": json.load(f)}
            except: pass
        return {"projects": []}
    
    def estimate_cost(self, data: Dict) -> Dict:
        """估算任务成本"""
        try:
            req = data.get("requirement", "")
            if not req:
                return {"success": False, "error": "需求不能为空"}
            
            # 基于需求长度和复杂度估算
            char_count = len(req)
            
            # 基础 token 估算 (中文字符约 1.5 token/字)
            estimated_tokens = int(char_count * 1.5)
            
            # 复杂度系数 (根据关键词判断)
            complexity_keywords = {
                "系统": 2.0, "平台": 2.0, "引擎": 1.8,
                "管理": 1.5, "分析": 1.5, "报表": 1.5,
                "用户": 1.3, "数据": 1.3, "接口": 1.3,
                "功能": 1.2, "模块": 1.2
            }
            
            complexity = 1.0
            found_complexity = []
            for kw, factor in complexity_keywords.items():
                if kw in req:
                    complexity = max(complexity, factor)
                    found_complexity.append(kw)
            
            # 阶段估算 (6 个阶段)
            phases = {
                "1_requirement": {"tokens": 2000, "cost_per_1k": 0.02},
                "2_design": {"tokens": 4000, "cost_per_1k": 0.02},
                "3_development": {"tokens": 8000, "cost_per_1k": 0.02},
                "4_testing": {"tokens": 3000, "cost_per_1k": 0.02},
                "5_review": {"tokens": 5000, "cost_per_1k": 0.01},
                "6_deploy": {"tokens": 1000, "cost_per_1k": 0.02}
            }
            
            # 总估算
            total_tokens = 0
            total_cost = 0.0
            
            for phase, info in phases.items():
                phase_tokens = int(info["tokens"] * complexity)
                phase_cost = (phase_tokens / 1000) * info["cost_per_1k"]
                total_tokens += phase_tokens
                total_cost += phase_cost
            
            # 添加需求本身的 token
            total_tokens += estimated_tokens
            
            # 按模型估算 (qwen-max)
            model_estimates = {
                "qwen-max": {"tokens": total_tokens, "cost": total_cost * 1.0},
                "qwen-plus": {"tokens": total_tokens, "cost": total_cost * 0.5},
                "qwen-coder-plus": {"tokens": total_tokens, "cost": total_cost * 0.8}
            }
            
            # 确定复杂度等级
            if complexity >= 1.8:
                level = "high"
                level_name = "高复杂度"
            elif complexity >= 1.3:
                level = "medium"
                level_name = "中复杂度"
            else:
                level = "low"
                level_name = "低复杂度"
            
            return {
                "success": True,
                "estimated_tokens": total_tokens,
                "estimated_cost": round(total_cost, 2),
                "complexity": complexity,
                "complexity_level": level,
                "complexity_name": level_name,
                "found_keywords": found_complexity,
                "char_count": char_count,
                "models": model_estimates,
                "phase_breakdown": {
                    "1_requirement": {"name": "需求分析", "tokens": int(phases["1_requirement"]["tokens"] * complexity)},
                    "2_design": {"name": "技术设计", "tokens": int(phases["2_design"]["tokens"] * complexity)},
                    "3_development": {"name": "开发实现", "tokens": int(phases["3_development"]["tokens"] * complexity)},
                    "4_testing": {"name": "测试验证", "tokens": int(phases["4_testing"]["tokens"] * complexity)},
                    "5_review": {"name": "代码审查", "tokens": int(phases["5_review"]["tokens"] * complexity)},
                    "6_deploy": {"name": "部署上线", "tokens": int(phases["6_deploy"]["tokens"] * complexity)}
                }
            }
        except Exception as e:
            logger.error(f"成本估算失败：{e}")
            return {"success": False, "error": str(e)}
    
    def check_requirement(self, data: Dict) -> Dict:
        """预检查需求完整性"""
        try:
            req = data.get("requirement", "")
            if not req:
                return {"success": False, "error": "需求不能为空"}
            
            # 基础检查
            issues = []
            suggestions = []
            score = 100
            
            # 检查长度
            if len(req) < 20:
                issues.append("需求描述过短")
                suggestions.append("请详细描述功能需求，建议至少 50 字")
                score -= 30
            elif len(req) < 50:
                suggestions.append("建议补充更多细节，如用户场景、功能列表等")
                score -= 10
            
            # 检查是否有关键词
            keywords = ["功能", "需要", "实现", "支持", "用户", "系统", "数据", "界面"]
            found_keywords = [kw for kw in keywords if kw in req]
            if len(found_keywords) < 2:
                issues.append("缺少关键功能描述词")
                suggestions.append("请明确说明需要实现什么功能")
                score -= 20
            
            # 检查是否有明确的目标
            if not any(c in req for c in ['。', '！', '!', '?', '\n']):
                suggestions.append("建议使用分点描述，使需求更清晰")
                score -= 10
            
            # 检查是否过于模糊
            vague_words = ["大概", "可能", "也许", "随便", "看着办"]
            if any(vw in req for vw in vague_words):
                issues.append("需求描述过于模糊")
                suggestions.append("请给出明确的功能要求和边界")
                score -= 25
            
            # 确保分数不低于 0
            score = max(0, score)
            
            # 判定结果
            if score >= 80:
                level = "excellent"
                message = "✅ 需求描述清晰，可以提交"
            elif score >= 60:
                level = "good"
                message = "⚠️ 需求基本清晰，建议补充细节"
            elif score >= 40:
                level = "warning"
                message = "⚠️ 需求描述不够清晰，建议完善后再提交"
            else:
                level = "poor"
                message = "❌ 需求描述过于模糊，请重新整理后提交"
            
            return {
                "success": True,
                "score": score,
                "level": level,
                "message": message,
                "issues": issues,
                "suggestions": suggestions,
                "char_count": len(req),
                "keywords_found": found_keywords
            }
        except Exception as e:
            logger.error(f"需求检查失败：{e}")
            return {"success": False, "error": str(e)}
    
    def submit_task(self, data):
        req = data.get("requirement", "")
        project = data.get("project", "default")
        if not req: return {"success": False, "error": "需求不能为空"}
        try:
            task_id = f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            log_file = LOGS_DIR / f"task_{task_id}.log"
            
            # 记录任务提交
            logger.info(f"📥 收到新任务：{task_id}")
            logger.info(f"   项目：{project}")
            logger.info(f"   需求：{req[:100]}...")
            
            # 保存任务状态
            self._save_task_state(task_id, {"requirement": req, "project": project, "status": "running", "created_at": datetime.now().isoformat()})
            
            # 启动 orchestrator (日志输出到独立文件)
            subprocess.Popen(
                f"cd {BASE_DIR} && python3 orchestrator.py \"{req}\" >> {log_file} 2>&1",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info(f"✅ 任务已提交：{task_id}")
            return {"success": True, "message": "任务已提交", "task_id": task_id}
        except Exception as e:
            logger.error(f"❌ 任务提交失败：{e}")
            return {"success": False, "error": str(e)}
    
    def _save_task_state(self, task_id: str, state: Dict):
        """保存任务状态"""
        tasks_file = MEMORY_DIR / "active_tasks.json"
        tasks = {}
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            except:
                pass
        tasks[task_id] = state
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    def _load_task_state(self) -> Dict:
        """加载所有任务状态"""
        tasks_file = MEMORY_DIR / "active_tasks.json"
        if not tasks_file.exists():
            return {}
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _archive_completed_task(self, task_id: str):
        """归档已完成的任务"""
        try:
            tasks = self._load_task_state()
            if task_id not in tasks:
                return False
            
            task = tasks[task_id]
            if task.get('status') not in ['completed', 'failed']:
                return False
            
            # 加载历史任务
            history_file = MEMORY_DIR / "completed_tasks.json"
            history = []
            if history_file.exists():
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except:
                    pass
            
            # 添加到历史
            task['archived_at'] = datetime.now().isoformat()
            history.insert(0, task)
            
            # 保留最近 100 条
            history = history[:100]
            
            # 保存历史
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            # 从 active 移除
            del tasks[task_id]
            tasks_file = MEMORY_DIR / "active_tasks.json"
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 任务已归档：{task_id}")
            return True
        except Exception as e:
            logger.error(f"归档任务失败：{e}")
            return False
    
    def get_system_load(self) -> Dict:
        """获取系统负载信息"""
        try:
            import subprocess
            
            # CPU 使用率
            cpu_result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
            cpu_line = [l for l in cpu_result.stdout.split('\n') if 'Cpu(s)' in l]
            cpu_usage = 0
            if cpu_line:
                parts = cpu_line[0].split(',')
                for p in parts:
                    if 'us' in p.lower():
                        try:
                            cpu_usage = float(p.split()[0])
                        except:
                            pass
            
            # 内存使用率
            mem_result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=5)
            mem_lines = mem_result.stdout.split('\n')
            mem_usage = 0
            if len(mem_lines) > 1:
                parts = mem_lines[1].split()
                if len(parts) >= 3:
                    total = float(parts[1])
                    used = float(parts[2])
                    mem_usage = (used / total) * 100 if total > 0 else 0
            
            # 运行中任务数
            tasks = self._load_task_state()
            running_count = sum(1 for t in tasks.values() if t.get('status') == 'running')
            
            # 计算推荐并发数
            # 规则：CPU<50% 且 内存<70% → max 5
            #      CPU<70% 且 内存<80% → max 3
            #      其他 → max 1
            if cpu_usage < 50 and mem_usage < 70:
                recommended = 5
            elif cpu_usage < 70 and mem_usage < 80:
                recommended = 3
            else:
                recommended = 1
            
            return {
                "success": True,
                "cpu_usage": round(cpu_usage, 1),
                "memory_usage": round(mem_usage, 1),
                "running_tasks": running_count,
                "recommended_concurrency": recommended,
                "current_max": 3  # 当前配置值
            }
        except Exception as e:
            logger.error(f"获取系统负载失败：{e}")
            return {"success": False, "error": str(e)}
    
    def get_task_retry_history(self, data: Dict = None) -> Dict:
        """获取任务重试历史"""
        try:
            task_id = data.get('task_id', '') if data else ''
            if not task_id:
                return {"success": False, "error": "缺少 task_id"}
            
            tasks = self._load_task_state()
            if task_id not in tasks:
                # 尝试从历史记录中查找
                history_file = MEMORY_DIR / "completed_tasks.json"
                if history_file.exists():
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                    for task in history:
                        if task.get('id') == task_id:
                            tasks[task_id] = task
                            break
            
            if task_id not in tasks:
                return {"success": False, "error": "任务不存在"}
            
            task = tasks[task_id]
            retry_history = []
            
            # 提取重试相关信息
            attempts = task.get('attempts', [])
            for i, attempt in enumerate(attempts):
                retry_history.append({
                    "attempt": i + 1,
                    "timestamp": attempt.get('timestamp', ''),
                    "agent": attempt.get('agent', ''),
                    "status": attempt.get('status', 'unknown'),
                    "failure_reason": attempt.get('failure_reason', ''),
                    "retry_strategy": attempt.get('retry_strategy', ''),
                    "next_action": attempt.get('next_action', '')
                })
            
            # 当前状态
            current_info = {
                "retry_count": task.get('retry_count', 0),
                "last_failure_reason": task.get('last_failure_reason', ''),
                "retry_strategy": task.get('retry_strategy', ''),
                "target_agent": task.get('target_agent', ''),
                "status": task.get('status', '')
            }
            
            return {
                "success": True,
                "task_id": task_id,
                "current": current_info,
                "history": retry_history,
                "total_attempts": len(retry_history)
            }
        except Exception as e:
            logger.error(f"获取重试历史失败：{e}")
            return {"success": False, "error": str(e)}
    
    def get_task_logs(self, data: Dict = None) -> Dict:
        """获取任务日志"""
        try:
            task_id = data.get('task_id', '') if data else ''
            if not task_id:
                return {"success": False, "error": "缺少 task_id"}
            
            # 查找任务日志文件
            log_file = LOGS_DIR / f"task_{task_id}.log"
            
            if not log_file.exists():
                # 尝试从 orchestrator 日志中查找
                orchestrator_log = LOGS_DIR / "orchestrator.log"
                if orchestrator_log.exists():
                    # 读取最近 100 行
                    with open(orchestrator_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-100:]
                    return {"success": True, "logs": ''.join(lines), "source": "orchestrator"}
                return {"success": True, "logs": "暂无日志记录", "source": "none"}
            
            # 读取日志文件（最近 200 行）
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-200:]
            
            return {"success": True, "logs": ''.join(lines), "source": "task", "lines": len(lines)}
        except Exception as e:
            logger.error(f"获取任务日志失败：{e}")
            return {"success": False, "error": str(e)}
    
    def get_task_history(self, data: Dict = None) -> Dict:
        """获取历史任务列表"""
        try:
            history_file = MEMORY_DIR / "completed_tasks.json"
            if not history_file.exists():
                return {"success": True, "history": [], "total": 0}
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 支持过滤
            status_filter = data.get('status') if data else None
            if status_filter:
                history = [t for t in history if t.get('status') == status_filter]
            
            # 按归档时间倒序
            history.sort(key=lambda x: x.get('archived_at', x.get('created_at', '')), reverse=True)
            
            return {"success": True, "history": history[:50], "total": len(history)}
        except Exception as e:
            logger.error(f"获取历史任务失败：{e}")
            return {"success": False, "error": str(e)}
    
    def get_workflows(self, data: Dict = None) -> Dict:
        """获取工作流列表（增强版 - 含进度信息）"""
        try:
            tasks = self._load_task_state()
            workflow_list = []
            
            # 定义阶段顺序和进度权重
            phase_progress = {
                "1_requirement": 10,
                "2_design": 25,
                "3_development": 50,
                "4_testing": 70,
                "5_review": 85,
                "6_deploy": 95,
                "completed": 100
            }
            
            phase_names = {
                "1_requirement": "需求分析",
                "2_design": "技术设计",
                "3_development": "开发实现",
                "4_testing": "测试验证",
                "5_review": "代码审查",
                "6_deploy": "部署上线",
                "completed": "已完成"
            }
            
            for task_id, task in tasks.items():
                phase = task.get("phase", "1_requirement")
                status = task.get("status", "unknown")
                
                # 计算进度百分比
                if status == "completed":
                    progress = 100
                elif status == "failed":
                    progress = phase_progress.get(phase, 0)
                else:
                    progress = phase_progress.get(phase, 0)
                
                workflow_list.append({
                    "id": task_id,
                    "requirement": task.get("requirement", "")[:100],
                    "project": task.get("project", "default"),
                    "status": status,
                    "created_at": task.get("created_at", ""),
                    "phase": phase,
                    "phase_name": phase_names.get(phase, phase),
                    "progress": progress,
                    "updated_at": task.get("updated_at", task.get("created_at", ""))
                })
            
            # 按创建时间倒序
            workflow_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return {"success": True, "workflows": workflow_list, "total": len(workflow_list)}
        except Exception as e:
            logger.error(f"获取工作流列表失败：{e}")
            return {"success": False, "error": str(e)}
    
    def save_template(self, data):
        tf = MEMORY_DIR / "templates.json"
        tpl = []
        if tf.exists():
            try:
                with open(tf, 'r', encoding='utf-8') as f: tpl = json.load(f)
            except: pass
        new = {"id": f"tpl_{datetime.now().strftime('%Y%m%d%H%M%S')}", "name": data.get("name",""), "description": data.get("description",""),
               "requirement": data.get("requirement",""), "project": data.get("project","default"), "created_at": datetime.now().isoformat()}
        tpl.append(new)
        with open(tf, 'w', encoding='utf-8') as f: json.dump(tpl, f, ensure_ascii=False, indent=2)
        return {"success": True, "template": new}
    
    def delete_template(self, data):
        tf = MEMORY_DIR / "templates.json"
        if not tf.exists(): return {"success": False, "error": "模板文件不存在"}
        with open(tf, 'r', encoding='utf-8') as f: tpl = json.load(f)
        tpl = [t for t in tpl if t.get("id") != data.get("id")]
        with open(tf, 'w', encoding='utf-8') as f: json.dump(tpl, f, ensure_ascii=False, indent=2)
        return {"success": True}

    # ============== HTML 页面 ==============
    def get_login_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>登录 - Agent 集群 V2.1</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}.login-container{background:white;border-radius:16px;padding:40px;width:100%;max-width:400px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}.logo{text-align:center;margin-bottom:30px}.logo h1{font-size:28px;color:#333;margin-bottom:10px}.logo p{color:#666;font-size:14px}.logo .version{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:4px 12px;border-radius:20px;font-size:12px;display:inline-block;margin-top:8px}.form-group{margin-bottom:20px}.form-group label{display:block;margin-bottom:8px;color:#555;font-weight:500}.form-group input{width:100%;padding:12px 16px;border:2px solid #e0e0e0;border-radius:8px;font-size:14px;transition:border-color 0.3s}.form-group input:focus{outline:none;border-color:#667eea}.btn{width:100%;padding:14px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:transform 0.2s,box-shadow 0.2s}.btn:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(102,126,234,0.4)}.btn:disabled{opacity:0.6;cursor:not-allowed;transform:none}.error-message{background:#fee;color:#c33;padding:12px;border-radius:8px;margin-bottom:20px;font-size:14px;display:none}.footer{text-align:center;margin-top:20px;color:#999;font-size:12px}.features{margin-top:20px;padding:15px;background:#f8f9fa;border-radius:8px}.features h4{color:#666;font-size:14px;margin-bottom:10px}.features ul{list-style:none}.features li{color:#888;font-size:12px;padding:4px 0}.features li:before{content:"✅ "}</style></head><body>
<div class="login-container"><div class="logo"><h1>🤖 Agent 集群</h1><p>智能协作开发系统</p><span class="version">V2.2.0 智能增强版</span></div>
<div class="error-message" id="errorMessage"></div>
<form id="loginForm"><div class="form-group"><label for="username">用户名</label><input type="text" id="username" name="username" placeholder="请输入用户名" autocomplete="username" required></div>
<div class="form-group"><label for="password">密码</label><input type="password" id="password" name="password" placeholder="请输入密码" autocomplete="current-password" required></div>
<button type="submit" class="btn" id="submitBtn">登录</button></form>
<div class="features"><h4>📊 系统特性</h4><ul><li>完整 6 阶段开发流程</li><li>10 个专业 Agent 协作</li><li>质量门禁自动审查</li><li>钉钉双向通知</li></ul></div>
<div class="footer">Agent Cluster Console v2.1</div></div>
<script>document.getElementById('loginForm').addEventListener('submit',async function(e){e.preventDefault();const btn=document.getElementById('submitBtn');const errorDiv=document.getElementById('errorMessage');const username=document.getElementById('username').value;const password=document.getElementById('password').value;btn.disabled=true;btn.textContent='登录中...';errorDiv.style.display='none';try{const res=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});const data=await res.json();if(data.success){document.cookie=`auth_token=${data.token};Path=/;Max-Age=${24*60*60};SameSite=Strict`;window.location.href='/';}else{errorDiv.textContent=data.error||'登录失败';errorDiv.style.display='block';btn.disabled=false;btn.textContent='登录';}}catch(err){errorDiv.textContent='网络错误，请稍后重试';errorDiv.style.display='block';btn.disabled=false;btn.textContent='登录';}});</script></body></html>"""

    def get_main_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Agent 集群 V2.1 控制台</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px 40px}.header-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.header h1{font-size:24px}.header .version{background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:20px;font-size:12px}.nav{display:flex;gap:15px;flex-wrap:wrap}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px;transition:background 0.3s;font-size:14px}.nav a:hover{background:rgba(255,255,255,0.2)}.container{max-width:1600px;margin:0 auto;padding:30px}.status-bar{background:white;border-radius:12px;padding:20px;margin-bottom:30px;display:flex;gap:30px;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.status-item{display:flex;align-items:center;gap:10px}.status-dot{width:12px;height:12px;border-radius:50%}.status-dot.green{background:#10b981}.status-dot.red{background:#ef4444}.status-dot.yellow{background:#f59e0b}.status-label{color:#666;font-size:14px}.status-value{font-weight:600;color:#333}.status-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08);transition:transform 0.2s}.card:hover{transform:translateY(-4px)}.card h3{color:#666;font-size:14px;margin-bottom:10px}.card .value{font-size:32px;font-weight:bold;color:#333}.card .sub{font-size:12px;color:#999;margin-top:8px}.card .icon{font-size:24px;margin-bottom:10px}.section{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.section h2{margin-bottom:20px;color:#333;font-size:18px}.phase-timeline{display:flex;gap:10px;overflow-x:auto;padding-bottom:10px}.phase-card{min-width:200px;background:#f8f9fa;border-radius:12px;padding:20px;border-left:4px solid #667eea}.phase-card h4{color:#333;margin-bottom:8px;font-size:16px}.phase-card p{color:#666;font-size:13px;margin-bottom:10px}.phase-card .agents{display:flex;flex-wrap:wrap;gap:5px}.phase-card .agent-tag{background:#e0e7ff;color:#4f46e5;padding:3px 8px;border-radius:4px;font-size:11px}.phase-card .quality-gate{background:#fef3c7;color:#d97706;padding:3px 8px;border-radius:4px;font-size:11px;margin-top:8px;display:inline-block}.submit-form{background:linear-gradient(135deg,#f8f9fa,#e9ecef);border-radius:12px;padding:30px;margin-bottom:30px}.submit-form h2{margin-bottom:20px;color:#333}.form-group{margin-bottom:20px}.form-group label{display:block;margin-bottom:8px;color:#555;font-weight:500}.form-group textarea{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;font-size:14px;resize:vertical;min-height:120px;font-family:inherit}.form-group textarea:focus{outline:none;border-color:#667eea}.form-group select{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;font-size:14px}.btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;padding:12px 30px;border-radius:8px;font-size:16px;cursor:pointer;transition:transform 0.2s}.btn:hover{transform:translateY(-2px)}.agent-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:15px}.agent-card{background:#f8f9fa;border-radius:10px;padding:16px;display:flex;align-items:center;gap:15px}.agent-avatar{width:48px;height:48px;border-radius:8px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-size:20px}.agent-info{flex:1}.agent-info h4{color:#333;font-size:14px;margin-bottom:4px}.agent-info p{color:#666;font-size:12px}.agent-info .model{color:#999;font-size:11px;margin-top:4px}.status-badge{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:500}.status-badge.ready{background:#d1fae5;color:#065f46}.workflow-list{max-height:400px;overflow-y:auto}.workflow-item{padding:15px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center}.workflow-item:last-child{border-bottom:none}.workflow-item .info{flex:1}.workflow-item .title{font-weight:500;color:#333;font-size:14px}.workflow-item .meta{font-size:12px;color:#999;margin-top:5px}.workflow-item .status-badge{padding:4px 12px;border-radius:20px;font-size:12px}.status-badge.completed{background:#d1fae5;color:#065f46}.status-badge.running{background:#dbeafe;color:#1e40af}.status-badge.failed{background:#fee2e2;color:#991b1b}.quick-actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-top:20px}.quick-action{background:white;border:2px solid #e0e0e0;border-radius:10px;padding:16px;text-align:center;cursor:pointer;transition:all 0.2s;text-decoration:none;color:#333}.quick-action:hover{border-color:#667eea;background:#f0f4ff}.quick-action .icon{font-size:28px;margin-bottom:8px}.quick-action .label{font-size:13px;font-weight:500}</style></head><body>
<div class="header"><div class="header-top"><h1>🤖 Agent 集群控制台</h1><span class="version">V2.2.0 智能增强版</span></div>
<div class="nav"><a href="/">📊 概览</a><a href="/phases">🔄 开发流程</a><a href="/agents">🤖 Agent 阵容</a><a href="/workflows">📋 工作流</a><a href="/history">📜 历史</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板库</a><a href="/costs">💰 成本统计</a><a href="/metrics">📈 指标</a><a href="/monitoring">📋 监控日志</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout();return false;">🚪 登出</a></div></div>
<div class="container">
<div class="status-bar"><div class="status-item"><span class="status-dot green" id="clusterStatusDot"></span><span class="status-label">集群状态:</span><span class="status-value" id="clusterStatus">-</span></div>
<div class="status-item"><span class="status-dot green" id="deployStatusDot"></span><span class="status-label">部署监听:</span><span class="status-value" id="deployStatus">-</span></div>
<div class="status-item"><span class="status-dot green" id="dingtalkStatusDot"></span><span class="status-label">钉钉通知:</span><span class="status-value" id="dingtalkStatus">-</span></div>
<div class="status-item" style="margin-left:auto;color:#999;font-size:13px;" id="lastUpdate"></div>
<div class="status-item" style="color:#666;font-size:13px;" id="systemLoad">负载：-</div></div>
<div class="status-cards"><div class="card"><div class="icon">🔄</div><h3>进行中的工作流</h3><div class="value" id="activeWorkflows">-</div><div class="sub">当前正在执行</div></div>
<div class="card"><div class="icon">✅</div><h3>今日完成</h3><div class="value" id="completedToday">-</div><div class="sub">成功完成的工作流</div></div>
<div class="card"><div class="icon">❌</div><h3>今日失败</h3><div class="value" id="failedToday">-</div><div class="sub">需要关注</div></div>
<div class="card"><div class="icon">🤖</div><h3>就绪 Agent</h3><div class="value" id="agentsReady">-</div><div class="sub">共 10 个 Agent</div></div></div>
<div class="submit-form"><h2>🚀 提交新任务</h2>
<div class="form-group"><label>📝 选择模板（可选）</label><select id="templateSelect" onchange="useTemplate()"><option value="">-- 选择预设模板 --</option></select></div>
<div class="form-group"><label>产品需求描述</label><textarea id="requirement" placeholder="详细描述你想要实现的功能... 也可以从上方模板快速选择" oninput="debounceEstimate()"></textarea></div>
<div class="form-group" id="costEstimateBox" style="display:none;background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:15px;margin-bottom:15px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;"><h4 style="margin:0;color:#0369a1;">💰 成本估算</h4><span id="complexityBadge" style="padding:4px 12px;border-radius:20px;font-size:12px;background:#e0e7ff;color:#4f46e5;">中复杂度</span></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:10px;"><div><div style="font-size:12px;color:#666;">预估 Token</div><div style="font-size:20px;font-weight:bold;color:#0369a1;" id="estTokens">-</div></div><div><div style="font-size:12px;color:#666;">预估成本</div><div style="font-size:20px;font-weight:bold;color:#059669;" id="estCost">¥-</div></div></div><div style="font-size:12px;color:#666;margin-bottom:8px;">分阶段估算:</div><div id="phaseBreakdown" style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:11px;"></div></div>
<div class="form-group"><label>选择项目</label><select id="project"><option value="default">默认项目</option><option value="ecommerce">电商项目</option><option value="blog">博客系统</option><option value="crm">CRM 系统</option></select></div>
<button class="btn" onclick="submitTask()">🚀 启动工作流</button></div>
<div class="section"><h2>🔄 完整开发流程（6 阶段）</h2><div class="phase-timeline" id="phaseTimeline"></div></div>
<div class="section"><h2>🤖 Agent 阵容（10 个）</h2><div class="agent-grid" id="agentGrid"></div></div>
<div class="section"><h2>📋 最近工作流</h2><div class="workflow-list" id="workflowList"></div></div>
<div id="logModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center;"><div style="background:white;border-radius:12px;width:90%;max-width:900px;max-height:80vh;display:flex;flex-direction:column;"><div style="padding:20px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;"><h3 style="margin:0;" id="logModalTitle">📜 任务日志</h3><button onclick="closeLogModal()" style="background:none;border:none;font-size:24px;cursor:pointer;color:#666;">&times;</button></div><div style="flex:1;overflow:auto;padding:20px;background:#1e1e1e;color:#d4d4d4;font-family:'Consolas','Monaco',monospace;font-size:13px;white-space:pre-wrap;word-break:break-all;" id="logContent">加载中...</div><div style="padding:15px;border-top:1px solid #eee;display:flex;justify-content:flex-end;"><button onclick="refreshLogs()" style="background:#667eea;color:white;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;margin-right:10px;">🔄 刷新</button><button onclick="closeLogModal()" style="background:#e0e0e0;color:#333;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;">关闭</button></div></div></div>
<div id="retryModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center;"><div style="background:white;border-radius:12px;width:90%;max-width:800px;max-height:80vh;display:flex;flex-direction:column;"><div style="padding:20px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;"><h3 style="margin:0;" id="retryModalTitle">🔄 重试历史</h3><button onclick="closeRetryModal()" style="background:none;border:none;font-size:24px;cursor:pointer;color:#666;">&times;</button></div><div style="flex:1;overflow:auto;padding:20px;" id="retryContent">加载中...</div><div style="padding:15px;border-top:1px solid #eee;display:flex;justify-content:flex-end;"><button onclick="closeRetryModal()" style="background:#e0e0e0;color:#333;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;">关闭</button></div></div></div>
<div class="section"><h2>⚡ 快捷操作</h2><div class="quick-actions"><a href="/phases" class="quick-action"><div class="icon">🔄</div><div class="label">查看流程</div></a><a href="/agents" class="quick-action"><div class="icon">🤖</div><div class="label">Agent 状态</div></a><a href="/quality" class="quick-action"><div class="icon">🚦</div><div class="label">质量门禁</div></a><a href="/templates" class="quick-action"><div class="icon">📝</div><div class="label">模板库</div></a><a href="/costs" class="quick-action"><div class="icon">💰</div><div class="label">成本统计</div></a><a href="/bugs" class="quick-action"><div class="icon">🐛</div><div class="label">Bug 管理</div></a><a href="/deployments" class="quick-action"><div class="icon">🚀</div><div class="label">发布管理</div></a></div></div></div>
<script>const phases=[{id:1,name:"Phase 1: 需求分析",agents:["Product Manager"],tags:["PRD 文档","用户故事"]},{id:2,name:"Phase 2: 技术设计",agents:["Tech Lead","Designer","DevOps"],tags:["架构设计","UI 设计","部署配置"]},{id:3,name:"Phase 3: 开发实现",agents:["Codex","Claude-Code"],tags:["后端代码","前端代码"]},{id:4,name:"Phase 4: 测试验证",agents:["Tester"],tags:["单元测试","集成测试"],qg:true},{id:5,name:"Phase 5: 代码审查",agents:["3 Reviewers"],tags:["逻辑审查","安全审查"],qg:true},{id:6,name:"Phase 6: 部署上线",agents:["DevOps"],tags:["Docker","CI/CD"]}];document.getElementById('phaseTimeline').innerHTML=phases.map(p=>`<div class="phase-card"><h4>${p.name}</h4><p>${p.agents.join('+')}</p><div class="agents">${p.tags.map(t=>`<span class="agent-tag">${t}</span>`).join('')}</div>${p.qg?'<span class="quality-gate">🚦 质量门禁</span>':''}</div>`).join('');
async function loadStatus(){try{const res=await fetch('/api/status');const d=await res.json();document.getElementById('clusterStatus').textContent=d.status==='running'?'运行中':'已停止';document.getElementById('clusterStatusDot').className='status-dot '+(d.status==='running'?'green':'red');document.getElementById('deployStatus').textContent=d.deploy_listener==='running'?'监听中':'已停止';document.getElementById('deployStatusDot').className='status-dot '+(d.deploy_listener==='running'?'green':'yellow');document.getElementById('dingtalkStatus').textContent=d.dingtalk_enabled?'已启用':'未配置';document.getElementById('dingtalkStatusDot').className='status-dot '+(d.dingtalk_enabled?'green':'yellow');document.getElementById('activeWorkflows').textContent=d.active_workflows;document.getElementById('completedToday').textContent=d.completed_today;document.getElementById('failedToday').textContent=d.failed_today;document.getElementById('agentsReady').textContent=d.agents_ready;document.getElementById('lastUpdate').textContent='最后更新：'+new Date(d.timestamp).toLocaleString('zh-CN');const loadRes=await fetch('/api/system/load');const loadD=await loadRes.json();if(loadD.success){const icon=loadD.recommended_concurrency>=5?'🟢':loadD.recommended_concurrency>=3?'🟡':'🔴';document.getElementById('systemLoad').textContent=`负载：${icon} CPU${loadD.cpu_usage}% 内存${loadD.memory_usage}% 并发${loadD.recommended_concurrency}`;}}catch(e){console.error(e);}}
async function loadAgents(){try{const res=await fetch('/api/agents');const d=await res.json();const all=[...d.executors,...d.reviewers];document.getElementById('agentGrid').innerHTML=all.map(a=>{const av=a.name.split(' ').map(w=>w[0]).join('').substring(0,2);return`<div class="agent-card"><div class="agent-avatar">${av}</div><div class="agent-info"><h4>${a.name}</h4><p>${a.role} · ${a.phase}</p><div class="model">${a.model}</div></div><span class="status-badge ready">就绪</span></div>`;}).join('');}catch(e){console.error(e);}}
let currentLogTaskId='';async function loadWorkflows(){try{const res=await fetch('/api/workflows');const d=await res.json();const list=document.getElementById('workflowList');if(!d.workflows||d.workflows.length===0){list.innerHTML='<div style="color:#999;text-align:center;padding:40px;">暂无工作流记录</div>';return;}list.innerHTML=d.workflows.slice(0,10).map(wf=>{const sc=wf.status==='completed'?'completed':wf.status==='failed'?'failed':'running';const st=wf.status==='completed'?'✅ 完成':wf.status==='failed'?'❌ 失败':'🔄 进行中';const progress=wf.progress||0;const phaseName=wf.phase_name||wf.phase||'需求';const isRunning=wf.status==='running';return`<div class="workflow-item"><div class="info" style="flex:1;min-width:0;"><div class="title" style="margin-bottom:8px;">${wf.requirement||'未命名任务'}</div><div class="meta" style="margin-bottom:8px;">${wf.id||'-'} · ${wf.project||'默认'} · ${new Date(wf.created_at).toLocaleString('zh-CN')}</div><div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;"><span style="font-size:12px;color:#666;min-width:60px;">${phaseName}</span><div style="flex:1;height:6px;background:#e0e0e0;border-radius:3px;overflow:hidden;"><div style="width:${progress}%;height:100%;background:linear-gradient(90deg,#667eea,#764ba2);transition:width 0.3s;"></div></div><span style="font-size:12px;color:#666;min-width:35px;text-align:right;">${progress}%</span></div></div><div style="display:flex;gap:8px;align-items:center;">${isRunning?`<button onclick="viewLogs('${wf.id}')" style="background:#667eea;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;">📜 日志</button>`:''}${wf.retry_count>0?`<button onclick="viewRetryHistory('${wf.id}')" style="background:#f59e0b;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;">🔄 重试${wf.retry_count}</button>`:''}<span class="status-badge ${sc}" style="align-self:flex-start;">${st}</span></div></div>`;}).join('');}catch(e){console.error('加载工作流失败:',e);}}
async function viewLogs(taskId){currentLogTaskId=taskId;document.getElementById('logModalTitle').textContent='📜 任务日志 - '+taskId;document.getElementById('logModal').style.display='flex';refreshLogs();}
async function refreshLogs(){if(!currentLogTaskId)return;try{const res=await fetch('/api/task/logs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:currentLogTaskId})});const d=await res.json();document.getElementById('logContent').textContent=d.logs||'暂无日志';}catch(e){document.getElementById('logContent').textContent='加载失败：'+e.message;}}
function closeLogModal(){document.getElementById('logModal').style.display='none';currentLogTaskId='';}
async function viewRetryHistory(taskId){document.getElementById('retryModalTitle').textContent='🔄 重试历史 - '+taskId;document.getElementById('retryModal').style.display='flex';try{const res=await fetch('/api/task/retry-history?task_id='+taskId);const d=await res.json();if(d.success){const c=d.current;const h=d.history||[];let html=`<div style="margin-bottom:20px;padding:15px;background:#f8f9fa;border-radius:8px;"><h4 style="margin:0 0 10px 0;">当前状态</h4><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:14px;">`;html+=`<div><strong>重试次数:</strong> ${c.retry_count||0}</div>`;html+=`<div><strong>状态:</strong> ${c.status||'unknown'}</div>`;html+=`<div><strong>失败原因:</strong> ${c.last_failure_reason||'-'}</div>`;html+=`<div><strong>策略:</strong> ${c.retry_strategy||'-'}</div>`;if(c.target_agent)html+=`<div><strong>目标 Agent:</strong> ${c.target_agent}</div>`;html+=`</div></div>`;if(h.length>0){html+=`<h4 style="margin:0 0 15px 0;">重试记录</h4>`;h.forEach((att,i)=>{html+=`<div style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;margin-bottom:10px;background:${i===h.length-1?'#fff3cd':'#fff'};">`;html+=`<div style="display:flex;justify-content:space-between;margin-bottom:8px;"><strong>第${att.attempt}次尝试</strong><span style="color:#666;font-size:12px;">${new Date(att.timestamp).toLocaleString('zh-CN')}</span></div>`;if(att.agent)html+=`<div style="font-size:13px;margin-bottom:5px;"><strong>Agent:</strong> ${att.agent}</div>`;if(att.failure_reason)html+=`<div style="font-size:13px;margin-bottom:5px;color:#c33;"><strong>失败:</strong> ${att.failure_reason}</div>`;if(att.retry_strategy)html+=`<div style="font-size:13px;margin-bottom:5px;color:#667eea;"><strong>策略:</strong> ${att.retry_strategy}</div>`;if(att.next_action)html+=`<div style="font-size:13px;color:#666;"><strong>下一步:</strong> ${att.next_action}</div>`;html+=`</div>`;});}else{html+=`<div style="text-align:center;color:#999;padding:40px;">暂无重试记录</div>`;}document.getElementById('retryContent').innerHTML=html;}else{document.getElementById('retryContent').textContent='加载失败：'+(d.error||'未知错误');}}catch(e){document.getElementById('retryContent').textContent='加载失败：'+e.message;}}
function closeRetryModal(){document.getElementById('retryModal').style.display='none';}
async function loadTemplates(){try{const res=await fetch('/api/templates');const d=await res.json();const sel=document.getElementById('templateSelect');if(!d.templates||d.templates.length===0){sel.innerHTML='<option value="">-- 暂无模板 --</option>';return;}sel.innerHTML='<option value="">-- 选择预设模板 --</option>'+d.templates.map(t=>`<option value="${t.requirement.replace(/"/g,'&quot;')}" data-project="${t.project||'default'}">${t.name} - ${t.description||t.requirement.substring(0,30)}...</option>`).join('');}catch(e){console.error('加载模板失败:',e);}}
function useTemplate(){const sel=document.getElementById('templateSelect');const req=document.getElementById('requirement');const proj=document.getElementById('project');if(sel.value){req.value=sel.value;if(sel.options[sel.selectedIndex].dataset.project){proj.value=sel.options[sel.selectedIndex].dataset.project;}}}
let estimateTimer=null;async function debounceEstimate(){clearTimeout(estimateTimer);const req=document.getElementById('requirement').value.trim();if(req.length<10){document.getElementById('costEstimateBox').style.display='none';return;}estimateTimer=setTimeout(estimateCost,500);}
async function estimateCost(){try{const req=document.getElementById('requirement').value.trim();if(req.length<10)return;const res=await fetch('/api/cost/estimate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({requirement:req})});const d=await res.json();if(d.success){document.getElementById('costEstimateBox').style.display='block';document.getElementById('estTokens').textContent=d.estimated_tokens.toLocaleString();document.getElementById('estCost').textContent='¥'+d.estimated_cost.toFixed(2);const badge=document.getElementById('complexityBadge');badge.textContent=d.complexity_name;badge.style.background=d.complexity_level==='high'?'#fee2e2':d.complexity_level==='medium'?'#fef3c7':'#d1fae5';badge.style.color=d.complexity_level==='high'?'#991b1b':d.complexity_level==='medium'?'#92400e':'#065f46';let phases='';for(let k in d.phase_breakdown){const p=d.phase_breakdown[k];phases+=`<div style="background:white;padding:8px;border-radius:4px;"><div style="color:#666;">${p.name}</div><div style="color:#0369a1;font-weight:bold;">${p.tokens.toLocaleString()}</div></div>`;}document.getElementById('phaseBreakdown').innerHTML=phases;}}catch(e){console.error('估算失败:',e);}}
async function submitTask(){const req=document.getElementById('requirement').value.trim();const proj=document.getElementById('project').value;if(!req){alert('请输入产品需求');return;}
// 预检查需求
const checkRes=await fetch('/api/requirement/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({requirement:req})});const checkData=await checkRes.json();if(checkData.level==='poor'){alert('⚠️ 需求检查未通过\\n\\n'+checkData.message+(checkData.suggestions.length?'\\n\\n建议：\\n'+checkData.suggestions.join('\\n'):''));return;}if(checkData.level==='warning'||checkData.level==='good'){if(!confirm('⚠️ 需求检查提示\\n\\n'+checkData.message+(checkData.suggestions.length?'\\n\\n建议：\\n'+checkData.suggestions.join('\\n'):'')+'\\n\\n仍要提交吗？'))return;}
if(!confirm('确定要启动工作流吗？\\n\\n这将启动完整的 6 阶段开发流程。'))return;try{const res=await fetch('/api/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({requirement:req,project:proj})});const d=await res.json();if(d.success){alert('✅ '+d.message);document.getElementById('requirement').value='';document.getElementById('costEstimateBox').style.display='none';loadStatus();loadWorkflows();}else{alert('❌ '+d.error);}catch(e){alert('提交失败：'+e.message);}}
async function logout(){if(!confirm('确定要登出吗？'))return;try{await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}catch(err){alert('登出失败：'+err.message);}}
loadStatus();loadAgents();loadWorkflows();loadTemplates();
setInterval(loadStatus,30000);
setInterval(loadWorkflows,10000);</script></body></html>"""

    def get_workflows_page(self): return self._list_page("工作流", "/api/workflows", ["workflow_id", "requirement", "project", "status", "created_at"])
    def get_history_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>执行历史 - Agent 集群</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.section{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.section h2{margin-bottom:20px}.filters{display:flex;gap:15px;margin-bottom:20px}.filters select{padding:8px 16px;border:1px solid #ddd;border-radius:6px}.table-container{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#f8f9fa;color:#666;font-weight:500;font-size:14px}.status-badge{padding:4px 12px;border-radius:20px;font-size:12px}.status-badge.completed{background:#d1fae5;color:#065f46}.status-badge.failed{background:#fee2e2;color:#991b1b}.empty{text-align:center;color:#999;padding:40px}</style></head><body>
<div class="header"><h1>📜 执行历史</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/history">📜 历史</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div>
<div class="container">
<div class="section"><h2>📜 历史任务</h2>
<div class="filters"><select id="statusFilter" onchange="loadHistory()"><option value="">全部状态</option><option value="completed">✅ 已完成</option><option value="failed">❌ 已失败</option></select><span id="totalCount" style="color:#666;margin-left:auto;"></span></div>
<div class="table-container"><table><thead><tr><th>任务 ID</th><th>需求</th><th>项目</th><th>状态</th><th>阶段</th><th>创建时间</th><th>归档时间</th></tr></thead><tbody id="historyBody"><tr><td colspan="7" class="empty">加载中...</td></tr></tbody></table></div></div></div>
<script>async function loadHistory(){const filter=document.getElementById('statusFilter').value;try{const res=await fetch('/api/task/history'+(filter?`?status=${filter}`:''));const d=await res.json();document.getElementById('totalCount').textContent=`共 ${d.total||0} 条`;const tbody=document.getElementById('historyBody');if(!d.history||d.history.length===0){tbody.innerHTML='<tr><td colspan="7" class="empty">暂无历史记录</td></tr>';return;}tbody.innerHTML=d.history.map(h=>{const sc=h.status==='completed'?'completed':'failed';const st=h.status==='completed'?'✅ 完成':'❌ 失败';return`<tr><td>${h.id||'-'}</td><td style="max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${(h.requirement||'').replace(/"/g,'&quot;')}">${h.requirement||'未命名'}</td><td>${h.project||'默认'}</td><td><span class="status-badge ${sc}">${st}</span></td><td>${(h.phase||'1_requirement').split('_')[1]||'需求'}</td><td>${new Date(h.created_at||'').toLocaleString('zh-CN')}</td><td>${new Date(h.archived_at||'').toLocaleString('zh-CN')}</td></tr>`;}).join('');}catch(e){console.error('加载历史失败:',e);}}
async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}
loadHistory();</script></body></html>"""
    def get_agents_page(self): return self._agents_page()
    def get_phases_page(self): return self._phases_page()
    def get_quality_page(self): return self._quality_page()
    def get_bugs_page(self): return self._bugs_page()

    def get_templates_page(self): return self._templates_page()
    def get_costs_page(self): return self._costs_page()
    def get_settings_page(self): return self._settings_page()
    
    def _list_page(self, title, api, fields):
        return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>{title} - Agent 集群</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}}.header{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}}.nav{{display:flex;gap:15px;margin-top:15px}}.nav a{{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}}.container{{max-width:1400px;margin:0 auto;padding:30px}}.content{{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #eee}}th{{background:#f8f9fa;color:#666;font-weight:500}}.status-badge{{padding:4px 12px;border-radius:20px;font-size:12px}}.status-badge.completed{{background:#d1fae5;color:#065f46}}.status-badge.running{{background:#dbeafe;color:#1e40af}}.status-badge.failed{{background:#fee2e2;color:#991b1b}}</style></head><body><div class="header"><h1>📋 {title}</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div><div class="container"><div class="content"><table><thead><tr>{''.join(f'<th>{f}</th>' for f in fields)}</tr></thead><tbody id="tbody"><tr><td colspan="{len(fields)}" style="text-align:center;color:#999;">加载中...</td></tr></tbody></table></div></div><script>async function load(){{const res=await fetch('{api}');const d=await res.json();document.getElementById('tbody').innerHTML=d{fields[0]}.length?d{fields[0]}.map(r=>`<tr>${{fields.map(f=>`<td>${{r[f]||'-'}}</td>`).join('')}}</tr>`).join(''):'<tr><td colspan="{len(fields)}" style="text-align:center;color:#999;">暂无数据</td></tr>'}}async function logout(){{if(!confirm('确定登出？'))return;await fetch('/api/logout',{{method:'POST'}});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}}load();</script></body></html>"""
    
    def _agents_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>Agent 阵容 - Agent 集群</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.section{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.section h2{margin-bottom:20px}.agent-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}.agent-card{background:#f8f9fa;border-radius:12px;padding:20px;display:flex;gap:15px}.agent-avatar{width:56px;height:56px;border-radius:12px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-size:24px;font-weight:bold}.agent-info h3{color:#333;margin-bottom:8px}.agent-info p{color:#666;font-size:14px;margin-bottom:5px}.agent-info .model{color:#999;font-size:12px}.status-badge{padding:4px 10px;border-radius:20px;font-size:12px;background:#d1fae5;color:#065f46}</style></head><body><div class="header"><h1>🤖 Agent 阵容</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div><div class="container"><div class="section"><h2>执行 Agent（7 个）</h2><div class="agent-grid" id="executors"></div></div><div class="section"><h2>审查 Agent（3 个）</h2><div class="agent-grid" id="reviewers"></div></div></div><script>async function load(){const res=await fetch('/api/agents');const d=await res.json();document.getElementById('executors').innerHTML=d.executors.map(a=>render(a)).join('');document.getElementById('reviewers').innerHTML=d.reviewers.map(a=>render(a)).join('');}function render(a){const av=a.name.split(' ').map(w=>w[0]).join('').substring(0,2);return`<div class="agent-card"><div class="agent-avatar">${av}</div><div class="agent-info"><h3>${a.name}</h3><p>${a.role}</p><p>${a.phase}</p><div class="model">${a.model}</div></div><span class="status-badge">就绪</span></div>`;}async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}load();</script></body></html>"""
    
    def _phases_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>开发流程 - Agent 集群</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.timeline{position:relative;max-width:1000px;margin:0 auto}.phase{background:white;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #667eea;position:relative}.phase h3{color:#333;margin-bottom:10px}.phase p{color:#666;margin-bottom:15px}.phase .agents{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:15px}.phase .agent-tag{background:#e0e7ff;color:#4f46e5;padding:6px 12px;border-radius:6px;font-size:13px}.phase .outputs{display:flex;flex-wrap:wrap;gap:8px}.phase .output-tag{background:#f0f9ff;color:#0369a1;padding:6px 12px;border-radius:6px;font-size:13px}.phase .quality-gate{position:absolute;top:24px;right:24px;background:#fef3c7;color:#d97706;padding:6px 12px;border-radius:20px;font-size:12px;font-weight:500}</style></head><body><div class="header"><h1>🔄 完整开发流程</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div><div class="container"><div class="timeline" id="timeline"></div></div><script>const phases=[{id:1,name:"Phase 1: 需求分析",desc:"理解产品需求，明确功能范围",agents:["Product Manager"],outputs:["PRD 文档","用户故事","验收标准"]},{id:2,name:"Phase 2: 技术设计",desc:"系统架构设计，UI/UX 设计，部署规划",agents:["Tech Lead","Designer","DevOps"],outputs:["架构设计文档","UI 设计稿","Docker 配置","CI/CD 配置"]},{id:3,name:"Phase 3: 开发实现",desc:"前后端代码开发",agents:["Codex","Claude-Code"],outputs:["后端代码","前端代码","数据库迁移"]},{id:4,name:"Phase 4: 测试验证",desc:"单元测试，集成测试，E2E 测试",agents:["Tester"],outputs:["测试报告","Bug 列表","覆盖率报告"],qg:true},{id:5,name:"Phase 5: 代码审查",desc:"多层代码审查",agents:["Codex Reviewer","Gemini Reviewer","Claude Reviewer"],outputs:["逻辑审查报告","安全审查报告","改进建议"],qg:true},{id:6,name:"Phase 6: 部署上线",desc:"部署到生产环境",agents:["DevOps"],outputs:["运行中的系统","监控告警","日志管理"],confirm:true}];document.getElementById('timeline').innerHTML=phases.map((p,i)=>`<div class="phase"><span style="color:#999;font-size:12px;">STEP ${i+1}</span><h3>${p.name}</h3><p>${p.desc}</p><div class="agents">${p.agents.map(a=>`<span class="agent-tag">${a}</span>`).join('')}</div><div class="outputs">${p.outputs.map(o=>`<span class="output-tag">📄 ${o}</span>`).join('')}</div>${p.qg?'<span class="quality-gate">🚦 质量门禁</span>':''}${p.confirm?'<span class="quality-gate" style="background:#dbeafe;color:#1e40af;">🔐 需要确认</span>':''}</div>`).join('');</script></body></html>"""
    
    def _quality_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>质量门禁 - Agent 集群</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.card h3{color:#333;margin-bottom:15px;display:flex;align-items:center;gap:10px}.card h3 .icon{font-size:24px}.item{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #eee}.item:last-child{border-bottom:none}.item .label{color:#666}.item .value{font-weight:600;color:#333}.item .value.ok{color:#10b981}.item .value.warn{color:#f59e0b}</style></head><body><div class="header"><h1>🚦 质量门禁</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div><div class="container"><div class="grid"><div class="card"><h3><span class="icon">🧪</span>Phase 4 测试门禁</h3><div class="item"><span class="label">状态</span><span class="value ok">✅ 启用</span></div><div class="item"><span class="label">最低测试覆盖率</span><span class="value">80%</span></div><div class="item"><span class="label">最大高危 Bug</span><span class="value">0 个</span></div><div class="item"><span class="label">最大中危 Bug</span><span class="value">3 个</span></div><div class="item"><span class="label">核心功能测试</span><span class="value ok">100% 通过</span></div></div><div class="card"><h3><span class="icon">🔍</span>Phase 5 审查门禁</h3><div class="item"><span class="label">状态</span><span class="value ok">✅ 启用</span></div><div class="item"><span class="label">最低审查评分</span><span class="value">80 分</span></div><div class="item"><span class="label">需要审查者通过</span><span class="value">3/3</span></div><div class="item"><span class="label">严重问题</span><span class="value">0 个</span></div></div><div class="card"><h3><span class="icon">🚀</span>部署确认</h3><div class="item"><span class="label">状态</span><span class="value ok">✅ 启用</span></div><div class="item"><span class="label">需要钉钉确认</span><span class="value">是</span></div><div class="item"><span class="label">确认超时时间</span><span class="value">30 分钟</span></div><div class="item"><span class="label">超时自动取消</span><span class="value">是</span></div></div><div class="card"><h3><span class="icon">🔁</span>Bug 修复循环</h3><div class="item"><span class="label">Phase 4 最大重试</span><span class="value">3 次</span></div><div class="item"><span class="label">Phase 5 最大重试</span><span class="value">3 次</span></div><div class="item"><span class="label">超时处理</span><span class="value warn">人工介入</span></div></div></div></div><script>async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}</script></body></html>"""
    
    def _templates_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>模板库 - Agent 集群</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.add-form{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.add-form h2{margin-bottom:20px}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#555}.form-group input,.form-group textarea{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px}.btn{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:20px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.card h3{color:#333;margin-bottom:10px}.card p{color:#666;font-size:14px;margin-bottom:15px}.card .meta{font-size:12px;color:#999}</style></head><body><div class="header"><h1>📝 模板库</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div><div class="container"><div class="add-form"><h2>➕ 新建模板</h2><div class="form-group"><label>模板名称</label><input type="text" id="name" placeholder="例如：电商购物车功能"></div><div class="form-group"><label>描述</label><input type="text" id="desc" placeholder="简短描述"></div><div class="form-group"><label>需求内容</label><textarea id="req" rows="4" placeholder="详细需求描述..."></textarea></div><div class="form-group"><label>项目</label><select id="project"><option value="default">默认项目</option><option value="ecommerce">电商项目</option><option value="blog">博客系统</option></select></div><button class="btn" onclick="save()">保存模板</button></div><div class="grid" id="grid"></div></div><script>async function load(){const res=await fetch('/api/templates');const d=await res.json();document.getElementById('grid').innerHTML=d.templates.length?d.templates.map(t=>`<div class="card"><h3>${t.name}</h3><p>${t.description||t.requirement.substring(0,100)}...</p><div class="meta">项目：${t.project} · ${new Date(t.created_at).toLocaleString('zh-CN')}</div><div style="margin-top:15px;"><button class="btn" onclick="use('${t.requirement.replace(/'/g,"\\'")}')">使用</button> <button class="btn" style="background:#f44336;margin-left:10px;" onclick="del('${t.id}')">删除</button></div></div>`).join(''):'<p style="color:#999;text-align:center;grid-column:1/-1;">暂无模板</p>';}async function save(){await fetch('/api/template/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('name').value,description:document.getElementById('desc').value,requirement:document.getElementById('req').value,project:document.getElementById('project').value})});alert('✅ 已保存');load();}async function del(id){if(!confirm('确定删除？'))return;await fetch('/api/template/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});alert('✅ 已删除');load();}function use(req){localStorage.setItem('template_req',req);window.location.href='/';}async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}load();</script></body></html>"""
    
    def _costs_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>成本统计 - Agent 集群</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.card h3{color:#666;font-size:14px;margin-bottom:10px}.card .value{font-size:28px;font-weight:bold;color:#333}.card .sub{font-size:12px;color:#999;margin-top:5px}.content{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}table{width:100%;border-collapse:collapse;margin-top:20px}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#f8f9fa;color:#666;font-weight:500}</style></head><body><div class="header"><h1>💰 成本统计</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div><div class="container"><div class="cards"><div class="card"><h3>今日成本</h3><div class="value" id="today">¥0.00</div><div class="sub" id="todayWf">0 个工作流</div></div><div class="card"><h3>本周成本</h3><div class="value" id="week">¥0.00</div><div class="sub" id="weekWf">0 个工作流</div></div><div class="card"><h3>本月成本</h3><div class="value" id="month">¥0.00</div><div class="sub" id="monthWf">0 个工作流</div></div><div class="card"><h3>平均单次</h3><div class="value" id="avg">¥0.00</div><div class="sub">每工作流平均</div></div></div><div class="content"><h2>按模型统计</h2><table><thead><tr><th>模型</th><th>调用次数</th><th>Token 消耗</th><th>成本</th></tr></thead><tbody id="modelBody"><tr><td colspan="4" style="text-align:center;color:#999;">暂无数据</td></tr></tbody></table></div></div><script>async function load(){const res=await fetch('/api/costs');const d=await res.json();document.getElementById('today').textContent='¥'+(d.today?.total||0).toFixed(2);document.getElementById('todayWf').textContent=(d.today?.workflows||0)+' 个工作流';document.getElementById('week').textContent='¥'+(d.week?.total||0).toFixed(2);document.getElementById('weekWf').textContent=(d.week?.workflows||0)+' 个工作流';document.getElementById('month').textContent='¥'+(d.month?.total||0).toFixed(2);document.getElementById('monthWf').textContent=(d.month?.workflows||0)+' 个工作流';const avg=d.today?.workflows>0?d.today.total/d.today.workflows:0;document.getElementById('avg').textContent='¥'+avg.toFixed(2);const tbody=document.getElementById('modelBody');const models=d.by_model||{};tbody.innerHTML=Object.keys(models).length?Object.entries(models).map(([m,s])=>`<tr><td>${m}</td><td>${s.calls||0}</td><td>${s.tokens||0}</td><td>¥${(s.cost||0).toFixed(2)}</td></tr>`).join(''):'<tr><td colspan="4" style="text-align:center;color:#999;">暂无数据</td></tr>';}async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}load();</script></body></html>"""
    
    def get_deployments_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>发布管理 - Agent 集群 V2.1</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.section{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.section h2{margin-bottom:20px;color:#333}.info-box{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:15px;margin-bottom:20px}.info-box p{color:#0369a1;font-size:14px}.deploy-form{background:#f8f9fa;border-radius:8px;padding:20px;margin-bottom:20px}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#555;font-weight:500}.form-group input,.form-group select{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px}.btn{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:14px}.btn:hover{transform:translateY(-2px)}.btn-danger{background:#f44336}.table-container{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#f8f9fa;color:#666;font-weight:500}.status-badge{padding:4px 12px;border-radius:20px;font-size:12px}.status-badge.completed{background:#d1fae5;color:#065f46}.status-badge.running{background:#dbeafe;color:#1e40af}.status-badge.failed{background:#fee2e2;color:#991b1b}.status-badge.pending{background:#fef3c7;color:#92400e}</style></head><body>
<div class="header"><h1>🚀 发布管理</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments" style="background:rgba(255,255,255,0.2);">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div>
<div class="container">
<div class="section"><h2>📋 部署工作流</h2><div class="info-box"><p>💡 选择已完成的工作流进行部署。部署前需要钉钉确认，确认后自动执行。</p></div>
<div class="deploy-form"><div class="form-group"><label>选择工作流</label><select id="workflowSelect"><option value="">-- 请选择 --</option></select></div>
<div class="form-group"><label>部署环境</label><select id="environment"><option value="production">🔴 生产环境</option><option value="staging">🟡 预发布环境</option></select></div>
<button class="btn" onclick="executeDeploy()">🚀 执行部署</button></div>
<div class="table-container"><table><thead><tr><th>部署 ID</th><th>工作流</th><th>环境</th><th>状态</th><th>开始时间</th><th>操作</th></tr></thead><tbody id="deployTable"><tr><td colspan="6" style="text-align:center;color:#999;">加载中...</td></tr></tbody></table></div></div></div>
<script>async function loadWorkflows(){try{const res=await fetch('/api/workflows');const d=await res.json();const select=document.getElementById('workflowSelect');const completed=d.workflows.filter(w=>w.status==='completed');select.innerHTML='<option value="">-- 请选择 --</option>'+completed.map(w=>`<option value="${w.workflow_id}">${(w.requirement||'未命名').substring(0,50)}...</option>`).join('');}catch(e){console.error(e);}}
async function loadDeployments(){try{const tbody=document.getElementById('deployTable');tbody.innerHTML='<tr><td colspan="6" style="text-align:center;color:#999;">暂无部署记录</td></tr>';}catch(e){console.error(e);}}
async function executeDeploy(){const wfId=document.getElementById('workflowSelect').value;const env=document.getElementById('environment').value;if(!wfId){alert('请选择工作流');return;}if(!confirm('确定要部署吗？\\n\\n工作流 ID: '+wfId+'\\n环境：'+env+'\\n\\n部署前需要钉钉确认！'))return;try{const res=await fetch('/api/deploy/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow_id:wfId,environment:env})});const d=await res.json();if(d.success){alert('✅ '+d.message);}else{alert('❌ '+d.error);}}catch(e){alert('部署失败：'+e.message);}}
async function stopDeploy(id){if(!confirm('确定停止部署？'))return;try{const res=await fetch('/api/deploy/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({deployment_id:id})});const d=await res.json();if(d.success){alert('✅ 已停止');loadDeployments();}else{alert('❌ '+d.error);}}catch(e){alert('操作失败：'+e.message);}}
async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}
loadWorkflows();loadDeployments();</script></body></html>"""

    def get_bugs_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>Bug 管理 - Agent 集群 V2.1</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.grid{display:grid;grid-template-columns:1fr 2fr;gap:30px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.card h2{margin-bottom:20px;color:#333}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#555;font-weight:500}.form-group input,.form-group textarea,.form-group select{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;font-family:inherit}.form-group textarea{min-height:120px;resize:vertical}.btn{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:14px}.btn:hover{transform:translateY(-2px)}.btn-danger{background:#f44336}.table-container{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#f8f9fa;color:#666;font-weight:500;font-size:14px}.status-badge{padding:4px 10px;border-radius:20px;font-size:12px}.status-badge.new{background:#dbeafe;color:#1e40af}.status-badge.fixing{background:#fef3c7;color:#92400e}.status-badge.fixed{background:#d1fae5;color:#065f46}.priority-badge{padding:4px 8px;border-radius:4px;font-size:11px}.priority-high{background:#fee2e2;color:#991b1b}.priority-medium{background:#fef3c7;color:#92400e}.priority-low{background:#e0e7ff;color:#4f46e5}.info-box{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:15px;margin-bottom:20px}.info-box p{color:#0369a1;font-size:14px}</style></head><body>
<div class="header"><h1>🐛 Bug 管理</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs" style="background:rgba(255,255,255,0.2);">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div>
<div class="container"><div class="grid"><div class="card"><h2>📝 提交 Bug</h2><div class="info-box"><p>💡 提交 Bug 后，Agent 集群将自动启动完整修复流程：分析→修复→测试→审查→PR</p></div>
<form id="bugForm"><div class="form-group"><label>Bug 标题</label><input type="text" id="title" placeholder="简短描述 Bug" required></div>
<div class="form-group"><label>优先级</label><select id="priority"><option value="high">🔴 高 - 严重影响功能</option><option value="medium" selected>🟡 中 - 部分影响</option><option value="low">🟢 低 - 轻微问题</option></select></div>
<div class="form-group"><label>Bug 描述</label><textarea id="description" placeholder="详细描述 Bug 现象、复现步骤、预期行为..." required></textarea></div>
<div class="form-group"><label>相关文件/路径</label><input type="text" id="files" placeholder="例如：src/api/user.py, tests/test_user.py"></div>
<div class="form-group"><label>关联项目</label><select id="project"><option value="default">默认项目</option><option value="ecommerce">电商项目</option><option value="blog">博客系统</option><option value="crm">CRM 系统</option></select></div>
<button type="submit" class="btn">🚀 提交并启动修复流程</button></form></div>
<div class="card"><h2>📊 Bug 统计</h2><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-top:20px"><div style="background:#dbeafe;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#1e40af" id="newCount">0</div><div style="color:#666;font-size:13px">待处理</div></div><div style="background:#fef3c7;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#92400e" id="fixingCount">0</div><div style="color:#666;font-size:13px">修复中</div></div><div style="background:#d1fae5;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#065f46" id="fixedCount">0</div><div style="color:#666;font-size:13px">已修复</div></div><div style="background:#f3e8ff;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#7e22ce" id="totalToday">0</div><div style="color:#666;font-size:13px">今日提交</div></div></div></div></div>
<div class="card"><h2>📋 Bug 列表</h2><div class="table-container"><table><thead><tr><th>ID</th><th>标题</th><th>优先级</th><th>状态</th><th>项目</th><th>提交时间</th><th>操作</th></tr></thead><tbody id="bugTable"><tr><td colspan="7" style="text-align:center;color:#999;">加载中...</td></tr></tbody></table></div></div></div></div>
<script>async function loadBugs(){try{const res=await fetch('/api/bugs');const d=await res.json();const tbody=document.getElementById('bugTable');if(!d.bugs||d.bugs.length===0){tbody.innerHTML='<tr><td colspan="7" style="text-align:center;color:#999;">暂无 Bug 记录</td></tr>';return;}tbody.innerHTML=d.bugs.map(b=>`<tr><td>#${b.id||'-'}</td><td>${b.title||'未命名'}</td><td><span class="priority-badge priority-${b.priority||'medium'}">${b.priority==='high'?'🔴 高':b.priority==='medium'?'🟡 中':'🟢 低'}</span></td><td><span class="status-badge ${b.status||'new'}">${b.status==='new'?'🆕 待处理':b.status==='fixing'?'🔧 修复中':'✅ 已修复'}</span></td><td>${b.project||'-'}</td><td>${new Date(b.created_at).toLocaleString('zh-CN')}</td><td><button class="btn" style="padding:6px 12px;font-size:12px;" onclick="viewBug('${b.id}')">查看</button></td></tr>`).join('');const stats={new:d.bugs.filter(b=>b.status==='new').length,fixing:d.bugs.filter(b=>b.status==='fixing').length,fixed:d.bugs.filter(b=>b.status==='fixed').length,today:d.bugs.filter(b=>new Date(b.created_at).toDateString()===new Date().toDateString()).length};document.getElementById('newCount').textContent=stats.new;document.getElementById('fixingCount').textContent=stats.fixing;document.getElementById('fixedCount').textContent=stats.fixed;document.getElementById('totalToday').textContent=stats.today;}catch(e){console.error('加载失败:',e);}}
document.getElementById('bugForm').addEventListener('submit',async function(e){e.preventDefault();const title=document.getElementById('title').value;const priority=document.getElementById('priority').value;const description=document.getElementById('description').value;const files=document.getElementById('files').value;const project=document.getElementById('project').value;if(!title||!description){alert('请填写标题和描述');return;}if(!confirm('确定提交 Bug 并启动自动修复流程吗？\\n\\nAgent 集群将执行：\\n1️⃣ 分析 Bug 原因\\n2️⃣ 修复代码\\n3️⃣ 运行测试\\n4️⃣ 代码审查\\n5️⃣ 创建 PR'))return;try{const res=await fetch('/api/bugs/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,priority,description,files,project})});const d=await res.json();if(d.success){alert('✅ '+d.message+'\\n\\n工作流 ID: '+(d.workflow_id||'-'));document.getElementById('title').value='';document.getElementById('description').value='';document.getElementById('files').value='';loadBugs();}else{alert('❌ '+d.error);}}catch(e){alert('提交失败：'+e.message);}});
function viewBug(id){alert('查看 Bug #'+id+'\\n\\n此功能可展示 Bug 详情、修复进度、相关 PR 链接等');}
async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}
loadBugs();setInterval(loadBugs,30000);</script></body></html>"""

    def execute_deploy(self, data):
        """执行部署"""
        try:
            from utils.deploy_executor import deploy_executor
            
            workflow_id = data.get('workflow_id', '')
            project = data.get('project', 'default')
            code_path = data.get('code_path', '')
            
            if not workflow_id:
                return {'success': False, 'error': '工作流 ID 不能为空'}
            
            result = deploy_executor.deploy(workflow_id, project, code_path)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_deploy(self, data):
        """停止部署"""
        try:
            from utils.deploy_executor import deploy_executor
            
            deployment_id = data.get('deployment_id', '')
            if not deployment_id:
                return {'success': False, 'error': '部署 ID 不能为空'}
            
            result = deploy_executor.stop(deployment_id)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_deploy_status(self, data):
        """获取部署状态"""
        try:
            from utils.deploy_executor import deploy_executor
            
            deployment_id = data.get('deployment_id', '')
            if not deployment_id:
                return {'success': False, 'error': '部署 ID 不能为空'}
            
            result = deploy_executor.get_deployment_status(deployment_id)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def submit_bug(self, data):
        """提交 Bug 并触发修复流程"""
        title = data.get("title", "")
        priority = data.get("priority", "medium")
        description = data.get("description", "")
        files = data.get("files", "")
        project = data.get("project", "default")
        
        if not title or not description:
            return {"success": False, "error": "标题和描述不能为空"}
        
        # 生成 Bug ID
        import random
        bug_id = f"BUG{random.randint(1000, 9999)}"
        
        # 保存 Bug 记录
        bugs_file = MEMORY_DIR / "bugs.json"
        bugs = []
        if bugs_file.exists():
            try:
                with open(bugs_file, 'r', encoding='utf-8') as f:
                    bugs = json.load(f)
            except:
                pass
        
        bug_record = {
            "id": bug_id,
            "title": title,
            "priority": priority,
            "description": description,
            "files": files,
            "project": project,
            "status": "new",
            "created_at": datetime.now().isoformat(),
            "workflow_id": None,
            "pr_url": None
        }
        bugs.append(bug_record)
        
        with open(bugs_file, 'w', encoding='utf-8') as f:
            json.dump(bugs, f, ensure_ascii=False, indent=2)
        
        # 构建修复需求
        requirement = f"""🐛 Bug 修复任务

**Bug ID**: {bug_id}
**标题**: {title}
**优先级**: {priority}

**问题描述**:
{description}

**相关文件**: {files if files else '待分析'}

**修复要求**:
1. 分析 Bug 根本原因
2. 修复相关代码
3. 编写/更新单元测试
4. 确保测试覆盖率 > 80%
5. 通过所有质量门禁
6. 创建 Pull Request

**完整流程**:
Phase 1: 分析 Bug 原因
Phase 2: 设计修复方案
Phase 3: 实现修复代码
Phase 4: 测试验证
Phase 5: 代码审查
Phase 6: 部署并创建 PR
"""
        
        # 触发修复工作流
        try:
            cmd = f"cd {BASE_DIR} && python3 orchestrator.py \"{requirement}\""
            subprocess.Popen(cmd, shell=True, stdout=open(LOGS_DIR / f"bug_{bug_id}.log", 'a'), stderr=subprocess.STDOUT)
            
            # 更新 Bug 状态
            bug_record["status"] = "fixing"
            bug_record["workflow_id"] = f"wf_{bug_id}"
            
            with open(bugs_file, 'w', encoding='utf-8') as f:
                json.dump(bugs, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "Bug 已提交，Agent 集群正在修复中",
                "bug_id": bug_id,
                "workflow_id": bug_record["workflow_id"]
            }
        except Exception as e:
            return {"success": False, "error": f"提交成功但启动修复失败：{str(e)}"}
    
    def get_bugs(self):
        """获取 Bug 列表"""
        bugs_file = MEMORY_DIR / "bugs.json"
        if bugs_file.exists():
            try:
                with open(bugs_file, 'r', encoding='utf-8') as f:
                    bugs = json.load(f)
                bugs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return {"bugs": bugs[-50:]}
            except:
                pass
        return {"bugs": []}
    
    # ========== 指标 API 方法 ==========
    
    def get_metrics_summary(self):
        """获取指标汇总"""
        try:
            collector = get_metrics_collector()
            stats = collector.get_summary()
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_metrics_agents(self):
        """获取 Agent 统计"""
        try:
            collector = get_metrics_collector()
            stats = collector.get_agent_stats()
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_metrics_tasks(self):
        """获取任务历史"""
        try:
            collector = get_metrics_collector()
            tasks = collector.get_task_history(limit=50)
            return {"success": True, "data": tasks}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_metrics_failures(self):
        """获取失败分析"""
        try:
            collector = get_metrics_collector()
            analysis = collector.get_failure_analysis()
            return {"success": True, "data": analysis}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_metrics_report(self):
        """获取完整报告"""
        try:
            collector = get_metrics_collector()
            report = collector.export_report()
            return {"success": True, "data": report}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _settings_page(self):
        """设置页面"""
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>设置 - Agent 集群</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:800px;margin:0 auto;padding:30px}.card{background:white;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.card h2{margin-bottom:20px}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#555}.form-group input{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px}.btn{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer}.info{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:15px;margin-bottom:20px}.info p{color:#0369a1;font-size:14px}</style></head><body>
<div class="header"><h1>⚙️ 设置</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug 管理</a><a href="/deployments">🚀 发布管理</a><a href="/templates">📝 模板库</a><a href="/costs">💰 成本统计</a><a href="/monitoring">📈 监控日志</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div>
<div class="container">
<div class="info"><p>ℹ️ 修改密码后，所有会话将失效，需要重新登录</p></div>
<div class="card"><h2>🔐 修改密码</h2><div class="form-group"><label>原密码</label><input type="password" id="oldPwd" placeholder="请输入原密码"></div><div class="form-group"><label>新密码</label><input type="password" id="newPwd" placeholder="请输入新密码（至少 6 位）"></div><div class="form-group"><label>确认新密码</label><input type="password" id="confirmPwd" placeholder="请再次输入新密码"></div><button class="btn" onclick="changePwd()">修改密码</button></div>
<div class="card"><h2>ℹ️ 系统信息</h2><div class="form-group"><label>版本</label><input type="text" value="V2.7.1" readonly></div><div class="form-group"><label>工作目录</label><input type="text" value="/home/admin/.openclaw/workspace/agent-cluster" readonly></div><div class="form-group"><label>后端端口</label><input type="text" value="8890" readonly></div></div></div>
<script>async function changePwd(){const old=document.getElementById('oldPwd').value;const new1=document.getElementById('newPwd').value;const new2=document.getElementById('confirmPwd').value;if(!old||!new1||!new2){alert('请填写所有字段');return;}if(new1!==new2){alert('两次输入的新密码不一致');return;}if(new1.length<6){alert('密码长度至少 6 位');return;}try{const res=await fetch('/api/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:old,new_password:new1})});const d=await res.json();if(d.success){alert('✅ '+d.message);document.getElementById('oldPwd').value='';document.getElementById('newPwd').value='';document.getElementById('confirmPwd').value='';setTimeout(()=>{window.location.href='/login';},1500);}else{alert('❌ '+d.error);}}catch(e){alert('请求失败：'+e.message);}}async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}</script></body></html>"""
    
    def get_metrics_dashboard(self):
        """指标 Dashboard 页面"""
        template_path = BASE_DIR / "templates" / "metrics_dashboard.html"
        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                pass
        # 如果模板文件不存在，返回简单版本
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>指标 Dashboard - Agent 集群</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.section{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.section h2{margin-bottom:20px;color:#333}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:20px}.stat-card{background:white;border-radius:12px;padding:24px;box-shadow:0 4px 6px rgba(0,0,0,0.1)}.stat-card h3{color:#718096;font-size:14px;text-transform:uppercase;margin-bottom:12px}.stat-card .value{color:#1a202c;font-size:36px;font-weight:bold;margin-bottom:8px}.loading{text-align:center;padding:40px;color:#718096}</style></head><body>
<div class="header"><h1>📊 指标 Dashboard</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug</a><a href="/deployments">🚀 发布</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/metrics" style="background:rgba(255,255,255,0.2);">📈 指标</a><a href="/monitoring">📋 监控</a><a href="/settings">⚙️ 设置</a><a href="#" onclick="logout()" style="margin-left:auto;">🚪 登出</a></div></div>
<div class="container">
<div class="section"><h2>📊 核心指标</h2><div class="stats-grid" id="statsGrid"><div class="loading">加载中...</div></div></div>
<div class="section"><h2>🤖 Agent 统计</h2><div id="agentsGrid"><div class="loading">加载中...</div></div></div>
</div>
<script>async function loadMetrics(){try{const res=await fetch('/api/metrics/summary');const d=await res.json();if(d.success){const s=d.data;document.getElementById('statsGrid').innerHTML=`<div class="stat-card"><h3>总任务数</h3><div class="value">${s.total_tasks||0}</div></div><div class="stat-card"><h3>完成数</h3><div class="value">${s.completed_tasks||0}</div></div><div class="stat-card"><h3>失败数</h3><div class="value">${s.failed_tasks||0}</div></div><div class="stat-card"><h3>总成本</h3><div class="value">¥${(s.total_cost||0).toFixed(2)}</div></div><div class="stat-card"><h3>CI 通过率</h3><div class="value">${((s.ci_pass_rate||0)*100).toFixed(1)}%</div></div><div class="stat-card"><h3>平均耗时</h3><div class="value">${Math.round(s.avg_duration_seconds||0)}秒</div></div>`;}const res2=await fetch('/api/metrics/agents');const d2=await res2.json();if(d2.success){const agents=d2.data;let html='';for(let k in agents){const a=agents[k];html+=`<div class="stat-card" style="margin-bottom:10px;"><h3>${a.agent_name||k}</h3><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;"><div>分配：<strong>${a.tasks_assigned||0}</strong></div><div>完成：<strong style="color:#22543d">${a.tasks_completed||0}</strong></div><div>失败：<strong style="color:#742a2a">${a.tasks_failed||0}</strong></div><div>成功率：<strong>${((a.success_rate||0)*100).toFixed(1)}%</strong></div></div></div>`;}document.getElementById('agentsGrid').innerHTML=html||'<div class="loading">暂无数据</div>';}}catch(e){console.error('加载失败:',e);document.getElementById('statsGrid').innerHTML='<div class="loading">加载失败：'+e.message+'</div>';}}
function logout(){if(!confirm('确定登出？'))return;fetch('/api/logout',{method:'POST'}).then(()=>{window.location.href='/login';});}
loadMetrics();setInterval(loadMetrics,30000);</script></body></html>"""
    
    def get_monitoring_page(self):
        """监控日志页面"""
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>监控日志 - Agent 集群</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.section{background:white;border-radius:12px;padding:24px;margin-bottom:30px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.section h2{margin-bottom:20px;color:#333}.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px}.card{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:12px;padding:24px;box-shadow:0 4px 12px rgba(102,126,234,0.3);transition:transform 0.2s}.card:hover{transform:translateY(-4px)}.card h3{font-size:16px;margin-bottom:10px;opacity:0.9}.card .url{font-size:14px;background:rgba(255,255,255,0.2);padding:8px;border-radius:6px;margin-bottom:15px;word-break:break-all}.card .btn{display:inline-block;background:white;color:#667eea;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:500}.card .btn:hover{background:#f0f0f0}.status{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;margin-left:10px}.status.ok{background:#d1fae5;color:#065f46}.status.error{background:#fee2e2;color:#991b1b}.info-box{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:15px;margin-bottom:20px}.info-box p{color:#0369a1;font-size:14px}</style></head><body>
<div class="header"><h1>📈 监控与日志</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs">🐛 Bug</a><a href="/deployments">🚀 发布</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/metrics">📈 指标</a><a href="/monitoring" style="background:rgba(255,255,255,0.2);">📋 监控日志</a><a href="/settings">⚙️ 设置</a><a href="#" onclick="logout()" style="margin-left:auto;">🚪 登出</a></div></div>
<div class="container">
<div class="section"><h2>🔗 快速访问</h2><div class="info-box"><p>💡 点击下方卡片快速访问监控和日志系统</p></div>
<div class="card-grid">
<div class="card"><h3>📊 Prometheus 监控</h3><div class="url">http://localhost:9090</div><a href="http://localhost:9090" target="_blank" class="btn">访问 →</a><span class="status ok" id="prometheusStatus">检查中...</span></div>
<div class="card"><h3>📈 Grafana 仪表板</h3><div class="url">http://localhost:3000</div><a href="http://localhost:3000" target="_blank" class="btn">访问 →</a><span class="status ok" id="grafanaStatus">检查中...</span></div>
<div class="card"><h3>🔍 Kibana 日志</h3><div class="url">http://localhost:5601</div><a href="http://localhost:5601" target="_blank" class="btn">访问 →</a><span class="status ok" id="kibanaStatus">检查中...</span></div>
<div class="card"><h3>🚨 Alertmanager</h3><div class="url">http://localhost:9093</div><a href="http://localhost:9093" target="_blank" class="btn">访问 →</a><span class="status ok" id="alertmanagerStatus">检查中...</span></div>
</div></div>
<div class="section"><h2>📋 服务状态</h2><div class="info-box"><p>ℹ️ 实时检查各监控服务运行状态</p></div>
<table style="width:100%;border-collapse:collapse"><thead><tr><th style="padding:12px;text-align:left;border-bottom:1px solid #eee">服务</th><th style="padding:12px;text-align:left;border-bottom:1px solid #eee">端口</th><th style="padding:12px;text-align:left;border-bottom:1px solid #eee">状态</th><th style="padding:12px;text-align:left;border-bottom:1px solid #eee">操作</th></tr></thead><tbody id="serviceTable"><tr><td style="padding:12px">Prometheus</td><td style="padding:12px">9090</td><td style="padding:12px"><span class="status ok" id="p9090">检查中...</span></td><td style="padding:12px"><button onclick="checkService(9090)">检查</button></td></tr><tr><td style="padding:12px">Grafana</td><td style="padding:12px">3000</td><td style="padding:12px"><span class="status ok" id="g3000">检查中...</span></td><td style="padding:12px"><button onclick="checkService(3000)">检查</button></td></tr><tr><td style="padding:12px">Elasticsearch</td><td style="padding:12px">9200</td><td style="padding:12px"><span class="status ok" id="e9200">检查中...</span></td><td style="padding:12px"><button onclick="checkService(9200)">检查</button></td></tr><tr><td style="padding:12px">Kibana</td><td style="padding:12px">5601</td><td style="padding:12px"><span class="status ok" id="k5601">检查中...</span></td><td style="padding:12px"><button onclick="checkService(5601)">检查</button></td></tr><tr><td style="padding:12px">Alertmanager</td><td style="padding:12px">9093</td><td style="padding:12px"><span class="status ok" id="a9093">检查中...</span></td><td style="padding:12px"><button onclick="checkService(9093)">检查</button></td></tr></tbody></table></div>
<div class="section"><h2>📖 使用指南</h2><div class="info-box"><p>📄 详细文档：<a href="/API_DOCUMENTATION.md" target="_blank">API_DOCUMENTATION.md</a></p></div>
<div style="line-height:1.8;color:#666">
<h3 style="margin:15px 0 10px;color:#333">🔍 日志查询（Kibana）</h3>
<ol style="margin-left:20px"><li>访问 Kibana: http://localhost:5601</li><li>创建索引模式：agent-cluster-logs-*</li><li>时间字段选择：@timestamp</li><li>在 Discover 中查看日志</li></ol>
<h3 style="margin:15px 0 10px;color:#333">📊 监控指标（Prometheus）</h3>
<ol style="margin-left:20px"><li>访问 Prometheus: http://localhost:9090</li><li>在 Graph 中查询指标</li><li>常用查询：up{job="agent-cluster"}</li></ol>
<h3 style="margin:15px 0 10px;color:#333">📈 仪表板（Grafana）</h3>
<ol style="margin-left:20px"><li>访问 Grafana: http://localhost:3000</li><li>登录：admin / admin123</li><li>导入 dashboard: monitoring/grafana_dashboard.json</li></ol>
</div></div></div>
<script>async function checkService(port){const statusEl=document.getElementById(port===9090?'p9090':port===3000?'g3000':port===9200?'e9200':port===5601?'k5601':'a9093');try{const res=await fetch(`http://localhost:${port}`, {method:'HEAD',mode:'no-cors'});statusEl.textContent='运行中';statusEl.className='status ok';}catch(e){statusEl.textContent='未运行';statusEl.className='status error';}}function checkAllServices(){[9090,3000,9200,5601,9093].forEach(checkService);}function logout(){if(!confirm('确定登出？'))return;fetch('/api/logout',{method:'POST'}).then(()=>{window.location.href='/login';});}window.onload=checkAllServices;</script></body></html>"""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8890)
    args = parser.parse_args()
    server = HTTPServer((args.host, args.port), WebUIHandler)
    logger.info(f"🌐 Agent 集群 Web V2.3.0 已启动！")
    logger.info(f"   本地访问：http://localhost:{args.port}")
    logger.info(f"   外网访问：http://39.107.101.25")
    logger.info(f"   默认账号：admin / admin123")
    logger.info("=" * 50)
    server.serve_forever()
