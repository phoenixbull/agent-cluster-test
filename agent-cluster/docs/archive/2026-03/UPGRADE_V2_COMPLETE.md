# OpenClaw V2 升级完整指南

**更新时间**: 2026-03-17 16:10  
**升级方式**: 从 GitHub 源码升级

---

## ⚠️ 问题说明

新版本 OpenClaw 使用现代 Python 项目结构：
- ❌ 不再有 `setup.py`
- ✅ 使用 `pyproject.toml`
- ✅ 使用 pnpm 管理前端依赖

---

## 🔧 正确的升级步骤

### 方法 1: 使用 pip 直接安装（推荐）

```bash
# 1. 停止当前服务
openclaw gateway stop

# 2. 进入源码目录
cd /tmp/openclaw-new

# 3. 安装构建工具
pip3 install build setuptools -q

# 4. 安装（使用 no-build-isolation）
pip3 install . --no-build-isolation

# 或者使用 pip 新版本
pip3 install --upgrade pip
pip3 install -e . --config-settings=--build-option=--no-build-isolation

# 5. 验证安装
openclaw --version

# 6. 启动服务
openclaw gateway start
```

### 方法 2: 使用 pnpm 构建（完整安装）

```bash
# 1. 安装 pnpm（如果没有）
curl -fsSL https://get.pnpm.io/install.sh | sh -

# 2. 安装依赖
cd /tmp/openclaw-new
pnpm install

# 3. 构建
pnpm build

# 4. 安装 Python 包
pip3 install -e .

# 5. 验证
openclaw --version
```

### 方法 3: 使用官方安装脚本（最简单）

```bash
# 1. 下载官方安装脚本
curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw/main/scripts/install.sh -o /tmp/install_openclaw.sh

# 2. 执行安装
bash /tmp/install_openclaw.sh

# 3. 验证
openclaw --version
```

---

## 🚀 快速升级命令

```bash
# 一键升级（方法 1）
cd /tmp/openclaw-new && \
pip3 install build setuptools -q && \
pip3 install . --no-build-isolation && \
openclaw --version && \
openclaw gateway restart
```

---

## ⚠️ 常见问题

### Q1: `pip3 install .` 报错 "Directory '.' is not installable"

**原因**: 缺少构建工具或使用了旧版 pip

**解决**:
```bash
# 升级 pip
pip3 install --upgrade pip

# 安装构建工具
pip3 install build setuptools

# 使用 no-build-isolation
pip3 install . --no-build-isolation
```

### Q2: 缺少 Python 依赖

**解决**:
```bash
# 从 pyproject.toml 安装依赖
cd /tmp/openclaw-new
pip3 install -r requirements.txt 2>/dev/null || true

# 或者让 pip 自动解析
pip3 install . --no-build-isolation
```

### Q3: 前端资源缺失

**解决**:
```bash
# 需要 pnpm 构建前端
pnpm install
pnpm build
```

---

## ✅ 升级后验证

```bash
# 1. 版本检查
openclaw --version

# 2. 服务状态
openclaw gateway status

# 3. Web 服务
curl http://localhost:8890/health

# 4. 工作区完整性
ls -lh /home/admin/.openclaw/workspace/agent-cluster/

# 5. Skills 检查
ls /home/admin/.openclaw/workspace/skills/
```

---

## 🔄 回滚方案

如果升级失败，可以回滚：

```bash
# 1. 停止服务
openclaw gateway stop

# 2. 恢复备份
cd /home/admin/.openclaw
tar -xzf workspace_backup_20260317_152353.tar.gz

# 3. 重新安装旧版本（如果有）
# pip3 install openclaw==2026.3.8

# 4. 启动服务
openclaw gateway start
```

---

## 📊 升级检查清单

- [ ] 停止当前服务
- [ ] 备份工作区（已完成）
- [ ] 克隆最新源码（已完成）
- [ ] 安装构建工具
- [ ] 安装新版本
- [ ] 验证版本号
- [ ] 启动服务
- [ ] 测试 Web 服务
- [ ] 验证 Skills
- [ ] 测试钉钉通知

---

**文档生成时间**: 2026-03-17 16:10  
**升级方式**: 源码安装  
**预计时间**: 10-15 分钟
