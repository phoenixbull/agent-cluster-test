"""简单函数测试"""
import unittest
from hello import greet, add, is_even


class TestFunctions(unittest.TestCase):
    def test_greet(self):
        self.assertIn("你好", greet("世界"))
    
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
    
    def test_is_even(self):
        self.assertTrue(is_even(4))
        self.assertFalse(is_even(3))


if __name__ == "__main__":
    unittest.main()
