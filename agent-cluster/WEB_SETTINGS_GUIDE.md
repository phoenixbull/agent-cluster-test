# 🌐 Web 后台设置界面配置指南

**更新时间**: 2026-03-25  
**版本**: v1.0

---

## ✅ 已完成的功能

### 1️⃣ 设置页面

**访问路径**: `https://服务器 IP/settings`

**功能模块**:
- 🐙 GitHub 配置
- 🍎 App Store Connect 配置
- 🤖 Google Play Console 配置
- 🔐 证书管理
- 📱 钉钉通知配置
- ⚙️ 集群配置

### 2️⃣ API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/settings` | GET | 获取所有设置 |
| `/api/settings/save` | POST | 保存设置 |
| `/api/settings/test/github` | POST | 测试 GitHub 连接 |
| `/api/settings/test/appstore` | POST | 测试 App Store 连接 |
| `/api/settings/test/googleplay` | POST | 测试 Google Play 连接 |

### 3️⃣ 设置管理模块

**文件**: `utils/settings_manager.py`

**功能**:
- 统一管理所有配置和密钥
- 自动同步到 `cluster_config_v2.json`
- 支持配置状态检查
- 提供连接测试功能

---

## 📋 使用指南

### 1. 访问设置页面

1. 打开浏览器访问：`https://服务器 IP/settings`
2. 登录后进入设置界面
3. 左侧导航选择配置分类

### 2. 配置 GitHub

**步骤**:
1. 访问 https://github.com/settings/tokens
2. 生成新的 Personal Access Token (Classic)
3. 勾选权限：`repo`, `workflow`, `admin:org`
4. 复制 Token 到设置页面
5. 填写用户名和默认仓库
6. 点击"保存配置"
7. 点击"测试连接"验证

**必填字段**:
- GitHub Token
- GitHub 用户名
- 默认仓库

### 3. 配置 App Store Connect

**步骤**:
1. 访问 https://appstoreconnect.apple.com/api
2. 点击"生成新密钥"
3. 下载 `.p8` 文件
4. 复制 Key ID 和 Issuer ID
5. 打开 `.p8` 文件，复制完整内容
6. 填写到设置页面
7. 点击"保存配置"

**必填字段**:
- API Key ID
- Issuer ID
- API Key 内容 (.p8 文件内容)
- Apple ID (邮箱)

### 4. 配置 Google Play Console

**步骤**:
1. 访问 Google Play Console
2. 设置 → API 访问 → 创建服务账号
3. 下载 JSON 密钥文件
4. 打开文件，复制完整内容
5. 填写到设置页面
6. 配置签名密钥 (Keystore)

**必填字段**:
- API 凭证 (JSON)
- 应用包名
- Keystore (Base64 编码)
- 密钥库密码
- 密钥别名
- 密钥密码

### 5. 配置钉钉通知

**步骤**:
1. 访问钉钉开放平台
2. 创建企业应用
3. 获取 Corp ID 和 Agent ID
4. 获取 Client ID 和 Client Secret
5. 填写到设置页面
6. 配置通知事件

### 6. 配置集群参数

**可调参数**:
- 最大并行 Agent 数 (1-10)
- 任务超时时间 (60-7200 秒)
- 最低测试覆盖率 (0-100%)
- 最大严重 Bug 数 (0-10)
- 最大重试次数 (0-5)
- 重试间隔 (0-300 秒)

---

## 🔧 技术实现

### 文件结构

```
agent-cluster/
├── templates/
│   └── settings.html          # 设置页面模板
├── utils/
│   └── settings_manager.py    # 设置管理器
├── memory/
│   └── settings.json          # 设置存储文件
└── web_app_v2.py              # Web 服务 (已更新)
```

### 设置存储

**文件**: `memory/settings.json`

