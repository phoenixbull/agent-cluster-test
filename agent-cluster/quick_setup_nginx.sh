#!/bin/bash
# quick_setup_nginx.sh - 快速配置 Nginx 反向代理
# 用途：5 分钟快速部署，适合测试环境

set -e

SERVER_IP="39.107.101.25"
BACKEND_PORT=8889

echo "🚀 快速配置 Nginx 反向代理..."
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    echo "   sudo ./quick_setup_nginx.sh"
    exit 1
fi

# 1. 安装 Nginx
echo "📦 安装 Nginx..."

# 检测包管理器
if command -v apt &> /dev/null; then
    apt update -qq
    apt install -y nginx > /dev/null 2>&1
elif command -v yum &> /dev/null; then
    yum install -y epel-release > /dev/null 2>&1
    yum install -y nginx > /dev/null 2>&1
elif command -v dnf &> /dev/null; then
    dnf install -y epel-release > /dev/null 2>&1
    dnf install -y nginx > /dev/null 2>&1
else
    echo "❌ 未找到支持的包管理器 (apt/yum/dnf)"
    exit 1
fi

systemctl start nginx
systemctl enable nginx > /dev/null 2>&1
echo "✅ Nginx 已安装"

# 2. 生成 SSL 证书
echo "🔒 生成 SSL 证书..."
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/privkey.pem \
    -out /etc/nginx/ssl/fullchain.pem \
    -subj "/C=CN/ST=Beijing/CN=$SERVER_IP" \
    2>/dev/null
echo "✅ SSL 证书已生成（自签名，有效期 365 天）"

# 3. 配置 Nginx
echo "⚙️  配置 Nginx..."

# 备份原配置
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.bak 2>/dev/null || true

# 创建配置文件
cat > /etc/nginx/sites-available/agent-cluster << EOF
server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/agent-cluster /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试并重启
nginx -t > /dev/null 2>&1
systemctl restart nginx
echo "✅ Nginx 配置完成"

# 4. 配置防火墙（如果 UFW 可用）
echo "🔥 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp > /dev/null 2>&1 || true
    ufw allow 443/tcp > /dev/null 2>&1 || true
    echo "✅ UFW 规则已添加"
else
    echo "⚠️  UFW 未安装，跳过防火墙配置"
fi

echo ""
echo "======================================"
echo "         ✅ 部署完成！"
echo "======================================"
echo ""
echo "  🌐 访问地址:"
echo "     HTTPS: https://$SERVER_IP"
echo "     HTTP:  http://$SERVER_IP"
echo ""
echo "  📋 状态检查:"
echo "     systemctl status nginx"
echo "     curl -k https://$SERVER_IP/api/status"
echo ""
echo "  ⚠️  注意:"
echo "     - 自签名证书会有安全警告，点击继续即可"
echo "     - 生产环境请替换为正式证书"
echo "     - 请在阿里云安全组开放 80/443 端口"
echo ""
