# 📱 Native App 优化实施报告

**实施时间**: 2026-03-25  
**版本**: v1.0

---

## ✅ 已完成的优化

### 1️⃣ 集群配置更新

**文件**: `cluster_config_v2.json`

#### 更新内容

| 配置项 | 修改前 | 修改后 |
|--------|--------|--------|
| `multimodal.figma_to_code` | `false` | `true` ✅ |
| `multimodal.design_tokens` | - | `true` ✅ |
| `multimodal.lottie_animation` | - | `true` ✅ |
| `mcp.servers` | 8 个 | 12 个 ✅ |

#### 新增 MCP 服务器

```json
{
  "mcp": {
    "servers": [
      "obsidian",
      "memory",
      "filesystem",
      "github",
      "database",
      "dingtalk",
      "figma",
      "excalidraw",
      "xcode",       // 新增
      "gradle",      // 新增
      "metro",       // 新增
      "flutter"      // 新增
    ]
  }
}
```

---

### 2️⃣ Mobile Tester Agent 创建

**文件**: `/home/admin/.openclaw/workspace/agents/mobile-tester/`

#### Agent 信息

| 属性 | 值 |
|------|-----|
| **ID** | `mobile-tester` |
| **名称** | 移动测试专家 |
| **角色** | mobile_qa_specialist |
| **模型** | qwen-coder-plus |
| **Emoji** | 📱 |

#### 技能列表

```json
{
  "skills": [
    "xctest",
    "espresso",
    "detox",
    "flutter_test",
    "appium",
    "screenshot_test",
    "performance_test"
  ]
}
```

#### 平台支持

| 平台 | 测试框架 | 工具 |
|------|----------|------|
| **iOS** | XCTest, XCUITest, Quick, Nimble | Instruments, simctl |
| **Android** | JUnit, Espresso, UI Automator | Android Profiler, adb |
| **跨平台** | Detox, Appium, Maestro | Firebase Test Lab |

---

### 3️⃣ CI/CD 配置 (GitHub Actions)

**文件**: `.github/workflows/mobile-build.yml`

#### 支持的平台

| 平台 | Runner | 构建命令 |
|------|--------|----------|
| **iOS** | macos-latest | `xcodebuild` |
| **Android** | ubuntu-latest | `./gradlew assembleRelease` |
| **React Native** | ubuntu-latest | `npm run build` |
| **Flutter** | ubuntu-latest | `flutter build` |

#### 触发条件

| 事件 | 分支 | 触发条件 |
|------|------|----------|
| Push | main, develop | 包含 `[iOS]`, `[Android]`, `[Mobile]`, `[React Native]`, `[Flutter]` |
| Pull Request | main | 所有 PR |
| Deploy | main | 包含 `[Deploy]` |

#### 部署目标

| 平台 | 部署目标 | 触发条件 |
|------|----------|----------|
| **iOS** | TestFlight | `main` 分支 + `[Deploy]` |
| **Android** | Google Play 内部测试 | `main` 分支 + `[Deploy]` |

---

### 4️⃣ Fastlane 配置

**目录**: `fastlane/`

#### 文件结构

```
fastlane/
├── README.md              # 使用指南
├── Fastfile               # 通用配置
├── Appfile                # 应用配置
├── ios/
│   └── Fastfile           # iOS 配置
└── android/
    ├── Fastfile           # Android 配置
    └── Appfile            # Android 配置
```

#### iOS Fastlane 命令

| 命令 | 说明 |
|------|------|
| `fastlane test` | 运行单元测试 |
| `fastlane beta` | 构建并上传到 TestFlight |
| `fastlane release` | 发布到 App Store |
| `fastlane match` | 管理证书 |

#### Android Fastlane 命令

| 命令 | 说明 |
|------|------|
| `fastlane test` | 运行单元测试 |
| `fastlane beta` | 上传到 Google Play 内部测试 |
| `fastlane release` | 发布到 Google Play 生产 |

---

## 📊 Agent 集群状态

### 当前 Agent 总数：12 个

