# 🎨 多模态能力使用指南

**版本**: v2.3.0+  
**状态**: 新增功能

---

## 📋 功能概览

| 功能 | 状态 | 说明 | 依赖 |
|------|------|------|------|
| **UI 截图** | ✅ 可用 | 自动捕获网页截图 | playwright |
| **视觉回归测试** | ✅ 可用 | 对比 UI 差异 | pillow |
| **Figma→代码** | ⏳ 待集成 | 设计稿转 HTML/CSS | Figma MCP |
| **语音→任务** | ⏳ 待集成 | 语音识别转任务描述 | whisper |
| **任务→语音** | ✅ 可用 | TTS 生成任务语音 | edge-tts |
| **PR GIF** | ✅ 可用 | 生成 PR 演示 GIF | pillow |
| **PR 视频** | ⏳ 待集成 | 生成 PR 演示视频 | ffmpeg |

---

## 🚀 快速开始

### 安装依赖

```bash
# 核心依赖
pip install playwright pillow

# 可选依赖
pip install edge-tts  # 语音合成
pip install openai-whisper  # 语音识别
pip install ffmpeg-python  # 视频生成

# 初始化 Playwright
playwright install
```

### 基础使用

```python
from utils.multimodal import get_multimodal_manager

manager = get_multimodal_manager()

# 1. 捕获截图
result = manager.capture_screenshot(
    url="http://localhost:8890",
    task_id="task-001",
    full_page=True
)
print(f"截图路径：{result['path']}")

# 2. 生成 PR 演示 GIF
gif_result = manager.generate_pr_gif(
    screenshots=["screenshot_1.png", "screenshot_2.png"],
    output_filename="pr_demo.gif"
)
print(f"GIF 路径：{gif_result['path']}")
```

---

## 📸 UI 截图功能

### 捕获截图

```python
result = manager.capture_screenshot(
    url="http://localhost:8890/metrics.html",
    task_id="metrics-test",
    full_page=True  # 完整页面
)

if result["success"]:
    print(f"✅ 截图成功：{result['path']}")
    print(f"   文件大小：{result['size_mb']} MB")
else:
    print(f"❌ 截图失败：{result['error']}")
```

### 视觉回归测试

```python
# 对比两个版本的 UI 差异
result = manager.visual_regression_test(
    url="http://localhost:8890",
    baseline_task_id="v2.1.0",  # 基准版本
    current_task_id="v2.2.0"    # 当前版本
)

if result["success"]:
    print(f"差异百分比：{result['diff_percent']}%")
    print(f"测试通过：{result['passed']}")
    print(f"差异图：{result['diff_image']}")
```

### 手动对比截图

```python
compare_result = manager.compare_screenshots(
    before_path="media/screenshots/before.png",
    after_path="media/screenshots/after.png",
    threshold=0.05  # 5% 差异阈值
)

print(f"差异：{compare_result['diff_percent']}%")
print(f"是否相同：{compare_result['identical']}")
```

---

## 🎵 语音功能

### 语音转任务

```python
result = manager.speech_to_task(
    audio_path="recordings/requirement.wav",
    language="zh-CN"
)

if result["success"]:
    print(f"识别结果：{result['text']}")
    print(f"置信度：{result['confidence']}")
    print(f"时长：{result['duration']} 秒")
else:
    print(f"识别失败：{result['error']}")
```

### 任务转语音

```python
result = manager.task_to_speech(
    text="实现用户登录功能，要求支持邮箱和密码登录，密码加密存储",
    output_filename="task-001-brief.mp3",
    voice="zh-CN-XiaoxiaoNeural"  # 中文女声
)

if result["success"]:
    print(f"✅ 语音生成成功：{result['path']}")
    print(f"   时长：{result['duration']} 秒")
    print(f"   语音：{result['voice']}")
```

**可用语音角色**:
- `zh-CN-XiaoxiaoNeural` - 中文女声
- `zh-CN-YunxiNeural` - 中文男声
- `en-US-JennyNeural` - 英文女声
- `en-US-GuyNeural` - 英文男声

---

## 🎥 PR 演示生成

### 生成 GIF

```python
result = manager.generate_pr_gif(
    screenshots=[
        "media/screenshots/step1.png",
        "media/screenshots/step2.png",
        "media/screenshots/step3.png"
    ],
    output_filename="pr-123-demo.gif",
    duration_per_frame=1000  # 每帧 1 秒
)

print(f"GIF 帧数：{result['frames']}")
print(f"GIF 时长：{result['duration']} 秒")
print(f"GIF 大小：{result['size_mb']} MB")
```

### 生成视频

```python
result = manager.generate_pr_video(
    screenshots=[
        "media/screenshots/step1.png",
        "media/screenshots/step2.png",
        "media/screenshots/step3.png"
    ],
    output_filename="pr-123-demo.mp4",
    fps=1  # 每秒 1 帧
)

print(f"视频时长：{result['duration']} 秒")
print(f"视频大小：{result['size_mb']} MB")
```

### 创建 PR 演示包

```python
package = manager.create_pr_demo_package(
    task_id="task-001",
    pr_number=123,
    screenshots=[
        "media/screenshots/login.png",
        "media/screenshots/dashboard.png",
        "media/screenshots/profile.png"
    ]
)

print(f"演示包路径：{package['package_path']}")
print(f"包含内容：{package['contents']}")
```

