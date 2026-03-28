# 📱 Mobile Agent 配置指南

**创建时间**: 2026-03-25  
**版本**: v2.0 (跨平台支持)

---

## ✅ 已创建 Agent

| Agent | ID | 角色 | 平台 | 状态 |
|-------|----|------|------|------|
| **iOS 专家** | `mobile-ios` | ios_specialist | iOS 15.0+ | ✅ 就绪 |
| **Android 专家** | `mobile-android` | android_specialist | Android 8.0+ | ✅ 就绪 |
| **React Native 专家** | `mobile-react-native` | cross_platform_specialist | iOS + Android | ✅ 就绪 |
| **Flutter 专家** | `mobile-flutter` | cross_platform_specialist | iOS + Android + Web + Desktop | ✅ 就绪 |

---

## 📂 目录结构

```
/home/admin/.openclaw/workspace/agents/
├── mobile-ios/
│   ├── SOUL.md            # 人格定义
│   ├── IDENTITY.md        # 身份标识
│   ├── memory/            # 长期记忆
│   └── sessions/          # 会话记录
├── mobile-android/
│   ├── SOUL.md            # 人格定义
│   ├── IDENTITY.md        # 身份标识
│   ├── memory/            # 长期记忆
│   └── sessions/          # 会话记录
├── mobile-react-native/
│   ├── SOUL.md            # 人格定义
│   ├── IDENTITY.md        # 身份标识
│   ├── memory/            # 长期记忆
│   └── sessions/          # 会话记录
└── mobile-flutter/
    ├── SOUL.md            # 人格定义
    ├── IDENTITY.md        # 身份标识
    ├── memory/            # 长期记忆
    └── sessions/          # 会话记录
```

---

## 🔧 集群配置 (`cluster_config_v2.json`)

### iOS 专家配置

```json
{
  "id": "mobile-ios",
  "name": "iOS 专家",
  "workspace": "~/.openclaw/workspace/agents/mobile-ios",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-coder-plus",
    "temperature": 0.3,
    "max_tokens": 8192
  },
  "role": "ios_specialist",
  "skills": [
    "swift",
    "swiftui",
    "uikit",
    "xcode",
    "app_store",
    "ios_architecture",
    "coredata",
    "push_notification"
  ],
  "mcp_servers": ["filesystem", "github", "xcode"],
  "enabled": true,
  "task_types": ["ios_app", "swiftui", "uikit", "app_store_deploy"],
  "weight": 0.9,
  "phase": "3_development",
  "platform": {
    "name": "iOS",
    "min_version": "15.0",
    "devices": ["iPhone", "iPad"],
    "ide": "Xcode 15+",
    "language": "Swift 5.9+",
    "ui_framework": "SwiftUI",
    "publish": "App Store"
  }
}
```

### Android 专家配置

```json
{
  "id": "mobile-android",
  "name": "Android 专家",
  "workspace": "~/.openclaw/workspace/agents/mobile-android",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-coder-plus",
    "temperature": 0.3,
    "max_tokens": 8192
  },
  "role": "android_specialist",
  "skills": [
    "kotlin",
    "jetpack_compose",
    "android_xml",
    "gradle",
    "google_play",
    "android_architecture",
    "room",
    "push_notification"
  ],
  "mcp_servers": ["filesystem", "github", "gradle"],
  "enabled": true,
  "task_types": ["android_app", "jetpack_compose", "android_xml", "play_store_deploy"],
  "weight": 0.9,
  "phase": "3_development",
  "platform": {
    "name": "Android",
    "min_version": "8.0",
    "api_level": 26,
    "devices": ["Phone", "Tablet", "Foldable"],
    "ide": "Android Studio Hedgehog+",
    "language": "Kotlin",
    "ui_framework": "Jetpack Compose",
    "publish": "Google Play"
  }
}
```

---

## 📋 开发阶段集成

### Phase 3: 开发实现

```
Phase 3: 编码实现
├── Web 前端 → claude-code (React/Vue)
├── 后端 → codex (FastAPI/Python)
├── iOS App → mobile-ios (Swift/SwiftUI)  ← 新增
└── Android App → mobile-android (Kotlin/Compose)  ← 新增
```

### 任务分配逻辑

```python
# orchestrator.py 中的任务分配
if task_type == "ios_app":
    agent = "mobile-ios"
elif task_type == "android_app":
    agent = "mobile-android"
elif task_type == "frontend":
    agent = "claude-code"
```

---

## ⚛️ React Native 专家配置

