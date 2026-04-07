"""
验证修复 - 新测试
测试修复验证功能和流程
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Status(Enum):
    """状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class Issue:
    """问题记录"""
    id: str
    description: str
    status: Status
    created_at: str
    fixed_at: Optional[str] = None
    verified_at: Optional[str] = None


@dataclass
class VerificationResult:
    """验证结果"""
    success: bool
    issue_id: str
    checks_passed: int
    checks_total: int
    elapsed_ms: float
    timestamp: str


class FixVerifier:
    """修复验证器"""
    
    def __init__(self):
        self.issues: Dict[str, Issue] = {}
        self.verification_history: List[VerificationResult] = []
    
    def create_issue(self, description: str) -> Issue:
        """创建问题记录"""
        issue_id = f"ISSUE-{len(self.issues) + 1:03d}"
        issue = Issue(
            id=issue_id,
            description=description,
            status=Status.PENDING,
            created_at=datetime.now().isoformat()
        )
        self.issues[issue_id] = issue
        print(f"📝 创建问题：{issue_id} - {description}")
        return issue
    
    def mark_fixed(self, issue_id: str) -> bool:
        """标记问题已修复"""
        if issue_id not in self.issues:
            print(f"❌ 问题不存在：{issue_id}")
            return False
        
        issue = self.issues[issue_id]
        issue.status = Status.FIXED
        issue.fixed_at = datetime.now().isoformat()
        print(f"🔧 修复问题：{issue_id}")
        return True
    
    def verify_fix(self, issue_id: str, checks: List[callable]) -> VerificationResult:
        """验证修复"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        if issue_id not in self.issues:
            return VerificationResult(
                success=False,
                issue_id=issue_id,
                checks_passed=0,
                checks_total=0,
                elapsed_ms=0,
                timestamp=timestamp
            )
        
        issue = self.issues[issue_id]
        checks_passed = 0
        
        print(f"\n🔍 验证修复：{issue_id}")
        print("-" * 50)
        
        for i, check in enumerate(checks, 1):
            try:
                result = check()
                if result:
                    checks_passed += 1
                    print(f"   ✓ 检查 {i}: 通过")
                else:
                    print(f"   ✗ 检查 {i}: 失败")
            except Exception as e:
                print(f"   ✗ 检查 {i}: 异常 - {e}")
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # 更新状态
        if checks_passed == len(checks):
            issue.status = Status.VERIFIED
            issue.verified_at = timestamp
            print(f"\n✅ 验证通过：{issue_id}")
        else:
            issue.status = Status.FAILED
            print(f"\n❌ 验证失败：{issue_id}")
        
        result = VerificationResult(
            success=(checks_passed == len(checks)),
            issue_id=issue_id,
            checks_passed=checks_passed,
            checks_total=len(checks),
            elapsed_ms=elapsed_ms,
            timestamp=timestamp
        )
        
        self.verification_history.append(result)
        return result
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.issues)
        by_status = {}
        for status in Status:
            by_status[status.value] = sum(
                1 for i in self.issues.values() if i.status == status
            )
        
        return {
            "total_issues": total,
            "by_status": by_status,
            "verification_count": len(self.verification_history)
        }


# ========== 测试检查函数 ==========

def check_function_exists() -> bool:
    """检查 1: 函数存在"""
    time.sleep(0.01)
    return True


def check_output_correct() -> bool:
    """检查 2: 输出正确"""
    time.sleep(0.01)
    return True


def check_performance_ok() -> bool:
    """检查 3: 性能达标"""
    time.sleep(0.01)
    return True


def check_edge_cases() -> bool:
    """检查 4: 边界情况"""
    time.sleep(0.01)
    return True


# ========== 测试流程 ==========

def run_verification_test():
    """运行验证测试"""
    print("=" * 60)
    print("🔍 新测试 - 验证修复")
    print("=" * 60)
    
    verifier = FixVerifier()
    results = []
    
    # 创建问题
    print("\n📋 创建问题记录")
    print("-" * 60)
    issue1 = verifier.create_issue("登录功能异常")
    issue2 = verifier.create_issue("数据导出失败")
    issue3 = verifier.create_issue("界面渲染错误")
    
    # 标记修复
    print("\n🔧 执行修复")
    print("-" * 60)
    verifier.mark_fixed(issue1.id)
    verifier.mark_fixed(issue2.id)
    verifier.mark_fixed(issue3.id)
    
    # 验证修复 1
    print("\n" + "=" * 60)
    print("验证 1: 登录功能")
    print("=" * 60)
    result1 = verifier.verify_fix(
        issue1.id,
        [check_function_exists, check_output_correct, check_performance_ok]
    )
    results.append(result1.success)
    
    # 验证修复 2
    print("\n" + "=" * 60)
    print("验证 2: 数据导出")
    print("=" * 60)
    result2 = verifier.verify_fix(
        issue2.id,
        [check_function_exists, check_output_correct, check_edge_cases]
    )
    results.append(result2.success)
    
    # 验证修复 3 (模拟失败)
    print("\n" + "=" * 60)
    print("验证 3: 界面渲染 (模拟部分失败)")
    print("=" * 60)
    
    def failing_check() -> bool:
        time.sleep(0.01)
        return False
    
    result3 = verifier.verify_fix(
        issue3.id,
        [check_function_exists, failing_check, check_performance_ok]
    )
    results.append(result3.success)
    
    # 显示统计
    print("\n" + "=" * 60)
    print("📊 验证统计")
    print("=" * 60)
    stats = verifier.get_stats()
    print(f"   总问题数：{stats['total_issues']}")
    print(f"   按状态分布:")
    for status, count in stats['by_status'].items():
        print(f"     - {status}: {count}")
    print(f"   验证次数：{stats['verification_count']}")
    
    # 验证历史
    print("\n📜 验证历史")
    print("-" * 60)
    for i, result in enumerate(verifier.verification_history, 1):
        status = "✅" if result.success else "❌"
        print(f"   {i}. {result.issue_id}: {status} "
              f"({result.checks_passed}/{result.checks_total}) "
              f"{result.elapsed_ms:.2f}ms")
    
    # 最终结果
    print("\n" + "=" * 60)
    print("📋 最终测试结果")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"   通过验证：{passed}/{total}")
    print(f"   成功率：{success_rate:.1f}%")
    print(f"   最终状态：{'✅ 完成' if passed >= total - 1 else '⚠️ 需复查'}")
    print("=" * 60)
    
    return passed >= total - 1  # 允许一个失败


if __name__ == "__main__":
    success = run_verification_test()
    exit(0 if success else 1)
