#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 切换策略
智能重试机制升级 - 步骤 2/5

基于失败原因和重试次数，智能选择最合适的 Agent 进行重试
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

# 导入失败分类器
try:
    from .failure_classifier import FailureReason, FailureCategory, FailureAnalysis
except ImportError:
    from failure_classifier import FailureReason, FailureCategory, FailureAnalysis


class SwitchStrategy(Enum):
    """切换策略类型"""
    SAME_AGENT = "same_agent"           # 原 Agent 重试
    SMART_SWITCH = "smart_switch"       # 智能切换
    ESCALATE = "escalate"               # 升级到更强模型
    DECOMPOSE = "decompose"             # 拆解任务
    HUMAN_INTERVENTION = "human"        # 人工介入


@dataclass
class AgentCapability:
    """Agent 能力画像"""
    agent_id: str
    model: str
    strengths: List[str]  # 擅长领域
    weaknesses: List[str]  # 不擅长领域
    avg_success_rate: float  # 平均成功率
    avg_duration: float  # 平均耗时 (秒)
    cost_per_call: float  # 单次调用成本 (元)


@dataclass
class SwitchDecision:
    """切换决策"""
    strategy: SwitchStrategy
    target_agent: Optional[str]
    reason: str
    confidence: float
    expected_improvement: str


