# Multimodal Tester - 多模态测试专家

## 角色定位

**专长**: 多模态功能测试、UI 截图、视觉回归、PR 演示生成

## 核心能力

### 1. UI 自动截图

```python
# 捕获网页截图
result = manager.capture_screenshot(
    url="http://localhost:8890/metrics.html",
    task_id="test-001",
    full_page=True
)
```

**使用场景**:
- PR 完成后自动截图
- 版本发布前 UI 验收
- 视觉回归测试基准

### 2. 视觉回归测试

```python
# 对比 UI 差异
result = manager.visual_regression_test(
    url="http://localhost:8890",
    baseline_task_id="v2.2.0",
    current_task_id="v2.3.0"
)
```

**使用场景**:
- 新版本 UI 变更检测
- Bug 修复后验证
- 多浏览器兼容性测试

### 3. PR 演示生成

```python
# 生成 GIF 演示
gif = manager.generate_pr_gif(
    screenshots=["s1.png", "s2.png", "s3.png"],
    output_filename="pr-123-demo.gif"
)

# 创建演示包
package = manager.create_pr_demo_package(
    task_id="task-001",
    pr_number=123,
    screenshots=["s1.png", "s2.png"]
)
```

**使用场景**:
- PR 审查时附带动图
- 客户演示
- 文档配图

### 4. 语音交互

```python
# 语音→任务
result = manager.speech_to_task(
    audio_path="requirement.wav",
    language="zh-CN"
)

# 任务→语音
speech = manager.task_to_speech(
    text="实现用户登录功能",
    output_filename="task-brief.mp3"
)
```

**使用场景**:
- 语音需求提交
- 任务简报生成
- 无障碍访问

---

## 集成到工作流

### Phase 4: 测试验证

在测试阶段自动执行:

```python
# 1. UI 截图
screenshot = capture_screenshot(
    url="http://localhost:8890",
    task_id=task_id
)

# 2. 视觉回归测试
regression = visual_regression_test(
    baseline="main",
    current=task_id
)

# 3. 生成测试报告
report = {
    "screenshot": screenshot["path"],
    "diff_percent": regression["diff_percent"],
    "passed": regression["passed"]
}
```

### Phase 6: 部署上线

在部署完成后:

```python
# 1. 捕获生产环境截图
prod_screenshot = capture_screenshot(
    url="https://production.com",
    task_id=f"prod-{task_id}"
)

# 2. 生成 PR 演示包
package = create_pr_demo_package(
    task_id=task_id,
    pr_number=pr_number,
    screenshots=[...]
)

# 3. 发送钉钉通知 (附带演示 GIF)
notify_with_media(
    message="PR 已完成",
    media_path=package["gif_path"]
)
```

---

## 测试用例

### 用例 1: Dashboard 截图测试

```python
def test_dashboard_screenshot():
    """测试 Dashboard 截图功能"""
    manager = get_multimodal_manager()
    
    result = manager.capture_screenshot(
        url="http://localhost:8890/metrics.html",
        task_id="dashboard-test",
        full_page=True
    )
    
    assert result["success"] == True
    assert result["size_mb"] < 5  # 文件大小合理
    print(f"✅ Dashboard 截图成功：{result['path']}")
```

### 用例 2: 视觉回归测试

```python
def test_visual_regression():
    """测试视觉回归检测"""
    manager = get_multimodal_manager()
    
    # 先创建基准截图
    manager.capture_screenshot(
        url="http://localhost:8890",
        task_id="baseline",
        full_page=False
    )
    
    # 模拟 UI 变更 (修改 CSS)
    # ... 修改代码 ...
    
    # 运行回归测试
    result = manager.visual_regression_test(
        url="http://localhost:8890",
        baseline_task_id="baseline",
        current_task_id="after-change"
    )
    
    print(f"差异百分比：{result['diff_percent']}%")
    print(f"测试通过：{result['passed']}")
```

### 用例 3: PR 演示生成

