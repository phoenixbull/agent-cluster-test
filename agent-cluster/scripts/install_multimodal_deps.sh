#!/bin/bash
#
# 多模态功能依赖安装脚本
# v2.3.0 多模态增强版
#

set -e

echo "========================================"
echo "  🎨 多模态功能依赖安装"
echo "========================================"
echo ""

# 检测 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📊 Python 版本：$PYTHON_VERSION"

# 核心依赖
echo ""
echo "📦 安装核心依赖..."
pip install pillow --quiet
echo "✅ Pillow 已安装"

# 可选依赖
echo ""
echo "📦 安装可选依赖..."

# Playwright (UI 截图)
read -p "安装 Playwright (UI 截图)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install playwright --quiet
    echo "✅ Playwright 已安装"
    echo "   正在安装浏览器 (这可能需要几分钟)..."
    playwright install chromium --quiet
    echo "✅ Chromium 浏览器已安装"
else
    echo "⏭️  跳过 Playwright"
fi

# Edge TTS (语音合成)
read -p "安装 Edge TTS (语音合成)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install edge-tts --quiet
    echo "✅ Edge TTS 已安装"
else
    echo "⏭️  跳过 Edge TTS"
fi

# Whisper (语音识别)
read -p "安装 Whisper (语音识别)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install openai-whisper --quiet
    echo "✅ Whisper 已安装"
else
    echo "⏭️  跳过 Whisper"
fi

# FFmpeg (视频生成)
echo ""
echo "📦 检查 FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg 已安装 ($(ffmpeg -version | head -1))"
else
    echo "⚠️  FFmpeg 未安装"
    echo "   请使用系统包管理器安装:"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   CentOS: sudo yum install ffmpeg"
    echo "   macOS: brew install ffmpeg"
fi

# 验证安装
echo ""
echo "========================================"
echo "  验证安装"
echo "========================================"
echo ""

python3 << 'EOF'
import sys

print("检查 Python 模块...\n")

modules = {
    "PIL": "pillow",
    "playwright": "playwright (可选)",
    "edge_tts": "edge-tts (可选)",
    "whisper": "whisper (可选)"
}

for module, package in modules.items():
    try:
        __import__(module)
        print(f"✅ {module:<15} ✓")
    except ImportError:
        if "(可选)" in package:
            print(f"⏭️  {module:<15} 未安装 (可选)")
        else:
            print(f"❌ {module:<15} 未安装")
EOF

echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "  1. 运行测试：python3 test_multimodal_integration.py"
echo "  2. 查看文档：cat docs/MULTIMODAL_GUIDE.md"
echo ""
