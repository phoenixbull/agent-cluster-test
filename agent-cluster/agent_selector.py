#!/usr/bin/env python3
"""
Agent 选择策略
根据任务类型自动选择最合适的 Agent
"""

from typing import Dict, List, Optional, Any


class AgentSelector:
    """
    Agent 选择器
    根据任务类型、复杂度、紧急程度选择最合适的 Agent
    """
    
    # 任务类型到 Agent 的映射
    TASK_TYPE_MAPPING = {
        # 后端任务 → Codex (qwen-coder-plus)
        "backend_logic": "codex",
        "api_design": "codex",
        "database": "codex",
        "bug_fix": "codex",
        "refactoring": "codex",
        "cross_file_reasoning": "codex",
        "performance": "codex",
        "security": "codex",
        
        # 前端任务 → Claude Code (qwen-plus)
        "frontend": "claude-code",
        "ui_component": "claude-code",
        "git_operation": "claude-code",
        "quick_fix": "claude-code",
        "responsive": "claude-code",
        "accessibility": "claude-code",
        
        # 设计任务 → Gemini (qwen-vl-plus)
        "ui_design": "gemini",
        "visual": "gemini",
        "html_css": "gemini",
        "design_spec": "gemini",
        "mockup": "gemini",
        "prototype": "gemini",
        
        # 文档任务 → Writer (qwen-plus)
        "documentation": "writer",
        "technical_writing": "writer",
        "changelog": "writer",
        
        # 研究任务 → Researcher (qwen-plus)
        "research": "researcher",
        "competitive_analysis": "researcher",
        "trend_analysis": "researcher",
    }
    
    # 多 Agent 协作的任务类型
    MULTI_AGENT_TASKS = {
        "full_feature": ["gemini", "claude-code", "codex"],  # 设计 → 前端 → 后端
        "new_page": ["gemini", "claude-code"],  # 设计 → 前端
        "api_with_ui": ["codex", "claude-code"],  # 后端 → 前端
        "design_system": ["gemini", "claude-code"],  # 设计规范 → 组件实现
    }
    
    # Agent 能力描述
    AGENT_PROFILES = {
        "codex": {
            "name": "Codex 后端专家",
            "model": "qwen-coder-plus",
            "strengths": ["后端逻辑", "复杂 bug", "多文件重构", "跨代码库推理"],
            "temperature": 0.3,
            "speed": "medium",
            "cost": "high",
            "best_for": "需要深度推理的任务"
        },
        "claude-code": {
            "name": "Claude Code 前端专家",
            "model": "qwen-plus",
            "strengths": ["前端开发", "git 操作", "快速迭代", "组件开发"],
            "temperature": 0.5,
            "speed": "fast",
            "cost": "medium",
            "best_for": "需要快速完成的前端任务"
        },
        "gemini": {
            "name": "Gemini 设计专家",
            "model": "qwen-vl-plus",
            "strengths": ["UI 设计", "视觉系统", "HTML/CSS", "设计规范"],
            "temperature": 0.6,
            "speed": "medium",
            "cost": "medium",
            "best_for": "需要设计审美的任务"
        },
        "writer": {
            "name": "写作专家",
            "model": "qwen-plus",
            "strengths": ["技术写作", "文档", "编辑"],
            "temperature": 0.8,
            "speed": "fast",
            "cost": "medium",
            "best_for": "文档和写作任务"
        },
        "researcher": {
            "name": "研究专家",
            "model": "qwen-plus",
            "strengths": ["网络搜索", "信息综合", "分析"],
            "temperature": 0.5,
            "speed": "medium",
            "cost": "medium",
            "best_for": "调研和分析任务"
        }
    }
    
    def __init__(self, available_agents: List[str] = None):
        """
        初始化选择器
        
        Args:
            available_agents: 可用的 Agent ID 列表
        """
        self.available_agents = available_agents or list(self.AGENT_PROFILES.keys())
    
    def select_agent(self, task_description: str, task_type: str = None) -> str:
        """
        选择最合适的 Agent
        
        Args:
            task_description: 任务描述
            task_type: 任务类型（可选，会自动识别）
        
        Returns:
            选中的 Agent ID
        """
        # 如果没有指定任务类型，自动识别
        if not task_type:
            task_type = self._identify_task_type(task_description)
        
        # 查找映射
        if task_type in self.TASK_TYPE_MAPPING:
            agent_id = self.TASK_TYPE_MAPPING[task_type]
            
            # 检查 Agent 是否可用
            if agent_id in self.available_agents:
                return agent_id
        
        # 如果没有精确匹配，使用启发式规则
        return self._heuristic_select(task_description, task_type)
    
    def select_multi_agent(self, task_description: str, task_type: str = None) -> List[str]:
        """
        选择多个 Agent 协作
        
        Args:
            task_description: 任务描述
            task_type: 任务类型
        
        Returns:
            Agent ID 列表
        """
        if not task_type:
            task_type = self._identify_task_type(task_description)
        
        if task_type in self.MULTI_AGENT_TASKS:
            agents = self.MULTI_AGENT_TASKS[task_type]
            return [a for a in agents if a in self.available_agents]
        
        # 默认返回单个 Agent
        return [self.select_agent(task_description, task_type)]
    
    def _identify_task_type(self, task_description: str) -> str:
        """从任务描述中识别任务类型"""
        text = task_description.lower()
        
        # 关键词匹配
        keywords_map = {
            "backend_logic": ["后端", "api", "服务器", "database", "backend", "接口"],
            "frontend": ["前端", "页面", "ui", "component", "frontend", "组件"],
            "ui_design": ["设计", "界面", "visual", "design", "ui", "视觉"],
            "bug_fix": ["bug", "错误", "fix", "修复", "问题"],
            "refactoring": ["重构", "refactor", "优化", "改进"],
            "documentation": ["文档", "doc", "说明", "手册", "changelog"],
            "research": ["调研", "研究", "research", "分析", "趋势"],
            "git_operation": ["git", "分支", "merge", "pr", "提交"],
            "quick_fix": ["快速", "简单", "小", "minor"],
        }
        
        # 计算匹配度
        scores = {}
        for task_type, keywords in keywords_map.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[task_type] = score
        
        # 返回最高分的任务类型
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 0:
                return best_match
        
        return "general"
    
    def _heuristic_select(self, task_description: str, task_type: str) -> str:
        """启发式选择"""
        # 根据任务类型前缀匹配
        for mapped_type, agent_id in self.TASK_TYPE_MAPPING.items():
            if task_type.startswith(mapped_type.split("_")[0]):
                if agent_id in self.available_agents:
                    return agent_id
        
        # 默认返回 Codex（最通用）
        return "codex" if "codex" in self.available_agents else self.available_agents[0]
    
    def get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """获取 Agent 档案"""
        return self.AGENT_PROFILES.get(agent_id, {})
    
    def explain_selection(self, task_description: str, selected_agent: str) -> str:
        """解释为什么选择这个 Agent"""
        profile = self.get_agent_profile(selected_agent)
        
        explanation = f"选择 {profile['name']} 的原因：\n"
        explanation += f"- 擅长：{', '.join(profile['strengths'])}\n"
        explanation += f"- 最适合：{profile['best_for']}\n"
        explanation += f"- 速度：{profile['speed']}\n"
        explanation += f"- 成本：{profile['cost']}"
        
        return explanation


