#!/bin/bash
#
# Agent 集群系统 - 版本发布脚本
# 用法：./scripts/release.sh <版本号> <版本类型>
#
# 示例:
#   ./scripts/release.sh 2.2.1 patch    # 修订版本 (Bug 修复)
#   ./scripts/release.sh 2.3.0 minor    # 次版本 (新功能)
#   ./scripts/release.sh 3.0.0 major    # 主版本 (破坏性变更)
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -lt 2 ]; then
    echo -e "${RED}用法：$0 <版本号> <版本类型>${NC}"
    echo ""
    echo "版本类型:"
    echo "  patch  - 修订版本 (Bug 修复)"
    echo "  minor  - 次版本 (新功能)"
    echo "  major  - 主版本 (破坏性变更)"
    echo ""
    echo "示例:"
    echo "  $0 2.2.1 patch"
    echo "  $0 2.3.0 minor"
    echo "  $0 3.0.0 major"
    exit 1
fi

VERSION=$1
TYPE=$2
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
CODENAME=""

# 根据类型设置代号
case $TYPE in
    patch)
        CODENAME="Bug 修复版"
        ;;
    minor)
        CODENAME="功能增强版"
        ;;
    major)
        CODENAME="架构重构版"
        ;;
    *)
        echo -e "${RED}错误：版本类型必须是 patch/minor/major${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agent 集群系统 - 版本发布${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "版本号：${GREEN}v${VERSION}${NC}"
echo -e "类型：${YELLOW}${TYPE}${NC} (${CODENAME})"
echo -e "日期：${DATE}"
echo ""

# 确认发布
read -p "确认发布版本 v${VERSION}? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}发布已取消${NC}"
    exit 0
fi

# 步骤 1: 备份当前版本
echo -e "${YELLOW}[1/6] 备份当前版本...${NC}"
mkdir -p "$BACKUP_DIR"
cp cluster_config_v2.json "$BACKUP_DIR/"
cp monitor.py "$BACKUP_DIR/" 2>/dev/null || true
cp web_app_v2.py "$BACKUP_DIR/" 2>/dev/null || true
cp VERSION.md "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✅ 备份完成：$BACKUP_DIR${NC}"

# 步骤 2: 更新配置文件版本号
echo -e "${YELLOW}[2/6] 更新配置文件...${NC}"
sed -i "s/\"version\": \"[0-9.]*\"/\"version\": \"${VERSION}\"/" cluster_config_v2.json
sed -i "s/\"release_date\": \"[0-9-]*\"/\"release_date\": \"${DATE}\"/" cluster_config_v2.json
sed -i "s/\"codename\": \"[^\"]*\"/\"codename\": \"${CODENAME}\"/" cluster_config_v2.json
echo -e "${GREEN}✅ 配置文件已更新${NC}"

# 步骤 3: 更新 Web 界面版本号
echo -e "${YELLOW}[3/6] 更新 Web 界面...${NC}"
sed -i "s/V[0-9.]* 智能增强版/V${VERSION} 智能增强版/" web_app_v2.py
sed -i "s/V[0-9.]* 智能增强版/V${VERSION} 智能增强版/" web_app_v2.py
echo -e "${GREEN}✅ Web 界面已更新${NC}"

# 步骤 4: 更新 VERSION.md
echo -e "${YELLOW}[4/6] 更新版本历史...${NC}"
# 这里需要手动编辑 VERSION.md，添加新版本记录
echo -e "${GREEN}✅ 请手动更新 VERSION.md 添加 v${VERSION} 记录${NC}"

# 步骤 5: 语法检查
echo -e "${YELLOW}[5/6] 语法检查...${NC}"
python3 -m py_compile web_app_v2.py
python3 -m py_compile monitor.py
echo -e "${GREEN}✅ 语法检查通过${NC}"

# 步骤 6: 创建 Git 标签
echo -e "${YELLOW}[6/6] 创建 Git 标签...${NC}"
if git rev-parse --git-dir > /dev/null 2>&1; then
    git add cluster_config_v2.json web_app_v2.py VERSION.md
    git commit -m "chore: 发布 v${VERSION} - ${CODENAME}"
    git tag "v${VERSION}"
    echo -e "${GREEN}✅ Git 标签已创建：v${VERSION}${NC}"
    echo ""
    echo -e "${YELLOW}提示：推送变更到远程仓库${NC}"
    echo "  git push origin main"
    echo "  git push origin --tags"
else
    echo -e "${YELLOW}⚠️  当前目录不是 Git 仓库，跳过 Git 操作${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 版本发布完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "新版本：${GREEN}v${VERSION}${NC}"
echo -e "代号：${YELLOW}${CODENAME}${NC}"
echo -e "备份：${BACKUP_DIR}"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo "  1. 重启 Web 服务：python3 web_app_v2.py --port 8890"
echo "  2. 验证新版本：curl http://localhost:8890/health"
echo "  3. 更新文档：README.md, AI_PRODUCT_DEV_AGENT_SUMMARY.md"
echo ""
