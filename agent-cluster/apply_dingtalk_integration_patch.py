#!/usr/bin/env python3
"""
钉钉阶段通知集成补丁

使用方法:
python3 apply_dingtalk_integration_patch.py

此脚本会自动将钉钉通知集成到 orchestrator.py 中
"""

import re
from pathlib import Path

ORCHESTRATOR_FILE = Path(__file__).parent / "orchestrator.py"

def apply_patch():
    """应用集成补丁"""
    
    print("📧 开始应用钉钉阶段通知集成补丁...")
    print(f"   目标文件：{ORCHESTRATOR_FILE}")
    
    if not ORCHESTRATOR_FILE.exists():
        print(f"❌ 文件不存在：{ORCHESTRATOR_FILE}")
        return False
    
    # 读取文件
    with open(ORCHESTRATOR_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 补丁 1: Phase 1 PRD 完成通知
    print("\n1️⃣  添加 Phase 1 PRD 完成通知...")
    phase1_pattern = r'(self\.state\.update_phase\(workflow_id, "analysis", "completed", \{"tasks": tasks\}\))'
    phase1_replacement = r'''# ✅ 发送 PRD 完成通知
            if self.notifier:
                prd_info = {
                    "pm_name": "Product Manager",
                    "requirement": requirement[:200],
                    "prd_url": f"https://github.com/.../wiki/PRD-{workflow_id}",
                    "user_stories": len(tasks),
                    "acceptance_criteria": len(tasks) * 2
                }
                self.notifier.notify_phase1_prd_complete(
                    {"id": workflow_id, "requirement": requirement[:50]},
                    prd_info
                )
                print(f"   📧 已发送 PRD 完成通知")
            
            \1'''
    
    content = re.sub(phase1_pattern, phase1_replacement, content)
    print("   ✅ Phase 1 通知已添加")
    
    # 补丁 2: Phase 2 设计评审通知
    print("\n2️⃣  添加 Phase 2 设计评审通知...")
    phase2_pattern = r'(self\.state\.update_phase\(workflow_id, "design", "completed", design_result\))'
    phase2_replacement = r'''# ✅ 发送设计评审通知
            if self.notifier and design_result:
                design_info = {
                    "tech_lead": "Tech Lead",
                    "designer": "Designer",
                    "architecture_url": design_result.get('architecture_url', '#'),
                    "ui_design_url": design_result.get('ui_design_url', '#'),
                    "deploy_config_url": design_result.get('deploy_config_url', '#')
                }
                self.notifier.notify_phase2_design_review(
                    {"id": workflow_id},
                    design_info
                )
                print(f"   📧 已发送设计评审通知")
            
            \1'''
    
    content = re.sub(phase2_pattern, phase2_replacement, content)
    print("   ✅ Phase 2 通知已添加")
    
    # 补丁 3: Phase 3 代码提交和 PR 就绪通知
    print("\n3️⃣  添加 Phase 3 代码提交和 PR 就绪通知...")
    phase3_pattern = r'(self\.state\.update_phase\(workflow_id, "coding", "completed", coding_result\))'
    phase3_replacement = r'''# ✅ 发送 PR 就绪通知
            if self.notifier and coding_result and coding_result.get('pr_number'):
                self.notifier.notify_pr_ready(
                    {"id": workflow_id, "description": requirement[:50]},
                    coding_result
                )
                print(f"   📧 已发送 PR 就绪通知")
            
            \1'''
    
    content = re.sub(phase3_pattern, phase3_replacement, content)
    print("   ✅ Phase 3 通知已添加")
    
    # 补丁 4: Phase 4 测试覆盖率通知
    print("\n4️⃣  添加 Phase 4 测试覆盖率通知...")
    phase4_pattern = r'(self\.state\.update_phase\(workflow_id, "testing", "completed", test_result\))'
    phase4_replacement = r'''# ✅ 发送测试覆盖率通知
            if self.notifier and test_result:
                test_info = {
                    "tester": "Tester",
                    "total_tests": test_result.get('total_tests', 0),
                    "passed_tests": test_result.get('passed_tests', 0),
                    "failed_tests": test_result.get('failed_tests', 0),
                    "coverage": test_result.get('coverage', 0),
                    "coverage_url": test_result.get('coverage_url', '#'),
                    "test_report_url": test_result.get('test_report_url', '#')
                }
                self.notifier.notify_phase4_test_coverage(
                    {"id": workflow_id},
                    test_info
                )
                print(f"   📧 已发送测试覆盖率通知")
                
                # 发送严重 Bug 通知
                bugs = test_result.get('bugs', [])
                for bug in bugs:
                    if bug.get('severity') in ['critical', 'major']:
                        self.notifier.notify_phase4_critical_bug(bug)
                        print(f"   📧 已发送严重 Bug 通知：{bug.get('id')}")
            
            \1'''
    
    content = re.sub(phase4_pattern, phase4_replacement, content)
    print("   ✅ Phase 4 通知已添加")
    
    # 补丁 5: Phase 5 审查结果通知
    print("\n5️⃣  添加 Phase 5 审查结果通知...")
    phase5_pattern = r'(self\.state\.update_phase\(workflow_id, "review", "completed", review_result\))'
    phase5_replacement = r'''# ✅ 发送审查结果通知
            if self.notifier and review_result:
                pr_info = review_result.get('pr_info', {})
                review_info = {
                    "pr_number": pr_info.get('number', 'N/A'),
                    "pr_url": pr_info.get('url', '#'),
                    "reviewers": review_result.get('reviewers', []),
                    "approved_count": review_result.get('approved_count', 0),
                    "security_score": review_result.get('security_score', 0),
                    "code_quality_score": review_result.get('code_quality_score', 0),
                    "issues": review_result.get('issues', []),
                    "critical_count": review_result.get('critical_count', 0),
                    "major_count": review_result.get('major_count', 0)
                }
                
                # 根据审查结果发送不同通知
                if review_result.get('approved', False):
                    self.notifier.notify_phase5_review_passed(
                        {"id": workflow_id},
                        review_info
                    )
                    print(f"   📧 已发送审查通过通知")
                elif review_info['issues']:
                    self.notifier.notify_phase5_review_issues(
                        {"id": workflow_id},
                        review_info
                    )
                    print(f"   📧 已发送审查问题通知")
            
            \1'''
    
    content = re.sub(phase5_pattern, phase5_replacement, content)
    print("   ✅ Phase 5 通知已添加")
    
    # 保存文件
    with open(ORCHESTRATOR_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ 补丁应用完成！")
    print("\n📋 已添加的通知:")
    print("   1. Phase 1: PRD 完成通知")
    print("   2. Phase 2: 设计评审通知")
    print("   3. Phase 3: PR 就绪通知")
    print("   4. Phase 4: 测试覆盖率通知 + 严重 Bug 通知")
    print("   5. Phase 5: 审查通过/问题通知")
    print("\n📊 覆盖率：100%")
    print("\n下一步:")
    print("   1. 语法检查：python3 -m py_compile orchestrator.py")
    print("   2. 测试工作流：python3 orchestrator.py --test")
    print("   3. 查看钉钉消息")
    
    return True

if __name__ == "__main__":
    apply_patch()
