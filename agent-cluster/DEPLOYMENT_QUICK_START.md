# 🚀 生产环境部署 - 快速选择指南

**服务器**: 39.107.101.25 (阿里云 ECS)  
**更新时间**: 2026-03-06

---

## 📋 部署方案选择

### 方案 A：快速部署（5 分钟，测试环境）

适合：快速验证、内部测试、开发环境

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
sudo ./quick_setup_nginx.sh
```

**包含**:
- ✅ Nginx 反向代理
- ✅ HTTP → HTTPS 重定向
- ✅ 自签名 SSL 证书
- ✅ 基础防火墙规则

**不包含**:
- ❌ Fail2Ban 防暴力破解
- ❌ 限流配置
- ❌ 详细日志监控

---

### 方案 B：完整部署（15 分钟，生产环境）

适合：正式使用、公网访问、长期运行

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
sudo ./deploy_production.sh
```

**包含**:
- ✅ Nginx 反向代理
- ✅ HTTP → HTTPS 重定向
- ✅ SSL 证书（自签名，可替换）
- ✅ UFW 防火墙
- ✅ Fail2Ban 防暴力破解
- ✅ 限流配置（防 DDoS）
- ✅ 安全头配置
- ✅ 监控脚本
- ✅ 定时任务

---

### 方案 C：手动配置（完全控制）

适合：有特殊需求、需要精细控制

参考文档：[PRODUCTION_SECURITY_CONFIG.md](PRODUCTION_SECURITY_CONFIG.md)

---

## 🔧 部署后配置

### 1. 阿里云安全组配置（必需）

登录阿里云控制台 → ECS → 安全组 → 配置规则

**入方向规则**:

| 端口 | 协议 | 授权对象 | 说明 |
|------|------|----------|------|
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 22 | TCP | 你的 IP/32 | SSH（建议限制） |

### 2. 替换 SSL 证书（推荐）

#### 使用 Let's Encrypt（免费）

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
sudo ./setup_ssl.sh
```

#### 使用阿里云证书

1. 阿里云控制台 → SSL 证书 → 购买/上传
2. 下载 Nginx 格式
3. 替换证书文件：

```bash
sudo cp fullchain.pem /etc/nginx/ssl/
sudo cp privkey.pem /etc/nginx/ssl/
sudo systemctl restart nginx
```

### 3. 验证部署

```bash
# 检查 Nginx 状态
systemctl status nginx

# 测试 HTTPS 访问
curl -k https://39.107.101.25/api/status

# 测试 HTTP 重定向
curl -I http://39.107.101.25

# 查看监控
/usr/local/bin/agent-cluster-monitor.sh
```

---

## 📊 部署对比

| 功能 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| Nginx 反向代理 | ✅ | ✅ | ✅ |
| HTTPS | ✅ | ✅ | ✅ |
| UFW 防火墙 | ⚠️ 基础 | ✅ 完整 | ✅ 自定义 |
| Fail2Ban | ❌ | ✅ | ✅ |
| 限流配置 | ❌ | ✅ | ✅ |
| 监控脚本 | ❌ | ✅ | ✅ |
| 部署时间 | 5 分钟 | 15 分钟 | 30+ 分钟 |
| 适用场景 | 测试 | 生产 | 特殊需求 |

---

## 🔒 安全建议

### 必须做

1. ✅ 配置阿里云安全组（只开放 80/443）
2. ✅ 限制 SSH 访问来源 IP
3. ✅ 使用 HTTPS（不要只用 HTTP）
4. ✅ 定期更新系统

### 建议做

1. ⭐ 使用正式 SSL 证书（非自签名）
2. ⭐ 配置 Fail2Ban 防暴力破解
3. ⭐ 定期备份配置文件
4. ⭐ 监控日志发现异常

### 高级防护

1. 🔐 配置 Web 应用基础认证
2. 🔐 使用 Cloudflare 等 CDN
3. 🔐 配置 WAF（Web 应用防火墙）
4. 🔐 定期安全审计

---

## 📋 常用命令

### 服务管理

```bash
# Nginx
systemctl start|stop|restart|status nginx
nginx -t  # 测试配置

# Web 应用
./start_web.sh
pkill -f "web_app.py"

# Fail2Ban
systemctl start|stop|restart|status fail2ban
fail2ban-client status  # 查看状态
```

### 日志查看

```bash
# Nginx 访问日志
tail -f /var/log/nginx/agent-cluster-access.log

# Nginx 错误日志
tail -f /var/log/nginx/agent-cluster-error.log

# Fail2Ban 日志
tail -f /var/log/fail2ban.log

# 监控日志
tail -f /var/log/agent-cluster-monitor.log
```

### 防火墙

```bash
# UFW 状态
ufw status verbose

# 添加规则
ufw allow 443/tcp
ufw allow from 1.2.3.4 to any port 22

# 禁用/启用
ufw disable
ufw enable
```

---

## 🆘 故障排查

### 问题 1: Nginx 无法启动

```bash
# 检查配置
nginx -t

# 查看错误
journalctl -u nginx -n 50

# 检查端口占用
ss -tlnp | grep :80
```

### 问题 2: HTTPS 无法访问

```bash
# 检查 SSL 证书
ls -la /etc/nginx/ssl/

# 检查安全组
# 阿里云控制台 → 安全组 → 确认 443 端口开放

# 测试本地访问
curl -k https://localhost:443
```

### 问题 3: 502 Bad Gateway

```bash
# 检查 Web 应用是否运行
pgrep -f "web_app.py"

# 检查端口
ss -tlnp | grep 8889

# 启动 Web 应用
./start_web.sh
```

### 问题 4: Fail2Ban 误封

```bash
# 查看被封 IP
fail2ban-client status nginx-http-auth

# 解封 IP
fail2ban-client set nginx-http-auth unbanip 1.2.3.4

# 重启 Fail2Ban
systemctl restart fail2ban
```

---

## 📄 相关文件

| 文件 | 用途 |
|------|------|
| `quick_setup_nginx.sh` | 快速部署脚本 |
| `deploy_production.sh` | 完整部署脚本 |
| `nginx_agent_cluster.conf` | Nginx 配置文件 |
| `setup_ssl.sh` | Let's Encrypt 证书脚本 |
| `PRODUCTION_SECURITY_CONFIG.md` | 详细配置文档 |

---

## ✅ 部署检查清单

部署完成后，请确认：

- [ ] Nginx 运行正常
- [ ] HTTPS 可以访问
- [ ] HTTP 自动重定向到 HTTPS
- [ ] 阿里云安全组已配置
- [ ] Web 应用运行正常
- [ ] 监控脚本已配置
- [ ] 日志正常无错误

---

**选择方案开始部署吧！** 🚀

- 测试环境 → 方案 A (`./quick_setup_nginx.sh`)
- 生产环境 → 方案 B (`./deploy_production.sh`)
