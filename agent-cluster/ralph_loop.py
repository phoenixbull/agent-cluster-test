#!/usr/bin/env python3
"""
改进版 Ralph Loop 实现
核心：失败时动态调整 prompt，而不是简单重试
"""

import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class MemorySystem:
    """记忆系统：存储成功/失败模式"""
    
    def __init__(self, memory_path: str = "~/.openclaw/workspace/zoe/memory"):
        self.memory_path = Path(memory_path).expanduser()
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.success_log = self.memory_path / "successes.jsonl"
        self.failure_log = self.memory_path / "failures.jsonl"
        self.patterns_file = self.memory_path / "patterns.json"
        
        self._load_patterns()
    
    def _load_patterns(self):
        """加载成功模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file, "r", encoding="utf-8") as f:
                self.patterns = json.load(f)
        else:
            self.patterns = {
                "prompt_templates": {},
                "agent_selection": {},
                "failure_patterns": {}
            }
    
    def _save_patterns(self):
        """保存模式"""
        with open(self.patterns_file, "w", encoding="utf-8") as f:
            json.dump(self.patterns, f, indent=2, ensure_ascii=False)
    
    def retrieve(self, task_description: str) -> Dict[str, Any]:
        """检索相关上下文"""
        # 语义搜索类似任务（简化版：关键词匹配）
        keywords = task_description.lower().split()
        
        similar_successes = []
        similar_failures = []
        
        # 读取成功日志
        if self.success_log.exists():
            with open(self.success_log, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if any(kw in record.get("task", "").lower() for kw in keywords):
                        similar_successes.append(record)
        
        # 读取失败日志
        if self.failure_log.exists():
            with open(self.failure_log, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if any(kw in record.get("task", "").lower() for kw in keywords):
                        similar_failures.append(record)
        
        return {
            "similar_successes": similar_successes[:5],  # 最多 5 个
            "similar_failures": similar_failures[:3],    # 最多 3 个
            "patterns": self.patterns
        }
    
    def save_success(self, task: str, prompt: str, result: Dict[str, Any], agent: str):
        """保存成功模式"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "prompt": prompt,
            "agent": agent,
            "result": result,
            "metrics": {
                "ci_passed": result.get("ci_status") == "success",
                "reviews_approved": result.get("reviews_approved", 0),
                "execution_time": result.get("execution_time", 0)
            }
        }
        
        with open(self.success_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        # 更新模式
        task_type = self._extract_task_type(task)
        if task_type not in self.patterns["prompt_templates"]:
            self.patterns["prompt_templates"][task_type] = []
        
        self.patterns["prompt_templates"][task_type].append({
            "template": prompt,
            "success_rate": 1.0,
            "count": 1
        })
        
        self._save_patterns()
        print(f"✅ 保存成功模式：{task_type}")
    
    def save_failure(self, task: str, prompt: str, failure_reason: str, agent: str):
        """保存失败模式"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "prompt": prompt,
            "agent": agent,
            "failure_reason": failure_reason
        }
        
        with open(self.failure_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        # 更新失败模式
        task_type = self._extract_task_type(task)
        if task_type not in self.patterns["failure_patterns"]:
            self.patterns["failure_patterns"][task_type] = []
        
        self.patterns["failure_patterns"][task_type].append({
            "reason": failure_reason,
            "count": 1
        })
        
        self._save_patterns()
        print(f"⚠️ 保存失败模式：{task_type} - {failure_reason}")
    
    def _extract_task_type(self, task: str) -> str:
        """从任务描述中提取任务类型"""
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["后端", "api", "database", "backend"]):
            return "backend"
        elif any(kw in task_lower for kw in ["前端", "ui", "component", "frontend"]):
            return "frontend"
        elif any(kw in task_lower for kw in ["设计", "design", "ui", "visual"]):
            return "design"
        elif any(kw in task_lower for kw in ["bug", "修复", "fix"]):
            return "bugfix"
        elif any(kw in task_lower for kw in ["重构", "refactor"]):
            return "refactoring"
        else:
            return "general"


class RalphLoop:
    """
    改进版 Ralph Loop
    核心：失败时分析原因并动态调整 prompt，而不是简单重试
    """
    
    def __init__(self, orchestrator, memory: MemorySystem = None):
        self.orchestrator = orchestrator
        self.memory = memory or MemorySystem()
        self.max_retries = 3
    
    async def execute_with_learning(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        执行任务并学习
        
        流程：
        1. 从记忆检索相关上下文
        2. 生成动态 prompt
        3. 执行 Agent
        4. 评估结果
        5. 成功则保存模式，失败则分析原因并调整 prompt 重试
        """
        task_description = task.get("description", "")
        agent_id = task.get("agent", "codex")
        
        print(f"\n🔄 Ralph Loop 执行任务：{task_description[:50]}...")
        
        for attempt in range(self.max_retries):
            print(f"  尝试 {attempt + 1}/{self.max_retries}")
            
            # 1. 从记忆检索相关上下文
            context = self.memory.retrieve(task_description)
            
            # 2. 生成动态 prompt
            prompt = await self._generate_dynamic_prompt(
                task=task,
                context=context,
                attempt=attempt
            )
            
            print(f"  Prompt 长度：{len(prompt)} 字符")
            
            # 3. 执行 Agent
            start_time = datetime.now()
            result = await self._execute_agent(agent_id, prompt, task)
            execution_time = (datetime.now() - start_time).total_seconds()
            result["execution_time"] = execution_time
            
            # 4. 评估结果
            success = await self._evaluate_result(result)
            
            if success:
                print(f"  ✅ 任务成功")
                # 5. 保存成功模式
                self.memory.save_success(task_description, prompt, result, agent_id)
                return result
            else:
                print(f"  ❌ 任务失败")
                # 6. 分析失败原因
                failure_reason = await self._analyze_failure(result)
                
                # 7. 保存失败模式（用于未来学习）
                self.memory.save_failure(task_description, prompt, failure_reason, agent_id)
                
                # 8. 如果是最后一次尝试，通知人工介入
                if attempt == self.max_retries - 1:
                    print(f"  ⚠️ 多次重试失败，需要人工介入")
                    await self._notify_human_intervention(task, result, failure_reason)
                    return None
        
        return None
    
    async def _generate_dynamic_prompt(self, task: Dict[str, Any], context: Dict[str, Any], attempt: int) -> str:
        """生成动态 prompt"""
        task_description = task.get("description", "")
        
        # 基础 prompt
        base_prompt = f"""请完成以下任务：

任务：{task_description}

"""
        
        # 添加成功模式（如果有）
        if context["similar_successes"]:
            base_prompt += "\n## 参考成功案例\n"
            for i, success in enumerate(context["similar_successes"][:2], 1):
                base_prompt += f"\n案例 {i}: {success.get('task', 'N/A')}\n"
                base_prompt += f"关键方法：{success.get('result', {}).get('key_approach', 'N/A')}\n"
        
        # 添加失败警告（如果有）
        if context["similar_failures"]:
            base_prompt += "\n## 避免以下失败模式\n"
            for i, failure in enumerate(context["similar_failures"], 1):
                base_prompt += f"\n警告 {i}: {failure.get('failure_reason', 'N/A')}\n"
        
        # 根据尝试次数调整
        if attempt > 0:
            base_prompt += f"\n## 前次尝试反馈\n"
            base_prompt += f"这是第 {attempt + 1} 次尝试。之前的尝试失败了，请特别注意：\n"
            base_prompt += f"- 仔细分析需求\n"
            base_prompt += f"- 确保测试覆盖\n"
            base_prompt += f"- 遵循代码规范\n"
        
        # 添加执行要求
        base_prompt += """
## 执行要求
1. 先理解任务目标，再开始编码
2. 编写必要的测试
3. 确保代码通过 lint 和 typecheck
4. 提交清晰的 commit message
5. 创建 PR 时附上描述和截图（如有 UI 改动）

请开始执行任务。
"""
        
        return base_prompt
    
    async def _execute_agent(self, agent_id: str, prompt: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent"""
        # 实际实现会调用 Agent 执行
        # 这里返回模拟结果
        return {
            "agent_id": agent_id,
            "status": "completed",
            "pr_created": True,
            "pr_number": 123,
            "ci_status": "success",
            "reviews_approved": 3,
            "output": "任务完成"
        }
    
    async def _evaluate_result(self, result: Dict[str, Any]) -> bool:
        """评估结果是否成功"""
        # 成功的定义：
        # 1. PR 已创建
        # 2. CI 通过
        # 3. 审查通过
        
        if not result.get("pr_created"):
            return False
        
        if result.get("ci_status") != "success":
            return False
        
        if result.get("reviews_approved", 0) < 2:
            return False
        
        return True
    
    async def _analyze_failure(self, result: Dict[str, Any]) -> str:
        """分析失败原因"""
        if not result.get("pr_created"):
            return "PR 创建失败"
        
        if result.get("ci_status") != "success":
            ci_errors = result.get("ci_errors", [])
            return f"CI 失败：{', '.join(ci_errors)}"
        
        if result.get("reviews_approved", 0) < 2:
            review_comments = result.get("review_comments", [])
            return f"审查未通过：{', '.join(review_comments)}"
        
        return "未知错误"
    
    async def _notify_human_intervention(self, task: Dict[str, Any], result: Dict[str, Any], failure_reason: str):
        """通知人工介入"""
        message = f"""
⚠️ 任务需要人工介入

任务：{task.get('description', 'N/A')}
失败原因：{failure_reason}
执行结果：{json.dumps(result, indent=2, ensure_ascii=False)}

请检查并决定下一步操作。
"""
        # 通过 Telegram 发送通知
        print(message)
        # await telegram.send(message)


# 使用示例
async def main():
    # 初始化
    orchestrator = None  # 实际使用时传入 Orchestrator 实例
    ralph_loop = RalphLoop(orchestrator)
    
    # 执行任务
    task = {
        "id": "feat-custom-templates",
        "description": "实现自定义邮件模板功能，让用户可以保存和编辑现有配置",
        "agent": "codex",
        "priority": "high"
    }
    
    result = await ralph_loop.execute_with_learning(task)
    
    if result:
        print(f"\n✅ 任务完成：{result}")
    else:
        print(f"\n❌ 任务失败，需要人工介入")


if __name__ == "__main__":
    asyncio.run(main())