```json
{
  "id": "mobile-react-native",
  "name": "React Native 专家",
  "workspace": "~/.openclaw/workspace/agents/mobile-react-native",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-coder-plus",
    "temperature": 0.3,
    "max_tokens": 8192
  },
  "role": "cross_platform_specialist",
  "skills": [
    "typescript",
    "react_native",
    "expo",
    "react_navigation",
    "reanimated",
    "redux",
    "app_store",
    "google_play"
  ],
  "mcp_servers": ["filesystem", "github", "metro"],
  "enabled": true,
  "task_types": ["cross_platform_app", "react_native", "expo", "mobile_web"],
  "weight": 0.95,
  "phase": "3_development",
  "platform": {
    "name": "Cross-Platform (React Native)",
    "min_version": "iOS 13.0+, Android 6.0+",
    "devices": ["iPhone", "iPad", "Android Phone", "Android Tablet"],
    "ide": "VS Code, Expo Go",
    "language": "TypeScript 5+",
    "ui_framework": "React Native Components",
    "publish": "App Store + Google Play",
    "features": {
      "hot_reload": true,
      "expo_support": true,
      "native_modules": true,
      "web_support": true
    }
  }
}
```

### 产出物格式

| 文件 | 格式 | 说明 |
|------|------|------|
| `App.tsx` | TypeScript | 应用入口 |
| `src/screens/*.tsx` | TypeScript | 页面组件 |
| `src/components/*.tsx` | TypeScript | 可复用组件 |
| `package.json` | JSON | 依赖配置 |
| `app.json` | JSON | Expo 配置 |
| `ios/` | Xcode | iOS 原生项目 |
| `android/` | Gradle | Android 原生项目 |

---

## 🎯 Flutter 专家配置

```json
{
  "id": "mobile-flutter",
  "name": "Flutter 专家",
  "workspace": "~/.openclaw/workspace/agents/mobile-flutter",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-coder-plus",
    "temperature": 0.3,
    "max_tokens": 8192
  },
  "role": "cross_platform_specialist",
  "skills": [
    "dart",
    "flutter",
    "provider",
    "riverpod",
    "bloc",
    "go_router",
    "hive",
    "platform_channel"
  ],
  "mcp_servers": ["filesystem", "github", "flutter"],
  "enabled": true,
  "task_types": ["cross_platform_app", "flutter", "mobile_web", "desktop_app"],
  "weight": 0.95,
  "phase": "3_development",
  "platform": {
    "name": "Cross-Platform (Flutter)",
    "min_version": "iOS 12.0+, Android 5.0+",
    "devices": ["iPhone", "iPad", "Android Phone", "Android Tablet", "Web", "Desktop"],
    "ide": "Android Studio, VS Code",
    "language": "Dart 3.0+",
    "ui_framework": "Material 3 + Cupertino",
    "publish": "App Store + Google Play + Web",
    "features": {
      "hot_reload": true,
      "six_platforms": true,
      "self_rendering": true,
      "native_performance": true
    }
  }
}
```

### 产出物格式

| 文件 | 格式 | 说明 |
|------|------|------|
| `lib/main.dart` | Dart | 应用入口 |
| `lib/screens/*.dart` | Dart | 页面组件 |
| `lib/widgets/*.dart` | Dart | 可复用组件 |
| `lib/models/*.dart` | Dart | 数据模型 |
| `pubspec.yaml` | YAML | 依赖配置 |
| `ios/` | Xcode | iOS 原生项目 |
| `android/` | Gradle | Android 原生项目 |
| `web/` | HTML/JS | Web 版本 |

---

## 🎯 使用示例

### 提交 iOS 任务

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 方式 1: 命令行
python3 orchestrator.py "[iOS] 创建一个待办事项应用，支持 Swift UI"

# 方式 2: API
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "创建一个 iOS 待办事项应用",
    "platform": "ios",
    "agent": "mobile-ios"
  }'
```

### 提交 Android 任务

```bash
# 命令行
python3 orchestrator.py "[Android] 创建一个待办事项应用，使用 Jetpack Compose"

# API
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "创建一个 Android 待办事项应用",
    "platform": "android",
    "agent": "mobile-android"
  }'
```

### 提交跨平台任务

```bash
# 同时生成 iOS 和 Android
python3 orchestrator.py "[Mobile] 创建一个跨平台待办事项应用，需要 iOS 和 Android 版本"
```

### 提交 React Native 任务

```bash
# 使用 React Native
python3 orchestrator.py "[React Native] 创建一个跨平台待办事项应用，使用 TypeScript 和 Expo"

# API 方式
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "创建一个跨平台待办事项应用",
    "framework": "react-native",
    "agent": "mobile-react-native"
  }'
```

### 提交 Flutter 任务

```bash
# 使用 Flutter
python3 orchestrator.py "[Flutter] 创建一个跨平台待办事项应用，使用 Dart 和 Flutter"

# API 方式
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "创建一个跨平台待办事项应用",
    "framework": "flutter",
    "agent": "mobile-flutter"
  }'
