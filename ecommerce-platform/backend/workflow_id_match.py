"""
方案 C 测试 3 - 增强工作流 ID 匹配
测试工作流 ID 的生成、验证和匹配功能
"""
import re
import uuid
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class IDFormat(Enum):
    """ID 格式枚举"""
    UUID = "uuid"
    TIMESTAMP = "timestamp"
    HASH = "hash"
    COMPOSITE = "composite"


@dataclass
class WorkflowID:
    """工作流 ID"""
    id: str
    format: IDFormat
    created_at: str
    checksum: str
    metadata: Dict = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证 ID 有效性"""
        return bool(self.id and len(self.id) > 0)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "format": self.format.value,
            "created_at": self.created_at,
            "checksum": self.checksum,
            "metadata": self.metadata
        }


@dataclass
class MatchResult:
    """匹配结果"""
    matched: bool
    confidence: float  # 0-1 置信度
    workflow_id: Optional[WorkflowID]
    match_type: str  # exact, partial, fuzzy
    elapsed_ms: float
    message: str = ""


class WorkflowIDGenerator:
    """工作流 ID 生成器"""
    
    def __init__(self, prefix: str = "wf"):
        self.prefix = prefix
        self.generated_ids: List[str] = []
    
    def generate_uuid(self) -> str:
        """生成 UUID 格式 ID"""
        uid = str(uuid.uuid4()).replace("-", "")[:8]
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        workflow_id = f"{self.prefix}-{timestamp}-{uid}"
        self.generated_ids.append(workflow_id)
        return workflow_id
    
    def generate_timestamp(self) -> str:
        """生成时间戳格式 ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        workflow_id = f"{self.prefix}-{timestamp}"
        self.generated_ids.append(workflow_id)
        return workflow_id
    
    def generate_hash(self, content: str) -> str:
        """生成哈希格式 ID"""
        hash_value = hashlib.md5(content.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        workflow_id = f"{self.prefix}-{timestamp}-{hash_value}"
        self.generated_ids.append(workflow_id)
        return workflow_id
    
    def generate_composite(self, user_id: str = "", project_id: str = "") -> str:
        """生成复合格式 ID"""
        uid = str(uuid.uuid4()).replace("-", "")[:6]
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        parts = [self.prefix, timestamp]
        if user_id:
            parts.append(user_id[:8])
        if project_id:
            parts.append(project_id[:6])
        parts.append(uid)
        
        workflow_id = "-".join(parts)
        self.generated_ids.append(workflow_id)
        return workflow_id
    
    def generate(self, format: IDFormat = IDFormat.COMPOSITE, **kwargs) -> WorkflowID:
        """生成工作流 ID"""
        timestamp = datetime.now().isoformat()
        
        if format == IDFormat.UUID:
            id_value = self.generate_uuid()
        elif format == IDFormat.TIMESTAMP:
            id_value = self.generate_timestamp()
        elif format == IDFormat.HASH:
            content = kwargs.get("content", str(time.time()))
            id_value = self.generate_hash(content)
        else:  # COMPOSITE
            user_id = kwargs.get("user_id", "")
            project_id = kwargs.get("project_id", "")
            id_value = self.generate_composite(user_id, project_id)
        
        checksum = hashlib.sha256(id_value.encode()).hexdigest()[:16]
        
        return WorkflowID(
            id=id_value,
            format=format,
            created_at=timestamp,
            checksum=checksum,
            metadata=kwargs
        )


class WorkflowIDMatcher:
    """工作流 ID 匹配器"""
    
    def __init__(self):
        self.match_history: List[MatchResult] = []
        # ID 模式定义
        self.patterns = {
            "uuid": re.compile(r'^wf-\d{8}-\d{6}-[a-f0-9]{8}$'),
            "timestamp": re.compile(r'^wf-\d{14,}$'),
            "hash": re.compile(r'^wf-\d{8}-\d{6}-[a-f0-9]{12}$'),
            "composite": re.compile(r'^wf-\d{8}-\d{6}(-[a-zA-Z0-9]{1,8})*-[a-f0-9]{6}$'),
        }
    
    def match_exact(self, input_id: str, target_id: str) -> MatchResult:
        """精确匹配"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        matched = input_id == target_id
        elapsed_ms = (time.time() - start_time) * 1000
        
        result = MatchResult(
            matched=matched,
            confidence=1.0 if matched else 0.0,
            workflow_id=WorkflowID(id=target_id, format=IDFormat.COMPOSITE, 
                                  created_at=timestamp, checksum="") if matched else None,
            match_type="exact",
            elapsed_ms=elapsed_ms,
            message="精确匹配成功" if matched else "精确匹配失败"
        )
        
        self.match_history.append(result)
        return result
    
    def match_pattern(self, input_id: str) -> MatchResult:
        """模式匹配"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        matched_format = None
        for format_name, pattern in self.patterns.items():
            if pattern.match(input_id):
                matched_format = IDFormat(format_name)
                break
        
        elapsed_ms = (time.time() - start_time) * 1000
        matched = matched_format is not None
        
        result = MatchResult(
            matched=matched,
            confidence=1.0 if matched else 0.0,
            workflow_id=WorkflowID(id=input_id, format=matched_format or IDFormat.COMPOSITE,
                                  created_at=timestamp, checksum="") if matched else None,
            match_type="pattern",
            elapsed_ms=elapsed_ms,
            message=f"匹配格式：{matched_format.value}" if matched else "未匹配任何模式"
        )
        
        self.match_history.append(result)
        return result
    
    def match_fuzzy(self, input_id: str, candidates: List[str]) -> MatchResult:
        """模糊匹配"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        best_match = None
        best_confidence = 0.0
        
        for candidate in candidates:
            confidence = self._calculate_similarity(input_id, candidate)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = candidate
        
        elapsed_ms = (time.time() - start_time) * 1000
        matched = best_confidence > 0.7  # 70% 相似度阈值
        
        result = MatchResult(
            matched=matched,
            confidence=best_confidence,
            workflow_id=WorkflowID(id=best_match, format=IDFormat.COMPOSITE,
                                  created_at=timestamp, checksum="") if matched else None,
            match_type="fuzzy",
            elapsed_ms=elapsed_ms,
            message=f"相似度：{best_confidence:.2%}" if matched else "相似度不足"
        )
        
        self.match_history.append(result)
        return result
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度"""
        if s1 == s2:
            return 1.0
        
        # 基于共同字符的相似度
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # 计算最长公共子序列
        common = sum(1 for c in s1 if c in s2)
        similarity = (2 * common) / (len1 + len2)
        
        return min(similarity, 1.0)
    
    def validate_id(self, workflow_id: WorkflowID) -> bool:
        """验证工作流 ID"""
        if not workflow_id.id:
            return False
        
        # 验证格式
        if workflow_id.format == IDFormat.UUID:
            return bool(self.patterns["uuid"].match(workflow_id.id))
        elif workflow_id.format == IDFormat.TIMESTAMP:
            return bool(self.patterns["timestamp"].match(workflow_id.id))
        elif workflow_id.format == IDFormat.HASH:
            return bool(self.patterns["hash"].match(workflow_id.id))
        else:
            return bool(self.patterns["composite"].match(workflow_id.id))
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.match_history)
        matched = sum(1 for r in self.match_history if r.matched)
        
        by_type = {}
        for result in self.match_history:
            by_type[result.match_type] = by_type.get(result.match_type, 0) + 1
        
        avg_confidence = sum(r.confidence for r in self.match_history) / total if total > 0 else 0
        avg_elapsed = sum(r.elapsed_ms for r in self.match_history) / total if total > 0 else 0
        
        return {
            "total_matches": total,
            "matched": matched,
            "failed": total - matched,
            "success_rate": round(matched / total * 100, 2) if total > 0 else 0,
            "by_type": by_type,
            "avg_confidence": round(avg_confidence, 4),
            "avg_elapsed_ms": round(avg_elapsed, 4)
        }


