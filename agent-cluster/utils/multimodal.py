#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态能力集成模块
智能重试机制升级 - v2.3.0 新功能

支持:
- UI 截图对比 (视觉回归测试)
- 设计稿→代码 (Figma MCP)
- 语音任务提交 (ElevenLabs TTS)
- PR 视频演示 (GIF/视频生成)
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import subprocess


class MultimodalManager:
    """多模态管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "cluster_config_v2.json"
        self.config = self._load_config()
        
        # 功能开关
        self.features = self.config.get("multimodal", {})
        
        # 目录结构
        self.media_dir = Path(__file__).parent.parent / "media"
        self.screenshots_dir = self.media_dir / "screenshots"
        self.videos_dir = self.media_dir / "videos"
        self.audio_dir = self.media_dir / "audio"
        
        # 创建目录
        for dir_path in [self.media_dir, self.screenshots_dir, self.videos_dir, self.audio_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict:
        """加载配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    # ========== 1. UI 截图对比 (视觉回归测试) ==========
    
    def capture_screenshot(
        self,
        url: str,
        task_id: str,
        full_page: bool = True
    ) -> Dict:
        """
        捕获网页截图
        
        Args:
            url: 目标 URL
            task_id: 任务 ID
            full_page: 是否完整页面
        
        Returns:
            Dict: {
                "success": bool,
                "path": str,
                "timestamp": str,
                "size": int
            }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task_id}_{timestamp}.png"
        output_path = self.screenshots_dir / filename
        
        try:
            # 使用 Playwright 截图
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                
                if full_page:
                    page.screenshot(path=str(output_path), full_page=True)
                else:
                    page.screenshot(path=str(output_path))
                
                browser.close()
            
            # 获取文件大小
            size = output_path.stat().st_size
            
            return {
                "success": True,
                "path": str(output_path),
                "filename": filename,
                "timestamp": timestamp,
                "size": size,
                "size_mb": round(size / 1024 / 1024, 2)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": None
            }
    
    def compare_screenshots(
        self,
        before_path: str,
        after_path: str,
        threshold: float = 0.05
    ) -> Dict:
        """
        对比两张截图差异
        
        Args:
            before_path: 之前截图路径
            after_path: 之后截图路径
            threshold: 差异阈值 (0-1)
        
        Returns:
            Dict: {
                "identical": bool,
                "diff_percent": float,
                "diff_path": str,
                "details": Dict
            }
        """
        try:
            from PIL import Image, ImageChips
            import numpy as np
            
            # 打开图片
            img1 = Image.open(before_path).convert('RGB')
            img2 = Image.open(after_path).convert('RGB')
            
            # 调整大小一致
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
            
            # 计算差异
            diff = ImageChips.difference(img1, img2)
            diff_array = np.array(diff)
            
            # 计算差异百分比
            total_pixels = diff_array.size
            diff_pixels = np.sum(np.any(diff_array > 0, axis=2))
            diff_percent = diff_pixels / total_pixels
            
            # 生成差异图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_path = self.screenshots_dir / f"diff_{timestamp}.png"
            diff.save(str(diff_path))
            
            return {
                "identical": diff_percent < threshold,
                "diff_percent": round(diff_percent * 100, 2),
                "diff_path": str(diff_path),
                "threshold": threshold,
                "passed": diff_percent < threshold
            }
            
        except Exception as e:
            return {
                "identical": False,
                "diff_percent": 100.0,
                "error": str(e)
            }
    
    def visual_regression_test(
        self,
        url: str,
        baseline_task_id: str,
        current_task_id: str
    ) -> Dict:
        """
        视觉回归测试
        
        Args:
            url: 测试 URL
            baseline_task_id: 基准任务 ID
            current_task_id: 当前任务 ID
        
        Returns:
            Dict: 测试结果
        """
        # 1. 捕获当前截图
        current_result = self.capture_screenshot(url, current_task_id)
        
        if not current_result["success"]:
            return {
                "success": False,
                "error": "截图失败",
                "details": current_result
            }
        
        # 2. 查找基准截图
        baseline_pattern = f"{baseline_task_id}_*.png"
        baseline_files = list(self.screenshots_dir.glob(baseline_pattern))
        
        if not baseline_files:
            return {
                "success": False,
                "error": "未找到基准截图",
                "baseline_task_id": baseline_task_id
            }
        
        baseline_path = str(baseline_files[0])
        
        # 3. 对比截图
        compare_result = self.compare_screenshots(
            baseline_path,
            current_result["path"]
        )
        
        return {
            "success": True,
            "baseline": baseline_path,
            "current": current_result["path"],
            "diff_percent": compare_result["diff_percent"],
            "passed": compare_result["passed"],
            "diff_image": compare_result.get("diff_path")
        }
    
    # ========== 2. 设计稿→代码 (Figma MCP) ==========
    
    def figma_to_code(
        self,
        figma_url: str,
        output_type: str = "html_css"
    ) -> Dict:
        """
        Figma 设计稿转代码
        
        Args:
            figma_url: Figma 设计稿 URL
            output_type: 输出类型 (html_css/react/vue)
        
        Returns:
            Dict: {
                "success": bool,
                "code": str,
                "assets": List[str]
            }
        """
        # TODO: 集成 Figma MCP
        # 当前返回示例结构
        
        return {
            "success": True,
            "code": f"""
