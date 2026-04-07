# 🔑 GitHub Token 申请与配置指南

## 第 1 步：创建 Personal Access Token

### 1.1 访问 Token 设置页面

打开浏览器访问：
```
https://github.com/settings/tokens
```

或者：
1. 登录 GitHub
2. 点击右上角头像
3. **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**

### 1.2 选择 Token 类型

点击 **"Generate new token"** → 选择 **"Generate new token (classic)"**

> ⚠️ 注意：选择 **classic** 版本，兼容性更好

### 1.3 配置 Token 信息

| 字段 | 填写内容 |
|------|----------|
| **Note** | `Agent Cluster V2.0` (或其他易识别的名称) |
| **Expiration** | `No expiration` (永久) 或 `90 days` |
| **Select scopes** | 勾选以下权限 |

### 1.4 选择权限（重要！）

**必须勾选的权限**:

```
✅ repo (Full control of private repositories)
   └─ 这会子选项全选：
      ✅ repo:status
      ✅ repo_deployment
      ✅ public_repo
      ✅ repo:invite
      ✅ security_events

✅ workflow (Update GitHub Action workflows)

✅ read:org (Read org and team membership)

✅ gist (Create gists)

✅ notifications (Read user notifications)

✅ delete_repo (Delete repositories) - 可选，用于清理
```

**简化版（最小权限）**:
```
✅ repo (全部子选项)
✅ workflow
```

### 1.5 生成 Token

1. 滚动到页面底部
2. 点击 **"Generate token"**
3. **⚠️ 立即复制 Token！** (例如：`ghp_xxxxxxxxxxxxxxxxxxxx`)

> ⚠️ **重要**: Token 只会显示一次！离开页面后无法再查看！
> 
> 如果丢失，需要重新生成。

---

## 第 2 步：保存 Token

### 2.1 临时保存（测试用）

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

### 2.2 永久保存（推荐）

编辑 `~/.bashrc` 或 `~/.zshrc`:

```bash
nano ~/.bashrc

# 添加到文件末尾
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_USER="your-github-username"

# 保存后重新加载
source ~/.bashrc
```

### 2.3 使用 Git Credential Manager

```bash
# 配置 Git 凭据助手
git config --global credential.helper store

# 首次 push 时会保存凭据
```

---

## 第 3 步：验证 Token

### 3.1 使用 gh CLI 验证

```bash
# 安装 gh CLI (如果未安装)
# Ubuntu/Debian
sudo apt install gh

# 使用 token 登录
gh auth login --with-token <<< "ghp_xxxxxxxxxxxxxxxxxxxx"

# 验证连接
gh auth status

# 查看用户信息
gh api user | jq .login

# 列出仓库
gh repo list
```

**预期输出**:
```
✓ Logged in to github.com as your-username
✓ Token: ghp_xxxxxxxxxxxxxxxxxxxx
✓ Git operations for github.com configured to use https protocol.
```

### 3.2 使用 curl 验证

```bash
curl -H "Authorization: token ghp_xxxxxxxxxxxxxxxxxxxx" \
     https://api.github.com/user
```

**预期输出**:
```json
{
  "login": "your-username",
  "id": 12345678,
  "node_id": "MDQ6VXNlcj...",
  "avatar_url": "https://...",
  ...
}
```

### 3.3 测试仓库权限

```bash
# 尝试列出仓库
curl -H "Authorization: token ghp_xxxxxxxxxxxxxxxxxxxx" \
     https://api.github.com/user/repos
```

---

## 第 4 步：创建测试仓库（可选）

### 4.1 创建新仓库

```bash
# 使用 gh CLI 创建
gh repo create agent-test-repo --private --confirm

# 或使用 curl
curl -X POST -H "Authorization: token ghp_xxxxxxxxxxxxxxxxxxxx" \
     -d '{"name":"agent-test-repo","private":true}' \
     https://api.github.com/user/repos
```

### 4.2 克隆到本地

```bash
cd /home/admin/.openclaw/workspace
git clone https://github.com/your-username/agent-test-repo.git
```

---

## 第 5 步：配置 Agent 集群

### 5.1 更新 cluster_config.json

编辑 `cluster_config.json`:

```json
{
  "github": {
    "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "user": "your-username",
    "repo": "agent-test-repo",
    "branch_prefix": "agent/",
    "auto_create_pr": true,
    "auto_merge": false
  },
  "agents": {
    "codex": {
      "mcp_servers": ["filesystem", "github"]
    },
    "claude-code": {
      "mcp_servers": ["filesystem", "github"]
    }
  },
  "workflows": {
    "ci_cd": {
      "enabled": true,
      "github_repo": "your-username/agent-test-repo",
      "required_checks": ["lint", "typecheck", "tests"]
    }
  }
}
```