# ========== 测试函数 ==========

def test_id_generation(generator: WorkflowIDGenerator) -> bool:
    """测试 1: ID 生成"""
    print("\n🔑 测试 ID 生成")
    print("-" * 60)
    
    formats = [
        (IDFormat.UUID, {}),
        (IDFormat.TIMESTAMP, {}),
        (IDFormat.HASH, {"content": "test_content"}),
        (IDFormat.COMPOSITE, {"user_id": "user123", "project_id": "proj456"}),
    ]
    
    all_success = True
    for format_type, kwargs in formats:
        workflow_id = generator.generate(format_type, **kwargs)
        is_valid = workflow_id.validate()
        
        print(f"   {format_type.value}: {workflow_id.id}")
        print(f"      校验和：{workflow_id.checksum}")
        print(f"      验证：{'✅' if is_valid else '❌'}")
        
        if not is_valid:
            all_success = False
    
    return all_success


def test_pattern_matching(matcher: WorkflowIDMatcher) -> bool:
    """测试 2: 模式匹配"""
    print("\n🔍 测试模式匹配")
    print("-" * 60)
    
    test_ids = [
        "wf-20260331-144618-abc12345",  # UUID 格式
        "wf-20260331144618",             # 时间戳格式
        "wf-20260331-144618-abc123def456",  # 哈希格式
        "wf-20260331-144618-user123-proj456-abc123",  # 复合格式
        "invalid_id",                    # 无效格式
    ]
    
    all_success = True
    for test_id in test_ids:
        result = matcher.match_pattern(test_id)
        print(f"   {test_id[:40]}...")
        print(f"      匹配：{'✅' if result.matched else '❌'}")
        print(f"      消息：{result.message}")
        
        if test_id != "invalid_id" and not result.matched:
            all_success = False
        elif test_id == "invalid_id" and result.matched:
            all_success = False
    
    return all_success


