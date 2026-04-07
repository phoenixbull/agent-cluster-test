"""
清理后重新测试 - 单元测试
"""
import unittest
import os
import tempfile
from retest_after_cleanup import TestEnvironment, RetestRunner, TestResult


class TestTestEnvironment(unittest.TestCase):
    """测试环境测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.env = TestEnvironment(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_setup(self):
        """测试环境设置"""
        result = self.env.setup()
        
        self.assertTrue(result)
        self.assertFalse(self.env.is_clean)
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertGreater(len(self.env.test_files), 0)
    
    def test_cleanup(self):
        """测试环境清理"""
        self.env.setup()
        report = self.env.cleanup()
        
        self.assertTrue(self.env.is_clean)
        self.assertFalse(os.path.exists(self.temp_dir))
        self.assertGreater(report.files_removed, 0)
        self.assertGreater(report.dirs_removed, 0)
    
    def test_verify_clean(self):
        """测试清理验证"""
        self.env.setup()
        self.env.cleanup()
        
        is_clean = self.env.verify_clean()
        self.assertTrue(is_clean)
    
    def test_verify_not_clean(self):
        """测试未清理验证"""
        self.env.setup()
        
        is_clean = self.env.verify_clean()
        self.assertFalse(is_clean)


class TestRetestRunner(unittest.TestCase):
    """重新测试运行器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.runner = RetestRunner()
    
    def test_run_test_success(self):
        """测试成功运行"""
        def success_test():
            return (True, "成功")
        
        result = self.runner.run_test("Test-1", success_test)
        
        self.assertTrue(result.success)
        self.assertEqual(result.name, "Test-1")
        self.assertEqual(result.message, "成功")
    
    def test_run_test_failure(self):
        """测试失败运行"""
        def fail_test():
            return (False, "失败")
        
        result = self.runner.run_test("Test-1", fail_test)
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "失败")
    
    def test_run_test_exception(self):
        """测试异常处理"""
        def error_test():
            raise ValueError("测试错误")
        
        result = self.runner.run_test("Test-1", error_test)
        
        self.assertFalse(result.success)
        self.assertIn("测试错误", result.message)
    
    def test_multiple_tests(self):
        """测试多个测试"""
        def test1(): return (True, "")
        def test2(): return (True, "")
        def test3(): return (False, "")
        
        self.runner.run_test("Test-1", test1)
        self.runner.run_test("Test-2", test2)
        self.runner.run_test("Test-3", test3)
        
        self.assertEqual(len(self.runner.results), 3)
        passed = sum(1 for r in self.runner.results if r.success)
        self.assertEqual(passed, 2)
    
    def test_generate_report(self):
        """测试报告生成"""
        def test1(): return (True, "")
        def test2(): return (True, "")
        
        self.runner.run_test("Test-1", test1)
        self.runner.run_test("Test-2", test2)
        
        # 模拟清理报告
        from retest_after_cleanup import CleanupReport
        self.runner.cleanup_report = CleanupReport(
            files_removed=5,
            dirs_removed=2,
            space_freed_bytes=1000,
            elapsed_ms=10.0
        )
        
        report = self.runner.generate_report(
            setup_success=True,
            is_clean=True,
            final_cleanup=self.runner.cleanup_report
        )
        
        self.assertEqual(report['test_summary']['total'], 2)
        self.assertEqual(report['test_summary']['passed'], 2)
        self.assertEqual(report['test_summary']['success_rate'], 100.0)
        self.assertTrue(report['cleanup_summary']['verified_clean'])


class TestCleanupReport(unittest.TestCase):
    """清理报告测试"""
    
    def test_cleanup_report_creation(self):
        """测试清理报告创建"""
        from retest_after_cleanup import CleanupReport
        
        report = CleanupReport(
            files_removed=10,
            dirs_removed=3,
            space_freed_bytes=5000,
            elapsed_ms=25.5
        )
        
        self.assertEqual(report.files_removed, 10)
        self.assertEqual(report.dirs_removed, 3)
        self.assertEqual(report.space_freed_bytes, 5000)
        self.assertEqual(report.elapsed_ms, 25.5)


if __name__ == "__main__":
    unittest.main()
