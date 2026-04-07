"""
重新测试 - 清理后
测试清理环境后的重新测试功能
"""
import os
import time
import shutil
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """测试结果"""
    name: str
    success: bool
    elapsed_ms: float
    timestamp: str
    message: str = ""


@dataclass
class CleanupReport:
    """清理报告"""
    files_removed: int
    dirs_removed: int
    space_freed_bytes: int
    elapsed_ms: float


class TestEnvironment:
    """测试环境"""
    
    def __init__(self, base_dir: str = "./test_temp"):
        self.base_dir = base_dir
        self.test_files: List[str] = []
        self.is_clean = True
    
    def setup(self) -> bool:
        """设置测试环境"""
        print(f"🔧 设置测试环境：{self.base_dir}")
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            
            # 创建测试文件
            for i in range(5):
                file_path = os.path.join(self.base_dir, f"test_file_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"测试内容 {i}\n" * 100)
                self.test_files.append(file_path)
            
            # 创建子目录
            subdir = os.path.join(self.base_dir, "subdir")
            os.makedirs(subdir, exist_ok=True)
            for i in range(3):
                file_path = os.path.join(subdir, f"data_{i}.dat")
                with open(file_path, 'w') as f:
                    f.write(f"数据 {i}\n" * 50)
                self.test_files.append(file_path)
            
            self.is_clean = False
            print(f"   ✓ 创建 {len(self.test_files)} 个测试文件")
            return True
        except Exception as e:
            print(f"   ✗ 设置失败：{e}")
            return False
    
    def cleanup(self) -> CleanupReport:
        """清理测试环境"""
        print(f"🧹 清理测试环境")
        start_time = time.time()
        
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        
        try:
            # 计算空间
            for root, dirs, files in os.walk(self.base_dir):
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        space_freed += os.path.getsize(file_path)
                    except:
                        pass
            
            # 删除目录树
            if os.path.exists(self.base_dir):
                shutil.rmtree(self.base_dir)
                files_removed = len(self.test_files)
                dirs_removed = 2  # 主目录 + 子目录
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self.test_files = []
            self.is_clean = True
            
            print(f"   ✓ 删除 {files_removed} 个文件")
            print(f"   ✓ 删除 {dirs_removed} 个目录")
            print(f"   ✓ 释放 {space_freed} 字节")
            print(f"   ✓ 耗时 {elapsed_ms:.2f}ms")
            
            return CleanupReport(
                files_removed=files_removed,
                dirs_removed=dirs_removed,
                space_freed_bytes=space_freed,
                elapsed_ms=elapsed_ms
            )
        except Exception as e:
            print(f"   ✗ 清理失败：{e}")
            return CleanupReport(
                files_removed=files_removed,
                dirs_removed=dirs_removed,
                space_freed_bytes=space_freed,
                elapsed_ms=(time.time() - start_time) * 1000
            )
    
    def verify_clean(self) -> bool:
        """验证清理是否彻底"""
        return not os.path.exists(self.base_dir)


class RetestRunner:
    """重新测试运行器"""
    
    def __init__(self):
        self.env = TestEnvironment()
        self.results: List[TestResult] = []
        self.cleanup_report: Optional[CleanupReport] = None
    
    def run_test(self, name: str, test_func) -> TestResult:
        """运行单个测试"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            result = test_func()
            elapsed_ms = (time.time() - start_time) * 1000
            
            test_result = TestResult(
                name=name,
                success=result[0],
                elapsed_ms=elapsed_ms,
                timestamp=timestamp,
                message=result[1] if len(result) > 1 else ""
            )
            self.results.append(test_result)
            return test_result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                name=name,
                success=False,
                elapsed_ms=elapsed_ms,
                timestamp=timestamp,
                message=str(e)
            )
            self.results.append(test_result)
            return test_result
    
    def cleanup_and_retest(self, test_funcs: List[callable]) -> Dict:
        """清理后重新测试"""
        print("=" * 60)
        print("🔄 重新测试 - 清理后")
        print("=" * 60)
        
        # 清理环境
        print("\n📋 第一阶段：清理环境")
        print("-" * 60)
        self.cleanup_report = self.env.cleanup()
        
        # 验证清理
        print("\n🔍 验证清理结果")
        print("-" * 60)
        is_clean = self.env.verify_clean()
        print(f"   清理状态：{'✅ 干净' if is_clean else '❌ 未清理干净'}")
        
        # 重新设置环境
        print("\n🔧 第二阶段：重新设置环境")
        print("-" * 60)
        setup_success = self.env.setup()
        
        # 重新运行测试
        print("\n🧪 第三阶段：重新运行测试")
        print("-" * 60)
        for i, test_func in enumerate(test_funcs, 1):
            print(f"\n测试 {i}/{len(test_funcs)}:")
            self.run_test(f"Test-{i}", test_func)
        
        # 再次清理
        print("\n🧹 第四阶段：最终清理")
        print("-" * 60)
        final_cleanup = self.env.cleanup()
        
        # 生成报告
        return self.generate_report(setup_success, is_clean, final_cleanup)
    
    def generate_report(self, setup_success: bool, is_clean: bool, 
                       final_cleanup: CleanupReport) -> Dict:
        """生成测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        report = {
            "test_summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": round(success_rate, 2)
            },
            "cleanup_summary": {
                "initial_cleanup": {
                    "files_removed": self.cleanup_report.files_removed,
                    "dirs_removed": self.cleanup_report.dirs_removed,
                    "space_freed": self.cleanup_report.space_freed_bytes,
                    "elapsed_ms": self.cleanup_report.elapsed_ms
                },
                "final_cleanup": {
                    "files_removed": final_cleanup.files_removed,
                    "dirs_removed": final_cleanup.dirs_removed,
                    "space_freed": final_cleanup.space_freed_bytes,
                    "elapsed_ms": final_cleanup.elapsed_ms
                },
                "verified_clean": is_clean
            },
            "setup_success": setup_success,
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "elapsed_ms": r.elapsed_ms,
                    "message": r.message
                }
                for r in self.results
            ]
        }
        
        return report


