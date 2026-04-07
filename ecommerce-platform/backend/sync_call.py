"""
同步调用 - 最终测试
测试同步调用功能和性能
"""
import time
import threading
from typing import Any, Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallResult:
    """调用结果"""
    success: bool
    data: Any
    elapsed_ms: float
    timestamp: str


class SyncCaller:
    """同步调用器"""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.call_history: List[Dict] = []
        self.is_locked = False
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> CallResult:
        """
        同步调用函数
        
        参数:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        返回:
            CallResult: 调用结果
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # 获取锁
            with self._lock:
                self.is_locked = True
                
                # 执行调用
                result = func(*args, **kwargs)
                
                # 释放锁
                self.is_locked = False
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 记录历史
            self.call_history.append({
                "func": func.__name__,
                "success": True,
                "elapsed_ms": elapsed_ms,
                "timestamp": timestamp
            })
            
            return CallResult(
                success=True,
                data=result,
                elapsed_ms=elapsed_ms,
                timestamp=timestamp
            )
            
        except Exception as e:
            self.is_locked = False
            elapsed_ms = (time.time() - start_time) * 1000
            
            self.call_history.append({
                "func": func.__name__,
                "success": False,
                "error": str(e),
                "elapsed_ms": elapsed_ms,
                "timestamp": timestamp
            })
            
            return CallResult(
                success=False,
                data=str(e),
                elapsed_ms=elapsed_ms,
                timestamp=timestamp
            )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.call_history:
            return {
                "total_calls": 0,
                "success_count": 0,
                "failed_count": 0,
                "avg_elapsed_ms": 0
            }
        
        total = len(self.call_history)
        success = sum(1 for c in self.call_history if c["success"])
        failed = total - success
        avg_elapsed = sum(c["elapsed_ms"] for c in self.call_history) / total
        
        return {
            "total_calls": total,
            "success_count": success,
            "failed_count": failed,
            "avg_elapsed_ms": round(avg_elapsed, 2),
            "is_locked": self.is_locked
        }


# ========== 测试函数 ==========

def test_function_1(x: int, y: int) -> int:
    """测试函数 1：加法"""
    time.sleep(0.01)  # 模拟延迟
    return x + y


def test_function_2(data: Dict) -> Dict:
    """测试函数 2：数据处理"""
    time.sleep(0.01)
    return {"processed": True, "original": data}


def test_function_3() -> str:
    """测试函数 3：返回字符串"""
    time.sleep(0.01)
    return "Hello, Sync!"


def test_function_error() -> int:
    """测试函数 4：抛出异常"""
    time.sleep(0.01)
    raise ValueError("测试错误")


# ========== 测试流程 ==========

def run_final_test():
    """运行最终测试"""
    print("=" * 60)
    print("🚀 最终测试 - 同步调用")
    print("=" * 60)
    
    caller = SyncCaller(timeout=30.0)
    results = []
    
    # 测试 1: 基础调用
    print("\n1️⃣ 基础同步调用测试")
    print("-" * 60)
    result = caller.call(test_function_1, 10, 20)
    print(f"   函数：test_function_1(10, 20)")
    print(f"   结果：{result.data}")
    print(f"   耗时：{result.elapsed_ms:.2f}ms")
    print(f"   状态：{'✅ 成功' if result.success else '❌ 失败'}")
    results.append(result.success)
    
    # 测试 2: 字典处理
    print("\n2️⃣ 数据处理测试")
    print("-" * 60)
    result = caller.call(test_function_2, {"key": "value", "num": 42})
    print(f"   函数：test_function_2({...})")
    print(f"   结果：{result.data}")
    print(f"   耗时：{result.elapsed_ms:.2f}ms")
    print(f"   状态：{'✅ 成功' if result.success else '❌ 失败'}")
    results.append(result.success)
    
    # 测试 3: 无参数调用
    print("\n3️⃣ 无参数调用测试")
    print("-" * 60)
    result = caller.call(test_function_3)
    print(f"   函数：test_function_3()")
    print(f"   结果：{result.data}")
    print(f"   耗时：{result.elapsed_ms:.2f}ms")
    print(f"   状态：{'✅ 成功' if result.success else '❌ 失败'}")
    results.append(result.success)
    
    # 测试 4: 异常处理
    print("\n4️⃣ 异常处理测试")
    print("-" * 60)
    result = caller.call(test_function_error)
    print(f"   函数：test_function_error()")
    print(f"   错误：{result.data}")
    print(f"   耗时：{result.elapsed_ms:.2f}ms")
    print(f"   状态：{'⚠️ 预期失败' if not result.success else '❌ 应该失败'}")
    results.append(not result.success)  # 期望失败
    
    # 测试 5: 多次调用
    print("\n5️⃣ 多次调用测试")
    print("-" * 60)
    for i in range(5):
        result = caller.call(test_function_1, i, i*2)
        print(f"   调用 {i+1}: {i} + {i*2} = {result.data} ({result.elapsed_ms:.2f}ms)")
        results.append(result.success)
    
    # 显示统计
    print("\n📊 调用统计")
    print("-" * 60)
    stats = caller.get_stats()
    print(f"   总调用次数：{stats['total_calls']}")
    print(f"   成功次数：{stats['success_count']}")
    print(f"   失败次数：{stats['failed_count']}")
    print(f"   平均耗时：{stats['avg_elapsed_ms']:.2f}ms")
    print(f"   锁定状态：{'🔒' if stats['is_locked'] else '🔓'}")
    
    # 最终结果
    print("\n" + "=" * 60)
    print("📋 最终测试结果")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"   通过测试：{passed}/{total}")
    print(f"   成功率：{success_rate:.1f}%")
    print(f"   最终状态：{'✅ 全部通过' if passed == total else '⚠️ 部分通过'}")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_final_test()
    exit(0 if success else 1)
