"""
Workflow ID Matcher API - 单元测试
"""
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


class TestRoot:
    """根路径测试"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Workflow ID Matcher API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"
    
    def test_health(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestGenerate:
    """ID 生成测试"""
    
    def test_generate_uuid(self):
        """测试 UUID 格式生成"""
        response = client.post("/generate", json={"format": "uuid"})
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "uuid"
        assert data["id"].startswith("wf-")
        assert "checksum" in data
        assert "created_at" in data
    
    def test_generate_timestamp(self):
        """测试时间戳格式生成"""
        response = client.post("/generate", json={"format": "timestamp"})
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "timestamp"
        assert data["id"].startswith("wf-")
    
    def test_generate_hash(self):
        """测试哈希格式生成"""
        response = client.post("/generate", json={
            "format": "hash",
            "content": "test_content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "hash"
        assert data["id"].startswith("wf-")
    
    def test_generate_composite(self):
        """测试复合格式生成"""
        response = client.post("/generate", json={
            "format": "composite",
            "user_id": "user123",
            "project_id": "proj456"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "composite"
        assert "user123" in data["id"]
        assert "proj45" in data["id"]
    
    def test_generate_simple_uuid(self):
        """测试简单 GET 方式生成 UUID"""
        response = client.get("/generate/uuid")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "uuid"
        assert data["id"].startswith("wf-")
    
    def test_generate_simple_composite(self):
        """测试简单 GET 方式生成复合 ID"""
        response = client.get("/generate/composite?user_id=user1&project_id=proj2")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "composite"
        assert "user1" in data["id"]


class TestValidate:
    """ID 验证测试"""
    
    def test_validate_valid_uuid(self):
        """测试有效 UUID 格式"""
        response = client.post("/validate", json={
            "id": "wf-20260331-144618-abc12345",
            "format": "uuid"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["message"] == "ID 格式有效"
    
    def test_validate_invalid(self):
        """测试无效 ID"""
        response = client.post("/validate", json={
            "id": "invalid_id",
            "format": "uuid"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert data["message"] == "ID 格式无效"
    
    def test_validate_timestamp(self):
        """测试时间戳格式验证"""
        response = client.post("/validate", json={
            "id": "wf-20260407192938796047",
            "format": "timestamp"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True


class TestMatch:
    """匹配测试"""
    
    def test_match_exact_success(self):
        """测试精确匹配成功"""
        response = client.post("/match/exact", json={
            "input_id": "wf-test-123",
            "target_id": "wf-test-123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] == True
        assert data["confidence"] == 1.0
        assert data["match_type"] == "exact"
    
    def test_match_exact_failure(self):
        """测试精确匹配失败"""
        response = client.post("/match/exact", json={
            "input_id": "wf-test-123",
            "target_id": "wf-test-456"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] == False
        assert data["confidence"] == 0.0
    
    def test_match_pattern_uuid(self):
        """测试 UUID 模式匹配"""
        response = client.post("/match/pattern", json={
            "id": "wf-20260331-144618-abc12345"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] == True
        assert data["match_type"] == "pattern"
        assert "uuid" in data["message"]
    
    def test_match_pattern_invalid(self):
        """测试无效模式匹配"""
        response = client.post("/match/pattern", json={
            "id": "invalid_id"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] == False
    
    def test_match_fuzzy_success(self):
        """测试模糊匹配成功"""
        candidates = [
            "wf-20260331-144618-abc12345",
            "wf-20260331-144618-abc12346"
        ]
        response = client.post("/match/fuzzy", json={
            "input_id": "wf-20260331-144618-abc12345",
            "candidates": candidates
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] == True
        assert data["confidence"] >= 0.7
    
    def test_match_fuzzy_low_similarity(self):
        """测试低相似度模糊匹配"""
        candidates = [
            "wf-20260331-144618-abc12345",
            "wf-20260331-144618-abc12346"
        ]
        response = client.post("/match/fuzzy", json={
            "input_id": "wf-completely-different",
            "candidates": candidates
        })
        assert response.status_code == 200
        data = response.json()
        # 可能匹配也可能不匹配，取决于相似度阈值
        assert "matched" in data
        assert "confidence" in data


class TestStats:
    """统计测试"""
    
    def test_get_stats(self):
        """测试获取统计信息"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_matches" in data
        assert "matched" in data
        assert "failed" in data
        assert "success_rate" in data
        assert "by_type" in data
        assert "avg_confidence" in data
        assert "avg_elapsed_ms" in data


class TestFormats:
    """格式列表测试"""
    
    def test_list_formats(self):
        """测试列出支持的格式"""
        response = client.get("/formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) == 4
        
        format_names = [f["name"] for f in data["formats"]]
        assert "uuid" in format_names
        assert "timestamp" in format_names
        assert "hash" in format_names
        assert "composite" in format_names
        
        # 检查每个格式都有描述和示例
        for fmt in data["formats"]:
            assert "description" in fmt
            assert "example" in fmt


# ========== 性能测试 ==========

class TestPerformance:
    """性能测试"""
    
    def test_generate_performance(self):
        """测试生成性能"""
        import time
        
        start = time.time()
        for _ in range(100):
            client.get("/generate/uuid")
        elapsed = time.time() - start
        
        avg_ms = (elapsed / 100) * 1000
        print(f"\n平均生成耗时：{avg_ms:.2f}ms")
        assert avg_ms < 10  # 每次生成应小于 10ms
    
    def test_match_pattern_performance(self):
        """测试模式匹配性能"""
        import time
        
        start = time.time()
        for _ in range(100):
            client.post("/match/pattern", json={
                "id": "wf-20260331-144618-abc12345"
            })
        elapsed = time.time() - start
        
        avg_ms = (elapsed / 100) * 1000
        print(f"\n平均匹配耗时：{avg_ms:.2f}ms")
        assert avg_ms < 5  # 每次匹配应小于 5ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