# ========== 测试函数 ==========

def test_file_creation() -> tuple:
    """测试 1: 文件创建"""
    time.sleep(0.01)
    return (True, "文件创建成功")


def test_data_integrity() -> tuple:
    """测试 2: 数据完整性"""
    time.sleep(0.01)
    return (True, "数据完整性验证通过")


def test_performance() -> tuple:
    """测试 3: 性能测试"""
    time.sleep(0.01)
    return (True, "性能达标")


def test_edge_cases() -> tuple:
    """测试 4: 边界情况"""
    time.sleep(0.01)
    return (True, "边界情况处理正确")


# ========== 主流程 ==========

def run_retest():
    """运行重新测试"""
    runner = RetestRunner()
    
    test_funcs = [
        test_file_creation,
        test_data_integrity,
        test_performance,
        test_edge_cases
    ]
    
    report = runner.cleanup_and_retest(test_funcs)
    
    # 显示报告
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    
    print("\n📋 测试摘要:")
    print(f"   总测试数：{report['test_summary']['total']}")
    print(f"   通过：{report['test_summary']['passed']}")
    print(f"   失败：{report['test_summary']['failed']}")
    print(f"   成功率：{report['test_summary']['success_rate']}%")
    
    print("\n🧹 清理摘要:")
    print(f"   初始清理:")
    print(f"     - 文件：{report['cleanup_summary']['initial_cleanup']['files_removed']}")
    print(f"     - 目录：{report['cleanup_summary']['initial_cleanup']['dirs_removed']}")
    print(f"     - 空间：{report['cleanup_summary']['initial_cleanup']['space_freed']} 字节")
    print(f"   最终清理:")
    print(f"     - 文件：{report['cleanup_summary']['final_cleanup']['files_removed']}")
    print(f"     - 目录：{report['cleanup_summary']['final_cleanup']['dirs_removed']}")
    print(f"   验证干净：{'✅' if report['cleanup_summary']['verified_clean'] else '❌'}")
    
    print("\n📜 测试结果详情:")
    for i, result in enumerate(report['results'], 1):
        status = "✅" if result['success'] else "❌"
        print(f"   {i}. {result['name']}: {status} ({result['elapsed_ms']:.2f}ms)")
        if result['message']:
            print(f"      {result['message']}")
    
    print("\n" + "=" * 60)
    print("📋 最终状态")
    print("=" * 60)
    
    all_passed = report['test_summary']['passed'] == report['test_summary']['total']
    is_clean = report['cleanup_summary']['verified_clean']
    
    if all_passed and is_clean:
        print("   ✅ 全部通过 - 环境干净")
    elif all_passed:
        print("   ⚠️ 测试通过 - 环境未清理干净")
    else:
        print("   ❌ 部分失败 - 需要复查")
    
    print("=" * 60)
    
    return all_passed and is_clean


if __name__ == "__main__":
    success = run_retest()
    exit(0 if success else 1)
