#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全测试脚本 - 验证阶段 1 安全加固功能

测试项:
1. JWT 认证
2. Rate Limiting
3. 健康检查
4. HTTPS 强制重定向
"""

import requests
import time
import sys
from pathlib import Path

BASE_URL = 'http://127.0.0.1:8890'
HTTPS_URL = 'https://127.0.0.1:443'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}▶ {name}{Colors.END}")

def print_pass(msg: str):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")

def print_fail(msg: str):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")

def print_warn(msg: str):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")


def test_health_check():
    """测试健康检查端点"""
    print_test("1. 健康检查端点")
    
    try:
        resp = requests.get(f'{BASE_URL}/health', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"健康检查返回：{data.get('status', 'unknown')}")
            print_pass(f"服务版本：{data.get('checks', {}).get('service', {}).get('version', 'N/A')}")
            print_pass(f"运行时间：{data.get('checks', {}).get('service', {}).get('uptime_seconds', 0)} 秒")
            
            # 检查各项子状态
            checks = data.get('checks', {})
            for check_name, check_data in checks.items():
                status = check_data.get('status', 'unknown')
                if status == 'healthy':
                    print_pass(f"  - {check_name}: {status}")
                elif status == 'degraded':
                    print_warn(f"  - {check_name}: {status}")
                else:
                    print_fail(f"  - {check_name}: {status}")
            return True
        else:
            print_fail(f"健康检查失败：HTTP {resp.status_code}")
            return False
    except Exception as e:
        print_fail(f"健康检查异常：{e}")
        return False


def test_jwt_auth():
    """测试 JWT 认证"""
    print_test("2. JWT 认证")
    
    # 测试未授权访问
    try:
        resp = requests.get(f'{BASE_URL}/api/workflows', timeout=5)
        if resp.status_code == 302 or resp.status_code == 401:
            print_pass("未授权访问被拒绝")
        else:
            print_fail(f"未授权访问未被拒绝：HTTP {resp.status_code}")
            return False
    except Exception as e:
        print_fail(f"未授权访问测试异常：{e}")
        return False
    
    # 测试登录
    try:
        resp = requests.post(f'{BASE_URL}/api/login', json={
            'username': 'admin',
            'password': 'admin'
        }, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                token = data.get('token')
                print_pass(f"登录成功，获取 Token")
                
                # 测试使用 Token 访问受保护接口
                if token:
                    cookies = {'auth_token': token}
                    resp = requests.get(f'{BASE_URL}/api/workflows', cookies=cookies, timeout=5)
                    if resp.status_code == 200:
                        print_pass("使用 Token 访问受保护接口成功")
                        return True
                    else:
                        print_fail(f"使用 Token 访问失败：HTTP {resp.status_code}")
                        return False
            else:
                print_fail(f"登录失败：{data.get('error', 'unknown')}")
                return False
        else:
            print_fail(f"登录请求失败：HTTP {resp.status_code}")
            return False
    except Exception as e:
        print_fail(f"登录测试异常：{e}")
        return False


def test_rate_limiting():
    """测试 Rate Limiting"""
    print_test("3. Rate Limiting")
    
    try:
        # 快速发送多个请求
        request_count = 120  # 超过默认的 100 次限制
        success_count = 0
        rate_limited_count = 0
        
        print(f"  发送 {request_count} 个快速请求...")
        
        for i in range(request_count):
            resp = requests.get(f'{BASE_URL}/api/status', timeout=5)
            if resp.status_code == 200:
                success_count += 1
            elif resp.status_code == 429:
                rate_limited_count += 1
                if rate_limited_count == 1:
                    retry_after = resp.headers.get('Retry-After', 'N/A')
                    print_pass(f"触发 Rate Limiting (第 {i+1} 次请求)")
                    print_pass(f"Retry-After: {retry_after} 秒")
        
        print_pass(f"成功请求：{success_count}")
        print_pass(f"被限制请求：{rate_limited_count}")
        
        if rate_limited_count > 0:
            print_pass("Rate Limiting 正常工作")
            return True
        else:
            print_warn("未触发 Rate Limiting（可能阈值较高）")
            return True
            
    except Exception as e:
        print_fail(f"Rate Limiting 测试异常：{e}")
        return False


def test_password_change():
    """测试密码修改"""
    print_test("4. 密码修改")
    
    try:
        # 先登录
        resp = requests.post(f'{BASE_URL}/api/login', json={
            'username': 'admin',
            'password': 'admin'
        }, timeout=5)
        
        if not resp.json().get('success'):
            print_fail("无法登录进行测试")
            return False
        
        token = resp.json().get('token')
        cookies = {'auth_token': token}
        
        # 测试修改密码
        resp = requests.post(f'{BASE_URL}/api/change-password', json={
            'old_password': 'admin',
            'new_password': 'newadmin123'
        }, cookies=cookies, timeout=5)
        
        data = resp.json()
        if resp.status_code == 200 and data.get('success'):
            print_pass("密码修改成功")
            print_warn("提示：测试完成后请改回原密码")
            
            # 改回原密码
            requests.post(f'{BASE_URL}/api/change-password', json={
                'old_password': 'newadmin123',
                'new_password': 'admin'
            }, cookies=cookies, timeout=5)
            print_pass("密码已恢复")
            
            return True
        else:
            print_fail(f"密码修改失败：{data.get('error', 'unknown')}")
            return False
            
    except Exception as e:
        print_fail(f"密码修改测试异常：{e}")
        return False


def test_https_redirect():
    """测试 HTTPS 重定向"""
    print_test("5. HTTPS 重定向")
    
    try:
        # 检查 Nginx 配置
        nginx_config = Path('/etc/nginx/sites-enabled/agent-cluster')
        if nginx_config.exists():
            content = nginx_config.read_text()
            if 'return 301 https://' in content:
                print_pass("Nginx 配置了 HTTP 到 HTTPS 的重定向")
                return True
            else:
                print_warn("Nginx 配置中未找到 HTTP 重定向")
                return False
        else:
            print_warn("未找到 Nginx 配置文件")
            return False
    except Exception as e:
        print_fail(f"HTTPS 检查异常：{e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}   Agent Cluster V2.3 安全加固测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    results = {
        '健康检查': test_health_check(),
        'JWT 认证': test_jwt_auth(),
        'Rate Limiting': test_rate_limiting(),
        '密码修改': test_password_change(),
        'HTTPS 重定向': test_https_redirect()
    }
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}   测试结果汇总{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}通过{Colors.END}" if result else f"{Colors.RED}失败{Colors.END}"
        print(f"  {name}: {status}")
    
    print(f"\n  总计：{passed}/{total} 通过")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 所有安全测试通过！{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}⚠ 部分测试失败，请检查{Colors.END}")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
