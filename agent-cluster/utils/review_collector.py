#!/usr/bin/env python3
"""
P2: 代码审查结果收集器
与 Phase 5 审查结果联动，收集审查意见并反馈给编码阶段
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ReviewCollector:
    """代码审查结果收集器"""
    
    def __init__(self, workspace: str = "~/.openclaw/workspace/agent-cluster"):
        self.workspace = Path(workspace).expanduser()
        self.reviews_dir = self.workspace / "reviews"
        self.reviews_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_review_results(self, workflow_id: str) -> Dict:
        """
        收集工作流的审查结果
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            {
                "workflow_id": str,
                "reviews": [...],
                "summary": {...},
                "issues": [...],
                "approved": bool
            }
        """
        # 查找审查结果文件
        review_files = list(self.reviews_dir.glob(f"*{workflow_id}*.json"))
        
        if not review_files:
            return {
                "workflow_id": workflow_id,
                "reviews": [],
                "summary": {"total": 0, "approved": 0, "rejected": 0},
                "issues": [],
                "approved": False,
                "note": "未找到审查结果"
            }
        
        all_reviews = []
        all_issues = []
        approved_count = 0
        
        for review_file in review_files:
            with open(review_file, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
            
            all_reviews.append(review_data)
            
            # 统计审查结果
            if review_data.get('status') == 'approved':
                approved_count += 1
            elif review_data.get('status') == 'rejected':
                pass
            
            # 收集问题
            issues = review_data.get('issues', [])
            all_issues.extend(issues)
        
        summary = {
            "total": len(all_reviews),
            "approved": approved_count,
            "rejected": len(all_reviews) - approved_count,
            "issues_count": len(all_issues)
        }
        
        # 判断是否通过 (至少 2 个审查者批准)
        approved = approved_count >= 2
        
        return {
            "workflow_id": workflow_id,
            "reviews": all_reviews,
            "summary": summary,
            "issues": all_issues,
            "approved": approved
        }
    
    def get_code_feedback(self, workflow_id: str) -> Dict:
        """
        获取代码审查反馈 (用于增量代码生成)
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            {
                "files_to_modify": [...],
                "suggestions": [...],
                "critical_issues": [...],
                "style_issues": [...]
            }
        """
        review_result = self.collect_review_results(workflow_id)
        
        feedback = {
            "files_to_modify": [],
            "suggestions": [],
            "critical_issues": [],
            "style_issues": [],
            "review_approved": review_result['approved']
        }
        
        for issue in review_result.get('issues', []):
            severity = issue.get('severity', 'info')
            
            if severity == 'critical':
                feedback['critical_issues'].append(issue)
                if 'file' in issue:
                    feedback['files_to_modify'].append(issue['file'])
            elif severity == 'warning':
                feedback['suggestions'].append(issue)
            elif severity == 'style':
                feedback['style_issues'].append(issue)
        
        return feedback
    
    def save_review_result(self, workflow_id: str, reviewer_id: str, result: Dict):
        """
        保存审查结果
        
        Args:
            workflow_id: 工作流 ID
            reviewer_id: 审查者 ID
            result: 审查结果
        """
        review_file = self.reviews_dir / f"review_{workflow_id}_{reviewer_id}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        review_data = {
            "workflow_id": workflow_id,
            "reviewer_id": reviewer_id,
            "timestamp": datetime.now().isoformat(),
            "status": result.get('status', 'pending'),
            "score": result.get('score', 0),
            "issues": result.get('issues', []),
            "comments": result.get('comments', []),
            "approved_files": result.get('approved_files', []),
            "rejected_files": result.get('rejected_files', [])
        }
        
        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 审查结果已保存：{review_file}")
    
    def get_review_statistics(self, days: int = 7) -> Dict:
        """
        获取审查统计信息
        
        Args:
            days: 统计天数
        
        Returns:
            {
                "total_reviews": int,
                "approval_rate": float,
                "average_score": float,
                "common_issues": [...]
            }
        """
        # 查找最近的审查文件
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        all_reviews = []
        for review_file in self.reviews_dir.glob("review_*.json"):
            mtime = review_file.stat().st_mtime
            if mtime >= cutoff_date:
                with open(review_file, 'r', encoding='utf-8') as f:
                    all_reviews.append(json.load(f))
        
        if not all_reviews:
            return {
                "total_reviews": 0,
                "approval_rate": 0,
                "average_score": 0,
                "common_issues": [],
                "period_days": days
            }
        
        # 计算统计信息
        total = len(all_reviews)
        approved = sum(1 for r in all_reviews if r.get('status') == 'approved')
        scores = [r.get('score', 0) for r in all_reviews if r.get('score')]
        
        # 统计常见问题
        issue_counts = {}
        for review in all_reviews:
            for issue in review.get('issues', []):
                issue_type = issue.get('type', 'unknown')
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_reviews": total,
            "approval_rate": round(approved / total * 100, 2) if total > 0 else 0,
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "common_issues": [{"type": t, "count": c} for t, c in common_issues],
            "period_days": days
        }


class CodeReviewIntegration:
    """
    P2: 代码审查集成器
    连接 Phase 3 (编码) 和 Phase 5 (审查)
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace/agent-cluster"):
        self.workspace = Path(workspace).expanduser()
        self.collector = ReviewCollector(str(workspace))
    
    def apply_review_feedback(self, workflow_id: str, code_files: List[Dict]) -> Dict:
        """
        应用审查反馈到代码文件
        
        Args:
            workflow_id: 工作流 ID
            code_files: 代码文件列表
        
        Returns:
            {
                "modified_files": [...],
                "feedback_applied": bool,
                "issues_addressed": [...]
            }
        """
        feedback = self.collector.get_code_feedback(workflow_id)
        
        result = {
            "modified_files": [],
            "feedback_applied": False,
            "issues_addressed": [],
            "feedback_summary": feedback
        }
        
        if not feedback['review_approved']:
            # 审查未通过，需要根据反馈修改代码
            print(f"\n📝 应用审查反馈 (工作流：{workflow_id})")
            print(f"   关键问题：{len(feedback['critical_issues'])}")
            print(f"   建议：{len(feedback['suggestions'])}")
            print(f"   风格问题：{len(feedback['style_issues'])}")
            
            # 标记需要修改的文件
            for code_file in code_files:
                file_path = code_file.get('path', '')
                if any(file_path in f for f in feedback['files_to_modify']):
                    code_file['needs_revision'] = True
                    code_file['revision_reason'] = "审查未通过"
                    result['modified_files'].append(file_path)
            
            result['feedback_applied'] = True
            result['issues_addressed'] = feedback['critical_issues']
        
        return result
    
    def generate_revision_prompt(self, workflow_id: str, original_task: str) -> str:
        """
        生成代码修改提示 (基于审查反馈)
        
        Args:
            workflow_id: 工作流 ID
            original_task: 原始任务描述
        
        Returns:
            包含审查反馈的修改提示
        """
        feedback = self.collector.get_code_feedback(workflow_id)
        
        prompt = f"""{original_task}

【审查反馈 - 需要修复】

"""
        
        if feedback['critical_issues']:
            prompt += "### 关键问题 (必须修复)\n"
            for i, issue in enumerate(feedback['critical_issues'], 1):
                prompt += f"{i}. {issue.get('description', '未描述')}\n"
                if 'file' in issue:
                    prompt += f"   文件：{issue['file']}\n"
            prompt += "\n"
        
        if feedback['suggestions']:
            prompt += "### 改进建议 (推荐修复)\n"
            for i, issue in enumerate(feedback['suggestions'], 1):
                prompt += f"{i}. {issue.get('description', '未描述')}\n"
            prompt += "\n"
        
        if feedback['style_issues']:
            prompt += "### 代码风格 (建议优化)\n"
            for i, issue in enumerate(feedback['style_issues'], 1):
                prompt += f"{i}. {issue.get('description', '未描述')}\n"
        
        prompt += "\n请根据以上审查反馈修改代码，确保所有关键问题都已解决。"
        
        return prompt


if __name__ == "__main__":
    # 测试代码审查集成
    collector = ReviewCollector()
    
    print("=== 代码审查收集器测试 ===\n")
    
    # 模拟保存审查结果
    test_review = {
        "status": "approved",
        "score": 85,
        "issues": [
            {"type": "security", "severity": "critical", "description": "SQL 注入风险", "file": "backend/api.py"},
            {"type": "style", "severity": "style", "description": "命名不规范", "file": "backend/models.py"}
        ],
        "comments": ["代码整体质量不错", "注意安全性"]
    }
    
    collector.save_review_result("wf-test-001", "codex-reviewer", test_review)
    
    # 获取审查反馈
    feedback = collector.get_code_feedback("wf-test-001")
    print(f"\n审查反馈:")
    print(f"  关键问题：{len(feedback['critical_issues'])}")
    print(f"  建议：{len(feedback['suggestions'])}")
    print(f"  审查通过：{feedback['review_approved']}")
    
    # 获取统计信息
    stats = collector.get_review_statistics()
    print(f"\n审查统计:")
    print(f"  总审查数：{stats['total_reviews']}")
    print(f"  通过率：{stats['approval_rate']}%")
    print(f"  平均分：{stats['average_score']}")
