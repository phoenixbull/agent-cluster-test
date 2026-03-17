#!/usr/bin/env python3
"""
钉钉 Webhook 接收器
接收钉钉群消息，触发 Agent 集群工作流
"""

import json
import hmac
import hashlib
import base64
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
import threading

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator


class DingTalkWebhookHandler(BaseHTTPRequestHandler):
    """钉钉 Webhook 请求处理器"""
    
    orchestrator = Orchestrator()
    
    def do_POST(self):
        """处理 POST 请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # 验证签名 (如果配置了加签密钥)
            if not self._verify_signature(data):
                self._send_response({"errcode": 401, "errmsg": "签名验证失败"})
                return
            
            # 解析消息
            message = self._parse_message(data)
            
            if message:
                # 异步处理工作流
                thread = threading.Thread(
                    target=self._process_requirement,
                    args=(message,)
                )
                thread.start()
                
                # 立即回复确认
                self._send_response({
                    "msgtype": "text",
                    "text": {
                        "content": "✅ 需求已接收，工作流已启动\n预计完成时间：60-90 分钟\n完成后会收到通知。"
                    }
                })
            else:
                self._send_response({"errcode": 400, "errmsg": "无法解析消息"})
        
        except Exception as e:
            print(f"处理钉钉消息失败：{e}")
            self._send_response({"errcode": 500, "errmsg": str(e)})
    
    def _verify_signature(self, data: Dict) -> bool:
        """验证钉钉签名"""
        # TODO: 实现签名验证
        # 钉钉会发送 timestamp 和 sign 参数
        # 需要使用加签密钥验证
        return True
    
    def _parse_message(self, data: Dict) -> str:
        """解析钉钉消息"""
        msgtype = data.get('msgtype')
        
        if msgtype == 'text':
            return data.get('text', {}).get('content', '')
        
        elif msgtype == 'markdown':
            markdown_text = data.get('markdown', {}).get('text', '')
            # 提取纯文本（去除 Markdown 格式）
            return self._extract_text_from_markdown(markdown_text)
        
        return ''
    
    def _extract_text_from_markdown(self, markdown: str) -> str:
        """从 Markdown 提取纯文本"""
        # 简单的 Markdown 清理
        text = markdown
        text = text.replace('**', '')
        text = text.replace('__', '')
        text = text.replace('`', '')
        lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('#')]
        return ' '.join(lines)
    
    def _process_requirement(self, requirement: str):
        """处理产品需求"""
        print(f"\n📥 钉钉需求：{requirement[:100]}...")
        
        try:
            workflow_id = self.orchestrator.receive_requirement(requirement, source="dingtalk")
            print(f"✅ 工作流已启动：{workflow_id}")
        except Exception as e:
            print(f"❌ 工作流执行失败：{e}")
    
    def _send_response(self, data: Dict):
        """发送响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[Webhook] {args[0]}")


def run_webhook_server(port: int = 8888):
    """启动 Webhook 服务器"""
    server = HTTPServer(('0.0.0.0', port), DingTalkWebhookHandler)
    print(f"🚀 钉钉 Webhook 服务器已启动")
    print(f"   监听端口：{port}")
    print(f"   Webhook URL: http://<your-server-ip>:{port}/dingtalk")
    print(f"\n在钉钉机器人配置中设置:")
    print(f"   HTTP POST 地址：http://<your-server-ip>:{port}/dingtalk")
    print(f"\n按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务器...")
        server.shutdown()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='钉钉 Webhook 接收器')
    parser.add_argument('--port', type=int, default=8888, help='监听端口 (默认：8888)')
    args = parser.parse_args()
    
    run_webhook_server(args.port)


if __name__ == "__main__":
    main()
