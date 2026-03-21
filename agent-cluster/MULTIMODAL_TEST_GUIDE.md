# 🧪 多模态功能测试指南

**版本**: v2.3.0  
**更新日期**: 2026-03-19

---

## 📋 测试概览

| 测试类型 | 文件 | 依赖 | 预计时间 |
|---------|------|------|---------|
| 集成测试 | `test_multimodal_integration.py` | pillow | 2 分钟 |
| UI 截图测试 | - | playwright | 5 分钟 |
| 语音测试 | - | edge-tts | 3 分钟 |
| GIF 生成测试 | - | pillow | 2 分钟 |

---

## 🚀 快速开始

### 方式 1: 自动安装依赖并测试

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 运行安装脚本 (交互式)
./scripts/install_multimodal_deps.sh

# 运行测试
python3 test_multimodal_integration.py
```

### 方式 2: 手动安装依赖

```bash
# 核心依赖 (必需)
pip install pillow

# UI 截图 (可选)
pip install playwright
playwright install chromium

# 语音合成 (可选)
pip install edge-tts

# 运行测试
python3 test_multimodal_integration.py
```

---

## 📊 测试结果说明

### 通过 ✅

```
✅ 目录结构
✅ 配置加载
✅ 截图功能
✅ GIF 生成
✅ 语音合成
✅ PR 演示包

总计：6/6 通过 (100.0%)
```

**含义**: 所有多模态功能正常，可以投入使用。

### 部分通过 ⚠️

```
✅ 目录结构
✅ 配置加载
❌ 截图功能          No module named 'playwright'
✅ GIF 生成
❌ 语音合成          No module named 'edge_tts'
✅ PR 演示包

总计：4/6 通过 (66.7%)
```

**含义**: 核心功能正常，部分可选功能需要安装依赖。

**解决方案**:
```bash
# 安装缺失的依赖
pip install playwright edge-tts
playwright install chromium

# 重新测试
python3 test_multimodal_integration.py
```

---

## 🧪 单项功能测试

### 测试 1: UI 截图

```python
from utils.multimodal import get_multimodal_manager

manager = get_multimodal_manager()

# 截图测试
result = manager.capture_screenshot(
    url="http://localhost:8890",
    task_id="manual-test-1",
    full_page=False
)

if result["success"]:
    print(f"✅ 截图成功：{result['path']}")
    print(f"   文件大小：{result['size_mb']} MB")
else:
    print(f"❌ 截图失败：{result['error']}")
```

**预期输出**:
```
✅ 截图成功：media/screenshots/manual-test-1_20260319_134500.png
   文件大小：0.5 MB
```

### 测试 2: GIF 生成

```python
from utils.multimodal import get_multimodal_manager
from PIL import Image

manager = get_multimodal_manager()

# 创建测试图片
images = []
for i, color in enumerate(["red", "green", "blue"]):
    img = Image.new('RGB', (200, 200), color=color)
    temp_path = manager.screenshots_dir / f"frame_{i}.png"
    img.save(temp_path)
    images.append(str(temp_path))

# 生成 GIF
gif_result = manager.generate_pr_gif(
    screenshots=images,
    output_filename="test.gif",
    duration_per_frame=500
)

print(f"GIF 路径：{gif_result['path']}")
print(f"帧数：{gif_result['frames']}")
print(f"时长：{gif_result['duration']} 秒")
```

**预期输出**:
```
GIF 路径：media/videos/test.gif
帧数：3
时长：1.5 秒
```

### 测试 3: 语音合成

```python
from utils.multimodal import get_multimodal_manager

manager = get_multimodal_manager()

# 语音合成测试
result = manager.task_to_speech(
    text="这是一个测试任务，用于验证语音合成功能",
    output_filename="test-speech.mp3",
    voice="zh-CN-XiaoxiaoNeural"
)

if result["success"]:
    print(f"✅ 语音合成成功：{result['path']}")
    print(f"   时长：{result['duration']} 秒")
    print(f"   语音：{result['voice']}")
else:
    print(f"❌ 语音合成失败：{result['error']}")
```

**预期输出**:
```
✅ 语音合成成功：media/audio/test-speech.mp3
   时长：2.0 秒
   语音：zh-CN-XiaoxiaoNeural
```

### 测试 4: 视觉回归

```python
from utils.multimodal import get_multimodal_manager

manager = get_multimodal_manager()

# 创建基准截图
baseline = manager.capture_screenshot(
    url="http://localhost:8890",
    task_id="baseline",
    full_page=False
)

# 立即对比 (应该相同)
result = manager.visual_regression_test(
    url="http://localhost:8890",
    baseline_task_id="baseline",
    current_task_id="current"
)

