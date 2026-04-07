# 🔒 生产环境安全配置指南

**更新时间**: 2026-03-06  
**服务器**: 阿里云 ECS (39.107.101.25)

---

## 📋 配置清单

| 配置项 | 状态 | 说明 |
|--------|------|------|
| 阿里云安全组 | ⏳ 待配置 | 限制入站流量 |
| Nginx 反向代理 | ⏳ 待配置 | HTTPS、限流、认证 |
| 系统防火墙 | ⏳ 待配置 | 额外防护层 |
| Fail2Ban | ⏳ 待配置 | 防暴力破解 |

---

## 一、阿里云安全组配置

### 1.1 推荐规则

登录阿里云控制台：https://ecs.console.aliyun.com

**入方向规则**：

| 优先级 | 策略 | 协议 | 端口 | 授权对象 | 说明 |
|--------|------|------|------|----------|------|
| 1 | 允许 | TCP | 443 | 0.0.0.0/0 | HTTPS |
| 2 | 允许 | TCP | 80 | 0.0.0.0/0 | HTTP (重定向到 HTTPS) |
| 3 | 允许 | TCP | 22 | 你的办公 IP/32 | SSH (限制 IP) |
| 100 | 拒绝 | ALL | - | 0.0.0.0/0 | 默认拒绝 |

### 1.2 获取你的办公 IP

```bash
curl ifconfig.co
```

### 1.3 配置步骤

1. ECS 控制台 → 实例 → 安全组 → 配置规则
2. 删除 8889 端口的开放规则
3. 添加上述规则
4. 保存

---

## 二、Nginx 反向代理配置

### 2.1 安装 Nginx

```bash
# 安装 Nginx
sudo apt update
sudo apt install -y nginx

# 或使用阿里云镜像
sudo yum install -y nginx

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2.2 配置反向代理

创建配置文件：

```bash
sudo nano /etc/nginx/sites-available/agent-cluster
```

配置内容：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name 39.107.101.25;
    
    # 所有 HTTP 请求重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name 39.107.101.25;
    
    # SSL 证书配置（使用 Let's Encrypt 或阿里云证书）
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 访问日志
    access_log /var/log/nginx/agent-cluster-access.log;
    error_log /var/log/nginx/agent-cluster-error.log;
    
    # 限流配置（防止滥用）
    limit_req_zone $binary_remote_addr zone=agent_limit:10m rate=10r/s;
    limit_req zone=agent_limit burst=20 nodelay;
    
    # 客户端大小限制
    client_max_body_size 50M;
    
    # 反向代理到 Web 应用
    location / {
        proxy_pass http://127.0.0.1:8889;
        proxy_http_version 1.1;
        
        # 代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket 支持（如需要）
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API 限流（更严格）
    location /api/ {
        limit_req_zone $binary_remote_addr zone=api_limit:10m rate=5r/s;
        limit_req zone=api_limit burst=10 nodelay;
        
        proxy_pass http://127.0.0.1:8889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # 禁止访问敏感路径
    location ~ /\. {
        deny all;
    }
    
    location ~* \.(git|svn|env|bak)$ {
        deny all;
    }
}
```

### 2.3 启用配置

```bash
# 创建 SSL 目录
sudo mkdir -p /etc/nginx/ssl

# 启用站点
sudo ln -s /etc/nginx/sites-available/agent-cluster /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 三、SSL 证书配置

### 3.1 使用 Let's Encrypt（免费）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d 39.107.101.25

# 或如果使用域名
sudo certbot --nginx -d your-domain.com
```

### 3.2 使用阿里云证书

1. 阿里云控制台 → SSL 证书 → 购买/上传证书
2. 下载 Nginx 格式证书
3. 上传到服务器：

```bash
sudo cp fullchain.pem /etc/nginx/ssl/
sudo cp privkey.pem /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/privkey.pem
```

### 3.3 自动续期（Let's Encrypt）

```bash
# 测试续期
sudo certbot renew --dry-run

# 添加定时任务（已自动添加）
sudo crontab -l | grep certbot
```

---

## 四、系统防火墙配置

### 4.1 安装 UFW（Ubuntu）

```bash
sudo apt install -y ufw

# 配置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许必要端口
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow from <你的办公 IP> to any port 22  # SSH

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status verbose
```

### 4.2 使用 Firewalld（CentOS）

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<你的办公 IP>" port port="22" protocol="tcp" accept'
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

---

## 五、Fail2Ban 防暴力破解

### 5.1 安装 Fail2Ban

```bash
sudo apt install -y fail2ban
```

### 5.2 配置 Nginx 保护

创建配置文件：

```bash
sudo nano /etc/fail2ban/jail.local
```

