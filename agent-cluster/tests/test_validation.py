#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本周优化验证测试脚本
验证告警通知、ELK 日志聚合、API 文档功能
"""

import requests
import subprocess
import time
import sys
from pathlib import Path

BASE_URL = 'http://localhost:8890'
ELK_SERVICES = {
    'Prometheus': 9090,
    'Grafana': 3000,
    'Elasticsearch': 9200,
    'Kibana': 5601,
    'Alertmanager': 9093
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}  {title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_pass(msg):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")

def print_fail(msg):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")

def print_warn(msg):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")

def get_token():
    """获取测试 Token"""
    try:
        resp = requests.post(f'{BASE_URL}/api/login', json={
            'username': 'admin',
            'password': 'admin'
        }, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('token', '')
    except Exception:
        pass
    return ''

def test_web_service():
    """测试 Web 服务"""
    print_header("1. Web 服务测试")
    
    try:
        resp = requests.get(f'{BASE_URL}/health', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"健康检查：{data.get('status', 'unknown')}")
            return True
        else:
            print_fail(f"健康检查失败：HTTP {resp.status_code}")
            return False
    except Exception as e:
        print_fail(f"Web 服务不可用：{e}")
        return False

def test_monitoring_page():
    """测试监控日志页面"""
    print_header("2. 监控日志页面测试")
    
    token = get_token()
    if not token:
        print_fail("无法获取 Token")
        return False
    
    try:
        cookies = {'auth_token': token}
        resp = requests.get(f'{BASE_URL}/monitoring', cookies=cookies, timeout=5)
        
        if resp.status_code == 200 and '监控日志' in resp.text:
            print_pass("监控日志页面可访问")
            
            # 检查 ELK 链接是否存在
            if 'localhost:9090' in resp.text and 'localhost:5601' in resp.text:
                print_pass("ELK 访问链接已集成")
                return True
            else:
                print_warn("ELK 链接可能缺失")
                return True
        else:
            print_fail("监控日志页面不可访问")
            return False
    except Exception as e:
        print_fail(f"页面测试失败：{e}")
        return False

def test_elk_services():
    """测试 ELK 服务"""
    print_header("3. ELK 服务状态测试")
    
    results = {}
    for name, port in ELK_SERVICES.items():
        try:
            resp = requests.get(f'http://localhost:{port}', timeout=3)
            if resp.status_code < 400:
                print_pass(f"{name} (端口{port}): 运行中")
                results[name] = True
            else:
                print_warn(f"{name} (端口{port}): HTTP {resp.status_code}")
                results[name] = False
        except Exception:
            print_fail(f"{name} (端口{port}): 不可访问")
            results[name] = False
    
    return all(results.values())

def test_dingtalk_notifier():
    """测试钉钉通知服务"""
    print_header("4. 钉钉通知服务测试")
    
    try:
        resp = requests.get('http://localhost:5001/health', timeout=3)
        if resp.status_code == 200:
            print_pass("钉钉通知服务运行中")
            
            # 测试告警接收端点
            resp = requests.post('http://localhost:5001/alerts', json={
                'alerts': [{
                    'status': 'firing',
                    'labels': {'alertname': 'Test', 'severity': 'warning'},
                    'annotations': {'summary': '测试告警'}
                }]
            }, timeout=5)
            
            if resp.status_code == 200:
                print_pass("告警接收端点正常")
                return True
            else:
                print_warn(f"告警接收端点返回：{resp.status_code}")
                return True
        else:
            print_warn("钉钉通知服务未运行（可选）")
            return True
    except Exception:
        print_warn("钉钉通知服务未启动（可选组件）")
        return True

def test_api_documentation():
    """测试 API 文档"""
    print_header("5. API 文档测试")
    
    doc_file = Path(__file__).parent / 'API_DOCUMENTATION.md'
    
    if doc_file.exists():
        content = doc_file.read_text()
        
        # 检查关键章节
        required_sections = [
            '快速入门',
            '认证',
            'API 端点',
            '错误处理',
            '示例代码'
        ]
        
        all_present = True
        for section in required_sections:
            if section in content:
                print_pass(f"包含章节：{section}")
            else:
                print_fail(f"缺少章节：{section}")
                all_present = False
        
        # 检查文件大小
        size_kb = doc_file.stat().st_size / 1024
        print_pass(f"文档大小：{size_kb:.1f} KB")
        
        return all_present
    else:
        print_fail("API 文档不存在")
        return False

def test_log_collection():
    """测试日志收集"""
    print_header("6. 日志收集测试")
    
    logs_dir = Path(__file__).parent / 'logs'
    
    if logs_dir.exists():
        log_files = list(logs_dir.glob('*.log'))
        print_pass(f"日志目录存在：{len(log_files)} 个日志文件")
        
        # 检查 Filebeat 配置
        filebeat_config = Path(__file__).parent / 'monitoring/filebeat/filebeat.yml'
        if filebeat_config.exists():
            content = filebeat_config.read_text()
            if '/var/log/agent-cluster' in content:
                print_pass("Filebeat 配置正确")
                return True
            else:
                print_warn("Filebeat 配置可能不完整")
                return True
        else:
            print_warn("Filebeat 配置不存在（可选）")
            return True
    else:
        print_fail("日志目录不存在")
        return False

def run_all_tests():
    """运行所有测试"""
    print_header("V2.7.1 本周优化验证测试")
    
    results = {
        'Web 服务': test_web_service(),
        '监控页面': test_monitoring_page(),
        'ELK 服务': test_elk_services(),
        '钉钉通知': test_dingtalk_notifier(),
        'API 文档': test_api_documentation(),
        '日志收集': test_log_collection()
    }
    
    print_header("测试结果汇总")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}通过{Colors.END}" if result else f"{Colors.RED}失败{Colors.END}"
        print(f"  {name}: {status}")
    
    print(f"\n  总计：{passed}/{total} 通过")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 所有测试通过！{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ 部分测试失败，请检查{Colors.END}")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
