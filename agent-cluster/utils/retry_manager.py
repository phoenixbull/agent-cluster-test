#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能重试管理器
智能重试机制升级 - 步骤 3/5 + 4/5 + 5/5 集成

整合:
- 步骤 3: 任务拆解引擎
- 步骤 4: 上下文增强 (RAG)
- 步骤 5: Prompt 动态生成
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

# 导入前两步的模块
try:
    from .failure_classifier import FailureClassifier, FailureReason, FailureAnalysis, get_classifier
    from .agent_switcher import AgentSwitcher, SwitchDecision, SwitchStrategy, get_switcher
except ImportError:
    from failure_classifier import FailureClassifier, FailureReason, FailureAnalysis, get_classifier
    from agent_switcher import AgentSwitcher, SwitchDecision, SwitchStrategy, get_switcher


@dataclass
class SubTask:
    """子任务"""
    id: str
    description: str
    parent_task_id: str
    estimated_time: int  # 预计时间 (分钟)
    dependencies: List[str]  # 依赖的子任务 ID
    status: str = "pending"  # pending/running/completed/failed
    result: Optional[str] = None


@dataclass
class RetryContext:
    """重试上下文"""
    task_id: str
    original_description: str
    current_agent: str
    retry_count: int
    failure_analysis: FailureAnalysis
    switch_decision: SwitchDecision
    enhanced_context: Dict
    retry_prompt: str


