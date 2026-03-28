# Fastlane 配置

Fastlane 用于自动化 iOS 和 Android 应用的构建和发布流程。

## 目录结构

```
fastlane/
├── README.md           # 本文档
├── Fastfile            # Fastlane 配置
├── Appfile             # 应用配置
├── Matchfile           # 证书管理 (iOS)
├── android/
│   └── Fastfile        # Android 配置
└── ios/
    └── Fastfile        # iOS 配置
```

## 设置步骤

### iOS 设置

1. **安装 Fastlane**
   ```bash
   sudo gem install fastlane
   ```

2. **配置 App Store Connect API**
   - 访问 https://appstoreconnect.apple.com/api
   - 创建 API Key
   - 下载 `AuthKey_XXXXXXXXXX.p8`
   - 将密钥内容添加到 GitHub Secrets:
     - `APP_STORE_CONNECT_API_KEY_ID`
     - `APP_STORE_CONNECT_API_ISSUER_ID`
     - `APP_STORE_CONNECT_API_KEY_CONTENT`

3. **配置证书管理 (Match)**
   ```bash
   fastlane match init
   fastlane match development
   ```

4. **运行 Beta 构建**
   ```bash
   cd ios
   fastlane beta
   ```

### Android 设置

1. **安装 Fastlane**
   ```bash
   sudo gem install fastlane
   ```

2. **配置 Google Play API**
   - 访问 Google Play Console
   - 创建服务账号
   - 下载 JSON 密钥文件
   - 将内容 Base64 编码后添加到 GitHub Secrets:
     - `GOOGLE_PLAY_CREDENTIALS`

3. **配置签名密钥**
   - 将 Keystore 文件添加到 GitHub Secrets:
     - `ANDROID_KEYSTORE` (Base64 编码)
     - `ANDROID_KEYSTORE_PASSWORD`
     - `ANDROID_KEY_ALIAS`
     - `ANDROID_KEY_PASSWORD`

4. **运行 Beta 构建**
   ```bash
   cd android
   fastlane beta
   ```

## 可用命令

### iOS

| 命令 | 说明 |
|------|------|
| `fastlane test` | 运行单元测试 |
| `fastlane beta` | 构建并上传到 TestFlight |
| `fastlane release` | 构建并发布到 App Store |
| `fastlane match` | 管理证书和配置文件 |

### Android

| 命令 | 说明 |
|------|------|
| `fastlane test` | 运行单元测试 |
| `fastlane beta` | 构建并上传到 Google Play 内部测试 |
| `fastlane release` | 构建并发布到 Google Play 生产轨道 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `MATCH_PASSWORD` | Match 仓库密码 |
| `APP_STORE_CONNECT_API_KEY_ID` | App Store Connect API Key ID |
| `APP_STORE_CONNECT_API_ISSUER_ID` | App Store Connect Issuer ID |
| `GOOGLE_PLAY_CREDENTIALS` | Google Play API 凭证 |
| `ANDROID_KEYSTORE` | Android 签名密钥库 |