class AgentSwitcher:
    """Agent 切换器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "cluster_config_v2.json"
        self.agents = self._load_agents()
        self.switch_rules = self._build_switch_rules()
    
    def _load_agents(self) -> Dict[str, AgentCapability]:
        """加载 Agent 配置"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            # 返回默认配置
            return self._get_default_agents()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            agents = {}
            for agent in config.get("agents", []):
                agent_id = agent.get("id")
                model_info = agent.get("model", {})
                
                # 从历史数据估算能力和成功率
                agents[agent_id] = AgentCapability(
                    agent_id=agent_id,
                    model=model_info.get("model", "unknown"),
                    strengths=agent.get("skills", []),
                    weaknesses=[],  # 动态计算
                    avg_success_rate=0.8,  # 默认 80%
                    avg_duration=1800,  # 默认 30 分钟
                    cost_per_call=0.05,  # 默认 0.05 元
                )
            
            return agents
        except Exception as e:
            print(f"加载 Agent 配置失败：{e}")
            return self._get_default_agents()
    
    def _get_default_agents(self) -> Dict[str, AgentCapability]:
        """默认 Agent 配置"""
        return {
            "codex": AgentCapability(
                agent_id="codex",
                model="qwen-coder-plus",
                strengths=["backend_logic", "bug_fixing", "refactoring", "api_design"],
                weaknesses=["frontend", "ui_design"],
                avg_success_rate=0.85,
                avg_duration=1800,
                cost_per_call=0.04,
            ),
            "claude-code": AgentCapability(
                agent_id="claude-code",
                model="kimi-k2.5",
                strengths=["frontend", "git_operation", "quick_fix", "component"],
                weaknesses=["complex_backend", "database"],
                avg_success_rate=0.75,
                avg_duration=1200,
                cost_per_call=0.03,
            ),
            "designer": AgentCapability(
                agent_id="designer",
                model="qwen-vl-plus",
                strengths=["ui_design", "visual", "html_css", "mockup"],
                weaknesses=["backend_logic", "database"],
                avg_success_rate=0.70,
                avg_duration=2400,
                cost_per_call=0.06,
            ),
            "tech-lead": AgentCapability(
                agent_id="tech-lead",
                model="qwen-max",
                strengths=["architecture", "tech_review", "api_design", "system_design"],
                weaknesses=["implementation"],
                avg_success_rate=0.90,
                avg_duration=600,
                cost_per_call=0.08,
            ),
        }
    
    def _build_switch_rules(self) -> Dict[FailureReason, Dict]:
        """构建切换规则"""
        return {
            # ========== Prompt 相关 ==========
            FailureReason.PROMPT_AMBIGUOUS: {
                "strategy": SwitchStrategy.ESCALATE,
                "target": "tech-lead",  # 升级到更强的编排层
                "reason": "需求理解问题，需要更强的理解能力",
            },
            FailureReason.PROMPT_INCOMPLETE: {
                "strategy": SwitchStrategy.ESCALATE,
                "target": "tech-lead",
                "reason": "需要补充上下文，编排层更擅长信息收集",
            },
            FailureReason.PROMPT_CONTRADICTORY: {
                "strategy": SwitchStrategy.ESCALATE,
                "target": "tech-lead",
                "reason": "需要统一指令，编排层更擅长协调",
            },
            
            # ========== 模型相关 ==========
            FailureReason.MODEL_HALLUCINATION: {
                "strategy": SwitchStrategy.SMART_SWITCH,
                "alternatives": ["codex", "tech-lead"],  # 多个备选
                "reason": "模型幻觉，切换到更可靠的模型",
            },
            FailureReason.MODEL_TIMEOUT: {
                "strategy": SwitchStrategy.SMART_SWITCH,
                "prefer_faster": True,  # 优先选择更快的
                "reason": "超时问题，切换到更快的 Agent",
            },
            FailureReason.MODEL_OUTPUT_INVALID: {
                "strategy": SwitchStrategy.SAME_AGENT,
                "adjust_prompt": True,  # 调整 Prompt 后重试
                "reason": "输出格式问题，调整指令后重试",
            },
            
            # ========== 代码相关 ==========
            FailureReason.CODE_SYNTAX_ERROR: {
                "strategy": SwitchStrategy.SAME_AGENT,
                "retry_count": 1,  # 允许重试 1 次
                "reason": "语法错误，通常是粗心，原 Agent 可修复",
            },
            FailureReason.CODE_LOGIC_ERROR: {
                "strategy": SwitchStrategy.SMART_SWITCH,
                "target": "codex",  # 切换到后端专家
                "reason": "逻辑错误，切换到后端专家重新实现",
            },
            FailureReason.CODE_IMPORT_ERROR: {
                "strategy": SwitchStrategy.SAME_AGENT,
                "add_context": True,  # 添加依赖信息
                "reason": "导入问题，提供依赖列表后重试",
            },
            
            # ========== 测试相关 ==========
            FailureReason.TEST_SYNTAX_ERROR: {
                "strategy": SwitchStrategy.SAME_AGENT,
                "retry_count": 1,
                "reason": "测试代码语法错误，原 Agent 可快速修复",
            },
            FailureReason.TEST_ASSERTION_FAILED: {
                "strategy": SwitchStrategy.SMART_SWITCH,
                "target": "tester",  # 切换到测试专家
                "reason": "断言失败，测试专家更擅长分析",
            },
            
            # ========== 审查相关 ==========
            FailureReason.REVIEW_STYLE_ISSUE: {
                "strategy": SwitchStrategy.SAME_AGENT,
                "use_formatter": True,  # 使用格式化工具
                "reason": "风格问题，使用工具自动修复",
            },
            FailureReason.REVIEW_SECURITY_ISSUE: {
                "strategy": SwitchStrategy.ESCALATE,
                "target": "tech-lead",
                "reason": "安全问题，需要技术负责人审查",
            },
            FailureReason.REVIEW_ARCHITECTURE_ISSUE: {
                "strategy": SwitchStrategy.ESCALATE,
                "target": "tech-lead",
                "reason": "架构问题，需要重新设计",
            },
            
            # ========== 环境相关 ==========
            FailureReason.ENV_GIT_ERROR: {
                "strategy": SwitchStrategy.SMART_SWITCH,
                "target": "claude-code",  # Git 操作是前端专家的强项
                "reason": "Git 问题，切换到更擅长 Git 的 Agent",
            },
            FailureReason.ENV_TIMEOUT: {
                "strategy": SwitchStrategy.DECOMPOSE,  # 拆解任务
                "reason": "环境问题导致超时，拆解为小任务",
            },
        }
    
    def decide_switch(
        self,
        current_agent: str,
        failure_analysis: FailureAnalysis,
        retry_count: int,
        task_context: Optional[Dict] = None
    ) -> SwitchDecision:
        """
        决策是否切换 Agent
        
        Args:
            current_agent: 当前 Agent
            failure_analysis: 失败分析结果
            retry_count: 重试次数
            task_context: 任务上下文
        
        Returns:
            SwitchDecision: 切换决策
        """
        reason = failure_analysis.reason
        
        # 1. 查找匹配的规则
        rule = self.switch_rules.get(reason)
        
        if not rule:
            # 无匹配规则 → 默认策略
            return self._default_decision(current_agent, retry_count)
        
        # 2. 根据重试次数调整策略
        strategy = self._adjust_strategy_by_retry(rule["strategy"], retry_count)
        
        # 3. 确定目标 Agent
        target_agent = self._select_target_agent(
            current_agent,
            rule,
            failure_analysis,
            retry_count
        )
        
        # 4. 生成决策
        decision = SwitchDecision(
            strategy=strategy,
            target_agent=target_agent,
            reason=rule.get("reason", ""),
            confidence=self._calculate_confidence(current_agent, target_agent, reason),
            expected_improvement=self._estimate_improvement(current_agent, target_agent, reason)
        )
        
        return decision
    
    def _adjust_strategy_by_retry(self, base_strategy: SwitchStrategy, retry_count: int) -> SwitchStrategy:
        """根据重试次数调整策略"""
        # 第 1 次失败 → 原策略
        if retry_count <= 1:
            return base_strategy
        
        # 第 2 次失败 → 升级策略
        if retry_count == 2:
            if base_strategy == SwitchStrategy.SAME_AGENT:
                return SwitchStrategy.SMART_SWITCH
            if base_strategy == SwitchStrategy.SMART_SWITCH:
                return SwitchStrategy.ESCALATE
        
        # 第 3 次失败 → 拆解或人工介入
        if retry_count >= 3:
            if base_strategy in [SwitchStrategy.SAME_AGENT, SwitchStrategy.SMART_SWITCH]:
                return SwitchStrategy.DECOMPOSE
            if base_strategy == SwitchStrategy.ESCALATE:
                return SwitchStrategy.HUMAN_INTERVENTION
        
        return base_strategy
    
    def _select_target_agent(
        self,
        current_agent: str,
        rule: Dict,
        failure_analysis: FailureAnalysis,
        retry_count: int
    ) -> Optional[str]:
        """选择目标 Agent"""
        
        # 同 Agent 重试
        if rule.get("strategy") == SwitchStrategy.SAME_AGENT:
            return current_agent
        
        # 指定目标
        if "target" in rule:
            target = rule["target"]
            if target in self.agents:
                return target
        
        # 多个备选 → 选择成功率最高的
        if "alternatives" in rule:
            alternatives = rule["alternatives"]
            best_agent = max(
                alternatives,
                key=lambda a: self.agents.get(a, AgentCapability(a, "", [], [], 0, 0, 0)).avg_success_rate,
                default=current_agent
            )
            return best_agent
        
        # 优先选择更快的
        if rule.get("prefer_faster"):
            fastest = min(
                self.agents.keys(),
                key=lambda a: self.agents[a].avg_duration,
                default=current_agent
            )
            return fastest
        
        # 默认返回当前 Agent
        return current_agent
    
    def _default_decision(self, current_agent: str, retry_count: int) -> SwitchDecision:
        """默认决策"""
        if retry_count >= 3:
            return SwitchDecision(
                strategy=SwitchStrategy.HUMAN_INTERVENTION,
                target_agent=None,
                reason="多次重试失败，需要人工介入",
                confidence=0.9,
                expected_improvement="人工指导可解决问题"
            )
        
        if retry_count >= 1:
            return SwitchDecision(
                strategy=SwitchStrategy.SMART_SWITCH,
                target_agent="tech-lead",
                reason="重试失败，升级到更强模型",
                confidence=0.7,
                expected_improvement="更强模型可能解决问题"
            )
        
        return SwitchDecision(
            strategy=SwitchStrategy.SAME_AGENT,
            target_agent=current_agent,
            reason="首次失败，原 Agent 重试",
            confidence=0.6,
            expected_improvement="可能是偶发问题"
        )
    
    def _calculate_confidence(self, current_agent: str, target_agent: str, reason: FailureReason) -> float:
        """计算决策置信度"""
        base_confidence = 0.7
        
        # 目标 Agent 擅长该领域 → 提高置信度
        if target_agent in self.agents:
            agent = self.agents[target_agent]
            if reason.value.split("_")[0] in agent.strengths:
                base_confidence += 0.15
        
        # 历史成功率 → 调整置信度
        if target_agent in self.agents:
            success_rate = self.agents[target_agent].avg_success_rate
            base_confidence += (success_rate - 0.8) * 0.2
        
        return min(0.95, max(0.3, base_confidence))
    
    def _estimate_improvement(self, current_agent: str, target_agent: str, reason: FailureReason) -> str:
        """预估改进效果"""
        if current_agent == target_agent:
            return "原 Agent 重试，预计解决率 60%"
        
        current_success = self.agents.get(current_agent, AgentCapability("", "", [], [], 0.7, 0, 0)).avg_success_rate
        target_success = self.agents.get(target_agent, AgentCapability("", "", [], [], 0.7, 0, 0)).avg_success_rate
        
        improvement = (target_success - current_success) * 100
        
        if improvement > 10:
            return f"切换到 {target_agent}，预计成功率提升 {improvement:.0f}%"
        elif improvement > 0:
            return f"切换到 {target_agent}，预计成功率小幅提升 {improvement:.0f}%"
        else:
            return f"切换到 {target_agent}，预计效果相当"
    
    def get_agent_recommendation(self, task_type: str) -> str:
        """根据任务类型推荐 Agent"""
        skill_to_agent = {
            "backend": "codex",
            "frontend": "claude-code",
            "ui_design": "designer",
            "architecture": "tech-lead",
            "testing": "tester",
        }
        return skill_to_agent.get(task_type, "codex")