**演示包结构**:
```
pr_123_task-001/
├── demo.gif           # PR 演示动画
├── screenshot_1.png   # 页面截图 1
├── screenshot_2.png   # 页面截图 2
├── screenshot_3.png   # 页面截图 3
└── README.md          # 说明文档
```

---

## 🎨 Figma 集成 (待实现)

### 设计稿转代码

```python
result = manager.figma_to_code(
    figma_url="https://www.figma.com/file/xxx/Login-Page",
    output_type="react"  # html_css/react/vue
)

if result["success"]:
    print(f"生成代码：{result['code'][:200]}...")
    print(f"资源文件：{result['assets']}")
```

### 提取设计令牌

```python
tokens = manager.extract_design_tokens(
    figma_url="https://www.figma.com/file/xxx/Design-System"
)

print(f"颜色：{tokens['colors']}")
print(f"字体：{tokens['fonts']}")
print(f"间距：{tokens['spacing']}")
```

---

## 📊 集成到工作流

### 自动截图 (PR 完成时)

```python
# 在 monitor.py 中集成
async def notify_completion(self, task: Dict, result: Dict):
    # ... 原有代码 ...
    
    # 自动捕获 PR 截图
    if result.get("pr_number"):
        manager = get_multimodal_manager()
        screenshot = manager.capture_screenshot(
            url=f"https://github.com/phoenixbull/agent-cluster-test/pull/{result['pr_number']}",
            task_id=task.get("id")
        )
        
        if screenshot["success"]:
            print(f"✅ PR 截图已保存：{screenshot['path']}")
```

### 视觉回归测试 (CI/CD)

```yaml
# .github/workflows/visual-regression.yml
name: Visual Regression Test

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: pip install playwright pillow
        run: playwright install
      
      - name: Run visual regression test
        run: |
          python -c "
          from utils.multimodal import get_multimodal_manager
          manager = get_multimodal_manager()
          result = manager.visual_regression_test(
              url='http://localhost:8890',
              baseline_task_id='main',
              current_task_id='pr-${{ github.event.number }}'
          )
          assert result['passed'], f'UI 差异超过阈值：{result[\"diff_percent\"]}%'
          "
```

### 语音任务提交 (Web 界面)

```html
<!-- 在 Web 界面添加语音输入 -->
<div class="voice-input">
  <button onclick="startRecording()">🎤 语音输入</button>
  <audio id="recording" style="display:none"></audio>
</div>

<script>
async function startRecording() {
  // 录音实现
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  // ... 录音逻辑
  
  // 发送到后端转换
  const formData = new FormData();
  formData.append('audio', blob);
  
  const response = await fetch('/api/speech-to-task', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  document.getElementById('requirement').value = result.text;
}
</script>
```

---

## 🔧 配置选项

在 `cluster_config_v2.json` 中配置:

```json
{
  "multimodal": {
    "enabled": true,
    "screenshot": true,           // UI 截图
    "visual_regression": true,    // 视觉回归测试
    "figma_to_code": false,       // Figma→代码
    "speech_to_task": false,      // 语音→任务
    "task_to_speech": true,       // 任务→语音
    "pr_gif": true,               // PR GIF
    "pr_video": false             // PR 视频
  }
}
```

---

## 📁 文件结构

```
agent-cluster/
├── media/                      # 媒体文件目录
│   ├── screenshots/           # 截图
│   ├── videos/                # 视频/GIF
│   └── audio/                 # 音频
├── utils/
│   └── multimodal.py          # 多模态管理器
└── docs/
    └── MULTIMODAL_GUIDE.md    # 本文档
```

---

## 🧪 测试示例

```python
from utils.multimodal import get_multimodal_manager

manager = get_multimodal_manager()

# 测试 1: 截图
print("📸 测试截图...")
result = manager.capture_screenshot(
    url="http://localhost:8890",
    task_id="test-001"
)
print(f"结果：{result}")

# 测试 2: 生成 GIF
print("\n🎥 测试 GIF 生成...")
gif_result = manager.generate_pr_gif(
    screenshots=[result["path"]],
    output_filename="test.gif"
)
print(f"结果：{gif_result}")

# 测试 3: 语音合成
print("\n🎵 测试语音合成...")
speech_result = manager.task_to_speech(
    text="这是一个测试任务",
    output_filename="test.mp3"
)
print(f"结果：{speech_result}")
```

---

## ⚠️ 注意事项

### 依赖安装

```bash
# 必需依赖
pip install playwright pillow

# 可选依赖
pip install edge-tts           # 语音合成
pip install openai-whisper     # 语音识别
pip install ffmpeg-python      # 视频生成

# 初始化浏览器
playwright install chromium
```

### 性能优化

- **截图**: 使用 `full_page=False` 只截可视区域
- **GIF**: 限制帧数 (<20 帧) 和尺寸 (<800x600)
- **视频**: 使用较低 FPS (1-2 fps)
- **语音**: 使用较短文本 (<500 字)

### 存储管理

```bash
# 定期清理旧媒体文件
find media/screenshots -mtime +7 -delete
find media/videos -mtime +7 -delete
find media/audio -mtime +7 -delete
```

---

## 🔗 相关资源

- [Playwright 文档](https://playwright.dev/python/)
- [Pillow 文档](https://pillow.readthedocs.io/)
- [Edge TTS](https://github.com/rany2/edge-tts)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [FFmpeg](https://ffmpeg.org/)

---

**最后更新**: 2026-03-19  
**版本**: v2.3.0  
**维护者**: Agent 集群团队