# 使用示例
def main():
    selector = AgentSelector()
    
    # 测试用例
    test_tasks = [
        ("实现用户登录 API", "backend_logic"),
        ("修复首页按钮点击无响应的问题", "bug_fix"),
        ("设计新的仪表盘界面", "ui_design"),
        ("重构用户模块代码", "refactoring"),
        ("编写 API 文档", "documentation"),
        ("调研竞品功能", "research"),
        ("创建新用户注册页面", "frontend"),
        ("实现完整的用户管理功能（设计 + 前端 + 后端）", "full_feature"),
    ]
    
    print("=" * 60)
    print("Agent 选择策略测试")
    print("=" * 60)
    
    for task, expected_type in test_tasks:
        agent = selector.select_agent(task, expected_type)
        profile = selector.get_agent_profile(agent)
        
        print(f"\n任务：{task}")
        print(f"选中 Agent: {profile['name']} ({agent})")
        print(f"原因：{profile['best_for']}")
        
        # 多 Agent 任务
        if expected_type in selector.MULTI_AGENT_TASKS:
            multi_agents = selector.select_multi_agent(task, expected_type)
            print(f"协作 Agent: {[selector.AGENT_PROFILES[a]['name'] for a in multi_agents]}")


if __name__ == "__main__":
    main()