```

---

## 📦 产出物格式

### iOS 专家产出

| 文件 | 格式 | 说明 |
|------|------|------|
| `ContentView.swift` | Swift | SwiftUI 主视图 |
| `AppDelegate.swift` | Swift | 应用代理 |
| `Info.plist` | XML | 应用配置 |
| `*.xcodeproj` | Xcode | 项目文件 |
| `Package.swift` | Swift | SPM 依赖 |
| `README.md` | Markdown | 使用说明 |

### Android 专家产出

| 文件 | 格式 | 说明 |
|------|------|------|
| `MainActivity.kt` | Kotlin | 主 Activity |
| `*.kt` | Kotlin | Compose 组件 |
| `build.gradle.kts` | Kotlin | Gradle 配置 |
| `AndroidManifest.xml` | XML | 应用清单 |
| `settings.gradle.kts` | Kotlin | 项目设置 |
| `README.md` | Markdown | 使用说明 |

---

## 🔗 与其他 Agent 协作

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: 需求分析 (product-manager)                    │
│  输出：PRD 文档 (包含平台特定需求)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2: 设计 (tech-lead + designer)                   │
│  输出：架构设计 + UI 设计 (包含 iOS/Android 规范)          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┬───────────┐
         │           │           │           │
         ▼           ▼           ▼           ▼
┌─────────────┐ ┌─────────┐ ┌───────────┐ ┌───────────┐
│ claude-code │ │  codex  │ │ mobile-ios│ │  mobile-  │
│  (Web 前端)  │ │ (后端)  │ │  (iOS)    │ │  android  │
│             │ │         │ │           │ │ (Android) │
└─────────────┘ └─────────┘ └───────────┘ └───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 4: 测试 (tester)                                 │
│  输出：Web 测试 + iOS 测试 + Android 测试                  │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ 环境要求

### iOS 开发环境
- macOS 13.0+
- Xcode 15.0+
- Swift 5.9+
- iOS Simulator 或真机

### Android 开发环境
- macOS/Windows/Linux
- Android Studio Hedgehog+
- JDK 17+
- Android Emulator 或真机

---

## 📱 平台特定能力

### iOS 专家能力

| 能力 | 支持 |
|------|------|
| SwiftUI | ✅ |
| UIKit | ✅ |
| CoreData | ✅ |
| CloudKit | ✅ |
| Push Notification | ✅ |
| In-App Purchase | ✅ |
| TestFlight | ✅ |
| App Store 发布 | ✅ |

### Android 专家能力

| 能力 | 支持 |
|------|------|
| Jetpack Compose | ✅ |
| XML Views | ✅ |
| Room Database | ✅ |
| Firebase | ✅ |
| Push Notification | ✅ |
| In-App Billing | ✅ |
| Google Play 发布 | ✅ |
| 国内应用商店 | ✅ |

### React Native 专家能力

| 能力 | 支持 |
|------|------|
| TypeScript | ✅ |
| React Native | ✅ |
| Expo | ✅ |
| React Navigation | ✅ |
| Reanimated | ✅ |
| Redux/Zustand | ✅ |
| 原生模块集成 | ✅ |
| App Store + Google Play | ✅ |
| Web 支持 | ✅ |

### Flutter 专家能力

| 能力 | 支持 |
|------|------|
| Dart 3.0 | ✅ |
| Flutter 3.0 | ✅ |
| Provider/Riverpod/Bloc | ✅ |
| Material 3 + Cupertino | ✅ |
| Platform Channel | ✅ |
| Hive/Isar | ✅ |
| 6 平台支持 | ✅ (iOS/Android/Web/Windows/macOS/Linux) |
| App Store + Google Play + Web | ✅ |

---

## 🚀 下一步

1. **测试 Agent 执行**: 提交一个简单的 iOS/Android/RN/Flutter 任务验证
2. **添加 MCP 工具**: 配置 Xcode/Gradle/Metro/Flutter MCP 服务器
3. **配置 CI/CD**: 添加 GitHub Actions 用于构建和发布
4. **性能优化**: 添加性能分析和监控

---

## 📊 技术选型对比

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **iOS Native** | 最佳性能，完整平台特性 | 仅支持 iOS，需 Swift 专家 | iOS 独占应用 |
| **Android Native** | 最佳性能，完整平台特性 | 仅支持 Android，需 Kotlin 专家 | Android 独占应用 |
| **React Native** | 单一代码库，Web 开发者友好，生态丰富 | 性能略低于原生，复杂动画受限 | 快速迭代，团队有 Web 经验 |
| **Flutter** | 6 平台支持，自渲染 UI 一致，高性能 | Dart 学习成本，包体积较大 | 多平台需求，UI 一致性要求高 |

---

## 🎯 推荐方案

| 需求 | 推荐方案 | 使用 Agent |
|------|----------|------------|
| 仅 iOS | iOS Native | `mobile-ios` |
| 仅 Android | Android Native | `mobile-android` |
| iOS + Android (快速) | React Native | `mobile-react-native` |
| iOS + Android + Web + Desktop | Flutter | `mobile-flutter` |
| 高性能 + 完整平台特性 | Native (双团队) | `mobile-ios` + `mobile-android` |

---

**文档结束**
