#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
失败模式分类器
智能重试机制升级 - 步骤 1/5

细粒度分类 15+ 种失败原因，为后续重试策略提供依据
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


class FailureCategory(Enum):
    """失败原因大类"""
    PROMPT = "prompt"           # Prompt 相关
    MODEL = "model"             # 模型相关
    CODE = "code"               # 代码相关
    TEST = "test"               # 测试相关
    REVIEW = "review"           # 审查相关
    ENV = "env"                 # 环境相关
    MOBILE = "mobile"           # P3 新增：移动端特定


class FailureReason(Enum):
    """详细失败原因 (15+ 种)"""
    
    # ========== Prompt 相关 (3 种) ==========
    PROMPT_AMBIGUOUS = "prompt_ambiguous"         # 需求描述模糊
    PROMPT_INCOMPLETE = "prompt_incomplete"       # 上下文/信息缺失
    PROMPT_CONTRADICTORY = "prompt_contradictory" # 指令矛盾
    
    # ========== 模型相关 (3 种) ==========
    MODEL_HALLUCINATION = "model_hallucination"   # 模型幻觉 (捏造 API/函数)
    MODEL_TIMEOUT = "model_timeout"               # 模型超时
    MODEL_OUTPUT_INVALID = "model_output_invalid" # 输出格式错误
    
    # ========== 代码相关 (3 种) ==========
    CODE_SYNTAX_ERROR = "code_syntax_error"       # 语法错误
    CODE_LOGIC_ERROR = "code_logic_error"         # 逻辑错误
    CODE_IMPORT_ERROR = "code_import_error"       # 导入/依赖问题
    
    # ========== 测试相关 (2 种) ==========
    TEST_SYNTAX_ERROR = "test_syntax_error"       # 测试代码语法错误
    TEST_ASSERTION_FAILED = "test_assertion_failed" # 测试断言失败
    
    # ========== 审查相关 (3 种) ==========
    REVIEW_STYLE_ISSUE = "review_style_issue"     # 代码风格问题
    REVIEW_SECURITY_ISSUE = "review_security_issue" # 安全问题
    REVIEW_ARCHITECTURE_ISSUE = "review_architecture_issue" # 架构问题
    
    # ========== 环境相关 (2 种) ==========
    ENV_GIT_ERROR = "env_git_error"               # Git 操作失败
    ENV_TIMEOUT = "env_timeout"                   # 环境超时
    
    # ========== P3 新增：Native 移动端特定失败模式 ==========
    # iOS 相关
    IOS_BUILD_ERROR = "ios_build_error"           # Xcode 构建失败
    IOS_SIMULATOR_ERROR = "ios_simulator_error"   # 模拟器启动失败
    IOS_CERTIFICATE_ERROR = "ios_certificate_error" # 证书/签名问题
    
    # Android 相关
    ANDROID_BUILD_ERROR = "android_build_error"   # Gradle 构建失败
    ANDROID_EMULATOR_ERROR = "android_emulator_error" # 模拟器启动失败
    ANDROID_SDK_ERROR = "android_sdk_error"       # SDK 配置问题
    
    # 跨平台相关
    NATIVE_MODULE_ERROR = "native_module_error"   # 原生模块链接失败
    PLATFORM_SPECIFIC_BUG = "platform_specific_bug" # 平台特定 Bug


@dataclass
class FailureAnalysis:
    """失败分析结果"""
    reason: FailureReason
    category: FailureCategory
    confidence: float  # 置信度 0-1
    evidence: List[str]  # 证据 (错误信息片段)
    suggestion: str  # 重试建议
    severity: str  # low/medium/high/critical


