#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉告警通知脚本
接收 Alertmanager 的 Webhook 告警并发送到钉钉
"""

import json
import hmac
import hashlib
import base64
import time
import requests
import sys
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# 钉钉配置
DINGTALK_WEBHOOK = 'https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea'
DINGTALK_SECRET = 'SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e'


def generate_sign(timestamp, secret):
    """生成钉钉签名"""
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign


def send_dingtalk(message: dict, at_all: bool = False):
    """发送钉钉消息"""
    timestamp = str(round(time.time() * 1000))
    sign = generate_sign(timestamp, DINGTALK_SECRET)
    
    url = f'{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}'
    
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    
    data = {
        'msgtype': 'markdown',
        'markdown': {
            'title': message.get('title', '告警通知'),
            'text': message.get('text', '')
        },
        'at': {
            'isAtAll': at_all
        }
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=10)
    return response.json()


def format_alerts(alerts: list) -> dict:
    """格式化告警消息"""
    if not alerts:
        return None
    
    # 判断是否严重（有 critical 级别）
    at_all = any(alert.get('labels', {}).get('severity') == 'critical' for alert in alerts)
    
    # 构建消息
    status = alerts[0].get('status', 'unknown')
    status_emoji = '🔴' if status == 'firing' else '🟢'
    status_text = '告警触发' if status == 'firing' else '告警恢复'
    
    text = f"""## {status_emoji} {status_text}

**告警数量**: {len(alerts)}  
**触发时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    for i, alert in enumerate(alerts[:5], 1):  # 最多显示 5 条
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        text += f"""**{i}. {labels.get('alertname', 'Unknown')}**  
- **严重程度**: {labels.get('severity', 'unknown')}  
- **实例**: {labels.get('instance', 'unknown')}  
- **摘要**: {annotations.get('summary', '无')}  
- **描述**: {annotations.get('description', '无')}  

"""
    
    if len(alerts) > 5:
        text += f"\n... 还有 {len(alerts) - 5} 条告警\n"
    
    return {
        'title': f'{status_text} - Agent Cluster',
        'text': text
    }, at_all


@app.route('/alerts', methods=['POST'])
def receive_alerts():
    """接收 Alertmanager 告警"""
    try:
        data = request.json
        
        # 解析告警
        alerts = data.get('alerts', [])
        if not alerts:
            return jsonify({'status': 'error', 'message': 'No alerts'}), 400
        
        # 格式化消息
        message, at_all = format_alerts(alerts)
        if not message:
            return jsonify({'status': 'error', 'message': 'Invalid alerts'}), 400
        
        # 发送钉钉
        result = send_dingtalk(message, at_all)
        
        if result.get('errcode') == 0:
            return jsonify({'status': 'success', 'message': 'Alert sent'}), 200
        else:
            return jsonify({'status': 'error', 'message': result.get('errmsg')}), 500
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║         钉钉告警通知服务                                   ║
╠═══════════════════════════════════════════════════════════╣
║  监听端口：5001                                           ║
║  告警端点：POST /alerts                                   ║
║  健康检查：GET /health                                    ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
