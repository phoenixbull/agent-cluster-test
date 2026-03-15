#!/bin/bash
# 每周清理脚本

WORKSPACE="/home/admin/.openclaw/workspace"

echo "🧹 开始每周清理..."

# Python 缓存
find $WORKSPACE -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "✅ Python 缓存已清理"

# 临时文件
find $WORKSPACE -name "*.tmp" -delete 2>/dev/null
find $WORKSPACE -name "*.bak" -delete 2>/dev/null
echo "✅ 临时文件已清理"

# 7 天前的日志
find /var/log/nginx -name "*.log" -mtime +7 -exec truncate -s 0 {} \; 2>/dev/null
echo "✅ Nginx 旧日志已清理"

# npm 缓存
npm cache clean --force 2>/dev/null
echo "✅ npm 缓存已清理"

echo "✅ 每周清理完成"
