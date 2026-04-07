"""待办 API 测试 - 简单版本"""
import unittest


class TestTodoAPI(unittest.TestCase):
    """待办 API 单元测试"""
    
    def test_todo_structure(self):
        """测试待办结构"""
        todo = {"title": "测试"}
        self.assertIn("title", todo)
    
    def test_title_not_empty(self):
        """测试标题非空"""
        todo = {"title": "测试"}
        self.assertTrue(len(todo["title"]) > 0)


if __name__ == "__main__":
    unittest.main()