# ========== 全局实例 ==========

_switcher: Optional[AgentSwitcher] = None


def get_switcher(config_path: Optional[str] = None) -> AgentSwitcher:
    """获取切换器实例"""
    global _switcher
    if _switcher is None:
        _switcher = AgentSwitcher(config_path)
    return _switcher


def decide_agent_switch(
    current_agent: str,
    failure_reason: FailureReason,
    retry_count: int
) -> SwitchDecision:
    """便捷函数：决策 Agent 切换"""
    try:
        from .failure_classifier import FailureAnalysis
    except ImportError:
        from failure_classifier import FailureAnalysis
    
    # 创建简单的分析对象
    analysis = FailureAnalysis(
        reason=failure_reason,
        category=failure_reason.name.split("_")[0].lower(),
        confidence=0.8,
        evidence=[],
        suggestion="",
        severity="medium"
    )
    
    return get_switcher().decide_switch(current_agent, analysis, retry_count)


# ========== 测试 ==========

if __name__ == "__main__":
    switcher = AgentSwitcher()
    
    # 测试用例
    test_cases = [
        ("codex", FailureReason.CODE_SYNTAX_ERROR, 0),
        ("codex", FailureReason.CODE_SYNTAX_ERROR, 1),
        ("codex", FailureReason.CODE_LOGIC_ERROR, 0),
        ("claude-code", FailureReason.CODE_LOGIC_ERROR, 0),
        ("codex", FailureReason.REVIEW_SECURITY_ISSUE, 0),
        ("codex", FailureReason.ENV_GIT_ERROR, 0),
        ("codex", FailureReason.PROMPT_AMBIGUOUS, 2),
    ]
    
    print("🧪 Agent 切换策略测试:\n")
    for agent, reason, retry in test_cases:
        decision = decide_agent_switch(agent, reason, retry)
        print(f"当前：{agent:<12} | 失败：{reason.value:<25} | 重试：{retry}")
        print(f"  → 策略：{decision.strategy.value}")
        print(f"  → 目标：{decision.target_agent or 'N/A'}")
        print(f"  → 原因：{decision.reason}")
        print(f"  → 置信度：{decision.confidence:.2f}")
        print(f"  → 预期：{decision.expected_improvement}")
        print()
