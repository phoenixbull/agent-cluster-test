"""
简单的 Python 函数示例
"""


def greet(name: str) -> str:
    """问候函数"""
    return f"你好，{name}！👋"


def add(a: int, b: int) -> int:
    """加法函数"""
    return a + b


def is_even(n: int) -> bool:
    """判断偶数"""
    return n % 2 == 0


if __name__ == "__main__":
    print(greet("世界"))
    print(f"2 + 3 = {add(2, 3)}")
    print(f"4 是偶数吗？{is_even(4)}")