def test_exact_matching(matcher: WorkflowIDMatcher) -> bool:
    """测试 3: 精确匹配"""
    print("\n🎯 测试精确匹配")
    print("-" * 60)
    
    target_id = "wf-20260331-144618-abc12345"
    
    # 测试匹配成功
    result1 = matcher.match_exact(target_id, target_id)
    print(f"   相同 ID: {result1.matched}")
    print(f"   置信度：{result1.confidence:.2%}")
    
    # 测试匹配失败
    result2 = matcher.match_exact("wf-different-id", target_id)
    print(f"   不同 ID: {result2.matched}")
    print(f"   置信度：{result2.confidence:.2%}")
    
    return result1.matched and not result2.matched


def test_fuzzy_matching(matcher: WorkflowIDMatcher) -> bool:
    """测试 4: 模糊匹配"""
    print("\n🔎 测试模糊匹配")
    print("-" * 60)
    
    candidates = [
        "wf-20260331-144618-abc12345",
        "wf-20260331-144618-abc12346",
        "wf-20260331-144619-abc12345",
        "wf-20260330-144618-abc12345",
    ]
    
    # 测试相似 ID
    result1 = matcher.match_fuzzy("wf-20260331-144618-abc12345", candidates)
    print(f"   输入：wf-20260331-144618-abc12345")
    print(f"   匹配：{result1.matched}")
    print(f"   置信度：{result1.confidence:.2%}")
    print(f"   结果：{result1.workflow_id.id if result1.workflow_id else 'None'}")
    
    # 测试部分相似
    result2 = matcher.match_fuzzy("wf-20260331-144618-xyz99999", candidates)
    print(f"\n   输入：wf-20260331-144618-xyz99999")
    print(f"   匹配：{result2.matched}")
    print(f"   置信度：{result2.confidence:.2%}")
    
    return result1.matched and result1.confidence > 0.9


def test_id_validation(generator: WorkflowIDGenerator, matcher: WorkflowIDMatcher) -> bool:
    """测试 5: ID 验证"""
    print("\n✓ 测试 ID 验证")
    print("-" * 60)
    
    # 生成有效 ID
    valid_id = generator.generate(IDFormat.COMPOSITE)
    is_valid = matcher.validate_id(valid_id)
    print(f"   有效 ID: {valid_id.id}")
    print(f"   验证：{'✅' if is_valid else '❌'}")
    
    # 测试无效 ID
    invalid_id = WorkflowID(
        id="invalid",
        format=IDFormat.COMPOSITE,
        created_at=datetime.now().isoformat(),
        checksum=""
    )
    is_invalid = not matcher.validate_id(invalid_id)
    print(f"   无效 ID: {invalid_id.id}")
    print(f"   验证：{'✅' if is_invalid else '❌'} (应无效)")
    
    return is_valid and is_invalid


# ========== 主流程 ==========

def run_workflow_id_test():
    """运行工作流 ID 匹配测试"""
    print("=" * 60)
    print("📋 方案 C 测试 3 - 增强工作流 ID 匹配")
    print("=" * 60)
    
    # 初始化
    generator = WorkflowIDGenerator(prefix="wf")
    matcher = WorkflowIDMatcher()
    results = []
    
    # 测试 1: ID 生成
    print("\n" + "=" * 60)
    print("测试 1/5: ID 生成")
    print("=" * 60)
    result1 = test_id_generation(generator)
    results.append(result1)
    
    # 测试 2: 模式匹配
    print("\n" + "=" * 60)
    print("测试 2/5: 模式匹配")
    print("=" * 60)
    result2 = test_pattern_matching(matcher)
    results.append(result2)
    
    # 测试 3: 精确匹配
    print("\n" + "=" * 60)
    print("测试 3/5: 精确匹配")
    print("=" * 60)
    result3 = test_exact_matching(matcher)
    results.append(result3)
    
    # 测试 4: 模糊匹配
    print("\n" + "=" * 60)
    print("测试 4/5: 模糊匹配")
    print("=" * 60)
    result4 = test_fuzzy_matching(matcher)
    results.append(result4)
    
    # 测试 5: ID 验证
    print("\n" + "=" * 60)
    print("测试 5/5: ID 验证")
    print("=" * 60)
    result5 = test_id_validation(generator, matcher)
    results.append(result5)
    
    # 显示统计
    print("\n📊 匹配统计")
    print("-" * 60)
    stats = matcher.get_stats()
    print(f"   总匹配数：{stats['total_matches']}")
    print(f"   成功：{stats['matched']}")
    print(f"   失败：{stats['failed']}")
    print(f"   成功率：{stats['success_rate']}%")
    print(f"   平均置信度：{stats['avg_confidence']:.2%}")
    print(f"   平均耗时：{stats['avg_elapsed_ms']:.4f}ms")
    print(f"   按类型：{stats['by_type']}")
    
    # 最终结果
    print("\n" + "=" * 60)
    print("📋 最终测试结果")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"   通过测试：{passed}/{total}")
    print(f"   成功率：{success_rate:.1f}%")
    
    all_passed = passed == total
    print(f"   最终状态：{'✅ 全部通过' if all_passed else '⚠️ 部分失败'}")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_workflow_id_test()
    exit(0 if success else 1)