```python
def test_pr_demo_generation():
    """测试 PR 演示包生成"""
    manager = get_multimodal_manager()
    
    # 准备截图
    screenshots = []
    for i, url in enumerate([
        "http://localhost:8890/",
        "http://localhost:8890/metrics.html",
        "http://localhost:8890/workflows"
    ]):
        result = manager.capture_screenshot(
            url=url,
            task_id=f"pr-demo-{i}"
        )
        screenshots.append(result["path"])
    
    # 生成演示包
    package = manager.create_pr_demo_package(
        task_id="pr-test-001",
        pr_number=999,
        screenshots=screenshots
    )
    
    assert package["success"] == True
    assert len(package["contents"]) > 0
    print(f"✅ PR 演示包已生成：{package['package_path']}")
```

### 用例 4: 语音任务提交

```python
def test_speech_to_task():
    """测试语音转任务"""
    manager = get_multimodal_manager()
    
    # 录制语音 (或使用测试文件)
    result = manager.speech_to_task(
        audio_path="test_audio/requirement.wav",
        language="zh-CN"
    )
    
    if result["success"]:
        print(f"识别结果：{result['text']}")
        print(f"置信度：{result['confidence']}")
    else:
        print(f"识别失败：{result['error']}")
```

---

## 自动化测试脚本

创建 `test_multimodal_integration.py`:

```python
#!/usr/bin/env python3
"""
多模态功能集成测试
运行：python3 test_multimodal_integration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from multimodal import get_multimodal_manager


def run_all_tests():
    """运行所有多模态测试"""
    manager = get_multimodal_manager()
    
    print("=" * 60)
    print("🧪 多模态功能集成测试")
    print("=" * 60)
    
    tests = [
        ("UI 截图测试", test_screenshot, manager),
        ("视觉回归测试", test_visual_regression, manager),
        ("PR 演示生成", test_pr_demo, manager),
        ("语音合成测试", test_speech_synthesis, manager),
    ]
    
    results = []
    for name, test_func, mgr in tests:
        print(f"\n📋 {name}...")
        try:
            result = test_func(mgr)
            results.append((name, True, result))
            print(f"✅ {name} 通过")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"❌ {name} 失败：{e}")
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("📊 测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, detail in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print(f"\n总计：{passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    return passed == total


def test_screenshot(manager):
    """截图测试"""
    result = manager.capture_screenshot(
        url="http://localhost:8890",
        task_id="test-screenshot",
        full_page=False
    )
    
    if not result["success"]:
        raise Exception(f"截图失败：{result.get('error')}")
    
    return f"截图路径：{result['path']}"


def test_visual_regression(manager):
    """视觉回归测试"""
    # 先创建基准
    baseline = manager.capture_screenshot(
        url="http://localhost:8890",
        task_id="baseline"
    )
    
    if not baseline["success"]:
        raise Exception("基准截图失败")
    
    # 立即对比 (应该相同)
    result = manager.visual_regression_test(
        url="http://localhost:8890",
        baseline_task_id="baseline",
        current_task_id="current"
    )
    
    if not result["success"]:
        raise Exception(f"回归测试失败：{result.get('error')}")
    
    return f"差异：{result['diff_percent']}%"


def test_pr_demo(manager):
    """PR 演示测试"""
    # 捕获 2 张截图
    screenshots = []
    for i, url in enumerate([
        "http://localhost:8890/",
        "http://localhost:8890/metrics.html"
    ]):
        result = manager.capture_screenshot(
            url=url,
            task_id=f"pr-demo-{i}"
        )
        screenshots.append(result["path"])
    
    # 生成 GIF
    gif_result = manager.generate_pr_gif(
        screenshots=screenshots,
        output_filename="test-demo.gif"
    )
    
    if not gif_result["success"]:
        raise Exception(f"GIF 生成失败：{gif_result.get('error')}")
    
    return f"GIF 路径：{gif_result['path']}"


def test_speech_synthesis(manager):
    """语音合成测试"""
    result = manager.task_to_speech(
        text="这是一个测试任务，用于验证语音合成功能",
        output_filename="test-speech.mp3"
    )
    
    if not result["success"]:
        raise Exception(f"语音合成失败：{result.get('error')}")
    
    return f"语音路径：{result['path']}"


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
```

---

## 集成到监控脚本

修改 `monitor.py` 添加多模态测试:

```python
# 在 ClusterMonitor 类中添加

def __init__(self, config_path: str = "cluster_config.json"):
    # ... 原有代码 ...
    
    # 初始化多模态管理器
    if self.config.get("multimodal", {}).get("enabled"):
        from multimodal import get_multimodal_manager
        self.multimodal = get_multimodal_manager()
        print("✅ 多模态管理器已初始化")
    else:
        self.multimodal = None

async def check_ui_changes(self, task: Dict) -> Dict:
    """检查 UI 变更 (视觉回归测试)"""
    if not self.multimodal:
        return {"enabled": False}
    
    url = task.get("preview_url")
    if not url:
        return {"enabled": False, "error": "无预览 URL"}
    
    # 运行视觉回归测试
    result = self.multimodal.visual_regression_test(
        url=url,
        baseline_task_id=task.get("baseline_id", "main"),
        current_task_id=task.get("id")
    )
    
    return {
        "enabled": True,
        "success": result.get("success", False),
        "diff_percent": result.get("diff_percent", 0),
        "passed": result.get("passed", False)
    }
```

---

## 在 Web 界面添加测试入口

在 `web_app_v2.py` 中添加测试页面:

```python
def get_multimodal_test_page(self):
    """多模态测试页面"""
    return """<!DOCTYPE html>
<html>
<head><title>多模态测试</title></head>
<body>
<h1>🎨 多模态功能测试</h1>

<div class="test-section">
  <h2>📸 UI 截图测试</h2>
  <input type="text" id="screenshotUrl" value="http://localhost:8890">
  <button onclick="takeScreenshot()">截图</button>
  <div id="screenshotResult"></div>
</div>

<div class="test-section">
  <h2>🔄 视觉回归测试</h2>
  <button onclick="runRegressionTest()">运行测试</button>
  <div id="regressionResult"></div>
</div>

<div class="test-section">
  <h2>🎥 PR 演示生成</h2>
  <button onclick="generateDemo()">生成演示</button>
  <div id="demoResult"></div>
</div>

<div class="test-section">
  <h2>🎵 语音合成测试</h2>
  <textarea id="speechText">这是一个测试任务</textarea>
  <button onclick="synthesizeSpeech()">生成语音</button>
  <audio id="audioPlayer" controls style="display:none"></audio>
</div>

<script>
async function takeScreenshot() {
  const url = document.getElementById('screenshotUrl').value;
  const res = await fetch('/api/multimodal/screenshot', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url, task_id: 'web-test-' + Date.now()})
  });
  const result = await res.json();
  document.getElementById('screenshotResult').innerHTML = 
    result.success ? '✅ 截图成功' : '❌ 截图失败：' + result.error;
}

async function runRegressionTest() {
  const res = await fetch('/api/multimodal/regression-test', {method: 'POST'});
  const result = await res.json();
  document.getElementById('regressionResult').innerHTML = 
    `差异：${result.diff_percent}%，通过：${result.passed}`;
}

async function generateDemo() {
  const res = await fetch('/api/multimodal/generate-demo', {method: 'POST'});
  const result = await res.json();
  document.getElementById('demoResult').innerHTML = 
    result.success ? '✅ 演示已生成' : '❌ 生成失败';
}

async function synthesizeSpeech() {
  const text = document.getElementById('speechText').value;
  const res = await fetch('/api/multimodal/speech', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  });
  const result = await res.json();
  if (result.success) {
    const audio = document.getElementById('audioPlayer');
    audio.src = result.path;
    audio.style.display = 'block';
    audio.play();
  }
}
</script>
</body>
</html>"""
```

---

## 运行测试

### 方式 1: 命令行测试

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 安装依赖
pip install playwright pillow
playwright install chromium

# 运行集成测试
python3 test_multimodal_integration.py
```

### 方式 2: Web 界面测试

访问：`http://服务器 IP:8890/multimodal-test`

### 方式 3: 自动测试 (CI/CD)

```yaml
# .github/workflows/multimodal-test.yml
name: Multimodal Test

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          pip install playwright pillow
          playwright install chromium
      
      - name: Run multimodal tests
        run: python3 test_multimodal_integration.py
```

---

**现在可以运行测试了！需要我帮您执行哪个测试？**

1. 运行集成测试脚本
2. 在 Web 界面添加测试入口
3. 集成到监控脚本
4. 创建 CI/CD 工作流

请告诉我您想先测试哪个功能！🧪
