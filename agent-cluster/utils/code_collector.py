#!/usr/bin/env python3
"""
代码文件收集器
从 Agent 会话结果中提取生成的代码文件
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class CodeFileCollector:
    """
    代码文件收集器
    
    功能:
    - 解析 Agent 会话消息
    - 提取代码块
    - 推断文件名
    - 保存代码文件
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化收集器
        
        Args:
            output_dir: 输出目录 (默认：临时目录)
        """
        if output_dir:
            self.output_dir = Path(output_dir).expanduser()
        else:
            self.output_dir = Path("/tmp/agent-generated-code").expanduser()
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.collected_files = []
    
    def collect_from_session(self, session_file: str) -> List[Dict]:
        """
        从会话文件收集代码
        
        Args:
            session_file: 会话文件路径
        
        Returns:
            收集到的文件列表
        """
        session_path = Path(session_file).expanduser()
        
        if not session_path.exists():
            print(f"   ⚠️ 会话文件不存在：{session_file}")
            return []
        
        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        
        return self.collect_from_session_data(session_data)
    
    def collect_from_session_data(self, session_data: Dict) -> List[Dict]:
        """
        从会话数据收集代码
        
        Args:
            session_data: 会话数据
        
        Returns:
            收集到的文件列表
        """
        messages = session_data.get("messages", [])
        task = session_data.get("task", "")
        agent_id = session_data.get("agent_id", "unknown")
        
        collected = []
        
        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            
            content = msg.get("content", "")
            
            # 提取代码块
            code_blocks = self._extract_code_blocks(content)
            
            for code_block in code_blocks:
                code = code_block.get("code", "")
                language = code_block.get("language", "")
                
                # 推断文件名
                filename = self._infer_filename(code, language, task, agent_id)
                
                # 保存文件
                file_path = self._save_code_file(filename, code)
                
                collected.append({
                    "filename": filename,
                    "path": str(file_path),
                    "language": language,
                    "size": len(code),
                    "agent_id": agent_id
                })
        
        # 如果没有提取到代码块，创建一个说明文件
        if not collected:
            readme_file = self._create_readme_file(session_data)
            collected.append({
                "filename": readme_file.name,
                "path": str(readme_file),
                "language": "markdown",
                "size": readme_file.stat().st_size,
                "agent_id": agent_id
            })
        
        self.collected_files.extend(collected)
        return collected
    
    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """
        从内容中提取代码块
        
        Args:
            content: 消息内容
        
        Returns:
            代码块列表
        """
        code_blocks = []
        
        # 匹配 Markdown 代码块 ```language ... ```
        pattern = r'```(\w+)?\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append({
                "code": code.strip(),
                "language": language or "text"
            })
        
        # 如果没有找到 Markdown 代码块，尝试查找内联代码
        if not code_blocks:
            # 匹配 `code` 内联代码
            inline_pattern = r'`([^`]+)`'
            inline_matches = re.findall(inline_pattern, content)
            
            for code in inline_matches:
                if len(code) > 20:  # 只收集较长的代码
                    code_blocks.append({
                        "code": code.strip(),
                        "language": "text"
                    })
        
        # 如果还是没有，将整个内容作为代码
        if not code_blocks and len(content) > 50:
            code_blocks.append({
                "code": content,
                "language": "text"
            })
        
        return code_blocks
    
    def _infer_filename(self, code: str, language: str, task: str, agent_id: str) -> str:
        """
        推断文件名
        
        Args:
            code: 代码内容
            language: 编程语言
            task: 任务描述
            agent_id: Agent ID
        
        Returns:
            文件名
        """
        # 根据语言确定扩展名
        ext_map = {
            "python": ".py",
            "py": ".py",
            "javascript": ".js",
            "js": ".js",
            "typescript": ".ts",
            "ts": ".ts",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "sql": ".sql",
            "java": ".java",
            "cpp": ".cpp",
            "c": ".c",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "shell": ".sh",
            "bash": ".sh"
        }
        
        ext = ext_map.get(language.lower(), ".txt")
        
        # 根据任务生成文件名
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 简化任务描述作为文件名
        task_words = task.split()[:3]
        task_slug = "-".join(task_words).lower()
        task_slug = re.sub(r'[^\w\-]', '', task_slug)
        
        # 根据 Agent 类型添加前缀
        prefix_map = {
            "codex": "backend",
            "claude-code": "frontend",
            "designer": "design",
            "coder": "code"
        }
        prefix = prefix_map.get(agent_id, "code")
        
        filename = f"{prefix}-{task_slug}-{timestamp}{ext}"
        
        # 清理文件名
        filename = re.sub(r'[^\w\-\.]', '-', filename)
        filename = re.sub(r'-+', '-', filename)
        filename = filename.strip('-')
        
        return filename
    
    def _save_code_file(self, filename: str, code: str) -> Path:
        """
        保存代码文件
        
        Args:
            filename: 文件名
            code: 代码内容
        
        Returns:
            文件路径
        """
        file_path = self.output_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        print(f"   📝 保存文件：{filename} ({len(code)} 字节)")
        return file_path
    
    def _create_readme_file(self, session_data: Dict) -> Path:
        """
        创建 README 说明文件
        
        Args:
            session_data: 会话数据
        
        Returns:
            文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"README-{timestamp}.md"
        
        task = session_data.get("task", "未知任务")
        agent_id = session_data.get("agent_id", "unknown")
        session_id = session_data.get("id", "unknown")
        
        content = f"""# Agent 生成的代码

## 任务信息

- **任务**: {task}
- **Agent**: {agent_id}
- **会话 ID**: {session_id}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 说明

此任务由 Agent 集群 V2.0 自动生成。

由于代码文件收集功能还在完善中，具体的代码实现需要查看 Agent 会话记录。

## 下一步

1. 查看 Agent 会话文件获取详细实现
2. 手动添加代码文件到 Git 仓库
3. 提交并创建 PR

---

**生成时间**: {datetime.now().isoformat()}
**Agent 集群**: V2.0
"""
        
        file_path = self.output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"   📝 创建说明文件：{filename}")
        return file_path
    
    def get_all_files(self) -> List[Dict]:
        """获取所有收集的文件"""
        return self.collected_files
    
    def get_files_for_git(self) -> List[str]:
        """获取适合 Git 提交的文件路径列表"""
        return [f["path"] for f in self.collected_files]
    
    def clear(self):
        """清空收集的文件列表"""
        self.collected_files = []


