#!/bin/bash
# deploy_production.sh - Agent 集群生产环境部署脚本
# 用途：配置 Nginx 反向代理、SSL、防火墙、Fail2Ban

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
NGINX_PORT_HTTP=80
NGINX_PORT_HTTPS=443
BACKEND_PORT=8889
SERVER_IP="39.107.101.25"
WORKSPACE="/home/admin/.openclaw/workspace/agent-cluster"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 root 权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        log_info "检测到操作系统：$OS ($VERSION_ID)"
    else
        log_error "无法检测操作系统"
        exit 1
    fi
}

# 安装 Nginx
install_nginx() {
    log_info "安装 Nginx..."
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt update
        apt install -y nginx
    elif [ "$OS" = "centos" ] || [ "$OS" = "almalinux" ] || [ "$OS" = "rocky" ]; then
        yum install -y epel-release
        yum install -y nginx
    else
        log_error "不支持的操作系统：$OS"
        exit 1
    fi
    
    systemctl start nginx
    systemctl enable nginx
    log_success "Nginx 安装完成"
}

# 生成自签名 SSL 证书（测试用）
generate_ssl_cert() {
    log_info "生成自签名 SSL 证书（测试环境）..."
    
    mkdir -p /etc/nginx/ssl
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/privkey.pem \
        -out /etc/nginx/ssl/fullchain.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=AgentCluster/CN=$SERVER_IP" \
        2>/dev/null
    
    chmod 600 /etc/nginx/ssl/privkey.pem
    chmod 644 /etc/nginx/ssl/fullchain.pem
    
    log_success "SSL 证书生成完成（有效期：365 天）"
    log_warn "生产环境请替换为正式证书（Let's Encrypt 或阿里云证书）"
}

# 配置 Nginx
configure_nginx() {
    log_info "配置 Nginx 反向代理..."
    
    # 复制配置文件
    cp "$WORKSPACE/nginx_agent_cluster.conf" /etc/nginx/sites-available/agent-cluster
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/agent-cluster /etc/nginx/sites-enabled/
    
    # 删除默认配置
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    
    # 重启 Nginx
    systemctl restart nginx
    
    log_success "Nginx 配置完成"
}

# 配置 UFW 防火墙
configure_ufw() {
    log_info "配置 UFW 防火墙..."
    
    # 检查 UFW 是否安装
    if ! command -v ufw &> /dev/null; then
        log_warn "UFW 未安装，正在安装..."
        apt install -y ufw
    fi
    
    # 配置默认策略
    ufw default deny incoming
    ufw default allow outgoing
    
    # 允许必要端口
    ufw allow $NGINX_PORT_HTTP/tcp comment "HTTP"
    ufw allow $NGINX_PORT_HTTPS/tcp comment "HTTPS"
    
    # SSH 端口（建议限制 IP）
    log_warn "SSH 端口 22 保持开放，建议限制来源 IP"
    ufw allow 22/tcp comment "SSH"
    
    # 启用防火墙
    echo "y" | ufw enable
    
    log_success "UFW 防火墙配置完成"
    ufw status verbose
}