class RetryManager:
    """智能重试管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.classifier = get_classifier()
        self.switcher = get_switcher(config_path)
        self.config_path = config_path or "cluster_config_v2.json"
    
    # ========== 步骤 3: 任务拆解引擎 ==========
    
    def decompose_task(
        self,
        task_description: str,
        failure_reason: FailureReason,
        max_subtasks: int = 5
    ) -> List[SubTask]:
        """
        任务拆解引擎
        
        根据失败原因，将大任务拆解为可并行执行的小任务
        """
        # 拆解策略
        if failure_reason in [FailureReason.CODE_LOGIC_ERROR]:
            return self._decompose_by_logic(task_description, max_subtasks)
        
        elif failure_reason == FailureReason.ENV_TIMEOUT:
            return self._decompose_by_steps(task_description, max_subtasks)
        
        elif failure_reason in [FailureReason.PROMPT_AMBIGUOUS, FailureReason.PROMPT_INCOMPLETE]:
            return self._decompose_by_clarification(task_description, max_subtasks)
        
        else:
            # 默认按功能模块拆解
            return self._decompose_by_module(task_description, max_subtasks)
    
    def _decompose_by_logic(self, description: str, max_subtasks: int) -> List[SubTask]:
        """按逻辑模块拆解"""
        # 简化实现：生成通用拆解模板
        return [
            SubTask(
                id=f"sub-1",
                description=f"分析需求并设计数据结构",
                parent_task_id="main",
                estimated_time=15,
                dependencies=[]
            ),
            SubTask(
                id=f"sub-2",
                description=f"实现核心业务逻辑",
                parent_task_id="main",
                estimated_time=20,
                dependencies=["sub-1"]
            ),
            SubTask(
                id=f"sub-3",
                description=f"实现 API 接口",
                parent_task_id="main",
                estimated_time=15,
                dependencies=["sub-1"]
            ),
            SubTask(
                id=f"sub-4",
                description=f"编写单元测试",
                parent_task_id="main",
                estimated_time=15,
                dependencies=["sub-2", "sub-3"]
            ),
        ][:max_subtasks]
    
    def _decompose_by_steps(self, description: str, max_subtasks: int) -> List[SubTask]:
        """按执行步骤拆解"""
        return [
            SubTask(
                id=f"step-1",
                description=f"步骤 1: 准备环境和依赖",
                parent_task_id="main",
                estimated_time=10,
                dependencies=[]
            ),
            SubTask(
                id=f"step-2",
                description=f"步骤 2: 实现基础功能",
                parent_task_id="main",
                estimated_time=20,
                dependencies=["step-1"]
            ),
            SubTask(
                id=f"step-3",
                description=f"步骤 3: 实现高级功能",
                parent_task_id="main",
                estimated_time=20,
                dependencies=["step-2"]
            ),
            SubTask(
                id=f"step-4",
                description=f"步骤 4: 测试和验证",
                parent_task_id="main",
                estimated_time=10,
                dependencies=["step-3"]
            ),
        ][:max_subtasks]
    
    def _decompose_by_clarification(self, description: str, max_subtasks: int) -> List[SubTask]:
        """按澄清需求拆解"""
        return [
            SubTask(
                id="clarify-1",
                description="明确需求目标和范围",
                parent_task_id="main",
                estimated_time=5,
                dependencies=[]
            ),
            SubTask(
                id="clarify-2",
                description="确定输入输出格式",
                parent_task_id="main",
                estimated_time=5,
                dependencies=["clarify-1"]
            ),
            SubTask(
                id="clarify-3",
                description="确认技术栈和约束条件",
                parent_task_id="main",
                estimated_time=5,
                dependencies=["clarify-1"]
            ),
            SubTask(
                id="clarify-4",
                description="基于澄清的需求实现功能",
                parent_task_id="main",
                estimated_time=30,
                dependencies=["clarify-2", "clarify-3"]
            ),
        ][:max_subtasks]
    
    def _decompose_by_module(self, description: str, max_subtasks: int) -> List[SubTask]:
        """按功能模块拆解"""
        return [
            SubTask(
                id="mod-1",
                description="模块 1: 数据模型设计",
                parent_task_id="main",
                estimated_time=15,
                dependencies=[]
            ),
            SubTask(
                id="mod-2",
                description="模块 2: 业务逻辑实现",
                parent_task_id="main",
                estimated_time=20,
                dependencies=["mod-1"]
            ),
            SubTask(
                id="mod-3",
                description="模块 3: 接口层实现",
                parent_task_id="main",
                estimated_time=15,
                dependencies=["mod-1"]
            ),
            SubTask(
                id="mod-4",
                description="模块 4: 集成测试",
                parent_task_id="main",
                estimated_time=15,
                dependencies=["mod-2", "mod-3"]
            ),
        ][:max_subtasks]
    
    # ========== 步骤 4: 上下文增强 (RAG) ==========
    
    def enhance_context(
        self,
        task_description: str,
        failure_reason: FailureReason,
        files: Optional[List[str]] = None,
        project: str = "default"
    ) -> Dict:
        """
        上下文增强
        
        检索相关代码片段、文档、设计规范等
        """
        enhanced = {
            "original_description": task_description,
            "business_context": self._get_business_context(project),
            "technical_context": self._get_technical_context(project),
        }
        
        # 根据失败原因添加特定上下文
        if failure_reason in [FailureReason.CODE_LOGIC_ERROR, FailureReason.CODE_SYNTAX_ERROR]:
            enhanced["related_code"] = self._search_similar_code(files or [])
            enhanced["code_patterns"] = self._get_code_patterns()
        
        elif failure_reason in [FailureReason.REVIEW_STYLE_ISSUE]:
            enhanced["design_specs"] = self._get_design_specs(project)
            enhanced["style_guide"] = self._get_style_guide()
        
        elif failure_reason in [FailureReason.REVIEW_SECURITY_ISSUE]:
            enhanced["security_checklist"] = self._get_security_checklist()
            enhanced["common_vulnerabilities"] = self._get_security_examples()
        
        elif failure_reason in [FailureReason.MODEL_HALLUCINATION]:
            enhanced["api_docs"] = self._search_api_docs(files or [])
            enhanced["available_functions"] = self._get_available_functions()
        
        elif failure_reason in [FailureReason.PROMPT_INCOMPLETE]:
            enhanced["similar_tasks"] = self._search_similar_tasks(task_description)
            enhanced["required_info"] = self._get_required_information()
        
        return enhanced
    
    def _get_business_context(self, project: str) -> Dict:
        """获取业务上下文"""
        # 简化实现
        return {
            "project_name": project,
            "domain": "web_application",
            "users": "end_users",
            "key_requirements": ["reliability", "performance", "security"]
        }
    
    def _get_technical_context(self, project: str) -> Dict:
        """获取技术上下文"""
        return {
            "language": "Python 3.8+",
            "framework": "FastAPI/Flask",
            "database": "PostgreSQL/MySQL",
            "testing": "pytest"
        }
    
    def _search_similar_code(self, files: List[str]) -> List[Dict]:
        """检索相似代码"""
        # TODO: 实现向量检索
        return []
    
    def _get_code_patterns(self) -> List[str]:
        """获取代码模式"""
        return [
            "使用异常处理包装外部调用",
            "使用类型注解提高代码可读性",
            "遵循单一职责原则"
        ]
    
    def _get_design_specs(self, project: str) -> Dict:
        """获取设计规范"""
        return {
            "colors": ["#667eea", "#764ba2"],
            "fonts": ["system-ui", "sans-serif"],
            "spacing": "8px baseline grid"
        }
    
    def _get_style_guide(self) -> str:
        """获取风格指南"""
        return "PEP 8 - Python 代码风格指南"
    
    def _get_security_checklist(self) -> List[str]:
        """获取安全检查清单"""
        return [
            "✓ 输入验证（防止 SQL 注入、XSS）",
            "✓ 认证和授权",
            "✓ 敏感数据加密",
            "✓ 安全日志记录",
            "✓ 错误信息不泄露敏感数据"
        ]
    
    def _get_security_examples(self) -> List[Dict]:
        """获取安全示例"""
        return [
            {
                "vulnerability": "SQL 注入",
                "bad": "cursor.execute(f\"SELECT * FROM users WHERE id={user_id}\")",
                "good": "cursor.execute(\"SELECT * FROM users WHERE id=?\", (user_id,))"
            }
        ]
    
    def _search_api_docs(self, files: List[str]) -> List[Dict]:
        """检索 API 文档"""
        # TODO: 实现文档检索
        return []
    
    def _get_available_functions(self) -> List[str]:
        """获取可用函数列表"""
        return ["os.path.exists", "json.loads", "requests.get"]
    
    def _search_similar_tasks(self, description: str) -> List[Dict]:
        """检索相似任务"""
        # TODO: 实现任务检索
        return []
    
    def _get_required_information(self) -> List[str]:
        """获取必需信息列表"""
        return [
            "输入数据格式",
            "输出数据格式",
            "边界条件",
            "性能要求",
            "兼容性要求"
        ]
    
    # ========== 步骤 5: Prompt 动态生成 ==========
    
    def generate_retry_prompt(
        self,
        task_description: str,
        failure_analysis: FailureAnalysis,
        enhanced_context: Dict,
        previous_attempts: List[Dict]
    ) -> str:
        """
        生成重试 Prompt
        
        基于失败原因和上下文，生成针对性的重试指令
        """
        reason = failure_analysis.reason
        
        # 基础 Prompt
        prompt = f"""# 任务重试