class FailureClassifier:
    """失败模式分类器"""
    
    def __init__(self):
        # 关键词映射
        self.keyword_map = self._build_keyword_map()
        
        # 失败模式库
        self.patterns = self._load_failure_patterns()
    
    def _build_keyword_map(self) -> Dict[FailureReason, List[str]]:
        """构建关键词映射"""
        return {
            # Prompt 相关
            FailureReason.PROMPT_AMBIGUOUS: [
                "不理解", "不清楚", "模糊", "ambiguous", "unclear",
                "无法确定", "confused", "what do you mean"
            ],
            FailureReason.PROMPT_INCOMPLETE: [
                "缺少", "缺失", "没有提供", "incomplete", "missing",
                "need more", "please provide", "上下文"
            ],
            FailureReason.PROMPT_CONTRADICTORY: [
                "矛盾", "冲突", "contradict", "conflict",
                "inconsistent", "不一致"
            ],
            
            # 模型相关
            FailureReason.MODEL_HALLUCINATION: [
                "不存在的 API", "undefined", "not found",
                "没有这个函数", "捏造", "hallucinate"
            ],
            FailureReason.MODEL_TIMEOUT: [
                "超时", "timeout", "took too long",
                "exceeded time", "响应超时"
            ],
            FailureReason.MODEL_OUTPUT_INVALID: [
                "格式错误", "invalid format", "parse error",
                "JSON 错误", "schema validation"
            ],
            
            # 代码相关
            FailureReason.CODE_SYNTAX_ERROR: [
                "SyntaxError", "语法错误", "invalid syntax",
                "unexpected token", "indentation error"
            ],
            FailureReason.CODE_LOGIC_ERROR: [
                "逻辑错误", "logic error", "wrong result",
                "预期", "expected", "assertion", "返回值错误"
            ],
            FailureReason.CODE_IMPORT_ERROR: [
                "ImportError", "ModuleNotFoundError", "无法导入",
                "no module", "cannot import", "依赖"
            ],
            
            # 测试相关
            FailureReason.TEST_SYNTAX_ERROR: [
                "测试代码错误", "test syntax", "test file error"
            ],
            FailureReason.TEST_ASSERTION_FAILED: [
                "AssertionError", "断言失败", "test failed",
                "expected", "but got", "测试不通过"
            ],
            
            # 审查相关
            FailureReason.REVIEW_STYLE_ISSUE: [
                "代码风格", "style", "PEP8", "lint",
                "格式不规范", "命名不规范"
            ],
            FailureReason.REVIEW_SECURITY_ISSUE: [
                "安全", "security", "vulnerability",
                "注入", "injection", "XSS", "CSRF", "敏感"
            ],
            FailureReason.REVIEW_ARCHITECTURE_ISSUE: [
                "架构", "architecture", "设计模式",
                "耦合", "扩展性", "maintainability"
            ],
            
            # 环境相关
            FailureReason.ENV_GIT_ERROR: [
                "git", "commit", "push", "merge",
                "冲突", "conflict", "repository"
            ],
            FailureReason.ENV_TIMEOUT: [
                "环境超时", "environment timeout",
                "执行超时", "execution timeout"
            ],
            
            # ========== P3 新增：Native 移动端失败模式关键词 ==========
            # iOS 相关
            FailureReason.IOS_BUILD_ERROR: [
                "xcodebuild", "build failed", "compilation error",
                "Xcode 构建", " linker error", "bitcode"
            ],
            FailureReason.IOS_SIMULATOR_ERROR: [
                "simulator", "无法启动", "failed to launch",
                "device not found", "no such device"
            ],
            FailureReason.IOS_CERTIFICATE_ERROR: [
                "certificate", "provisioning", "signature",
                "签名", "证书", "code signing"
            ],
            
            # Android 相关
            FailureReason.ANDROID_BUILD_ERROR: [
                "gradle", "build failed", "compileSdkVersion",
                "SDK 未找到", "android studio", "R8"
            ],
            FailureReason.ANDROID_EMULATOR_ERROR: [
                "emulator", "adb", "device offline",
                "无法连接", "unauthorized device"
            ],
            FailureReason.ANDROID_SDK_ERROR: [
                "SDK not found", "ANDROID_HOME", "sdkmanager",
                "platform-tools", "build-tools"
            ],
            
            # 跨平台相关
            FailureReason.NATIVE_MODULE_ERROR: [
                "native module", "bridge", "RN 链接",
                "pod install", "cocoapods", "react-native link"
            ],
            FailureReason.PLATFORM_SPECIFIC_BUG: [
                "仅 iOS", "仅 Android", "platform specific",
                "平台差异", "兼容性", "compatibility"
            ],
        }
    
    def _load_failure_patterns(self) -> Dict[str, List[Dict]]:
        """加载失败模式 (正则表达式)"""
        return {
            "python_error": [
                {
                    "pattern": r"File \"(.+?)\", line (\d+)\n\s*(.+?)\n\s*\^?\s*\n?(.*)",
                    "reason": FailureReason.CODE_SYNTAX_ERROR,
                    "extract": ["file", "line", "code", "error"]
                },
                {
                    "pattern": r"(ImportError|ModuleNotFoundError): (.+)",
                    "reason": FailureReason.CODE_IMPORT_ERROR,
                    "extract": ["type", "message"]
                },
                {
                    "pattern": r"AssertionError: (.+)",
                    "reason": FailureReason.TEST_ASSERTION_FAILED,
                    "extract": ["message"]
                },
            ],
            "git_error": [
                {
                    "pattern": r"(error:|fatal:)\s*(.+)",
                    "reason": FailureReason.ENV_GIT_ERROR,
                    "extract": ["prefix", "message"]
                },
            ],
            "review_comment": [
                {
                    "pattern": r"(建议 | 推荐 | 应该|consider|should)\s*(.+)",
                    "reason": FailureReason.REVIEW_STYLE_ISSUE,
                    "extract": ["type", "suggestion"]
                },
            ],
        }
    
    def classify(self, error_message: str, context: Optional[Dict] = None) -> FailureAnalysis:
        """
        分类失败原因
        
        Args:
            error_message: 错误信息
            context: 额外上下文 (可选)
                - task_type: 任务类型
                - agent: 执行 Agent
                - files: 相关文件
                - previous_attempts: 历史尝试
        
        Returns:
            FailureAnalysis: 失败分析结果
        """
        error_lower = error_message.lower()
        
        # 1. 关键词匹配
        matches = self._match_keywords(error_lower)
        
        # 2. 正则模式匹配
        pattern_matches = self._match_patterns(error_message)
        
        # 3. 合并结果
        all_matches = matches + pattern_matches
        
        if not all_matches:
            # 无匹配 → 未知错误
            return FailureAnalysis(
                reason=FailureReason.MODEL_OUTPUT_INVALID,
                category=FailureCategory.MODEL,
                confidence=0.3,
                evidence=[error_message[:100]],
                suggestion="错误信息不明确，建议添加详细日志",
                severity="medium"
            )
        
        # 4. 选择置信度最高的
        best_match = max(all_matches, key=lambda x: x[2])
        reason, evidence, confidence = best_match
        
        # 5. 生成建议
        suggestion = self._generate_suggestion(reason, error_message)
        
        # 6. 评估严重程度
        severity = self._evaluate_severity(reason, confidence)
        
        return FailureAnalysis(
            reason=reason,
            category=self._get_category(reason),
            confidence=confidence,
            evidence=evidence,
            suggestion=suggestion,
            severity=severity
        )
    
    def _match_keywords(self, error_lower: str) -> List[Tuple[FailureReason, List[str], float]]:
        """关键词匹配"""
        matches = []
        
        for reason, keywords in self.keyword_map.items():
            matched_keywords = [kw for kw in keywords if kw in error_lower]
            if matched_keywords:
                # 置信度 = 匹配关键词数 / 总关键词数
                confidence = min(0.9, len(matched_keywords) / max(3, len(keywords)) * 0.8)
                matches.append((reason, matched_keywords, confidence))
        
        return matches
    
    def _match_patterns(self, error_message: str) -> List[Tuple[FailureReason, List[str], float]]:
        """正则模式匹配"""
        matches = []
        
        for pattern_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                match = re.search(pattern_info["pattern"], error_message, re.MULTILINE)
                if match:
                    groups = match.groups()
                    reason = pattern_info["reason"]
                    confidence = 0.85  # 正则匹配置信度较高
                    matches.append((reason, list(groups), confidence))
        
        return matches
    
    def _generate_suggestion(self, reason: FailureReason, error_message: str) -> str:
        """生成重试建议"""
        suggestions = {
            FailureReason.PROMPT_AMBIGUOUS: "请先澄清需求，明确输入/输出/约束条件",
            FailureReason.PROMPT_INCOMPLETE: "补充缺失的上下文信息（业务背景、技术栈、已有代码）",
            FailureReason.PROMPT_CONTRADICTORY: "检查需求是否有矛盾，统一指令",
            FailureReason.MODEL_HALLUCINATION: "验证 API/函数是否存在，提供文档链接",
            FailureReason.MODEL_TIMEOUT: "简化任务或增加超时时间",
            FailureReason.MODEL_OUTPUT_INVALID: "明确输出格式要求，提供示例",
            FailureReason.CODE_SYNTAX_ERROR: "检查语法错误，使用 linter 预检查",
            FailureReason.CODE_LOGIC_ERROR: "添加单元测试，逐步验证逻辑",
            FailureReason.CODE_IMPORT_ERROR: "检查依赖是否安装，导入路径是否正确",
            FailureReason.TEST_SYNTAX_ERROR: "修复测试代码语法错误",
            FailureReason.TEST_ASSERTION_FAILED: "分析断言失败原因，验证预期值",
            FailureReason.REVIEW_STYLE_ISSUE: "遵循代码规范，运行格式化工具",
            FailureReason.REVIEW_SECURITY_ISSUE: "修复安全漏洞，参考 OWASP 指南",
            FailureReason.REVIEW_ARCHITECTURE_ISSUE: "重新设计架构，降低耦合度",
            FailureReason.ENV_GIT_ERROR: "检查 Git 配置，解决冲突后重试",
            FailureReason.ENV_TIMEOUT: "优化执行效率或增加超时时间",
        }
        return suggestions.get(reason, "分析错误原因后重试")
    
    def _get_category(self, reason: FailureReason) -> FailureCategory:
        """获取失败大类"""
        category_map = {
            FailureReason.PROMPT_AMBIGUOUS: FailureCategory.PROMPT,
            FailureReason.PROMPT_INCOMPLETE: FailureCategory.PROMPT,
            FailureReason.PROMPT_CONTRADICTORY: FailureCategory.PROMPT,
            FailureReason.MODEL_HALLUCINATION: FailureCategory.MODEL,
            FailureReason.MODEL_TIMEOUT: FailureCategory.MODEL,
            FailureReason.MODEL_OUTPUT_INVALID: FailureCategory.MODEL,
            FailureReason.CODE_SYNTAX_ERROR: FailureCategory.CODE,
            FailureReason.CODE_LOGIC_ERROR: FailureCategory.CODE,
            FailureReason.CODE_IMPORT_ERROR: FailureCategory.CODE,
            FailureReason.TEST_SYNTAX_ERROR: FailureCategory.TEST,
            FailureReason.TEST_ASSERTION_FAILED: FailureCategory.TEST,
            FailureReason.REVIEW_STYLE_ISSUE: FailureCategory.REVIEW,
            FailureReason.REVIEW_SECURITY_ISSUE: FailureCategory.REVIEW,
            FailureReason.REVIEW_ARCHITECTURE_ISSUE: FailureCategory.REVIEW,
            FailureReason.ENV_GIT_ERROR: FailureCategory.ENV,
            FailureReason.ENV_TIMEOUT: FailureCategory.ENV,
        }
        return category_map.get(reason, FailureCategory.MODEL)
    
    def _evaluate_severity(self, reason: FailureReason, confidence: float) -> str:
        """评估严重程度"""
        # 高严重程度
        if reason in [FailureReason.REVIEW_SECURITY_ISSUE, FailureReason.CODE_LOGIC_ERROR]:
            return "high"
        
        # 中严重程度
        if reason in [FailureReason.CODE_SYNTAX_ERROR, FailureReason.TEST_ASSERTION_FAILED,
                      FailureReason.ENV_GIT_ERROR, FailureReason.MODEL_HALLUCINATION]:
            return "medium"
        
        # 低严重程度
        return "low"
    
    def batch_classify(self, errors: List[str]) -> Dict[str, int]:
        """批量分类，返回统计"""
        stats = {}
        for error in errors:
            analysis = self.classify(error)
            key = analysis.reason.value
            stats[key] = stats.get(key, 0) + 1
        return stats