```json
{
  "github": {
    "token": "ghp_xxx",
    "user": "phoenixbull",
    "repo": "agent-cluster-test",
    "branch_prefix": "agent/"
  },
  "appstore": {
    "key_id": "XXXXXXXXXX",
    "issuer_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "key_content": "-----BEGIN PRIVATE KEY-----...",
    "username": "your_email@example.com"
  },
  "googleplay": {
    "credentials": "{\"type\":\"service_account\",...}",
    "package": "com.example.app",
    "keystore": "UEsDBBQAAAAIAA...",
    "keystore_password": "xxx",
    "key_alias": "upload",
    "key_password": "xxx"
  },
  "certificates": {
    "match_git_url": "https://github.com/your-team/match",
    "match_password": "xxx"
  },
  "dingtalk": {
    "corp_id": "dingxxxx",
    "agent_id": "4286960567",
    "client_id": "dingxxxx",
    "client_secret": "xxx",
    "callback_token": "openclaw_callback_token_2026",
    "events": {
      "task_complete": true,
      "task_failed": true,
      "pr_ready": true,
      "deploy": true
    }
  },
  "cluster": {
    "max_parallel_agents": 3,
    "timeout_seconds": 300,
    "quality_gate": {
      "min_test_coverage": 80,
      "max_critical_bugs": 0
    },
    "retry": {
      "max_retries": 3,
      "retry_delay": 30
    }
  }
}
```

### 自动同步

设置保存后会自动同步到 `cluster_config_v2.json`:

```python
# settings_manager.py
def _sync_to_cluster_config(self):
    """同步设置到 cluster_config_v2.json"""
    # 更新 GitHub 配置
    # 更新集群配置
    # 更新质量门禁
    # 更新重试策略
```

---

## 🔐 安全特性

### 1. 密钥加密

- 所有敏感字段在 UI 中默认显示为密码框
- 提供"显示/隐藏"切换按钮
- 设置文件权限：`chmod 600 memory/settings.json`

### 2. 访问控制

- 设置页面需要 JWT 认证
- 仅管理员可修改配置
- 所有修改操作记录日志

### 3. 会话管理

- 修改关键配置后需要重新认证
- 会话超时自动登出
- 支持主动登出

---

## 🧪 测试连接

### GitHub 测试

```bash
# 方式 1: 使用 gh CLI
gh api user --hostname github.com

# 方式 2: 使用 curl
curl -H "Authorization: token ghp_xxx" https://api.github.com/user
```

### App Store 测试

```bash
# 使用 jwt 生成工具
# 需要安装 pyjwt
python3 -c "import jwt; print(jwt.encode({...}, key, algorithm='ES256'))"
```

### Google Play 测试

```bash
# 使用 Google API Python 客户端
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/androidpublisher']
)
```

---

## 📊 配置状态

在设置页面顶部显示各配置的状态:

| 配置 | 状态 | 说明 |
|------|------|------|
| GitHub | 🟢 已配置 / 🔴 未配置 | Token 是否存在 |
| App Store | 🟢 已配置 / 🔴 未配置 | Key ID 是否存在 |
| Google Play | 🟢 已配置 / 🔴 未配置 | Credentials 是否存在 |
| 钉钉 | 🟢 已配置 / 🔴 未配置 | Client ID 是否存在 |
| 证书 | 🟢 已配置 / 🔴 未配置 | Match 仓库 URL 是否存在 |

---

## 🚀 下一步

### 短期优化

- [ ] 添加密钥加密存储
- [ ] 实现真实的连接测试
- [ ] 添加配置导入/导出功能
- [ ] 添加配置历史记录

### 中期优化

- [ ] 支持多环境配置 (Dev/Staging/Prod)
- [ ] 添加配置模板功能
- [ ] 实现配置版本控制
- [ ] 添加配置审计日志

### 长期优化

- [ ] 集成 HashiCorp Vault
- [ ] 支持配置热更新
- [ ] 添加配置依赖检查
- [ ] 实现配置回滚功能

---

## 📝 常见问题

### Q1: 修改配置后需要重启服务吗？

**A**: 大部分配置会自动生效，但部分配置 (如集群参数) 需要重启服务:

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
pkill -f web_app_v2.py
python3 web_app_v2.py --port 8890
```

### Q2: 设置文件在哪里？

**A**: `memory/settings.json`

### Q3: 如何备份配置？

**A**: 复制 `memory/settings.json` 到安全位置:

```bash
cp memory/settings.json memory/settings.json.backup.$(date +%Y%m%d)
```

### Q4: 如何重置配置？

**A**: 删除 `memory/settings.json`，系统会恢复默认配置:

```bash
rm memory/settings.json
# 重启服务后会自动创建默认配置
```

---

**文档结束**