配置内容：

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/*error.log

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/*error.log
maxretry = 10
bantime = 7200

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
```

### 5.3 启动 Fail2Ban

```bash
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
sudo systemctl status fail2ban
```

---

## 六、Web 应用基础认证（可选）

### 6.1 创建密码文件

```bash
sudo apt install -y apache2-utils

# 创建用户
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 添加更多用户
sudo htpasswd /etc/nginx/.htpasswd user2
```

### 6.2 Nginx 配置认证

在 location 块中添加：

```nginx
location / {
    auth_basic "Agent Cluster Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://127.0.0.1:8889;
    # ... 其他配置
}
```

---

## 七、完整部署脚本

创建自动化脚本：

```bash
#!/bin/bash
# deploy_production.sh - 生产环境部署脚本

set -e

echo "🚀 开始生产环境部署..."

# 1. 安装 Nginx
echo "📦 安装 Nginx..."
sudo apt update
sudo apt install -y nginx

# 2. 配置 Nginx
echo "⚙️ 配置 Nginx..."
sudo cp nginx_agent_cluster.conf /etc/nginx/sites-available/agent-cluster
sudo ln -sf /etc/nginx/sites-available/agent-cluster /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 3. 安装 SSL 证书
echo "🔒 配置 SSL..."
sudo mkdir -p /etc/nginx/ssl
# 复制证书文件...

# 4. 配置防火墙
echo "🔥 配置防火墙..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 5. 安装 Fail2Ban
echo "🛡️ 安装 Fail2Ban..."
sudo apt install -y fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# 6. 测试并重启 Nginx
echo "✅ 测试配置..."
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "✅ 部署完成！"
echo ""
echo "访问地址：https://39.107.101.25"
echo ""
```

---

## 八、验证清单

### 8.1 基础验证

```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 检查 SSL 配置
sudo nginx -t

# 检查防火墙状态
sudo ufw status

# 检查 Fail2Ban 状态
sudo systemctl status fail2ban
```

### 8.2 安全测试

```bash
# 测试 HTTP 重定向
curl -I http://39.107.101.25

# 测试 HTTPS
curl -kI https://39.107.101.25

# 检查 SSL 等级
# 访问：https://www.ssllabs.com/ssltest/

# 测试限流
for i in {1..30}; do curl -s -o /dev/null -w "%{http_code}\n" https://39.107.101.25/api/status; done
```

### 8.3 日志监控

```bash
# 查看访问日志
sudo tail -f /var/log/nginx/agent-cluster-access.log

# 查看错误日志
sudo tail -f /var/log/nginx/agent-cluster-error.log

# 查看 Fail2Ban 日志
sudo tail -f /var/log/fail2ban.log
```

---

## 九、监控和告警

### 9.1 Nginx 监控

```bash
# 安装 nginx-module-vts（可选，用于详细监控）
# 或使用简单脚本监控

cat > /usr/local/bin/nginx-monitor.sh << 'EOF'
#!/bin/bash
echo "=== Nginx 状态 ==="
systemctl status nginx --no-pager
echo ""
echo "=== 活跃连接 ==="
curl -s http://localhost/nginx_status 2>/dev/null || echo "未配置 status 模块"
echo ""
echo "=== 最近错误 ==="
tail -5 /var/log/nginx/agent-cluster-error.log
EOF

chmod +x /usr/local/bin/nginx-monitor.sh
```

### 9.2 添加 Crontab 监控

```bash
crontab -e

# 每 5 分钟检查 Nginx 状态
*/5 * * * * /usr/local/bin/nginx-monitor.sh >> /var/log/nginx-monitor.log 2>&1
```

---

## 十、配置文件备份

```bash
# 备份重要配置
mkdir -p ~/backup/nginx
sudo cp /etc/nginx/nginx.conf ~/backup/nginx/
sudo cp /etc/nginx/sites-available/agent-cluster ~/backup/nginx/
sudo cp /etc/fail2ban/jail.local ~/backup/nginx/

# 备份日期
DATE=$(date +%Y%m%d)
tar -czf ~/backup/nginx-$DATE.tar.gz ~/backup/nginx/
```

---

## 📋 配置完成后的访问方式

| 类型 | 地址 | 说明 |
|------|------|------|
| HTTPS | https://39.107.101.25 | 推荐，加密传输 |
| HTTP | http://39.107.101.25 | 自动重定向到 HTTPS |
| 内网 | http://127.0.0.1:8889 | Nginx 后端 |

---

## ⚠️ 注意事项

1. **先配置安全组**：在配置 Nginx 前，先在阿里云控制台开放 80/443 端口
2. **备份原配置**：修改前备份重要配置文件
3. **测试环境验证**：建议先在测试环境验证配置
4. **定期更新**：保持系统和软件更新
5. **日志监控**：定期检查日志发现异常

---

**下一步**: 运行部署脚本或按步骤手动配置
