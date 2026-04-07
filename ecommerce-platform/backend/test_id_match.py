"""
工作流 ID 匹配 - 单元测试
"""
import unittest
from workflow_id_match import (
    WorkflowID, WorkflowIDGenerator, WorkflowIDMatcher,
    IDFormat, MatchResult
)


class TestWorkflowID(unittest.TestCase):
    """工作流 ID 测试"""
    
    def test_workflow_id_creation(self):
        """测试 ID 创建"""
        wid = WorkflowID(
            id="wf-20260331-144618-abc12345",
            format=IDFormat.COMPOSITE,
            created_at="2026-03-31T14:46:18",
            checksum="abc123"
        )
        
        self.assertEqual(wid.id, "wf-20260331-144618-abc12345")
        self.assertEqual(wid.format, IDFormat.COMPOSITE)
        self.assertTrue(wid.validate())
    
    def test_workflow_id_to_dict(self):
        """测试 ID 转字典"""
        wid = WorkflowID(
            id="wf-test",
            format=IDFormat.UUID,
            created_at="2026-03-31",
            checksum="xyz"
        )
        
        d = wid.to_dict()
        self.assertEqual(d["id"], "wf-test")
        self.assertEqual(d["format"], "uuid")
    
    def test_workflow_id_invalid(self):
        """测试无效 ID"""
        wid = WorkflowID(
            id="",
            format=IDFormat.COMPOSITE,
            created_at="2026-03-31",
            checksum=""
        )
        
        self.assertFalse(wid.validate())


class TestWorkflowIDGenerator(unittest.TestCase):
    """工作流 ID 生成器测试"""
    
    def setUp(self):
        self.generator = WorkflowIDGenerator(prefix="wf")
    
    def test_generate_uuid(self):
        """测试 UUID 生成"""
        wid = self.generator.generate(IDFormat.UUID)
        
        self.assertTrue(wid.id.startswith("wf-"))
        self.assertEqual(wid.format, IDFormat.UUID)
        self.assertTrue(wid.validate())
    
    def test_generate_timestamp(self):
        """测试时间戳生成"""
        wid = self.generator.generate(IDFormat.TIMESTAMP)
        
        self.assertTrue(wid.id.startswith("wf-"))
        self.assertEqual(wid.format, IDFormat.TIMESTAMP)
        self.assertTrue(len(wid.id) > 15)
    
    def test_generate_hash(self):
        """测试哈希生成"""
        wid = self.generator.generate(IDFormat.HASH, content="test")
        
        self.assertTrue(wid.id.startswith("wf-"))
        self.assertEqual(wid.format, IDFormat.HASH)
        self.assertTrue(wid.validate())
    
    def test_generate_composite(self):
        """测试复合生成"""
        wid = self.generator.generate(
            IDFormat.COMPOSITE,
            user_id="user123",
            project_id="proj456"
        )
        
        self.assertTrue(wid.id.startswith("wf-"))
        self.assertIn("user123", wid.id)
        self.assertIn("proj45", wid.id)  # project_id 被截断为 6 位
        self.assertEqual(wid.format, IDFormat.COMPOSITE)
    
    def test_generate_unique(self):
        """测试 ID 唯一性"""
        ids = set()
        for _ in range(100):
            wid = self.generator.generate(IDFormat.UUID)
            ids.add(wid.id)
        
        self.assertEqual(len(ids), 100)  # 所有 ID 都唯一
    
    def test_generated_ids_tracking(self):
        """测试 ID 跟踪"""
        self.generator.generate(IDFormat.UUID)
        self.generator.generate(IDFormat.UUID)
        
        self.assertEqual(len(self.generator.generated_ids), 2)


