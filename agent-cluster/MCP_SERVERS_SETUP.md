# 🔧 MCP 服务器安装指南

**安装时间**: 2026-03-25  
**版本**: v1.0

---

## ✅ 已安装的 MCP 服务器

| 服务器 | 位置 | 状态 |
|--------|------|------|
| **Xcode MCP** | `mcp-servers/xcode/` | ✅ 已安装 |
| **Gradle MCP** | `mcp-servers/gradle/` | ✅ 已安装 |
| **Metro MCP** | `mcp-servers/metro/` | ✅ 已安装 |
| **Flutter MCP** | `mcp-servers/flutter/` | ✅ 已安装 |

---

## 📁 文件结构

```
agent-cluster/
└── mcp-servers/
    ├── package.json           # 依赖配置
    ├── node_modules/          # 已安装依赖
    ├── xcode/
    │   └── index.js           # Xcode MCP 服务器
    ├── gradle/
    │   └── index.js           # Gradle MCP 服务器
    ├── metro/
    │   └── index.js           # Metro MCP 服务器 (React Native)
    └── flutter/
        └── index.js           # Flutter MCP 服务器
```

---

## 🚀 启动方式

### 方式 1: 单独启动

```bash
cd /home/admin/.openclaw/workspace/agent-cluster/mcp-servers

# 启动 Xcode MCP
node xcode/index.js

# 启动 Gradle MCP
node gradle/index.js

# 启动 Metro MCP
node metro/index.js

# 启动 Flutter MCP
node flutter/index.js
```

### 方式 2: 通过 OpenClaw 配置

在 `cluster_config_v2.json` 中添加:

```json
{
  "protocols": {
    "mcp": {
      "servers": [
        {
          "name": "xcode",
          "command": "node",
          "args": ["/home/admin/.openclaw/workspace/agent-cluster/mcp-servers/xcode/index.js"]
        },
        {
          "name": "gradle",
          "command": "node",
          "args": ["/home/admin/.openclaw/workspace/agent-cluster/mcp-servers/gradle/index.js"]
        },
        {
          "name": "metro",
          "command": "node",
          "args": ["/home/admin/.openclaw/workspace/agent-cluster/mcp-servers/metro/index.js"]
        },
        {
          "name": "flutter",
          "command": "node",
          "args": ["/home/admin/.openclaw/workspace/agent-cluster/mcp-servers/flutter/index.js"]
        }
      ]
    }
  }
}
```

---

## 🛠️ 可用工具

### Xcode MCP (iOS)

| 工具 | 说明 | 示例 |
|------|------|------|
| `xcode_select` | 选择 Xcode 版本 | `{"path": "/Applications/Xcode.app"}` |
| `xcode_build` | 构建 iOS 项目 | `{"workspace": "App.xcworkspace", "scheme": "App"}` |
| `xcode_test` | 运行测试 | `{"workspace": "App.xcworkspace", "scheme": "App"}` |
| `simulator_list` | 列出模拟器 | `{}` |
| `simulator_launch` | 启动模拟器 | `{"device_id": "xxx"}` |
| `simulator_screenshot` | 截取屏幕 | `{"device_id": "xxx", "output": "/tmp/s.png"}` |
| `pod_install` | 安装 CocoaPods | `{"directory": "."}` |

### Gradle MCP (Android)

| 工具 | 说明 | 示例 |
|------|------|------|
| `gradle_build` | 构建 Android | `{"directory": ".", "task": "assembleRelease"}` |
| `gradle_test` | 运行测试 | `{"directory": "."}` |
| `gradle_dependencies` | 查看依赖 | `{"directory": "."}` |
| `avd_list` | 列出 AVD | `{}` |
| `avd_create` | 创建 AVD | `{"name": "test", "api": "30"}` |
| `avd_launch` | 启动模拟器 | `{"avd_name": "test"}` |
| `adb_devices` | 列出设备 | `{}` |
| `adb_install` | 安装 APK | `{"apk_path": "app.apk"}` |
| `adb_screenshot` | 截取屏幕 | `{"output": "/tmp/s.png"}` |

### Metro MCP (React Native)

| 工具 | 说明 | 示例 |
|------|------|------|
| `rn_bundle` | 打包应用 | `{"platform": "ios"}` |
| `rn_start` | 启动 Metro | `{"port": 8081}` |
| `rn_run_ios` | 运行 iOS | `{"device": "iPhone 15"}` |
| `rn_run_android` | 运行 Android | `{"deviceId": "xxx"}` |
| `rn_test` | 运行测试 | `{"coverage": true}` |
| `rn_doctor` | 检查环境 | `{}` |

### Flutter MCP

| 工具 | 说明 | 示例 |
|------|------|------|
| `flutter_build` | 构建应用 | `{"target": "apk", "release": true}` |
| `flutter_run` | 运行应用 | `{"device_id": "xxx"}` |
| `flutter_test` | 运行测试 | `{"coverage": true}` |
| `flutter_devices` | 列出设备 | `{}` |
| `flutter_doctor` | 检查环境 | `{}` |
| `flutter_build_apk` | 构建 APK | `{"release": true}` |
| `flutter_build_ios` | 构建 iOS | `{"release": true}` |
| `flutter_build_web` | 构建 Web | `{"release": true}` |

---

## 🧪 测试连接

### 测试 Xcode MCP

```bash
# 列出模拟器
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"simulator_list","arguments":{}}}' | \
  node xcode/index.js
```

### 测试 Gradle MCP

```bash
# 列出设备
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"adb_devices","arguments":{}}}' | \
  node gradle/index.js
```

### 测试 Metro MCP

```bash
# 检查环境
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"rn_doctor","arguments":{}}}' | \
  node metro/index.js
```

### 测试 Flutter MCP

```bash
# 检查环境
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"flutter_doctor","arguments":{}}}' | \
  node flutter/index.js
```

---

## ⚠️ 系统要求

### Xcode MCP (macOS only)

- macOS 13.0+
- Xcode 15.0+
- CocoaPods
- Node.js 18+

### Gradle MCP (跨平台)

- JDK 17+
- Android SDK
- Android Studio
- Node.js 18+

### Metro MCP (跨平台)

- Node.js 18+
- React Native CLI
- Watchman (macOS)

### Flutter MCP (跨平台)

- Flutter 3.0+
- Dart 3.0+
- Node.js 18+

---

## 🔧 故障排除

### 问题 1: 找不到命令

```bash
# 确保 Node.js 已安装
node --version

# 确保依赖已安装
cd mcp-servers
npm install
```

### 问题 2: Xcode 命令失败

```bash
# 检查 Xcode 路径
xcode-select -p

# 如果错误，重新设置
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### 问题 3: Android SDK 未找到

```bash
# 设置环境变量
export ANDROID_HOME=/Users/yourname/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

### 问题 4: Flutter 未找到

```bash
# 检查 Flutter 路径
which flutter

# 添加到 PATH
export PATH="$PATH:`pwd`/flutter/bin"
```

---

## 📝 注意事项

1. **macOS 限制**: Xcode MCP 仅能在 macOS 上运行
2. **权限要求**: 某些命令需要 sudo 权限
3. **模拟器资源**: 模拟器运行需要较多内存和 CPU
4. **真机调试**: 需要开发者证书和配置文件

---

## 🚀 下一步

1. **配置 OpenClaw**: 将 MCP 服务器添加到 `cluster_config_v2.json`
2. **测试连接**: 使用上述测试命令验证
3. **集成 Agent**: 让 Mobile Agent 使用这些 MCP 工具
4. **自动化**: 在 CI/CD 流程中使用 MCP 服务器

---

**文档结束**
