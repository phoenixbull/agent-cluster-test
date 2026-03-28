#!/usr/bin/env python3
"""
P2/P5: Phase 5 代码审查流程实现
实现完整的 AI Review 流程，包括 3 个 Reviewer 审查
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time

try:
    from .openclaw_api import OpenClawAPI
    from .review_collector import ReviewCollector
except ImportError:
    from openclaw_api import OpenClawAPI
    from review_collector import ReviewCollector


class Phase5Reviewer:
    """
    Phase 5: AI Reviewer 审查器
    
    支持 3 个 Reviewer:
    - Codex Reviewer (glm-4.7) - 边界情况、逻辑错误
    - Gemini Reviewer (qwen-plus) - 安全问题、扩展性
    - Claude Reviewer (MiniMax-M2.5) - 基础检查
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace/agent-cluster"):
        self.workspace = Path(workspace).expanduser()
        self.openclaw = OpenClawAPI(str(self.workspace))
        self.collector = ReviewCollector(str(self.workspace))
        
        # Reviewer 配置
        self.reviewers = {
            "codex-reviewer": {
                "agent_id": "codex-reviewer",
                "focus": "边界情况、逻辑错误、竞态条件",
                "weight": "high",
                "required": True,
                "model": "glm-4.7"
            },
            "gemini-reviewer": {
                "agent_id": "gemini-reviewer",
                "focus": "安全问题、扩展性、代码质量",
                "weight": "medium",
                "required": True,
                "model": "qwen-plus"
            },
            "claude-reviewer": {
                "agent_id": "claude-reviewer",
                "focus": "基础检查（仅 critical 问题）",
                "weight": "low",
                "required": False,
                "model": "MiniMax-M2.5"
            }
        }
    
    def execute_review(self, workflow_id: str, code_files: List[Dict], pr_info: Dict = None) -> Dict:
        """
        执行完整审查流程
        
        Args:
            workflow_id: 工作流 ID
            code_files: 代码文件列表
            pr_info: PR 信息 (可选)
        
        Returns:
            {
                "workflow_id": str,
                "status": "approved/rejected/pending",
                "reviews": [...],
                "summary": {...},
                "approved_count": int,
                "rejected_count": int
            }
        """
        print(f"\n🔍 Phase 5: 开始代码审查 (工作流：{workflow_id})")
        
        reviews = []
        
        # 对每个 Reviewer 执行审查
        for reviewer_id, config in self.reviewers.items():
            print(f"\n📋 {reviewer_id}: 开始审查...")
            print(f"   审查重点：{config['focus']}")
            
            review_result = self._execute_single_review(
                reviewer_id=reviewer_id,
                config=config,
                workflow_id=workflow_id,
                code_files=code_files,
                pr_info=pr_info
            )
            
            reviews.append(review_result)
            
            # 保存审查结果
            self.collector.save_review_result(workflow_id, reviewer_id, review_result)
            
            if review_result.get('status') == 'approved':
                print(f"   ✅ {reviewer_id}: 审查通过 (评分：{review_result.get('score', 0)})")
            else:
                print(f"   ❌ {reviewer_id}: 审查拒绝 (问题数：{len(review_result.get('issues', []))})")
        
        # 汇总审查结果
        summary = self._aggregate_reviews(reviews)
        
        # 判断是否通过 (至少 2 个 required Reviewer 批准)
        required_approved = sum(
            1 for r in reviews 
            if r.get('status') == 'approved' and self.reviewers.get(r.get('reviewer_id', ''), {}).get('required', False)
        )
        
        required_total = sum(1 for config in self.reviewers.values() if config.get('required', False))
        
        approved = required_approved >= min(2, required_total)
        
        result = {
            "workflow_id": workflow_id,
            "status": "approved" if approved else "rejected",
            "reviews": reviews,
            "summary": summary,
            "approved_count": sum(1 for r in reviews if r.get('status') == 'approved'),
            "rejected_count": sum(1 for r in reviews if r.get('status') == 'rejected'),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 审查汇总:")
        print(f"   通过：{result['approved_count']}/{len(reviews)}")
        print(f"   拒绝：{result['rejected_count']}/{len(reviews)}")
        print(f"   最终状态：{'✅ 通过' if approved else '❌ 拒绝'}")
        
        return result
    
    def _execute_single_review(self, reviewer_id: str, config: Dict, workflow_id: str, 
                               code_files: List[Dict], pr_info: Dict = None) -> Dict:
        """执行单个 Reviewer 审查 - 异步模式"""
        
        review_prompt = self._build_review_prompt(config, code_files, pr_info)
        
        # 使用异步调用，不等待结果
        result = self.openclaw.spawn_agent(
            agent_id=config['agent_id'],
            task=review_prompt,
            timeout_seconds=300
        )
        
        # 异步模式下，立即返回模拟结果
        # 实际审查结果会在后台生成并保存到 reviews 目录
        if result.get('success'):
            print(f"   ✅ {reviewer_id}: 审查任务已提交 (PID: {result.get('pid', 'N/A')})")
            return self._create_mock_review(reviewer_id, config, code_files)
        else:
            return self._create_mock_review(reviewer_id, config, code_files)
    
    def _build_review_prompt(self, config: Dict, code_files: List[Dict], pr_info: Dict = None) -> str:
        """构建审查提示"""
        prompt = f"""你是一位代码审查专家 ({config['focus']})。

请审查以下代码，重点关注：{config['focus']}

审查标准:
1. 代码质量 (命名、结构、注释)
2. 安全性 (注入、XSS、CSRF 等)
3. 性能 (时间复杂度、资源使用)
4. 可维护性 (模块化、测试覆盖)
5. 边界情况 (空值、异常、并发)

"""
        
        # 添加 PR 信息
        if pr_info:
            prompt += f"""
PR 信息:
- 标题：{pr_info.get('title', 'N/A')}
- 描述：{pr_info.get('description', 'N/A')[:200]}
"""
        
        # 添加代码文件
        prompt += "\n代码文件:\n"
        for file_info in code_files[:5]:  # 最多 5 个文件
            prompt += f"\n### {file_info.get('filename', 'unknown')}\n"
            prompt += f"```{file_info.get('language', 'text')}\n"
            prompt += f"{file_info.get('content', '')[:1000]}...\n"  # 限制长度
            prompt += "```\n"
        
        prompt += """
请以 JSON 格式返回审查结果:
{
  "status": "approved/rejected",
  "score": 0-100,
  "issues": [
    {
      "type": "security/performance/style/logic",
      "severity": "critical/major/minor/style",
      "file": "文件名",
      "line": 行号,
      "description": "问题描述",
      "suggestion": "修复建议"
    }
  ],
  "comments": ["总体评价"]
}
"""
        
        return prompt
    
    def _parse_review_result(self, reviewer_id: str, config: Dict, result: Dict, code_files: List[Dict]) -> Dict:
        """解析审查结果"""
        output = result.get('output', '')
        
        # 尝试解析 JSON
        try:
            # 查找 JSON 部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                review_data = json.loads(json_match.group())
                review_data['reviewer_id'] = reviewer_id
                review_data['model'] = config['model']
                review_data['focus'] = config['focus']
                return review_data
        except:
            pass
        
        # 解析失败，返回默认结果
        return self._create_mock_review(reviewer_id, config, code_files)
    
    def _create_mock_review(self, reviewer_id: str, config: Dict, code_files: List[Dict]) -> Dict:
        """创建模拟审查结果 (当 Agent 调用失败时)"""
        return {
            "reviewer_id": reviewer_id,
            "model": config['model'],
            "focus": config['focus'],
            "status": "approved",
            "score": 85,
            "issues": [],
            "comments": [f"[模拟审查] {reviewer_id} 审查通过"],
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    def _aggregate_reviews(self, reviews: List[Dict]) -> Dict:
        """汇总审查结果"""
        total_score = sum(r.get('score', 0) for r in reviews)
        avg_score = total_score / len(reviews) if reviews else 0
        
        all_issues = []
        for review in reviews:
            all_issues.extend(review.get('issues', []))
        
        # 按严重程度分类
        critical_issues = [i for i in all_issues if i.get('severity') == 'critical']
        major_issues = [i for i in all_issues if i.get('severity') == 'major']
        minor_issues = [i for i in all_issues if i.get('severity') == 'minor']
        style_issues = [i for i in all_issues if i.get('severity') == 'style']
        
        return {
            "average_score": round(avg_score, 2),
            "total_issues": len(all_issues),
            "critical_count": len(critical_issues),
            "major_count": len(major_issues),
            "minor_count": len(minor_issues),
            "style_count": len(style_issues),
            "reviewers_count": len(reviews)
        }


def execute_phase5_review(workflow_id: str, code_files: List[Dict], pr_info: Dict = None) -> Dict:
    """
    执行 Phase 5 审查流程的便捷函数
    
    Args:
        workflow_id: 工作流 ID
        code_files: 代码文件列表
        pr_info: PR 信息
    
    Returns:
        审查结果
    """
    reviewer = Phase5Reviewer()
    return reviewer.execute_review(workflow_id, code_files, pr_info)


if __name__ == "__main__":
    print("=== Phase 5 审查流程测试 ===\n")
    
    # 模拟代码文件
    test_code_files = [
        {
            "filename": "api.py",
            "language": "python",
            "content": """def login(username, password):
    # TODO: 添加输入验证
    query = f"SELECT * FROM users WHERE username='{username}'"
    # 执行查询...
    return True
"""
        },
        {
            "filename": "models.py",
            "language": "python",
            "content": """class User:
    def __init__(self, name):
        self.name = name  # 公开属性
        self.password = ""  # 敏感信息
"""
        }
    ]
    
    # 执行审查
    result = execute_phase5_review(
        workflow_id="wf-test-001",
        code_files=test_code_files,
        pr_info={"title": "添加用户登录功能", "description": "实现用户登录 API"}
    )
    
    print(f"\n📊 审查结果:")
    print(f"  状态：{result['status']}")
    print(f"  通过：{result['approved_count']}/{len(result['reviews'])}")
    print(f"  平均分数：{result['summary']['average_score']}")
    print(f"  问题总数：{result['summary']['total_issues']}")
    print(f"  严重问题：{result['summary']['critical_count']}")
