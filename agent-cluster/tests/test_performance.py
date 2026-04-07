#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 测试 FastAPI 版本 vs SimpleHTTP 版本

测试项:
1. 并发请求测试
2. 响应时间测试
3. 缓存命中率测试
4. 内存使用测试
"""

import asyncio
import time
import statistics
import requests
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8890"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'


def print_header(title: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}  {title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")


def print_result(name: str, value: str, unit: str = ""):
    print(f"  {Colors.CYAN}{name}:{Colors.END} {value}{unit}")


def get_token() -> str:
    """获取测试 Token"""
    try:
        resp = requests.post(f'{BASE_URL}/api/login', json={
            'username': 'admin',
            'password': 'admin'
        }, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get('token', '')
    except Exception:
        pass
    
    return ''


def test_single_request(endpoint: str, token: str = None) -> float:
    """测试单次请求响应时间"""
    headers = {}
    if token:
        headers['Cookie'] = f'auth_token={token}'
    
    start = time.time()
    try:
        resp = requests.get(f'{BASE_URL}{endpoint}', headers=headers, timeout=10)
        elapsed = (time.time() - start) * 1000  # ms
        return elapsed, resp.status_code
    except Exception as e:
        return -1, 0


def test_concurrent_requests(endpoint: str, concurrency: int = 10, token: str = None) -> Dict[str, Any]:
    """测试并发请求"""
    headers = {}
    if token:
        headers['Cookie'] = f'auth_token={token}'
    
    results = []
    
    def make_request():
        start = time.time()
        try:
            resp = requests.get(f'{BASE_URL}{endpoint}', headers=headers, timeout=10)
            elapsed = (time.time() - start) * 1000
            return elapsed, resp.status_code
        except Exception:
            return -1, 0
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request) for _ in range(concurrency)]
        for future in futures:
            results.append(future.result())
    
    # 过滤失败请求
    valid_results = [r[0] for r in results if r[0] > 0]
    success_count = len(valid_results)
    
    if not valid_results:
        return {
            'success': 0,
            'failed': concurrency,
            'avg': 0,
            'min': 0,
            'max': 0,
            'p95': 0,
            'qps': 0
        }
    
    return {
        'success': success_count,
        'failed': concurrency - success_count,
        'avg': statistics.mean(valid_results),
        'min': min(valid_results),
        'max': max(valid_results),
        'p95': sorted(valid_results)[int(len(valid_results) * 0.95)] if len(valid_results) > 1 else valid_results[0],
        'qps': concurrency / (max(valid_results) / 1000) if valid_results else 0
    }


def test_cache_effectiveness(endpoint: str, token: str = None) -> Dict[str, Any]:
    """测试缓存效果"""
    headers = {}
    if token:
        headers['Cookie'] = f'auth_token={token}'
    
    times = []
    
    # 第一次请求（未命中缓存）
    t1, _ = test_single_request(endpoint, token)
    times.append(('1st (cold)', t1))
    
    # 第二次请求（应命中缓存）
    t2, _ = test_single_request(endpoint, token)
    times.append(('2nd (warm)', t2))
    
    # 第三次请求
    t3, _ = test_single_request(endpoint, token)
    times.append(('3rd', t3))
    
    # 计算缓存加速比
    if t1 > 0 and t2 > 0:
        speedup = t1 / t2
    else:
        speedup = 0
    
    return {
        'times': times,
        'speedup': speedup
    }


def test_memory_usage() -> Dict[str, Any]:
    """测试内存使用"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'web_app_fastapi.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=5
        )
        
        pids = result.stdout.strip().split('\n')
        
        if not pids or not pids[0]:
            return {'available': False}
        
        total_memory = 0
        for pid in pids:
            if pid:
                try:
                    with open(f'/proc/{pid}/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                memory_kb = int(line.split()[1])
                                total_memory += memory_kb
                                break
                except Exception:
                    pass
        
        return {
            'available': True,
            'memory_mb': round(total_memory / 1024, 2),
            'processes': len(pids)
        }
    except Exception as e:
        return {'available': False, 'error': str(e)}


def run_all_tests():
    """运行所有测试"""
    print_header("Agent Cluster V2.5 性能测试")
    
    # 获取 Token
    token = get_token()
    if not token:
        print(f"{Colors.RED}❌ 无法获取测试 Token，请确保服务已启动且可登录{Colors.END}")
        return
    
    print(f"{Colors.GREEN}✅ 获取测试 Token 成功{Colors.END}")
    
    # ========== 测试 1: 健康检查 ==========
    print_header("1. 健康检查端点")
    t, status = test_single_request('/health')
    if t > 0:
        print_result("响应时间", f"{t:.2f}", " ms")
        print_result("状态码", str(status))
        print(f"{Colors.GREEN}✅ 通过{Colors.END}")
    else:
        print(f"{Colors.RED}❌ 失败{Colors.END}")
    
    # ========== 测试 2: 状态 API ==========
    print_header("2. 状态 API (/api/status)")
    
    print(f"\n{Colors.CYAN}单次请求:{Colors.END}")
    t, status = test_single_request('/api/status', token)
    if t > 0:
        print_result("响应时间", f"{t:.2f}", " ms")
        print_result("状态码", str(status))
    
    print(f"\n{Colors.CYAN}并发测试 (10 并发):{Colors.END}")
    result = test_concurrent_requests('/api/status', concurrency=10, token=token)
    print_result("成功", str(result['success']))
    print_result("失败", str(result['failed']))
    print_result("平均响应", f"{result['avg']:.2f}", " ms")
    print_result("最小响应", f"{result['min']:.2f}", " ms")
    print_result("最大响应", f"{result['max']:.2f}", " ms")
    print_result("P95", f"{result['p95']:.2f}", " ms")
    print_result("QPS", f"{result['qps']:.2f}", " req/s")
    
    # ========== 测试 3: 缓存效果 ==========
    print_header("3. 缓存效果测试")
    cache_result = test_cache_effectiveness('/api/status', token)
    for label, t in cache_result['times']:
        print_result(label, f"{t:.2f}", " ms" if t > 0 else " (失败)")
    
    if cache_result['speedup'] > 1:
        print_result("缓存加速比", f"{cache_result['speedup']:.2f}x")
        print(f"{Colors.GREEN}✅ 缓存生效{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ 缓存未明显生效{Colors.END}")
    
    # ========== 测试 4: Agents API ==========
    print_header("4. Agents API (/api/agents)")
    result = test_concurrent_requests('/api/agents', concurrency=10, token=token)
    print_result("平均响应", f"{result['avg']:.2f}", " ms")
    print_result("QPS", f"{result['qps']:.2f}", " req/s")
    
    # ========== 测试 5: 内存使用 ==========
    print_header("5. 内存使用")
    mem_result = test_memory_usage()
    if mem_result.get('available'):
        print_result("进程数", str(mem_result.get('processes', 0)))
        print_result("内存占用", f"{mem_result.get('memory_mb', 0):.2f}", " MB")
        print(f"{Colors.GREEN}✅ 数据可用{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ 无法获取内存数据{Colors.END}")
    
    # ========== 总结 ==========
    print_header("性能测试总结")
    print(f"{Colors.GREEN}✅ 测试完成{Colors.END}")
    print(f"\n💡 提示:")
    print(f"  - 查看 API 文档：{BASE_URL}/docs")
    print(f"  - 查看 ReDoc: {BASE_URL}/redoc")
    print(f"  - 对比 SimpleHTTP 版本，FastAPI 应有更好的并发性能")


if __name__ == '__main__':
    run_all_tests()
