"""
同步调用单元测试
"""
import unittest
import time
from sync_call import SyncCaller, CallResult


class TestSyncCaller(unittest.TestCase):
    """同步调用器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.caller = SyncCaller()
    
    def test_basic_call(self):
        """测试基础调用"""
        def add(x, y):
            return x + y
        
        result = self.caller.call(add, 2, 3)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, 5)
        self.assertGreater(result.elapsed_ms, 0)
    
    def test_call_with_kwargs(self):
        """测试关键字参数"""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        result = self.caller.call(greet, "World", greeting="Hi")
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, "Hi, World!")
    
    def test_call_exception(self):
        """测试异常处理"""
        def error_func():
            raise ValueError("测试错误")
        
        result = self.caller.call(error_func)
        
        self.assertFalse(result.success)
        self.assertIn("测试错误", result.data)
    
    def test_call_timing(self):
        """测试耗时计算"""
        def slow_func():
            time.sleep(0.05)
            return "done"
        
        result = self.caller.call(slow_func)
        
        self.assertTrue(result.success)
        self.assertGreater(result.elapsed_ms, 40)  # 至少 40ms
    
    def test_call_history(self):
        """测试调用历史"""
        def simple():
            return 1
        
        self.caller.call(simple)
        self.caller.call(simple)
        self.caller.call(simple)
        
        stats = self.caller.get_stats()
        
        self.assertEqual(stats["total_calls"], 3)
        self.assertEqual(stats["success_count"], 3)
        self.assertEqual(stats["failed_count"], 0)
    
    def test_lock_state(self):
        """测试锁定状态"""
        def simple():
            return 1
        
        self.assertFalse(self.caller.is_locked)
        self.caller.call(simple)
        self.assertFalse(self.caller.is_locked)  # 调用后应释放
    
    def test_stats_empty(self):
        """测试空统计"""
        stats = self.caller.get_stats()
        
        self.assertEqual(stats["total_calls"], 0)
        self.assertEqual(stats["avg_elapsed_ms"], 0)


if __name__ == "__main__":
    unittest.main()