print(f"差异百分比：{result['diff_percent']}%")
print(f"测试通过：{result['passed']}")
```

**预期输出**:
```
差异百分比：0.0%
测试通过：True
```

---

## 🎯 集成到智能体工作流

### 在 Agent 中使用

创建 `agents/designer/multimodal_actions.py`:

```python
from utils.multimodal import get_multimodal_manager

class MultimodalActions:
    """多模态操作类"""
    
    def __init__(self):
        self.manager = get_multimodal_manager()
    
    def capture_ui_after_deploy(self, url: str, task_id: str):
        """部署后捕获 UI 截图"""
        return self.manager.capture_screenshot(
            url=url,
            task_id=task_id,
            full_page=True
        )
    
    def generate_pr_demo(self, task_id: str, pr_number: int, urls: list):
        """生成 PR 演示包"""
        # 捕获所有 URL 的截图
        screenshots = []
        for url in urls:
            result = self.manager.capture_screenshot(
                url=url,
                task_id=f"{task_id}-{len(screenshots)}"
            )
            if result["success"]:
                screenshots.append(result["path"])
        
        # 生成演示包
        return self.manager.create_pr_demo_package(
            task_id=task_id,
            pr_number=pr_number,
            screenshots=screenshots
        )
    
    def run_visual_regression(self, url: str, baseline_id: str, current_id: str):
        """运行视觉回归测试"""
        return self.manager.visual_regression_test(
            url=url,
            baseline_task_id=baseline_id,
            current_task_id=current_id
        )
```

### 集成到监控脚本

在 `monitor.py` 中添加:

```python
async def check_ui_changes(self, task: Dict) -> Dict:
    """检查 UI 变更"""
    if not hasattr(self, 'multimodal') or not self.multimodal:
        return {"enabled": False}
    
    url = task.get("preview_url")
    if not url:
        return {"enabled": False}
    
    # 运行视觉回归测试
    result = self.multimodal.visual_regression_test(
        url=url,
        baseline_task_id="main",
        current_task_id=task.get("id")
    )
    
    # 如果差异过大，发送通知
    if result.get("diff_percent", 0) > 10:  # 超过 10% 差异
        await self.notify_ui_change(task, result)
    
    return result
```

---

## 📁 文件结构

```
agent-cluster/
├── test_multimodal_integration.py    # 集成测试脚本
├── MULTIMODAL_TEST_GUIDE.md          # 本文档
├── scripts/
│   └── install_multimodal_deps.sh    # 依赖安装脚本
├── utils/
│   └── multimodal.py                 # 多模态管理器
├── media/                            # 媒体文件目录
│   ├── screenshots/                  # 截图
│   ├── videos/                       # 视频/GIF
│   └── audio/                        # 音频
└── agents/
    └── multimodal-tester/
        └── SOUL.md                   # 多模态测试专家人格
```

---

## 🔧 故障排查

### 问题 1: Playwright 安装失败

```bash
# 错误：playwright install chromium 卡住
# 解决：使用国内镜像

export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### 问题 2: Pillow 导入失败

```bash
# 错误：No module named 'PIL'
# 解决：重新安装

pip uninstall pillow
pip install pillow --no-cache-dir
```

### 问题 3: 语音合成失败

```bash
# 错误：edge-tts 连接超时
# 解决：检查网络连接或使用代理

pip install edge-tts --upgrade
```

### 问题 4: GIF 太大

```python
# 解决：减小尺寸和帧数
gif_result = manager.generate_pr_gif(
    screenshots=screenshots,
    output_filename="demo.gif",
    duration_per_frame=1000  # 降低帧率
)
```

---

## 📖 相关文档

- [MULTIMODAL_GUIDE.md](docs/MULTIMODAL_GUIDE.md) - 多模态使用指南
- [VERSION.md](VERSION.md) - 版本历史 (v2.3.0)
- [agents/multimodal-tester/SOUL.md](agents/multimodal-tester/SOUL.md) - 测试专家人格

---

## ✅ 测试清单

运行测试前检查:

- [ ] Python 3.8+ 已安装
- [ ] 工作目录正确 (`/home/admin/.openclaw/workspace/agent-cluster`)
- [ ] 依赖已安装 (`pillow` 必需，其他可选)
- [ ] Web 服务运行中 (用于截图测试)

运行测试后验证:

- [ ] 所有目录已创建
- [ ] 配置文件正确加载
- [ ] 测试媒体文件已生成
- [ ] 无错误输出

---

**最后更新**: 2026-03-19  
**版本**: v2.3.0  
**维护者**: Agent 集群团队