**原始任务**:
{task_description}

**失败原因**: {failure_analysis.reason.value}
**失败分析**: {failure_analysis.suggestion}

"""
        # 根据失败类型添加特定指令
        if reason == FailureReason.CODE_LOGIC_ERROR:
            prompt += self._generate_logic_error_prompt(enhanced_context, previous_attempts)
        
        elif reason == FailureReason.PROMPT_AMBIGUOUS:
            prompt += self._generate_ambiguous_prompt(enhanced_context)
        
        elif reason == FailureReason.REVIEW_SECURITY_ISSUE:
            prompt += self._generate_security_prompt(enhanced_context)
        
        elif reason == FailureReason.CODE_SYNTAX_ERROR:
            prompt += self._generate_syntax_error_prompt(previous_attempts)
        
        elif reason == FailureReason.MODEL_HALLUCINATION:
            prompt += self._generate_hallucination_prompt(enhanced_context)
        
        else:
            prompt += self._generate_generic_prompt(enhanced_context)
        
        # 添加历史尝试分析
        if previous_attempts:
            prompt += self._add_attempt_history(previous_attempts)
        
        return prompt
    
    def _generate_logic_error_prompt(self, context: Dict, attempts: List[Dict]) -> str:
        """生成逻辑错误重试 Prompt"""
        return """
