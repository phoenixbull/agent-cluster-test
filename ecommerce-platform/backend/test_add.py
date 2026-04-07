"""
加法函数单元测试
"""
import pytest
from add import add


class TestAdd:
    """加法函数测试类"""
    
    def test_add_positive_integers(self):
        """测试正整数相加"""
        assert add(2, 3) == 5
        assert add(10, 20) == 30
        assert add(100, 200) == 300
    
    def test_add_negative_integers(self):
        """测试负整数相加"""
        assert add(-2, -3) == -5
        assert add(-10, -20) == -30
    
    def test_add_mixed_integers(self):
        """测试正负整数相加"""
        assert add(-1, 1) == 0
        assert add(5, -3) == 2
        assert add(-5, 3) == -2
    
    def test_add_floats(self):
        """测试浮点数相加"""
        assert add(2.5, 3.5) == 6.0
        assert add(1.1, 2.2) == pytest.approx(3.3, rel=1e-1)
    
    def test_add_mixed_types(self):
        """测试整数和浮点数相加"""
        assert add(2, 3.5) == 5.5
        assert add(2.5, 3) == 5.5
    
    def test_add_zero(self):
        """测试与零相加"""
        assert add(0, 0) == 0
        assert add(5, 0) == 5
        assert add(0, 5) == 5
    
    def test_add_large_numbers(self):
        """测试大数相加"""
        assert add(1000000, 2000000) == 3000000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
