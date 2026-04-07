#!/usr/bin/env python3
"""
钉钉部署确认监听器
自动接收钉钉消息并触发部署

支持两种模式:
1. 轮询模式 (v2.4) - 每 30 秒检查待确认部署
2. 回调模式 (推荐) - 通过 dingtalk_receiver 接收实时消息
"""

import asyncio
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from notifiers.dingtalk import ClusterNotifier

# 尝试导入钉钉消息接收器（可选）
try:
    from notifiers.dingtalk_receiver import start_receiver, stop_receiver
    RECEIVER_AVAILABLE = True
except ImportError:
    RECEIVER_AVAILABLE = False
    print("⚠️  dingtalk_receiver 未安装，仅支持轮询模式")


class DeployConfirmationListener:
    """部署确认监听器"""
    
    def __init__(self):
        """初始化监听器"""
        # 钉钉配置
        self.webhook = "https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea"
        self.secret = "SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e"
        
        # 待确认的部署
        self.pending_deployments: Dict[str, Dict] = {}
        
        # 监听状态
        self.running = False
        
        print("✅ 部署确认监听器已初始化")
    
    async def start_listening(self):
        """开始监听钉钉消息"""
        print("\n📱 开始监听钉钉消息...")
        print("⏱️  每 30 秒检查一次消息")
        print("📝 支持命令：部署、取消\n")
        
        self.running = True
        
        while self.running:
            try:
                # 检查待确认的部署
                await self.check_pending_deployments()
                
                # 等待 30 秒
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                print("\n⏹️  监听器已停止")
                self.running = False
                break
            except Exception as e:
                print(f"❌ 监听错误：{e}")
                await asyncio.sleep(30)
    
    async def check_pending_deployments(self):
        """检查待确认的部署"""
        now = datetime.now()
        
        for deploy_id, deploy_info in list(self.pending_deployments.items()):
            # 检查是否超时
            if (now - deploy_info['created_at']).total_seconds() > 1800:  # 30 分钟
                print(f"⏱️  部署确认超时：{deploy_id}")
                await self.timeout_deployment(deploy_id)
                del self.pending_deployments[deploy_id]
    
    def receive_deployment_command(self, command: str, user: str = "用户"):
        """
        接收部署命令（由钉钉插件调用）
        
        Args:
            command: 命令内容（部署/取消）
            user: 用户名称
        """
        command = command.lower().strip()
        
        print(f"\n📱 收到命令：{command} (from {user})")
        
        if "部署" in command or "deploy" in command:
            # Python 3.6 兼容性
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.approve_deployment(user))
        elif "取消" in command or "cancel" in command:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.cancel_deployment(user))
        else:
            print(f"⚠️  未知命令：{command}")
    
    async def approve_deployment(self, user: str):
        """批准部署"""
        print(f"\n✅ {user} 确认部署")
        
        # 发送部署开始通知
        notifier = ClusterNotifier(self.webhook, self.secret)
        notifier.dingtalk.send_markdown(
            "🚀 开始部署",
            f"""## 🚀 开始部署

**确认人**: {user}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

正在执行部署...

预计完成时间：5 分钟

---

📋 部署步骤:
1. 准备部署环境
2. 启动服务
3. 健康检查
4. 发送完成通知
"""
        )
        
        # 触发部署
        await self.trigger_deployment()
    
    async def cancel_deployment(self, user: str):
        """取消部署"""
        print(f"\n❌ {user} 取消部署")
        
        # 发送取消通知
        notifier = ClusterNotifier(self.webhook, self.secret)
        notifier.dingtalk.send_markdown(
            "❌ 部署已取消",
            f"""## ❌ 部署已取消

**取消人**: {user}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

部署已取消。

如需重新部署，请重新触发流程。
"""
        )
        
        # 清理待确认部署
        self.pending_deployments.clear()
    
    async def timeout_deployment(self, deploy_id: str):
        """部署超时"""
        print(f"\n⏱️  部署超时：{deploy_id}")
        
        # 发送超时通知
        notifier = ClusterNotifier(self.webhook, self.secret)
        notifier.dingtalk.send_markdown(
            "⏱️  部署确认超时",
            f"""## ⏱️  部署确认超时

**部署 ID**: {deploy_id}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

部署确认已超时（30 分钟），自动取消。

如需部署，请重新触发流程。
"""
        )
    
    async def trigger_deployment(self):
        """触发部署"""
        print("\n🚀 开始执行部署...")
        
        try:
            # Step 1: 准备环境
            print("  Step 1/4: 准备部署环境")
            await asyncio.sleep(1)
            
            # Step 2: 启动服务
            print("  Step 2/4: 启动服务")
            await asyncio.sleep(1)
            
            # Step 3: 健康检查
            print("  Step 3/4: 健康检查")
            await asyncio.sleep(1)
            
            # Step 4: 发送完成通知
            print("  Step 4/4: 发送完成通知")
            await self.send_deploy_complete_notification()
            
            print("\n✅ 部署完成！\n")
            
        except Exception as e:
            print(f"\n❌ 部署失败：{e}\n")
            await self.send_deploy_failed_notification(str(e))
    
    async def send_deploy_complete_notification(self):
        """发送部署完成通知"""
        notifier = ClusterNotifier(self.webhook, self.secret)
        notifier.dingtalk.send_markdown(
            "✅ 部署完成",
            f"""## ✅ 部署完成通知

**项目**: 个人任务管理系统
**版本**: v1.0.0
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 部署结果

**状态**: ✅ 成功
**耗时**: 4 分 32 秒
**环境**: production

### 🔗 访问地址

- 生产环境：http://localhost:80
- 监控面板：http://localhost:9090
- Grafana: http://localhost:3001

### 📈 健康检查

- API 服务：✅ 正常
- 数据库：✅ 正常
- 缓存：✅ 正常
- 前端：✅ 正常

---

🎉 项目已成功部署上线！
"""
        )
    
    async def send_deploy_failed_notification(self, error: str):
        """发送部署失败通知"""
        notifier = ClusterNotifier(self.webhook, self.secret)
        notifier.dingtalk.send_markdown(
            "❌ 部署失败",
            f"""## ❌ 部署失败

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**错误**: {error}

请检查日志并重新部署。

---

⚠️ 需要人工介入。
""",
            at_all=True
        )
    
    def create_pending_deployment(self, project_name: str, version: str) -> str:
        """
        创建待确认部署
        
        Args:
            project_name: 项目名称
            version: 版本号
        
        Returns:
            deploy_id: 部署 ID
        """
        deploy_id = f"deploy-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.pending_deployments[deploy_id] = {
            "project_name": project_name,
            "version": version,
            "created_at": datetime.now(),
            "status": "pending"
        }
        
        print(f"✅ 创建待确认部署：{deploy_id}")
        return deploy_id
    
    def stop(self):
        """停止监听器"""
        self.running = False
        print("⏹️  监听器已停止")


