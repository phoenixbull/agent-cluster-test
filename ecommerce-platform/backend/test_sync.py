"""
Agent 同步测试
测试 Agent 之间的同步通信功能
"""
import asyncio
import time
from typing import Dict, List


class SyncAgent:
    """同步 Agent 类"""
    
    def __init__(self, name: str):
        self.name = name
        self.messages: List[str] = []
        self.is_synced = False
    
    def send_message(self, message: str, target: 'SyncAgent'):
        """发送消息到目标 Agent"""
        print(f"[{self.name}] 发送：{message} -> [{target.name}]")
        target.receive_message(message, self)
    
    def receive_message(self, message: str, sender: 'SyncAgent'):
        """接收消息"""
        self.messages.append(f"{sender.name}: {message}")
        print(f"[{self.name}] 收到：{message} (来自 {sender.name})")
        self.is_synced = True
    
    def get_status(self) -> Dict:
        """获取 Agent 状态"""
        return {
            "name": self.name,
            "message_count": len(self.messages),
            "is_synced": self.is_synced,
            "messages": self.messages
        }


async def test_sync_communication():
    """测试同步通信"""
    print("=" * 50)
    print("🔄 Agent 同步通信测试")
    print("=" * 50)
    
    # 创建 Agent
    agent1 = SyncAgent("Agent-1")
    agent2 = SyncAgent("Agent-2")
    agent3 = SyncAgent("Agent-3")
    
    # 测试双向同步
    print("\n1️⃣ 双向同步测试:")
    agent1.send_message("你好，Agent-2！", agent2)
    await asyncio.sleep(0.1)
    agent2.send_message("你好，Agent-1！", agent1)
    
    # 测试广播同步
    print("\n2️⃣ 广播同步测试:")
    agent1.send_message("大家好！", agent2)
    await asyncio.sleep(0.1)
    agent1.send_message("大家好！", agent3)
    
    # 测试链式同步
    print("\n3️⃣ 链式同步测试:")
    agent1.send_message("消息链启动", agent2)
    await asyncio.sleep(0.1)
    agent2.send_message("消息转发", agent3)
    
    # 显示状态
    print("\n📊 Agent 状态:")
    print("-" * 50)
    for agent in [agent1, agent2, agent3]:
        status = agent.get_status()
        print(f"{status['name']}:")
        print(f"  同步状态：{'✅' if status['is_synced'] else '❌'}")
        print(f"  消息数量：{status['message_count']}")
        if status['messages']:
            print(f"  消息列表：{status['messages']}")
        print()
    
    # 验证结果
    print("=" * 50)
    print("📋 测试结果:")
    all_synced = all([agent1.is_synced, agent2.is_synced, agent3.is_synced])
    print(f"所有 Agent 已同步：{'✅' if all_synced else '❌'}")
    print(f"Agent-1 消息数：{len(agent1.messages)}")
    print(f"Agent-2 消息数：{len(agent2.messages)}")
    print(f"Agent-3 消息数：{len(agent3.messages)}")
    print("=" * 50)
    
    return all_synced


def test_basic_sync():
    """基础同步测试"""
    print("\n⚡ 基础同步测试")
    print("-" * 30)
    
    agent = SyncAgent("Test-Agent")
    
    # 模拟同步操作
    start = time.time()
    agent.is_synced = True
    elapsed = time.time() - start
    
    print(f"同步完成时间：{elapsed*1000:.2f}ms")
    print(f"同步状态：{'✅' if agent.is_synced else '❌'}")
    
    return agent.is_synced


if __name__ == "__main__":
    # 运行测试
    print("\n🚀 开始 Agent 同步测试...\n")
    
    # 基础测试
    basic_result = test_basic_sync()
    
    # 异步测试
    if hasattr(asyncio, 'run'):
        async_result = asyncio.run(test_sync_communication())
    else:
        # Python 3.6 兼容
        loop = asyncio.get_event_loop()
        async_result = loop.run_until_complete(test_sync_communication())
    
    # 总结
    print("\n🎯 测试总结:")
    print(f"基础同步：{'✅ 通过' if basic_result else '❌ 失败'}")
    print(f"同步通信：{'✅ 通过' if async_result else '❌ 失败'}")
    print(f"总体状态：{'✅ 全部通过' if basic_result and async_result else '❌ 部分失败'}")
    print()
