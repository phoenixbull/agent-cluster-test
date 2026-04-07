#!/bin/bash
# setup_ssl.sh - 配置 Let's Encrypt SSL 证书
# 用途：获取正式的免费 SSL 证书

set -e

SERVER_IP="39.107.101.25"

echo "🔒 配置 Let's Encrypt SSL 证书..."
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 1. 安装 Certbot
echo "📦 安装 Certbot..."
apt install -y certbot python3-certbot-nginx

# 2. 获取证书
echo ""
echo "📝 获取证书..."
echo ""
echo "注意：Standlone 模式需要临时关闭 80 端口"
echo ""

# 停止 Nginx 临时释放 80 端口
systemctl stop nginx

# 获取证书
certbot certonly --standalone \
    -d $SERVER_IP \
    --non-interactive \
    --agree-tos \
    --email admin@example.com \
    --force-renewal

# 3. 复制证书
echo ""
echo "📋 复制证书..."
cp /etc/letsencrypt/live/$SERVER_IP/fullchain.pem /etc/nginx/ssl/
cp /etc/letsencrypt/live/$SERVER_IP/privkey.pem /etc/nginx/ssl/
chmod 644 /etc/nginx/ssl/fullchain.pem
chmod 600 /etc/nginx/ssl/privkey.pem

# 4. 重启 Nginx
systemctl start nginx
systemctl restart nginx

# 5. 配置自动续期
echo ""
echo "⏰ 配置自动续期..."
certbot renew --dry-run

echo ""
echo "======================================"
echo "         ✅ SSL 证书配置完成！"
echo "======================================"
echo ""
echo "  证书有效期：90 天（自动续期）"
echo "  续期命令：certbot renew"
echo ""
echo "  访问地址：https://$SERVER_IP"
echo ""
