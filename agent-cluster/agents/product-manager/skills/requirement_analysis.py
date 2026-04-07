#!/usr/bin/env python3
"""
Product Manager Agent - 需求分析工具
"""

import json
from typing import Dict, List


class RequirementAnalyzer:
    """需求分析器"""
    
    def __init__(self):
        self.requirements = []
    
    def analyze_5w1h(self, user_request: str) -> Dict:
        """
        5W1H 需求分析
        
        Args:
            user_request: 用户原始需求描述
        
        Returns:
            分析结果字典
        """
        analysis = {
            "what": {
                "question": "这是什么产品/功能？",
                "answer": "",
                "details": []
            },
            "why": {
                "question": "为什么需要这个？",
                "answer": "",
                "pain_points": []
            },
            "who": {
                "question": "目标用户是谁？",
                "answer": "",
                "personas": []
            },
            "when": {
                "question": "什么时候使用？",
                "answer": "",
                "scenarios": []
            },
            "where": {
                "question": "在哪里使用？",
                "answer": "",
                "environments": []
            },
            "how": {
                "question": "如何使用？",
                "answer": "",
                "user_flow": []
            }
        }
        
        # TODO: 调用 AI 模型进行分析
        # 这里预留 AI 分析接口
        
        return analysis
    
    def create_user_stories(self, features: List[Dict]) -> List[Dict]:
        """
        创建用户故事
        
        Args:
            features: 功能列表
        
        Returns:
            用户故事列表
        """
        stories = []
        
        for feature in features:
            story = {
                "id": f"US-{len(stories)+1:03d}",
                "title": feature.get("name", ""),
                "description": {
                    "as_a": feature.get("user_role", "用户"),
                    "i_want": feature.get("description", ""),
                    "so_that": feature.get("value", "")
                },
                "acceptance_criteria": [],
                "priority": feature.get("priority", "M"),
                "estimated_points": 0
            }
            stories.append(story)
        
        return stories
    
    def define_acceptance_criteria(self, story: Dict) -> List[Dict]:
        """
        定义验收标准（Given/When/Then 格式）
        
        Args:
            story: 用户故事
        
        Returns:
            验收标准列表
        """
        criteria = []
        
        # TODO: 根据用户故事自动生成验收标准
        # 示例格式:
        # {
        #     "given": "用户已登录",
        #     "when": "点击提交按钮",
        #     "then": "显示成功提示"
        # }
        
        return criteria
    
    def prioritize_features(self, features: List[Dict]) -> List[Dict]:
        """
        功能优先级排序（MoSCoW 法则）
        
        Args:
            features: 功能列表
        
        Returns:
            排序后的功能列表
        """
        priority_order = {"M": 0, "S": 1, "C": 2, "W": 3}
        
        # 为每个功能分配优先级
        for feature in features:
            if "priority" not in feature:
                # 自动判断优先级
                feature["priority"] = self._auto_prioritize(feature)
        
        # 按优先级排序
        features.sort(key=lambda x: priority_order.get(x.get("priority", "W"), 3))
        
        return features
    
    def _auto_prioritize(self, feature: Dict) -> str:
        """自动判断功能优先级"""
        # 核心功能 - Must have
        core_keywords = ["登录", "注册", "支付", "核心", "必须", "基本"]
        
        # 重要功能 - Should have
        important_keywords = ["重要", "应该", "优化", "提升"]
        
        # 可选功能 - Could have
        optional_keywords = ["可以", "可选", "锦上添花", "如果有"]
        
        description = feature.get("description", "") + feature.get("name", "")
        
        for keyword in core_keywords:
            if keyword in description:
                return "M"
        
        for keyword in important_keywords:
            if keyword in description:
                return "S"
        
        for keyword in optional_keywords:
            if keyword in description:
                return "C"
        
        # 默认 Should have
        return "S"
    
    def generate_prd(self, analysis: Dict, stories: List[Dict]) -> Dict:
        """
        生成 PRD 文档
        
        Args:
            analysis: 需求分析结果
            stories: 用户故事列表
        
        Returns:
            PRD 文档结构
        """
        prd = {
            "meta": {
                "title": "",
                "version": "1.0",
                "created_at": "",
                "updated_at": "",
                "author": "Product Manager Agent"
            },
            "overview": {
                "background": "",
                "objectives": [],
                "success_metrics": []
            },
            "target_users": {
                "personas": [],
                "pain_points": []
            },
            "features": {
                "must_have": [],
                "should_have": [],
                "could_have": [],
                "wont_have": []
            },
            "user_stories": stories,
            "requirements": {
                "functional": [],
                "non_functional": []
            },
            "timeline": {
                "phases": [],
                "milestones": []
            },
            "risks": [],
            "appendix": {
                "references": [],
                "glossary": []
            }
        }
        
        return prd


# 主函数 - 供集群调用
def analyze_requirement(user_request: str) -> Dict:
    """
    分析用户需求
    
    Args:
        user_request: 用户原始需求
    
    Returns:
        分析结果
    """
    analyzer = RequirementAnalyzer()
    
    # 1. 5W1H 分析
    analysis = analyzer.analyze_5w1h(user_request)
    
    # 2. 提取功能列表
    features = extract_features(user_request)
    
    # 3. 创建用户故事
    stories = analyzer.create_user_stories(features)
    
    # 4. 定义验收标准
    for story in stories:
        story["acceptance_criteria"] = analyzer.define_acceptance_criteria(story)
    
    # 5. 优先级排序
    sorted_features = analyzer.prioritize_features(features)
    
    # 6. 生成 PRD
    prd = analyzer.generate_prd(analysis, stories)
    
    return {
        "analysis": analysis,
        "features": sorted_features,
        "user_stories": stories,
        "prd": prd
    }


def extract_features(user_request: str) -> List[Dict]:
    """从用户需求中提取功能列表"""
    # TODO: 调用 AI 模型提取功能
    # 这里返回示例数据
    return [
        {
            "name": "核心功能",
            "description": "实现基本功能",
            "user_role": "用户",
            "value": "解决问题",
            "priority": "M"
        }
    ]


if __name__ == "__main__":
    # 测试
    result = analyze_requirement("我需要一个在线商城系统")
    print(json.dumps(result, indent=2, ensure_ascii=False))