class TestWorkflowIDMatcher(unittest.TestCase):
    """工作流 ID 匹配器测试"""
    
    def setUp(self):
        self.matcher = WorkflowIDMatcher()
    
    def test_match_exact_success(self):
        """测试精确匹配成功"""
        result = self.matcher.match_exact("wf-test", "wf-test")
        
        self.assertTrue(result.matched)
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.match_type, "exact")
    
    def test_match_exact_failure(self):
        """测试精确匹配失败"""
        result = self.matcher.match_exact("wf-test1", "wf-test2")
        
        self.assertFalse(result.matched)
        self.assertEqual(result.confidence, 0.0)
    
    def test_match_pattern_uuid(self):
        """测试 UUID 模式匹配"""
        result = self.matcher.match_pattern("wf-20260331-144618-abc12345")
        
        self.assertTrue(result.matched)
        self.assertEqual(result.match_type, "pattern")
    
    def test_match_pattern_timestamp(self):
        """测试时间戳模式匹配"""
        result = self.matcher.match_pattern("wf-20260331144618")
        
        self.assertTrue(result.matched)
    
    def test_match_pattern_invalid(self):
        """测试无效模式"""
        result = self.matcher.match_pattern("invalid_id")
        
        self.assertFalse(result.matched)
    
    def test_match_fuzzy_success(self):
        """测试模糊匹配成功"""
        candidates = [
            "wf-20260331-144618-abc12345",
            "wf-20260331-144618-abc12346",
        ]
        
        result = self.matcher.match_fuzzy("wf-20260331-144618-abc12345", candidates)
        
        self.assertTrue(result.matched)
        self.assertGreater(result.confidence, 0.7)
    
    def test_match_fuzzy_failure(self):
        """测试模糊匹配失败"""
        candidates = ["wf-completely-different"]
        
        result = self.matcher.match_fuzzy("xyz-abc-123", candidates)
        
        self.assertFalse(result.matched)
    
    def test_validate_id(self):
        """测试 ID 验证"""
        # 使用 UUID 格式测试（模式更明确）
        valid_id = WorkflowID(
            id="wf-20260331-144618-abc12345",
            format=IDFormat.UUID,
            created_at="2026-03-31",
            checksum=""
        )
        
        self.assertTrue(self.matcher.validate_id(valid_id))
    
    def test_validate_invalid_id(self):
        """测试无效 ID 验证"""
        invalid_id = WorkflowID(
            id="invalid",
            format=IDFormat.COMPOSITE,
            created_at="2026-03-31",
            checksum=""
        )
        
        self.assertFalse(self.matcher.validate_id(invalid_id))
    
    def test_get_stats(self):
        """测试统计信息"""
        self.matcher.match_exact("wf-test", "wf-test")
        self.matcher.match_exact("wf-test1", "wf-test2")
        self.matcher.match_pattern("wf-20260331-144618-abc12345")
        
        stats = self.matcher.get_stats()
        
        self.assertEqual(stats["total_matches"], 3)
        self.assertEqual(stats["matched"], 2)
        self.assertEqual(stats["failed"], 1)
        self.assertGreater(stats["avg_elapsed_ms"], 0)
    
    def test_match_history(self):
        """测试匹配历史"""
        self.matcher.match_exact("a", "a")
        self.matcher.match_exact("b", "c")
        
        self.assertEqual(len(self.matcher.match_history), 2)


class TestMatchResult(unittest.TestCase):
    """匹配结果测试"""
    
    def test_match_result_creation(self):
        """测试匹配结果创建"""
        from workflow_id_match import WorkflowID
        
        result = MatchResult(
            matched=True,
            confidence=0.95,
            workflow_id=WorkflowID(
                id="wf-test",
                format=IDFormat.UUID,
                created_at="2026-03-31",
                checksum=""
            ),
            match_type="fuzzy",
            elapsed_ms=1.5,
            message="测试消息"
        )
        
        self.assertTrue(result.matched)
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.match_type, "fuzzy")
        self.assertEqual(result.elapsed_ms, 1.5)
        self.assertEqual(result.message, "测试消息")


class TestIDFormat(unittest.TestCase):
    """ID 格式枚举测试"""
    
    def test_id_format_values(self):
        """测试 ID 格式值"""
        self.assertEqual(IDFormat.UUID.value, "uuid")
        self.assertEqual(IDFormat.TIMESTAMP.value, "timestamp")
        self.assertEqual(IDFormat.HASH.value, "hash")
        self.assertEqual(IDFormat.COMPOSITE.value, "composite")


if __name__ == "__main__":
    unittest.main()