# ========== 便捷函数 ==========

def collect_code_from_sessions(session_files: List[str], output_dir: str = None) -> List[Dict]:
    """
    从多个会话文件收集代码
    
    Args:
        session_files: 会话文件列表
        output_dir: 输出目录
    
    Returns:
        收集到的文件列表
    """
    collector = CodeFileCollector(output_dir)
    
    for session_file in session_files:
        collector.collect_from_session(session_file)
    
    return collector.get_all_files()


# ========== 测试入口 ==========

def main():
    """测试函数"""
    import sys
    
    collector = CodeFileCollector()
    
    # 测试会话文件
    test_sessions = [
        "/home/admin/.openclaw/workspace/agents/codex/sessions/e88fd33f.json",
        "/home/admin/.openclaw/workspace/agents/claude-code/sessions/401c0487.json"
    ]
    
    print("📊 测试代码文件收集器")
    print("=" * 60)
    
    for session_file in test_sessions:
        print(f"\n处理会话：{session_file}")
        files = collector.collect_from_session(session_file)
        
        for f in files:
            print(f"  - {f['filename']} ({f['language']}, {f['size']} 字节)")
    
    print(f"\n✅ 共收集 {len(collector.get_all_files())} 个文件")
    print(f"📁 输出目录：{collector.output_dir}")


if __name__ == "__main__":
    main()
