"""
验证修复 - 单元测试
"""
import unittest
from verify_fix import FixVerifier, Status, Issue


class TestFixVerifier(unittest.TestCase):
    """修复验证器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.verifier = FixVerifier()
    
    def test_create_issue(self):
        """测试创建问题"""
        issue = self.verifier.create_issue("测试问题")
        
        self.assertEqual(issue.id, "ISSUE-001")
        self.assertEqual(issue.description, "测试问题")
        self.assertEqual(issue.status, Status.PENDING)
        self.assertIsNotNone(issue.created_at)
    
    def test_mark_fixed(self):
        """测试标记修复"""
        issue = self.verifier.create_issue("测试问题")
        result = self.verifier.mark_fixed(issue.id)
        
        self.assertTrue(result)
        self.assertEqual(issue.status, Status.FIXED)
        self.assertIsNotNone(issue.fixed_at)
    
    def test_mark_fixed_not_found(self):
        """测试标记不存在的问题"""
        result = self.verifier.mark_fixed("ISSUE-999")
        
        self.assertFalse(result)
    
    def test_verify_fix_success(self):
        """测试验证成功"""
        issue = self.verifier.create_issue("测试问题")
        self.verifier.mark_fixed(issue.id)
        
        def passing_check():
            return True
        
        result = self.verifier.verify_fix(issue.id, [passing_check, passing_check])
        
        self.assertTrue(result.success)
        self.assertEqual(result.checks_passed, 2)
        self.assertEqual(result.checks_total, 2)
        self.assertEqual(issue.status, Status.VERIFIED)
        self.assertIsNotNone(issue.verified_at)
    
    def test_verify_fix_failure(self):
        """测试验证失败"""
        issue = self.verifier.create_issue("测试问题")
        self.verifier.mark_fixed(issue.id)
        
        def passing_check():
            return True
        
        def failing_check():
            return False
        
        result = self.verifier.verify_fix(issue.id, [passing_check, failing_check])
        
        self.assertFalse(result.success)
        self.assertEqual(result.checks_passed, 1)
        self.assertEqual(issue.status, Status.FAILED)
    
    def test_verify_fix_not_found(self):
        """测试验证不存在的问题"""
        def check():
            return True
        
        result = self.verifier.verify_fix("ISSUE-999", [check])
        
        self.assertFalse(result.success)
        self.assertEqual(result.checks_total, 0)
    
    def test_get_stats(self):
        """测试统计信息"""
        self.verifier.create_issue("问题 1")
        self.verifier.create_issue("问题 2")
        
        stats = self.verifier.get_stats()
        
        self.assertEqual(stats["total_issues"], 2)
        self.assertEqual(stats["by_status"]["pending"], 2)
        self.assertEqual(stats["verification_count"], 0)
    
    def test_multiple_issues(self):
        """测试多个问题"""
        issues = []
        for i in range(5):
            issues.append(self.verifier.create_issue(f"问题{i}"))
        
        self.assertEqual(len(self.verifier.issues), 5)
        
        # 修复部分问题
        for issue in issues[:3]:
            self.verifier.mark_fixed(issue.id)
        
        stats = self.verifier.get_stats()
        self.assertEqual(stats["by_status"]["fixed"], 3)
        self.assertEqual(stats["by_status"]["pending"], 2)


if __name__ == "__main__":
    unittest.main()
