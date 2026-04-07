"""
加法函数模块
"""


def add(a: int | float, b: int | float) -> int | float:
    """
    计算两个数的和
    
    参数:
        a: 第一个数
        b: 第二个数
    
    返回:
        两数之和
    
    示例:
        >>> add(2, 3)
        5
        >>> add(2.5, 3.5)
        6.0
        >>> add(-1, 1)
        0
    """
    return a + b


if __name__ == "__main__":
    # 简单测试
    print(f"add(2, 3) = {add(2, 3)}")
    print(f"add(2.5, 3.5) = {add(2.5, 3.5)}")
    print(f"add(-1, 1) = {add(-1, 1)}")