# 安装 Fail2Ban
install_fail2ban() {
    log_info "安装 Fail2Ban..."
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt install -y fail2ban
    elif [ "$OS" = "centos" ] || [ "$OS" = "almalinux" ]; then
        yum install -y fail2ban
    fi
    
    # 创建 Jail 配置
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
backend = auto

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/*error.log
maxretry = 5

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/*error.log
maxretry = 10
bantime = 7200
EOF
    
    systemctl start fail2ban
    systemctl enable fail2ban
    
    log_success "Fail2Ban 安装完成"
}

# 创建监控脚本
create_monitor_script() {
    log_info "创建监控脚本..."
    
    cat > /usr/local/bin/agent-cluster-monitor.sh << 'EOF'
#!/bin/bash
echo "=== Agent Cluster 状态 ==="
echo "时间：$(date)"
echo ""
echo "=== Nginx 状态 ==="
systemctl status nginx --no-pager | head -5
echo ""
echo "=== Web 应用状态 ==="
pgrep -f "web_app.py" > /dev/null && echo "✅ Web 应用运行中" || echo "❌ Web 应用未运行"
echo ""
echo "=== 端口监听 ==="
ss -tlnp | grep -E ":(80|443|8889)" || echo "未找到监听端口"
echo ""
echo "=== 最近错误日志 ==="
tail -3 /var/log/nginx/agent-cluster-error.log 2>/dev/null || echo "无错误日志"
EOF
    
    chmod +x /usr/local/bin/agent-cluster-monitor.sh
    
    log_success "监控脚本创建完成：/usr/local/bin/agent-cluster-monitor.sh"
}

# 添加 Crontab 监控
setup_cron_monitor() {
    log_info "配置定时监控..."
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "agent-cluster-monitor"; then
        log_warn "监控任务已存在，跳过"
        return
    fi
    
    # 添加监控任务
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/agent-cluster-monitor.sh >> /var/log/agent-cluster-monitor.log 2>&1") | crontab -
    
    log_success "定时监控已配置（每 5 分钟）"
}

# 创建 Let's Encrypt 证书脚本
create_certbot_script() {
    log_info "创建 Let's Encrypt 证书脚本..."
    
    cat > "$WORKSPACE/setup_ssl.sh" << 'EOF'
#!/bin/bash
# 使用 Let's Encrypt 获取正式 SSL 证书

set -e

SERVER_IP="39.107.101.25"

# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 获取证书（如果有域名）
# certbot --nginx -d your-domain.com

# 或使用 standalone 模式（需要临时关闭 Nginx）
certbot certonly --standalone -d $SERVER_IP

# 复制证书
cp /etc/letsencrypt/live/$SERVER_IP/fullchain.pem /etc/nginx/ssl/
cp /etc/letsencrypt/live/$SERVER_IP/privkey.pem /etc/nginx/ssl/

# 重启 Nginx
systemctl restart nginx

echo "✅ SSL 证书配置完成"
EOF
    
    chmod +x "$WORKSPACE/setup_ssl.sh"
    
    log_success "Let's Encrypt 脚本创建完成：$WORKSPACE/setup_ssl.sh"
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    echo ""
    echo "======================================"
    echo "         部署验证结果"
    echo "======================================"
    echo ""
    
    # Nginx 状态
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx: 运行中"
    else
        echo "❌ Nginx: 未运行"
    fi
    
    # SSL 证书
    if [ -f /etc/nginx/ssl/fullchain.pem ]; then
        echo "✅ SSL 证书：已配置"
    else
        echo "❌ SSL 证书：未配置"
    fi
    
    # 防火墙
    if command -v ufw &> /dev/null && ufw status | grep -q "active"; then
        echo "✅ UFW 防火墙：已启用"
    else
        echo "⚠️  UFW 防火墙：未启用"
    fi
    
    # Fail2Ban
    if systemctl is-active --quiet fail2ban; then
        echo "✅ Fail2Ban: 运行中"
    else
        echo "⚠️  Fail2Ban: 未运行"
    fi
    
    # Web 应用
    if pgrep -f "web_app.py" > /dev/null; then
        echo "✅ Web 应用：运行中"
    else
        echo "❌ Web 应用：未运行"
    fi
    
    echo ""
    echo "======================================"
    echo "         访问地址"
    echo "======================================"
    echo ""
    echo "  HTTPS: https://$SERVER_IP"
    echo "  HTTP:  http://$SERVER_IP (自动重定向)"
    echo ""
    echo "======================================"
}

# 主函数
main() {
    echo ""
    echo "======================================"
    echo "  Agent 集群生产环境部署脚本"
    echo "  服务器：$SERVER_IP"
    echo "======================================"
    echo ""
    
    check_root
    detect_os
    
    echo ""
    log_info "开始部署..."
    echo ""
    
    install_nginx
    generate_ssl_cert
    configure_nginx
    configure_ufw
    install_fail2ban
    create_monitor_script
    setup_cron_monitor
    create_certbot_script
    
    verify_deployment
    
    echo ""
    log_success "部署完成！"
    echo ""
    log_warn "重要提示："
    echo "  1. 请在阿里云安全组开放 80 和 443 端口"
    echo "  2. 生产环境请替换为正式 SSL 证书"
    echo "  3. 建议限制 SSH 访问来源 IP"
    echo "  4. 定期检查日志和监控"
    echo ""
}

# 运行主函数
main "$@"
