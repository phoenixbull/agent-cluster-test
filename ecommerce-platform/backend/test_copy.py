"""
文件复制 - 单元测试
"""
import unittest
import os
import tempfile
import shutil
from file_copy_test import FileCopier, CopyResult, TestEnvironment


class TestFileCopier(unittest.TestCase):
    """文件复制器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.copier = FileCopier()
        
        # 创建测试文件
        self.source_file = os.path.join(self.temp_dir, "source.txt")
        self.dest_file = os.path.join(self.temp_dir, "dest.txt")
        
        with open(self.source_file, "w") as f:
            f.write("测试内容\n" * 100)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_copy_file_success(self):
        """测试文件复制成功"""
        result = self.copier.copy_file(self.source_file, self.dest_file)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(self.dest_file))
        self.assertEqual(result.source, self.source_file)
        self.assertEqual(result.destination, self.dest_file)
        self.assertGreater(result.file_size, 0)
        self.assertGreater(result.elapsed_ms, 0)
        self.assertTrue(result.checksum)
    
    def test_copy_file_checksum(self):
        """测试校验和验证"""
        result = self.copier.copy_file(self.source_file, self.dest_file)
        
        source_checksum = self.copier.calculate_checksum(self.source_file)
        dest_checksum = self.copier.calculate_checksum(self.dest_file)
        
        self.assertEqual(source_checksum, dest_checksum)
        self.assertEqual(result.checksum, dest_checksum)
    
    def test_copy_file_not_found(self):
        """测试文件不存在"""
        result = self.copier.copy_file(
            os.path.join(self.temp_dir, "nonexistent.txt"),
            self.dest_file
        )
        
        self.assertFalse(result.success)
        self.assertTrue(len(result.error) > 0)  # 只要有错误信息即可
    
    def test_copy_directory(self):
        """测试目录复制"""
        # 创建子目录
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir)
        
        for i in range(3):
            with open(os.path.join(subdir, f"file_{i}.txt"), "w") as f:
                f.write(f"内容 {i}")
        
        dest_dir = os.path.join(self.temp_dir, "dest")
        results = self.copier.copy_directory(subdir, dest_dir)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))
    
    def test_get_stats(self):
        """测试统计信息"""
        # 复制多个文件
        for i in range(3):
            dest = os.path.join(self.temp_dir, f"copy_{i}.txt")
            self.copier.copy_file(self.source_file, dest)
        
        stats = self.copier.get_stats()
        
        self.assertEqual(stats.total_files, 3)
        self.assertEqual(stats.copied_files, 3)
        self.assertEqual(stats.failed_files, 0)
        self.assertGreater(stats.total_bytes, 0)
        self.assertGreater(stats.total_elapsed_ms, 0)
    
    def test_clear_results(self):
        """测试清空结果"""
        self.copier.copy_file(self.source_file, self.dest_file)
        self.assertEqual(len(self.copier.results), 1)
        
        self.copier.clear_results()
        self.assertEqual(len(self.copier.results), 0)
    
    def test_calculate_checksum(self):
        """测试校验和计算"""
        checksum1 = self.copier.calculate_checksum(self.source_file)
        checksum2 = self.copier.calculate_checksum(self.source_file)
        
        self.assertEqual(checksum1, checksum2)
        self.assertEqual(len(checksum1), 32)  # MD5 长度为 32
    
    def test_copy_large_file(self):
        """测试大文件复制"""
        large_file = os.path.join(self.temp_dir, "large.bin")
        large_dest = os.path.join(self.temp_dir, "large_copy.bin")
        
        # 创建 1MB 文件
        with open(large_file, "wb") as f:
            f.write(os.urandom(1024 * 1024))
        
        result = self.copier.copy_file(large_file, large_dest)
        
        self.assertTrue(result.success)
        self.assertEqual(result.file_size, 1024 * 1024)
        self.assertGreater(result.elapsed_ms, 0)


class TestTestEnvironment(unittest.TestCase):
    """测试环境测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.env = TestEnvironment(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        self.env.cleanup()
    
    def test_setup(self):
        """测试环境设置"""
        files = self.env.setup(file_count=5, file_size=512)
        
        self.assertEqual(len(files), 8)  # 5 + 3 个子目录文件
        self.assertTrue(os.path.exists(self.env.source_dir))
        self.assertTrue(os.path.exists(self.env.dest_dir))
    
    def test_cleanup(self):
        """测试环境清理"""
        self.env.setup()
        self.env.cleanup()
        
        self.assertFalse(os.path.exists(self.temp_dir))
    
    def test_verify_copy_success(self):
        """测试验证复制成功"""
        self.env.setup()
        
        # 手动复制文件
        import shutil
        for root, dirs, files in os.walk(self.env.source_dir):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, self.env.source_dir)
                dest = os.path.join(self.env.dest_dir, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
        
        is_valid, missing, extra = self.env.verify_copy()
        
        self.assertTrue(is_valid)
        self.assertEqual(missing, 0)
        self.assertEqual(extra, 0)


class TestCopyResult(unittest.TestCase):
    """复制结果测试"""
    
    def test_copy_result_creation(self):
        """测试复制结果创建"""
        result = CopyResult(
            success=True,
            source="/src/file.txt",
            destination="/dest/file.txt",
            file_size=1024,
            elapsed_ms=10.5,
            checksum="abc123",
            timestamp="2026-03-31T14:40:00"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.file_size, 1024)
        self.assertEqual(result.elapsed_ms, 10.5)
        self.assertEqual(result.checksum, "abc123")


if __name__ == "__main__":
    unittest.main()