<!-- Figma 设计稿转换结果 -->
<!-- URL: {figma_url} -->
<!-- 类型：{output_type} -->

<div class="container">
  <h1>设计稿转换占位符</h1>
  <p>请集成 Figma MCP 后使用真实功能</p>
</div>

<style>
.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}}
</style>
""",
            "assets": [],
            "metadata": {
                "figma_url": figma_url,
                "output_type": output_type,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def extract_design_tokens(self, figma_url: str) -> Dict:
        """
        提取设计令牌 (颜色、字体、间距等)
        
        Args:
            figma_url: Figma 设计稿 URL
        
        Returns:
            Dict: 设计令牌
        """
        # TODO: 集成 Figma MCP
        
        return {
            "colors": {
                "primary": "#667eea",
                "secondary": "#764ba2",
                "success": "#10b981",
                "danger": "#ef4444"
            },
            "fonts": {
                "heading": "system-ui, sans-serif",
                "body": "Inter, sans-serif"
            },
            "spacing": {
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px"
            }
        }
    
    # ========== 3. 语音任务提交 (ElevenLabs TTS) ==========
    
    def speech_to_task(
        self,
        audio_path: str,
        language: str = "zh-CN"
    ) -> Dict:
        """
        语音转任务描述
        
        Args:
            audio_path: 音频文件路径
            language: 语言 (zh-CN/en-US)
        
        Returns:
            Dict: {
                "success": bool,
                "text": str,
                "confidence": float
            }
        """
        try:
            # 使用 Whisper 进行语音识别
            import whisper
            
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language=language)
            
            return {
                "success": True,
                "text": result["text"],
                "confidence": result.get("avg_logprob", 0.0),
                "language": result.get("language", language),
                "duration": result.get("segments", [{}])[0].get("end", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": None
            }
    
    def task_to_speech(
        self,
        text: str,
        output_filename: Optional[str] = None,
        voice: str = "zh-CN-XiaoxiaoNeural"
    ) -> Dict:
        """
        任务描述转语音 (TTS)
        
        Args:
            text: 文本内容
            output_filename: 输出文件名
            voice: 语音角色
        
        Returns:
            Dict: {
                "success": bool,
                "path": str,
                "duration": float
            }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"task_{timestamp}.mp3"
        output_path = self.audio_dir / filename
        
        try:
            # 使用 Edge TTS (免费)
            import asyncio
            import edge_tts
            
            async def generate_audio():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(output_path))
            
            asyncio.run(generate_audio())
            
            # 获取时长 (使用 ffprobe 或估算)
            duration = len(text) / 15  # 粗略估算：15 字/秒
            
            return {
                "success": True,
                "path": str(output_path),
                "filename": filename,
                "duration": round(duration, 2),
                "voice": voice,
                "text_length": len(text)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": None
            }
    
    # ========== 4. PR 视频演示 (GIF/视频生成) ==========
    
    def generate_pr_gif(
        self,
        screenshots: List[str],
        output_filename: Optional[str] = None,
        duration_per_frame: int = 1000
    ) -> Dict:
        """
        生成 PR 演示 GIF
        
        Args:
            screenshots: 截图路径列表
            output_filename: 输出文件名
            duration_per_frame: 每帧时长 (毫秒)
        
        Returns:
            Dict: {
                "success": bool,
                "path": str,
                "frames": int,
                "duration": float
            }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"pr_demo_{timestamp}.gif"
        output_path = self.videos_dir / filename
        
        try:
            from PIL import Image
            
            # 打开所有图片
            images = []
            for path in screenshots:
                img = Image.open(path)
                # 调整大小
                img = img.resize((800, 600), Image.Resampling.LANCZOS)
                images.append(img)
            
            if not images:
                return {
                    "success": False,
                    "error": "没有图片"
                }
            
            # 保存为 GIF
            images[0].save(
                str(output_path),
                save_all=True,
                append_images=images[1:],
                duration=duration_per_frame,
                loop=0
            )
            
            return {
                "success": True,
                "path": str(output_path),
                "filename": filename,
                "frames": len(images),
                "duration": round(len(images) * duration_per_frame / 1000, 2),
                "size_mb": round(output_path.stat().st_size / 1024 / 1024, 2)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_pr_video(
        self,
        screenshots: List[str],
        output_filename: Optional[str] = None,
        fps: int = 1
    ) -> Dict:
        """
        生成 PR 演示视频
        
        Args:
            screenshots: 截图路径列表
            output_filename: 输出文件名
            fps: 帧率
        
        Returns:
            Dict: {
                "success": bool,
                "path": str,
                "duration": float
            }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"pr_demo_{timestamp}.mp4"
        output_path = self.videos_dir / filename
        
        # 创建临时列表文件
        list_file = self.videos_dir / f"temp_{timestamp}.txt"
        with open(list_file, 'w') as f:
            for path in screenshots:
                f.write(f"file '{path}'\nduration 1\n")
        
        try:
            # 使用 ffmpeg 生成视频
            cmd = [
                "ffmpeg",
                "-y",  # 覆盖输出
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c:v", "libx264",
                "-r", str(fps),
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 清理临时文件
            list_file.unlink()
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "path": str(output_path),
                    "filename": filename,
                    "duration": round(len(screenshots) / fps, 2),
                    "fps": fps,
                    "frames": len(screenshots),
                    "size_mb": round(output_path.stat().st_size / 1024 / 1024, 2)
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            # 清理临时文件
            if list_file.exists():
                list_file.unlink()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    # ========== 综合功能 ==========
    
    def create_pr_demo_package(
        self,
        task_id: str,
        pr_number: int,
        screenshots: List[str]
    ) -> Dict:
        """
        创建 PR 演示包 (GIF + 截图 + 说明)
        
        Args:
            task_id: 任务 ID
            pr_number: PR 编号
            screenshots: 截图列表
        
        Returns:
            Dict: {
                "success": bool,
                "package_path": str,
                "contents": List[str]
            }
        """
        package_dir = self.videos_dir / f"pr_{pr_number}_{task_id}"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 生成 GIF
        gif_result = self.generate_pr_gif(
            screenshots,
            output_filename=f"demo.gif"
        )
        
        # 2. 复制截图到包
        copied_screenshots = []
        for i, path in enumerate(screenshots):
            dest = package_dir / f"screenshot_{i+1}.png"
            import shutil
            shutil.copy2(path, dest)
            copied_screenshots.append(str(dest))
        
        # 3. 移动 GIF 到包
        if gif_result["success"]:
            import shutil
            gif_dest = package_dir / "demo.gif"
            shutil.move(gif_result["path"], str(gif_dest))
        
        # 4. 生成说明文件
        readme_content = f"""# PR #{pr_number} 演示包

**任务 ID**: {task_id}
**生成时间**: {datetime.now().isoformat()}

## 内容

- demo.gif - PR 演示动画
- screenshot_*.png - 页面截图 ({len(screenshots)} 张)

## 统计

- 截图数量：{len(screenshots)}
- GIF 时长：{gif_result.get('duration', 0)} 秒
- GIF 大小：{gif_result.get('size_mb', 0)} MB
"""
        
        readme_path = package_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return {
            "success": True,
            "package_path": str(package_dir),
            "contents": [
                "demo.gif",
                f"screenshot_*.png ({len(screenshots)} 张)",
                "README.md"
            ],
            "gif_result": gif_result
        }


# ========== 全局实例 ==========

_manager: Optional[MultimodalManager] = None


def get_multimodal_manager(config_path: Optional[str] = None) -> MultimodalManager:
    """获取多模态管理器实例"""
    global _manager
    if _manager is None:
        _manager = MultimodalManager(config_path)
    return _manager


# ========== 测试 ==========

if __name__ == "__main__":
    print("🧪 多模态能力测试\n")
    
    manager = MultimodalManager()
    
    print(f"📁 媒体目录：{manager.media_dir}")
    print(f"📸 截图目录：{manager.screenshots_dir}")
    print(f"🎥 视频目录：{manager.videos_dir}")
    print(f"🎵 音频目录：{manager.audio_dir}")
    
    print("\n✅ 多模态管理器初始化完成!")
    print("\n⚠️  注意：部分功能需要安装额外依赖:")
    print("  pip install playwright pillow pillow-simd")
    print("  pip install openai-whisper edge-tts")
    print("  pip install ffmpeg-python")
    print("\n📖 使用示例:")
    print("  from utils.multimodal import get_multimodal_manager")
    print("  manager = get_multimodal_manager()")
    print("  result = manager.capture_screenshot('http://localhost:8890', 'test-001')")
