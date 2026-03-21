# 高优先级优化实施指南

**版本**: V2.2  
**更新时间**: 2026-03-15  
**备份 Tag**: v2.2-stable

---

## 📋 优化清单

### 1. 安全加固 🔴

- [x] Token 明文存储 → 环境变量
- [x] 无认证 → JWT 认证
- [ ] HTTPS → Nginx 配置（需手动配置）

### 2. 可靠性 🔴

- [x] 健康检查端点
- [x] systemd 服务配置
- [x] 自动重启脚本

### 3. 性能 🔴

- [x] 异步框架（可选）
- [x] 依赖清单

### 4. 实际部署 🔴

- [x] Docker 部署模块
- [x] 部署 API 端点
- [x] 部署管理页面

---

## 🚀 快速开始

### 1. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入实际值
vim .env
```

**必要配置**:
```bash
# GitHub 配置
GITHUB_TOKEN=your_token
GITHUB_USER=phoenixbull
GITHUB_REPO=agent-cluster-test

# 钉钉配置
DINGTALK_WEBHOOK=your_webhook
DINGTALK_SECRET=your_secret

# JWT 配置（重要）
JWT_SECRET_KEY=your_random_secret_key
```

### 2. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 可选：安装异步版本依赖
pip install fastapi uvicorn
```

### 3. 启动服务

**方式 1: 直接启动（同步版本）**
```bash
python3 web_app_v2.py --port 8890
```

**方式 2: 异步版本（推荐生产环境）**
```bash
python3 web_app_async.py
```

**方式 3: 使用看门狗**
```bash
python3 deployment/watchdog.py web_app_v2.py 8890
```

**方式 4: 使用 systemd（推荐）**
```bash
# 复制服务配置
sudo cp deployment/agent-cluster.service /etc/systemd/system/

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable agent-cluster
sudo systemctl start agent-cluster

# 查看状态
sudo systemctl status agent-cluster
```

---

## 🔧 功能使用

### 健康检查

**API**: `GET /api/health`

```bash
curl http://localhost:8890/api/health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-15T22:00:00",
  "service": "agent-cluster",
  "version": "2.2.0"
}
```

### 部署功能

**API**: `POST /api/deploy/execute`

```bash
curl -X POST http://localhost:8890/api/deploy/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "wf-20260315-xxx",
    "project": "my-project",
    "code_path": "/path/to/code"
  }'
```

**管理页面**: http://localhost:8890/web_deploy.html

---

## 🧪 测试

### 运行测试脚本

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 tests/test_optimization.py
```

### 测试清单

- [x] 健康检查端点
- [x] 状态检查端点
- [x] 用户登录
- [x] Agent 列表
- [x] 部署 API

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `GITHUB_TOKEN` | GitHub API Token | 无 |
| `GITHUB_USER` | GitHub 用户名 | phoenixbull |
| `GITHUB_REPO` | GitHub 仓库 | agent-cluster-test |
| `DINGTALK_WEBHOOK` | 钉钉 Webhook | 无 |
| `DINGTALK_SECRET` | 钉钉密钥 | 无 |
| `JWT_SECRET_KEY` | JWT 密钥 | change-this-secret-key |
| `JWT_ALGORITHM` | JWT 算法 | HS256 |
| `JWT_EXPIRATION_HOURS` | JWT 过期时间 | 24 |
| `HOST` | 服务主机 | 0.0.0.0 |
| `PORT` | 服务端口 | 8890 |
| `DEBUG` | 调试模式 | false |

---

## 🔒 安全建议

### 1. 生产环境配置

```bash
# .env 文件
DEBUG=false
JWT_SECRET_KEY=<随机生成的强密钥>
```

### 2. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 强制 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8890;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 防火墙配置

```bash
# 只开放必要端口
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
```

---

## 📊 监控

### 系统日志

```bash
# systemd 服务日志
sudo journalctl -u agent-cluster -f

# 应用日志
tail -f logs/web_app_v2.log
```

### 健康检查

```bash
# 定期检查
watch -n 10 'curl -s http://localhost:8890/api/health | jq .status'
```

---

## 🔄 回滚

### 回滚到优化前

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 切换到备份 tag
git checkout v2.2-stable

# 重启服务
sudo systemctl restart agent-cluster
```

---

## ❓ 故障排查

### 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8890

# 检查日志
sudo journalctl -u agent-cluster -n 50
```

### JWT 认证失败

```bash
# 检查 JWT_SECRET_KEY 是否配置
cat .env | grep JWT_SECRET_KEY

# 确保所有实例使用相同的密钥
```

### Docker 部署失败

```bash
# 检查 Docker 是否运行
sudo systemctl status docker

# 检查 Docker 权限
sudo usermod -aG docker $USER
```

---

## 📝 更新日志

### V2.2.0 (2026-03-15)

**新增**:
- ✅ 环境变量配置
- ✅ JWT 认证
- ✅ 健康检查端点
- ✅ systemd 服务配置
- ✅ 自动重启脚本
- ✅ Docker 部署模块
- ✅ 异步 Web 服务器

**优化**:
- ✅ 向后兼容所有原有功能
- ✅ 保留同步版本
- ✅ 渐进式迁移支持

---

**文档版本**: 1.0  
**维护者**: AI 助手  
**最后更新**: 2026-03-15