## ⚠️ 特别注意：逻辑错误

上次尝试出现了逻辑错误。请按以下步骤重新实现：

1. **先理解业务逻辑**
   - 输入是什么？
   - 期望输出是什么？
   - 有哪些边界情况？

2. **分步实现**
   - 先写伪代码/思路
   - 再实现具体代码
   - 每一步都验证正确性

3. **考虑边界情况**
   - 空值处理
   - 异常处理
   - 并发场景

4. **编写测试**
   - 正常流程测试
   - 边界条件测试
   - 异常场景测试

## 参考代码模式
""" + "\n".join(f"- {p}" for p in context.get("code_patterns", []))
    
    def _generate_ambiguous_prompt(self, context: Dict) -> str:
        """生成需求模糊重试 Prompt"""
        return """
## ⚠️ 需求不够清晰

在开始实现之前，请先确认以下信息：

**我的理解**:
- 目标：[请描述你理解的任务目标]
- 输入：[输入数据格式]
- 输出：[期望输出格式]
- 约束：[技术栈、性能等约束]

**如果有不确定的地方，请先提出以下问题**:
1. [问题 1]
2. [问题 2]
3. [问题 3]

**不要直接实现**，先确保理解正确！
"""
    
    def _generate_security_prompt(self, context: Dict) -> str:
        """生成安全问题重试 Prompt"""
        checklist = context.get("security_checklist", [])
        examples = context.get("common_vulnerabilities", [])
        
        return f"""
## ⚠️ 存在安全隐患

上次实现存在安全问题。请严格按照以下清单检查：

### 安全检查清单
""" + "\n".join(f"{item}" for item in checklist) + f"""

### 常见漏洞示例
""" + "\n".join(f"- {e.get('vulnerability')}: {e.get('bad')} → {e.get('good')}" for e in examples) + """

### 修复要求
1. 修复所有安全问题
2. 添加安全测试用例
3. 说明修复方案
"""
    
    def _generate_syntax_error_prompt(self, attempts: List[Dict]) -> str:
        """生成语法错误重试 Prompt"""
        return """
## ⚠️ 语法错误

上次实现存在语法错误。请：

1. **仔细检查代码语法**
   - Python 缩进
   - 括号匹配
   - 引号闭合

2. **使用 linter 预检查**
   - 运行 `python -m py_compile your_file.py`
   - 或使用 flake8/pylint

3. **分步验证**
   - 先确保能运行
   - 再验证功能

请提供更仔细的实现！
"""
    
    def _generate_hallucination_prompt(self, context: Dict) -> str:
        """生成模型幻觉重试 Prompt"""
        return f"""
## ⚠️ 使用了不存在的 API/函数

上次实现引用了不存在的 API 或函数。请：

### 只使用以下已验证的函数
""" + "\n".join(f"- {f}" for f in context.get("available_functions", [])) + """

### 如果需要使用其他功能
1. 先确认是否存在
2. 或提供替代方案
3. 不要捏造 API

### 建议
- 查阅官方文档
- 使用标准库
- 明确标注不确定的地方
"""
    
    def _generate_generic_prompt(self, context: Dict) -> str:
        """生成通用重试 Prompt"""
        return """
## 重试要求

请仔细分析失败原因，重新实现任务。

### 注意事项
1. 理解失败原因
2. 参考上下文信息
3. 分步验证实现
4. 编写测试用例

### 可用资源
- 业务上下文：已提供
- 技术上下文：已提供
- 相关代码：已提供

