#!/usr/bin/env python3
"""
服务看门狗
监控服务状态，异常时自动重启
"""

import os
import sys
import time
import signal
import subprocess
from datetime import datetime
from pathlib import Path

class ServiceWatchdog:
    """服务看门狗"""
    
    def __init__(self, script: str, port: int = 8890):
        self.script = script
        self.port = port
        self.process = None
        self.running = True
        self.restart_count = 0
        self.max_restarts = 5
        self.restart_delay = 5  # 秒
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        print(f"\n收到信号 {signum}, 停止看门狗...")
        self.running = False
        if self.process:
            self.process.terminate()
        sys.exit(0)
    
    def is_port_in_use(self) -> bool:
        """检查端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', self.port)) == 0
    
    def start_service(self):
        """启动服务"""
        try:
            print(f"[{datetime.now()}] 启动服务：{self.script}")
            self.process = subprocess.Popen(
                [sys.executable, self.script, '--port', str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(self.script).parent
            )
            time.sleep(2)  # 等待服务启动
            
            if self.process.poll() is None:
                print(f"[{datetime.now()}] 服务启动成功 (PID: {self.process.pid})")
                return True
            else:
                print(f"[{datetime.now()}] 服务启动失败")
                return False
        except Exception as e:
            print(f"[{datetime.now()}] 启动服务异常：{e}")
            return False
    
    def check_service(self) -> bool:
        """检查服务状态"""
        if self.process is None:
            return False
        
        if self.process.poll() is not None:
            print(f"[{datetime.now()}] 服务进程已退出 (code: {self.process.poll()})")
            return False
        
        # 检查端口
        if not self.is_port_in_use():
            print(f"[{datetime.now()}] 端口 {self.port} 未被监听")
            return False
        
        return True
    
    def run(self):
        """运行看门狗"""
        print(f"[{datetime.now()}] 看门狗启动")
        print(f"监控脚本：{self.script}")
        print(f"监控端口：{self.port}")
        print(f"最大重启次数：{self.max_restarts}")
        print()
        
        # 首次启动
        if not self.start_service():
            print(f"[{datetime.now()}] 首次启动失败，退出")
            return
        
        while self.running:
            time.sleep(10)  # 每 10 秒检查一次
            
            if not self.check_service():
                print(f"[{datetime.now()}] 服务异常，尝试重启...")
                
                if self.restart_count >= self.max_restarts:
                    print(f"[{datetime.now()}] 已达到最大重启次数，退出")
                    break
                
                self.restart_count += 1
                
                # 等待一段时间后重启
                time.sleep(self.restart_delay)
                
                if not self.start_service():
                    print(f"[{datetime.now()}] 重启失败")
                    break
            
            # 重置重启计数（服务正常运行 5 分钟后）
            if self.restart_count > 0:
                time.sleep(300)
                self.restart_count = 0
                print(f"[{datetime.now()}] 服务正常运行，重置重启计数")
        
        print(f"[{datetime.now()}] 看门狗停止")


if __name__ == '__main__':
    script = sys.argv[1] if len(sys.argv) > 1 else 'web_app_v2.py'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8890
    
    watchdog = ServiceWatchdog(script, port)
    watchdog.run()