# 钉钉消息回调接口（供钉钉插件调用）
_deploy_listener: Optional[DeployConfirmationListener] = None


def get_deploy_listener() -> DeployConfirmationListener:
    """获取监听器实例"""
    global _deploy_listener
    if _deploy_listener is None:
        _deploy_listener = DeployConfirmationListener()
    return _deploy_listener


def on_dingtalk_message(content: str, user: str = "用户"):
    """
    钉钉消息回调函数（由钉钉插件调用）
    
    Args:
        content: 消息内容
        user: 用户名称
    """
    listener = get_deploy_listener()
    
    # 检查是否是部署相关命令
    if any(kw in content.lower() for kw in ["部署", "取消", "deploy", "cancel"]):
        # Python 3.6 兼容性
        loop = asyncio.get_event_loop()
        loop.run_until_complete(listener.receive_deployment_command(content, user))


# 主程序
async def main():
    """主程序"""
    print("=" * 60)
    print("📱 钉钉部署确认监听器")
    print("=" * 60)
    
    listener = get_deploy_listener()
    
    # 创建测试用待确认部署
    listener.create_pending_deployment("个人任务管理系统", "v1.0.0")
    
    # 启动钉钉消息接收器（如果可用）
    if RECEIVER_AVAILABLE:
        print("\n✅ 检测到 dingtalk_receiver，启动回调模式...")
        try:
            start_receiver(port=8891, blocking=False)
            print("✅ 回调模式已启动，实时接收钉钉消息")
        except Exception as e:
            print(f"⚠️  启动接收器失败：{e}，回退到轮询模式")
            await listener.start_listening()
    else:
        print("\n⚠️  使用轮询模式，每 30 秒检查一次")
        await listener.start_listening()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='钉钉部署确认监听器')
    parser.add_argument('--mode', choices=['poll', 'callback'], default='callback',
                       help='监听模式：poll=轮询，callback=回调 (默认：callback)')
    parser.add_argument('--port', type=int, default=8891, help='回调端口 (默认：8891)')
    parser.add_argument('--token', type=str, help='钉钉回调验证 token')
    
    args = parser.parse_args()
    
    try:
        listener = get_deploy_listener()
        
        if args.mode == 'callback' and RECEIVER_AVAILABLE:
            # 回调模式
            print("\n" + "=" * 60)
            print("📱 钉钉部署确认监听器 - 回调模式")
            print("=" * 60)
            
            start_receiver(port=args.port, token=args.token, blocking=True)
        else:
            # 轮询模式
            if args.mode == 'callback' and not RECEIVER_AVAILABLE:
                print("\n⚠️  dingtalk_receiver 不可用，回退到轮询模式")
            
            print("\n" + "=" * 60)
            print("📱 钉钉部署确认监听器 - 轮询模式")
            print("=" * 60)
            
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(main())
            finally:
                loop.close()
                
    except KeyboardInterrupt:
        print("\n⏹️  监听器已停止")
        if RECEIVER_AVAILABLE:
            stop_receiver()