# ========== 全局实例 ==========

_classifier: Optional[FailureClassifier] = None


def get_classifier() -> FailureClassifier:
    """获取分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = FailureClassifier()
    return _classifier


def classify_failure(error_message: str, context: Optional[Dict] = None) -> FailureAnalysis:
    """便捷函数：分类失败原因"""
    return get_classifier().classify(error_message, context)


# ========== 测试 ==========

if __name__ == "__main__":
    classifier = FailureClassifier()
    
    # 测试用例
    test_cases = [
        ("SyntaxError: invalid syntax", FailureReason.CODE_SYNTAX_ERROR),
        ("ImportError: No module named 'requests'", FailureReason.CODE_IMPORT_ERROR),
        ("AssertionError: Expected 2 but got 3", FailureReason.TEST_ASSERTION_FAILED),
        ("fatal: merge conflict detected", FailureReason.ENV_GIT_ERROR),
        ("不理解你的需求，请澄清", FailureReason.PROMPT_AMBIGUOUS),
        ("安全漏洞：存在 SQL 注入风险", FailureReason.REVIEW_SECURITY_ISSUE),
    ]
    
    print("🧪 失败分类器测试:\n")
    for error, expected in test_cases:
        result = classifier.classify(error)
        status = "✅" if result.reason == expected else "❌"
        print(f"{status} {error[:40]:<40} → {result.reason.value}")
        print(f"   置信度：{result.confidence:.2f}, 建议：{result.suggestion[:30]}...")
        print()
