#!/usr/bin/env python3
"""
钉钉消息接收模块
通过 HTTP 回调接收钉钉消息，触发部署确认等交互

注意：需要使用钉钉企业自建应用，而非群机器人 webhook
文档：https://open.dingtalk.com/document/orgapp/receive-callbacks
"""

import json
import hmac
import hashlib
import base64
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from typing import Dict, List, Optional, Callable, Any
import threading
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from deploy_listener import on_dingtalk_message


class DingTalkMessageHandler(BaseHTTPRequestHandler):
    """钉钉消息回调处理器"""
    
    # 回调验证 token（需要在钉钉开放平台配置）
    CALLBACK_TOKEN = "your_callback_token_here"
    
    # 消息处理回调
    message_callbacks: List[Callable[[str, str], None]] = []
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().isoformat()}] {args[0]}")
    
    def do_GET(self):
        """处理 GET 请求（钉钉回调验证）"""
        if self.path.startswith('/dingtalk/callback'):
            # 解析查询参数
            params = parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
            
            signature = params.get('signature', [''])[0]
            timestamp = params.get('timestamp', [''])[0]
            nonce = params.get('nonce', [''])[0]
            
            # 验证签名
            if self._verify_signature(signature, timestamp, nonce):
                # 返回加密后的 echostr
                echostr = params.get('echostr', [''])[0]
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                # 简单场景直接返回 echostr（生产环境需要加密）
                self.wfile.write(echostr.encode())
                print("✅ 钉钉回调验证成功")
            else:
                self.send_response(403)
                self.end_headers()
                print("❌ 钉钉回调验证失败")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求（接收钉钉消息）"""
        if self.path.startswith('/dingtalk/callback'):
            try:
                # 读取请求体
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                
                # 验证签名
                signature = self.headers.get('x-ding-signature', '')
                timestamp = self.headers.get('x-ding-timestamp', '')
                nonce = self.headers.get('x-ding-nonce', '')
                
                if not self._verify_signature(signature, timestamp, nonce):
                    self.send_response(403)
                    self.end_headers()
                    print("❌ 消息签名验证失败")
                    return
                
                # 解析消息
                message = self._parse_message(data)
                if message:
                    print(f"📱 收到钉钉消息：{message['content']} (from {message['user']})")
                    
                    # 触发消息处理回调
                    for callback in self.message_callbacks:
                        try:
                            callback(message['content'], message['user'])
                        except Exception as e:
                            print(f"⚠️ 回调处理失败：{e}")
                    
                    # 返回成功响应
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
                    
            except Exception as e:
                print(f"❌ 处理消息失败：{e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _verify_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """验证钉钉签名"""
        # 简化验证（生产环境需要完整实现）
        if not signature:
            return True  # 开发环境跳过验证
        
        # 计算签名
        sign_str = f"{timestamp}\n{nonce}\n{self.CALLBACK_TOKEN}"
        expected = hmac.new(
            self.CALLBACK_TOKEN.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature == expected
    
    def _parse_message(self, data: Dict) -> Optional[Dict]:
        """解析钉钉消息"""
        try:
            # 钉钉回调消息格式
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
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
        except Exception as e:
            print(f"⚠️ 解析消息失败：{e}")
            return None


class DingTalkReceiver:
    """
    钉钉消息接收器
    
    功能:
    - 启动 HTTP 服务器接收钉钉回调
    - 注册消息处理回调
    - 转发消息到部署监听器
    """
    
    def __init__(self, port: int = 8891, token: str = None):
        """
        初始化接收器
        
        Args:
            port: HTTP 服务器端口
            token: 钉钉回调验证 token
        """
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        
        if token:
            DingTalkMessageHandler.CALLBACK_TOKEN = token
        
        # 注册部署监听器回调
        DingTalkMessageHandler.message_callbacks.append(on_dingtalk_message)
        
        print(f"✅ 钉钉消息接收器已初始化 (端口：{port})")
    
    def start(self, blocking: bool = False):
        """
        启动接收器
        
        Args:
            blocking: 是否阻塞运行
        """
        self.server = HTTPServer(('0.0.0.0', self.port), DingTalkMessageHandler)
        
        print(f"\n📱 钉钉消息接收器已启动")
        print(f"   监听端口：{self.port}")
        print(f"   回调 URL: http://服务器 IP:{self.port}/dingtalk/callback")
        print(f"   消息处理：已注册 deploy_listener.on_dingtalk_message()")
        print(f"\n⚠️  需要在钉钉开放平台配置回调地址:")
        print(f"   http://服务器 IP:{self.port}/dingtalk/callback\n")
        
        if blocking:
            self.server.serve_forever()
        else:
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """停止接收器"""
        if self.server:
            self.server.shutdown()
            print("⏹️  钉钉消息接收器已停止")


# ========== 便捷函数 ==========

_receiver: Optional[DingTalkReceiver] = None


def get_receiver() -> DingTalkReceiver:
    """获取接收器实例"""
    global _receiver
    if _receiver is None:
        _receiver = DingTalkReceiver()
    return _receiver


def start_receiver(port: int = 8891, token: str = None, blocking: bool = False):
    """启动钉钉消息接收器"""
    receiver = get_receiver()
    if token:
        receiver = DingTalkReceiver(port, token)
        _receiver = receiver
    receiver.start(blocking)


def stop_receiver():
    """停止钉钉消息接收器"""
    receiver = get_receiver()
    receiver.stop()


# ========== 主程序 ==========

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='钉钉消息接收器')
    parser.add_argument('--port', type=int, default=8891, help='HTTP 端口 (默认：8891)')
    parser.add_argument('--token', type=str, help='钉钉回调验证 token')
    parser.add_argument('--blocking', action='store_true', help='阻塞运行')
    
    args = parser.parse_args()
    
    try:
        start_receiver(port=args.port, token=args.token, blocking=args.blocking)
        
        if not args.blocking:
            print("按 Ctrl+C 停止...")
            while True:
                import time
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n⏹️  接收器已停止")
    except Exception as e:
        print(f"❌ 启动失败：{e}")
        sys.exit(1)
