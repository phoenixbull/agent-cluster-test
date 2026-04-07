"""
方案 C 测试 - 文件复制
测试文件复制功能和性能
"""
import os
import sys
import time
import hashlib
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CopyResult:
    """复制结果"""
    success: bool
    source: str
    destination: str
    file_size: int
    elapsed_ms: float
    checksum: str
    timestamp: str
    error: str = ""


@dataclass
class CopyStats:
    """复制统计"""
    total_files: int
    copied_files: int
    failed_files: int
    total_bytes: int
    total_elapsed_ms: float
    avg_speed_mbps: float


class FileCopier:
    """文件复制器"""
    
    def __init__(self, buffer_size: int = 8192):
        self.buffer_size = buffer_size
        self.results: List[CopyResult] = []
    
    def calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和 (MD5)"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self.buffer_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def copy_file(self, source: str, destination: str) -> CopyResult:
        """复制单个文件"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # 获取源文件大小
            file_size = os.path.getsize(source)
            
            # 复制文件
            shutil.copy2(source, destination)
            
            # 验证复制
            source_checksum = self.calculate_checksum(source)
            dest_checksum = self.calculate_checksum(destination)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if source_checksum != dest_checksum:
                result = CopyResult(
                    success=False,
                    source=source,
                    destination=destination,
                    file_size=file_size,
                    elapsed_ms=elapsed_ms,
                    checksum=dest_checksum,
                    timestamp=timestamp,
                    error="校验和不匹配"
                )
            else:
                result = CopyResult(
                    success=True,
                    source=source,
                    destination=destination,
                    file_size=file_size,
                    elapsed_ms=elapsed_ms,
                    checksum=dest_checksum,
                    timestamp=timestamp
                )
            
            self.results.append(result)
            return result
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            result = CopyResult(
                success=False,
                source=source,
                destination=destination,
                file_size=0,
                elapsed_ms=elapsed_ms,
                checksum="",
                timestamp=timestamp,
                error=str(e)
            )
            self.results.append(result)
            return result
    
    def copy_directory(self, source_dir: str, dest_dir: str, 
                      pattern: str = "*") -> List[CopyResult]:
        """复制整个目录"""
        from pathlib import Path
        import fnmatch
        
        results = []
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob(pattern):
            if file_path.is_file():
                rel_path = file_path.relative_to(source_path)
                dest_path = Path(dest_dir) / rel_path
                
                result = self.copy_file(
                    str(file_path),
                    str(dest_path)
                )
                results.append(result)
        
        return results
    
    def get_stats(self) -> CopyStats:
        """获取统计信息"""
        total_files = len(self.results)
        copied_files = sum(1 for r in self.results if r.success)
        failed_files = total_files - copied_files
        total_bytes = sum(r.file_size for r in self.results if r.success)
        total_elapsed_ms = sum(r.elapsed_ms for r in self.results)
        
        # 计算平均速度 (MB/s)
        if total_elapsed_ms > 0:
            avg_speed_mbps = (total_bytes / (1024 * 1024)) / (total_elapsed_ms / 1000)
        else:
            avg_speed_mbps = 0
        
        return CopyStats(
            total_files=total_files,
            copied_files=copied_files,
            failed_files=failed_files,
            total_bytes=total_bytes,
            total_elapsed_ms=total_elapsed_ms,
            avg_speed_mbps=round(avg_speed_mbps, 2)
        )
    
    def clear_results(self):
        """清空结果"""
        self.results = []


def verify_directory_copy(source_dir: str, dest_dir: str) -> Tuple[bool, int, int]:
    """验证目录复制结果"""
    source_files = set()
    dest_files = set()
    
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), source_dir)
            source_files.add(rel_path)
    
    for root, dirs, files in os.walk(dest_dir):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), dest_dir)
            dest_files.add(rel_path)
    
    missing = source_files - dest_files
    extra = dest_files - source_files
    
    return (len(missing) == 0 and len(extra) == 0, len(missing), len(extra))


class TestEnvironment:
    """测试环境"""
    
    def __init__(self, base_dir: str = "./copy_test"):
        self.base_dir = base_dir
        self.source_dir = os.path.join(base_dir, "source")
        self.dest_dir = os.path.join(base_dir, "destination")
    
    def setup(self, file_count: int = 10, file_size: int = 1024) -> List[str]:
        """设置测试环境"""
        print(f"🔧 设置测试环境：{self.base_dir}")
        
        # 创建目录
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.dest_dir, exist_ok=True)
        
        created_files = []
        
        # 创建测试文件
        for i in range(file_count):
            file_path = os.path.join(self.source_dir, f"test_file_{i}.dat")
            content = os.urandom(file_size)
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            created_files.append(file_path)
        
        # 创建子目录和文件
        subdir = os.path.join(self.source_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        for i in range(3):
            file_path = os.path.join(subdir, f"data_{i}.bin")
            content = os.urandom(file_size * 2)
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            created_files.append(file_path)
        
        print(f"   ✓ 创建 {len(created_files)} 个测试文件")
        print(f"   ✓ 每个文件大小：{file_size} 字节")
        
        return created_files
    
    def cleanup(self):
        """清理测试环境"""
        print(f"🧹 清理测试环境")
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        print(f"   ✓ 已删除 {self.base_dir}")
    
    def verify_copy(self) -> Tuple[bool, int, int]:
        """验证复制结果"""
        source_files = set()
        dest_files = set()
        
        for root, dirs, files in os.walk(self.source_dir):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), self.source_dir)
                source_files.add(rel_path)
        
        for root, dirs, files in os.walk(self.dest_dir):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), self.dest_dir)
                dest_files.add(rel_path)
        
        missing = source_files - dest_files
        extra = dest_files - source_files
        
        return (
            len(missing) == 0 and len(extra) == 0,
            len(missing),
            len(extra)
        )


# ========== 测试函数 ==========

def test_single_file_copy(copier: FileCopier, source: str, dest: str) -> bool:
    """测试 1: 单文件复制"""
    print(f"\n📄 测试单文件复制")
    print(f"   源：{source}")
    print(f"   目标：{dest}")
    
    result = copier.copy_file(source, dest)
    
    print(f"   大小：{result.file_size} 字节")
    print(f"   耗时：{result.elapsed_ms:.2f}ms")
    print(f"   校验和：{result.checksum[:16]}...")
    print(f"   状态：{'✅ 成功' if result.success else '❌ 失败'}")
    
    return result.success


def test_directory_copy(copier: FileCopier, source_dir: str, dest_dir: str) -> bool:
    """测试 2: 目录复制"""
    print(f"\n📁 测试目录复制")
    print(f"   源：{source_dir}")
    print(f"   目标：{dest_dir}")
    
    results = copier.copy_directory(source_dir, dest_dir)
    
    success_count = sum(1 for r in results if r.success)
    total_bytes = sum(r.file_size for r in results if r.success)
    total_time = sum(r.elapsed_ms for r in results)
    
    print(f"   文件数：{success_count}/{len(results)}")
    print(f"   总大小：{total_bytes} 字节")
    print(f"   总耗时：{total_time:.2f}ms")
    print(f"   状态：{'✅ 成功' if success_count == len(results) else '❌ 失败'}")
    
    return success_count == len(results)


def test_large_file_copy(copier: FileCopier, source: str, dest: str) -> bool:
    """测试 3: 大文件复制"""
    print(f"\n📦 测试大文件复制 (1MB)")
    
    # 创建大文件
    with open(source, "wb") as f:
        f.write(os.urandom(1024 * 1024))  # 1MB
    
    result = copier.copy_file(source, dest)
    
    print(f"   大小：{result.file_size / 1024:.2f} KB")
    print(f"   耗时：{result.elapsed_ms:.2f}ms")
    print(f"   速度：{result.file_size / (result.elapsed_ms / 1000) / 1024 / 1024:.2f} MB/s")
    print(f"   状态：{'✅ 成功' if result.success else '❌ 失败'}")
    
    return result.success


def test_verify_integrity(copier: FileCopier, source: str, dest: str) -> bool:
    """测试 4: 完整性验证"""
    print(f"\n🔍 测试完整性验证")
    
    # 计算校验和
    source_checksum = copier.calculate_checksum(source)
    dest_checksum = copier.calculate_checksum(dest)
    
    match = source_checksum == dest_checksum
    
    print(f"   源校验和：{source_checksum[:32]}...")
    print(f"   目标校验和：{dest_checksum[:32]}...")
    print(f"   匹配：{'✅ 是' if match else '❌ 否'}")
    
    return match


# ========== 主流程 ==========

def run_copy_test():
    """运行文件复制测试"""
    print("=" * 60)
    print("📋 方案 C 测试 - 文件复制")
    print("=" * 60)
    
    # 初始化
    copier = FileCopier(buffer_size=8192)
    env = TestEnvironment()
    results = []
    
    try:
        # 设置环境
        print("\n🔧 第一阶段：设置测试环境")
        print("-" * 60)
        env.setup(file_count=10, file_size=1024)
        
        # 测试 1: 单文件复制
        print("\n" + "=" * 60)
        print("测试 1/4: 单文件复制")
        print("=" * 60)
        source_file = os.path.join(env.source_dir, "test_file_0.dat")
        dest_file = os.path.join(env.dest_dir, "copy_0.dat")
        result1 = test_single_file_copy(copier, source_file, dest_file)
        results.append(result1)
        
        # 测试 2: 目录复制 (使用独立的目标目录)
        print("\n" + "=" * 60)
        print("测试 2/4: 目录复制")
        print("=" * 60)
        dir_dest = os.path.join(env.base_dir, "dest_dir")
        if os.path.exists(dir_dest):
            shutil.rmtree(dir_dest)
        os.makedirs(dir_dest)
        copier.clear_results()
        result2 = test_directory_copy(copier, env.source_dir, dir_dest)
        results.append(result2)
        
        # 测试 3: 大文件复制 (使用独立文件，不影响源目录)
        print("\n" + "=" * 60)
        print("测试 3/4: 大文件复制")
        print("=" * 60)
        temp_source = os.path.join(env.base_dir, "temp_large.bin")
        temp_dest = os.path.join(env.base_dir, "temp_large_copy.bin")
        result3 = test_large_file_copy(copier, temp_source, temp_dest)
        results.append(result3)
        # 清理临时大文件
        if os.path.exists(temp_source):
            os.remove(temp_source)
        if os.path.exists(temp_dest):
            os.remove(temp_dest)
        
        # 测试 4: 完整性验证 (使用目录复制中的文件)
        print("\n" + "=" * 60)
        print("测试 4/4: 完整性验证")
        print("=" * 60)
        verify_source = os.path.join(env.source_dir, "test_file_0.dat")
        verify_dest = os.path.join(dir_dest, "test_file_0.dat")
        result4 = test_verify_integrity(copier, verify_source, verify_dest)
        results.append(result4)
        
        # 验证复制
        print("\n🔍 验证复制结果")
        print("-" * 60)
        # 只验证目录复制的结果
        dir_dest = os.path.join(env.base_dir, "dest_dir")
        is_valid, missing, extra = verify_directory_copy(env.source_dir, dir_dest)
        print(f"   文件匹配：{'✅' if is_valid else '❌'}")
        print(f"   缺失文件：{missing}")
        print(f"   多余文件：{extra}")
        
        # 显示统计
        print("\n📊 复制统计")
        print("-" * 60)
        stats = copier.get_stats()
        print(f"   总文件数：{stats.total_files}")
        print(f"   成功：{stats.copied_files}")
        print(f"   失败：{stats.failed_files}")
        print(f"   总数据量：{stats.total_bytes} 字节")
        print(f"   总耗时：{stats.total_elapsed_ms:.2f}ms")
        print(f"   平均速度：{stats.avg_speed_mbps:.2f} MB/s")
        
        # 最终结果
        print("\n" + "=" * 60)
        print("📋 最终测试结果")
        print("=" * 60)
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"   通过测试：{passed}/{total}")
        print(f"   成功率：{success_rate:.1f}%")
        print(f"   验证状态：{'✅' if is_valid else '❌'}")
        
        all_passed = (passed == total) and is_valid
        print(f"   最终状态：{'✅ 全部通过' if all_passed else '⚠️ 部分失败'}")
        print("=" * 60)
        
        return all_passed
        
    finally:
        # 清理环境
        print("\n🧹 清理测试环境")
        print("-" * 60)
        env.cleanup()


if __name__ == "__main__":
    success = run_copy_test()
    exit(0 if success else 1)