请开始重新实现！
"""
    
    def _add_attempt_history(self, attempts: List[Dict]) -> str:
        """添加历史尝试分析"""
        history = "\n\n## 历史尝试\n"
        
        for i, attempt in enumerate(attempts, 1):
            history += f"\n### 尝试 {i}\n"
            history += f"- Agent: {attempt.get('agent', 'unknown')}\n"
            history += f"- 结果：{attempt.get('result', 'unknown')}\n"
            if attempt.get('error'):
                history += f"- 错误：{attempt.get('error')[:200]}...\n"
        
        history += "\n请分析历史失败原因，避免重复错误！\n"
        
        return history
    
    # ========== 集成方法 ==========
    
    def create_retry_context(
        self,
        task_id: str,
        task_description: str,
        current_agent: str,
        error_message: str,
        retry_count: int,
        files: Optional[List[str]] = None,
        project: str = "default",
        previous_attempts: Optional[List[Dict]] = None
    ) -> RetryContext:
        """
        创建完整的重试上下文
        
        整合所有步骤：分类 → 切换决策 → 上下文增强 → Prompt 生成
        """
        # 步骤 1: 失败分类
        failure_analysis = self.classifier.classify(error_message)
        
        # 步骤 2: Agent 切换决策
        switch_decision = self.switcher.decide_switch(
            current_agent,
            failure_analysis,
            retry_count,
            {"task_description": task_description}
        )
        
        # 步骤 3: 任务拆解（如果需要）
        if switch_decision.strategy == SwitchStrategy.DECOMPOSE:
            subtasks = self.decompose_task(task_description, failure_analysis.reason)
        else:
            subtasks = []
        
        # 步骤 4: 上下文增强
        enhanced_context = self.enhance_context(
            task_description,
            failure_analysis.reason,
            files,
            project
        )
        enhanced_context["subtasks"] = [asdict(s) for s in subtasks] if subtasks else []
        
        # 步骤 5: 生成重试 Prompt
        retry_prompt = self.generate_retry_prompt(
            task_description,
            failure_analysis,
            enhanced_context,
            previous_attempts or []
        )
        
        return RetryContext(
            task_id=task_id,
            original_description=task_description,
            current_agent=current_agent,
            retry_count=retry_count,
            failure_analysis=failure_analysis,
            switch_decision=switch_decision,
            enhanced_context=enhanced_context,
            retry_prompt=retry_prompt
        )


# ========== 全局实例 ==========

_manager: Optional[RetryManager] = None


def get_retry_manager(config_path: Optional[str] = None) -> RetryManager:
    """获取重试管理器实例"""
    global _manager
    if _manager is None:
        _manager = RetryManager(config_path)
    return _manager


# ========== 测试 ==========

if __name__ == "__main__":
    manager = RetryManager()
    
    # 测试任务拆解
    print("🧪 测试任务拆解:\n")
    subtasks = manager.decompose_task(
        "实现完整的用户系统",
        FailureReason.CODE_LOGIC_ERROR,
        max_subtasks=4
    )
    for task in subtasks:
        print(f"  {task.id}: {task.description} (依赖：{task.dependencies})")
    
    # 测试上下文增强
    print("\n🧪 测试上下文增强:\n")
    context = manager.enhance_context(
        "实现用户登录功能",
        FailureReason.REVIEW_SECURITY_ISSUE,
        project="ecommerce"
    )
    print(f"  业务上下文：{context.get('business_context', {})}")
    print(f"  安全检查清单：{len(context.get('security_checklist', []))} 项")
    
    # 测试 Prompt 生成
    print("\n🧪 测试 Prompt 生成:\n")
    analysis = FailureAnalysis(
        reason=FailureReason.CODE_LOGIC_ERROR,
        category="code",
        confidence=0.8,
        evidence=["测试失败"],
        suggestion="检查逻辑",
        severity="high"
    )
    prompt = manager.generate_retry_prompt(
        "实现用户登录",
        analysis,
        context,
        []
    )
    print(f"  生成 Prompt 长度：{len(prompt)} 字符")
    print(f"  前 200 字符：{prompt[:200]}...")
    
    print("\n✅ 所有测试完成!")