### 5.2 设置环境变量

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 临时设置
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_REPO="your-username/agent-test-repo"

# 或永久设置（添加到 ~/.bashrc）
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
echo 'export GITHUB_REPO="your-username/agent-test-repo"' >> ~/.bashrc
source ~/.bashrc
```

---

## 第 6 步：测试 GitHub 集成

### 6.1 运行测试脚本

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 测试 GitHub 连接
python3 -c "
import os
import requests

token = os.getenv('GITHUB_TOKEN')
if not token:
    print('❌ GITHUB_TOKEN 未设置')
    exit(1)

headers = {'Authorization': f'token {token}'}
response = requests.get('https://api.github.com/user', headers=headers)

if response.status_code == 200:
    user = response.json()
    print(f'✅ GitHub 连接成功')
    print(f'   用户：{user[\"login\"]}')
    print(f'   ID: {user[\"id\"]}')
else:
    print(f'❌ GitHub 连接失败：{response.status_code}')
"
```

### 6.2 运行真实任务

```bash
# 重新运行测试任务（会创建真实 PR）
python3 cluster_manager.py parallel test_tasks.json
```

### 6.3 查看 PR

任务完成后：
1. 访问 `https://github.com/your-username/agent-test-repo/pulls`
2. 查看新创建的 PR
3. 钉钉会发送包含真实 PR 链接的通知

---

## 🔒 安全建议

### Token 安全

| 建议 | 说明 |
|------|------|
| ✅ 不要提交到 Git | 将 token 添加到 `.gitignore` |
| ✅ 使用环境变量 | 不要硬编码在代码中 |
| ✅ 设置过期时间 | 建议 90 天，定期轮换 |
| ✅ 最小权限原则 | 只授予必要的权限 |
| ✅ 定期轮换 | 每 3 个月更换一次 |

### .gitignore 配置

```bash
# 在 .gitignore 中添加
.env
*.token
secrets.json
cluster_config.local.json
```

### 使用 .env 文件

创建 `.env` 文件：

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USER=your-username
GITHUB_REPO=your-username/agent-test-repo
```

在代码中加载：

```python
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('GITHUB_TOKEN')
```

---

## 🚀 快速配置（一键脚本）

创建 `setup_github.sh`:

```bash
#!/bin/bash

echo "🔑 GitHub Token 配置向导"
echo "========================"
echo ""

# 输入 Token
read -p "请输入 GitHub Token (ghp_开头): " GITHUB_TOKEN

# 验证 Token
echo ""
echo "🔍 验证 Token..."
response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user)
username=$(echo $response | jq -r '.login')

if [ "$username" == "null" ]; then
    echo "❌ Token 无效，请检查后重试"
    exit 1
fi

echo "✅ Token 有效！用户：$username"

# 保存配置
echo ""
echo "💾 保存配置..."
echo "export GITHUB_TOKEN=\"$GITHUB_TOKEN\"" >> ~/.bashrc
echo "export GITHUB_USER=\"$username\"" >> ~/.bashrc

# 重新加载
source ~/.bashrc

echo ""
echo "✅ GitHub 配置完成！"
echo ""
echo "下一步:"
echo "1. 创建测试仓库：gh repo create agent-test --private"
echo "2. 更新 cluster_config.json 中的 github.repo"
echo "3. 运行：python3 cluster_manager.py parallel test_tasks.json"
```

运行：

```bash
chmod +x setup_github.sh
./setup_github.sh
```

---

## 📝 常见问题

### Q1: Token 无效？

**A**: 检查以下几点：
- Token 是否完整复制（包括 `ghp_` 前缀）
- Token 是否已过期
- 权限是否正确勾选

### Q2: 权限不足？

**A**: 确保勾选了 `repo` (全部权限) 和 `workflow`

### Q3: Token 丢失了怎么办？

**A**: 只能重新生成：
1. 访问 https://github.com/settings/tokens
2. 删除旧 token
3. 生成新 token
4. 更新配置

### Q4: 如何撤销 Token？

**A**: 
1. 访问 https://github.com/settings/tokens
2. 找到对应的 token
3. 点击 **Delete**

---

## ✅ 配置完成检查清单

- [ ] 已创建 Personal Access Token
- [ ] Token 已复制并保存
- [ ] 权限已正确配置（repo + workflow）
- [ ] Token 已添加到环境变量
- [ ] gh CLI 已安装并验证
- [ ] 能够访问 GitHub API
- [ ] cluster_config.json 已更新
- [ ] 测试仓库已创建（可选）

---

**配置完成后，Agent 集群就可以创建真实的 PR 了！** 🎉
