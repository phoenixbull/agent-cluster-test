# CI/CD Secrets 配置指南

**生产环境必需** - 按照以下步骤配置 GitHub Secrets

---

## 🔑 必需配置的 Secrets

### 1. Docker Hub 认证

用于推送 Docker 镜像到 Docker Hub。

**Secrets 名称**:
- `DOCKER_USERNAME` - Docker Hub 用户名
- `DOCKER_PASSWORD` - Docker Hub 密码或 Access Token

**获取方式**:
1. 登录 https://hub.docker.com
2. Account Settings → Security
3. 创建 Access Token
4. 添加到 GitHub Secrets

**配置路径**:
```
GitHub 仓库 → Settings → Secrets and variables → Actions
→ New repository secret
```

---

### 2. Kubernetes 集群认证

用于部署到 K8s 集群。

**Secrets 名称**:
- `STAGING_KUBECONFIG` - Staging 集群 kubeconfig (Base64 编码)
- `PRODUCTION_KUBECONFIG` - Production 集群 kubeconfig (Base64 编码)

**获取方式**:
```bash
# Staging 集群
kubectl config view --raw --minify | base64 -w0

# Production 集群
kubectl config view --raw --minify | base64 -w0
```

**注意**: kubeconfig 文件包含敏感信息，请妥善保管。

---

### 3. 钉钉通知

用于发送部署通知到钉钉群。

**Secrets 名称**:
- `DINGTALK_WEBHOOK` - 钉钉机器人 Webhook URL
- `DINGTALK_SECRET` - 钉钉机器人加签密钥

**获取方式**:
1. 钉钉群 → 群设置 → 智能群助手
2. 添加机器人 → 自定义
3. 设置 webhook 和加签密钥
4. 添加到 GitHub Secrets

**Webhook 格式**:
```
https://oapi.dingtalk.com/robot/send?access_token=xxx
```

---

### 4. GitHub Token (可选)

用于触发工作流和 API 调用。

**Secrets 名称**:
- `GITHUB_TOKEN` - GitHub Personal Access Token

**获取方式**:
1. GitHub Settings → Developer settings → Personal access tokens
2. 生成新 Token (scope: repo, workflow)
3. 添加到 Secrets

---

## 📋 完整 Secrets 列表

| Secret 名称 | 必需 | 用途 | 环境 |
|------------|------|------|------|
| `DOCKER_USERNAME` | ✅ | Docker Hub 用户名 | 全部 |
| `DOCKER_PASSWORD` | ✅ | Docker Hub 密码 | 全部 |
| `STAGING_KUBECONFIG` | ✅ | Staging 集群认证 | Staging |
| `PRODUCTION_KUBECONFIG` | ✅ | Production 集群认证 | Production |
| `DINGTALK_WEBHOOK` | ✅ | 钉钉通知 | 全部 |
| `DINGTALK_SECRET` | ✅ | 钉钉加签 | 全部 |
| `GITHUB_TOKEN` | ⚠️ | GitHub API | 全部 |

---

## 🔧 配置步骤

### 步骤 1: 打开 Secrets 设置

1. 打开 GitHub 仓库
2. 点击 **Settings**
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**

### 步骤 2: 添加每个 Secret

对每个 Secret 重复以下步骤:

1. **Name**: 输入 Secret 名称 (如 `DOCKER_USERNAME`)
2. **Value**: 输入 Secret 值
3. 点击 **Add secret**

### 步骤 3: 验证配置

配置完成后，运行以下命令验证:

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 utils/cicd_integration.py status
```

---

## 🛡️ 安全最佳实践

### 1. 最小权限原则

- Docker Hub: 只给写权限，不要给管理员权限
- Kubernetes: 使用 ServiceAccount，限制命名空间权限
- GitHub Token: 只给必要的 scope

### 2. 定期轮换

- 每 90 天轮换一次所有 Secret
- 员工离职时立即轮换相关 Secret
- 使用 Secret 管理工具 (如 HashiCorp Vault)

### 3. 环境隔离

- Staging 和 Production 使用不同的 kubeconfig
- 不同环境使用不同的 Docker Hub 账号
- 钉钉通知使用不同的机器人

### 4. 审计日志

- 启用 GitHub Audit Log
- 定期检查 Secret 访问记录
- 监控异常部署行为

---

## 🚨 常见问题

### Q1: 部署失败，提示 "unauthorized"

**原因**: Docker Hub 认证失败

**解决**:
1. 检查 `DOCKER_USERNAME` 和 `DOCKER_PASSWORD` 是否正确
2. 确认 Docker Hub 账号有写权限
3. 重新生成 Access Token

### Q2: kubectl 命令失败

**原因**: Kubeconfig 配置错误

**解决**:
1. 确认 kubeconfig 已正确 Base64 编码
2. 检查 kubeconfig 中的集群地址是否可访问
3. 验证 ServiceAccount 权限

### Q3: 钉钉通知未发送

**原因**: Webhook 或加签密钥错误

**解决**:
1. 检查 Webhook URL 是否正确
2. 确认加签密钥匹配
3. 测试机器人是否正常工作

---

## 📝 验证清单

配置完成后，请确认:

- [ ] `DOCKER_USERNAME` 已配置
- [ ] `DOCKER_PASSWORD` 已配置
- [ ] `STAGING_KUBECONFIG` 已配置
- [ ] `PRODUCTION_KUBECONFIG` 已配置
- [ ] `DINGTALK_WEBHOOK` 已配置
- [ ] `DINGTALK_SECRET` 已配置
- [ ] CI 工作流测试通过
- [ ] Staging 部署测试通过
- [ ] Production 部署测试通过
- [ ] 钉钉通知测试通过

---

## 🎯 下一步

配置完成后:

1. **测试 CI 流程**: 推送代码到 develop 分支
2. **测试 Staging 部署**: 合并到 develop 或手动触发
3. **测试 Production 部署**: 合并到 main 并审批
4. **测试回滚流程**: 手动触发回滚工作流

---

**文档**: `CI_CD_SECRETS_SETUP.md`  
**更新时间**: 2026-03-28  
**版本**: v1.0