| 阶段 | Agent | 状态 |
|------|-------|------|
| **Phase 1** | product-manager | ✅ |
| **Phase 2** | tech-lead, designer | ✅ |
| **Phase 3** | codex, claude-code | ✅ |
| **Phase 3 (Mobile)** | mobile-ios, mobile-android | ✅ |
| **Phase 3 (Cross)** | mobile-react-native, mobile-flutter | ✅ |
| **Phase 4** | tester, mobile-tester | ✅ |
| **Phase 5** | 3 reviewers | ✅ |

---

## 🔧 需要手动配置的内容

### 1. GitHub Secrets

需要在 GitHub 仓库设置以下 Secrets:

#### App Store Connect (iOS)

| Secret | 说明 | 获取方式 |
|--------|------|----------|
| `APP_STORE_CONNECT_API_KEY_ID` | API Key ID | App Store Connect → Users and Access → Keys |
| `APP_STORE_CONNECT_API_ISSUER_ID` | Issuer ID | 同上 |
| `APP_STORE_CONNECT_API_KEY_CONTENT` | Key 内容 | 下载 `.p8` 文件 |
| `APP_STORE_CONNECT_USERNAME` | Apple ID | 你的 Apple ID |

#### Google Play (Android)

| Secret | 说明 | 获取方式 |
|--------|------|----------|
| `GOOGLE_PLAY_CREDENTIALS` | API 凭证 | Google Play Console → API Access |
| `ANDROID_KEYSTORE` | 签名密钥库 | 本地生成或 Play App Signing |
| `ANDROID_KEYSTORE_PASSWORD` | 密钥库密码 | 自设 |
| `ANDROID_KEY_ALIAS` | 密钥别名 | 自设 |
| `ANDROID_KEY_PASSWORD` | 密钥密码 | 自设 |

### 2. MCP 服务器安装

需要安装以下 MCP 服务器:

```bash
# Xcode MCP (macOS only)
npm install -g @modelcontextprotocol/server-xcode

# Gradle MCP
npm install -g @modelcontextprotocol/server-gradle

# Metro MCP (React Native)
npm install -g @modelcontextprotocol/server-metro

# Flutter MCP
npm install -g @modelcontextprotocol/server-flutter
```

### 3. 证书和签名配置

#### iOS

```bash
# 创建 Match 仓库
fastlane match init

# 创建开发证书
fastlane match development

# 创建发布证书
fastlane match appstore
```

#### Android

```bash
# 生成签名密钥
keytool -genkey -v -keystore keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload
```

---

## 🚀 使用指南

### 提交 Native App 任务

```bash
# iOS 任务
python3 orchestrator.py "[iOS] 创建一个待办事项应用"

# Android 任务
python3 orchestrator.py "[Android] 创建一个待办事项应用"

# React Native 任务
python3 orchestrator.py "[React Native] 创建跨平台应用"

# Flutter 任务
python3 orchestrator.py "[Flutter] 创建跨平台应用"

# 自动部署
python3 orchestrator.py "[Deploy] 发布应用到测试轨道"
```

### 触发 CI/CD

```bash
# 提交代码并触发构建
git commit -m "[iOS] 添加登录功能"
git push

# 触发部署
git commit -m "[Deploy] 发布 v1.0.0 到 TestFlight"
git push
```

---

## 📈 优化效果对比

| 能力 | 优化前 | 优化后 |
|------|--------|--------|
| **MCP 服务器** | 8 个 | 12 个 ✅ |
| **Mobile Agent** | 4 个 | 6 个 ✅ |
| **Figma 集成** | ❌ | ✅ |
| **CI/CD** | ❌ | ✅ (GitHub Actions) |
| **自动化发布** | ❌ | ✅ (Fastlane) |
| **移动测试** | ⚠️ 通用 | ✅ 平台特定 |

---

## 📝 下一步计划

### 短期 (1 周内)

- [ ] 安装 Xcode MCP 服务器
- [ ] 安装 Gradle MCP 服务器
- [ ] 配置 GitHub Secrets
- [ ] 测试 CI/CD 流程

### 中期 (2-4 周)

- [ ] 配置设备/模拟器管理
- [ ] 集成性能分析工具
- [ ] 设置线上监控 (Sentry/Firebase)
- [ ] 配置国内应用商店发布

### 长期 (1-3 月)

- [ ] 设备农场集成
- [ ] 自动化截图测试
- [ ] A/B 测试框架
- [ ] 灰度发布支持

---

**文档结束**
