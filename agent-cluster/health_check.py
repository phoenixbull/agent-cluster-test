#!/usr/bin/env python3
"""健康检查脚本 - 生产环境"""

import requests
import sys
import time
import json
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / "deploy_config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

def health_check(endpoint, timeout=30):
    """执行健康检查"""
    try:
        response = requests.get(endpoint, timeout=timeout)
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def main():
    config = load_config()
    health_config = config.get("health_check", {})
    
    endpoints = health_config.get("endpoints", ["/health"])
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"🔍 健康检查：{base_url}")
    
    all_healthy = True
    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint}"
        result = health_check(url)
        
        status_icon = "✅" if result["status"] == "healthy" else "❌"
        print(f"  {status_icon} {endpoint}: {result['status']}")
        
        if "response_time_ms" in result:
            print(f"     响应时间：{result['response_time_ms']:.2f}ms")
        
        if result["status"] != "healthy":
            all_healthy = False
            if "error" in result:
                print(f"     错误：{result['error']}")
    
    sys.exit(0 if all_healthy else 1)

if __name__ == "__main__":
    main()
