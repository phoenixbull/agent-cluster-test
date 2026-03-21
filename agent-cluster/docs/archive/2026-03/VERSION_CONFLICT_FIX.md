# OpenClaw 版本冲突解决方案

**问题时间**: 2026-03-17 17:36  
**问题**: 命令行显示版本 2026.2.9，实际运行版本 2026.3.8

---

## 🔍 问题原因

### PATH 优先级问题

你的 PATH 环境变量顺序：
```bash
echo $PATH | tr ':' '\n' | head -10
# 输出：
# 1. /home/linuxbrew/.linuxbrew/bin
# 2. /home/admin/.local/bin
# 3. /home/admin/bin
# 4. /usr/bin          ← npm 版本 (2026.3.8) 在这里
# ...
# 6. /home/admin/.local/share/pnpm  ← pnpm 版本 (2026.2.9) 在这里
```

**问题**: pnpm 的路径在 PATH 中，但不是第一个，但 pnpm 可能有自己的 shims。

### 实际执行情况

```bash
# 我执行的命令（使用完整路径或环境不同）
which openclaw
# 输出：/usr/bin/openclaw → 2026.3.8

# 你执行的命令（使用 PATH 查找）
openclaw --version
# 输出：2026.2.9 ← pnpm 版本
```

---

## ✅ 解决方案

### 方案 1: 使用完整路径（推荐）

```bash
# 直接使用 npm 安装的版本
/usr/bin/openclaw --version
# 或
/home/admin/.local/share/pnpm/openclaw --version
```

### 方案 2: 调整 PATH 优先级

**编辑 ~/.bashrc**:
```bash
vim ~/.bashrc
```

**在文件末尾添加**:
```bash
# 优先使用 npm 全局安装的 OpenClaw
export PATH="/usr/bin:$PATH"
```

**或者移除 pnpm 的 openclaw**:
```bash
# 从 pnpm 卸载 openclaw
pnpm uninstall -g openclaw

# 或移除 pnpm 的 openclaw 链接
rm -f /home/admin/.local/bin/openclaw
```

**使配置生效**:
```bash
source ~/.bashrc
```

### 方案 3: 统一版本（推荐）

**升级 pnpm 版本到最新**:
```bash
cd /home/admin/.local/share/pnpm/openclaw
git pull
pnpm install
pnpm build

# 验证
openclaw --version
```

**或者卸载 pnpm 版本，只用 npm 版本**:
```bash
# 卸载 pnpm 版本
pnpm uninstall -g openclaw

# 验证使用 npm 版本
openclaw --version
# 应显示：2026.3.8
```

### 方案 4: 创建别名

**编辑 ~/.bashrc**:
```bash
vim ~/.bashrc
```

**添加别名**:
```bash
# 强制使用 npm 版本的 OpenClaw
alias openclaw='/usr/bin/openclaw'
```

**使配置生效**:
```bash
source ~/.bashrc
```

---

## 🔍 验证方法

### 检查当前使用的版本

```bash
# 方法 1: 查看版本
openclaw --version

# 方法 2: 查看实际执行的命令
which openclaw
type openclaw

# 方法 3: 查看所有 openclaw
which -a openclaw
```

### 预期结果

**如果使用 npm 版本**:
```bash
openclaw --version
# 输出：OpenClaw 2026.3.8 (3caab92)

which openclaw
# 输出：/usr/bin/openclaw
```

**如果使用 pnpm 版本**:
```bash
openclaw --version
# 输出：2026.2.9

which openclaw
# 输出：/home/admin/.local/share/pnpm/openclaw
```

---

## 🎯 推荐方案

### 最简单：**方案 3 - 统一版本**

```bash
# 1. 卸载 pnpm 版本
pnpm uninstall -g openclaw

# 2. 验证使用 npm 版本
openclaw --version
# 应显示：2026.3.8

# 3. 验证服务
openclaw gateway status
```

### 最安全：**方案 1 - 使用完整路径**

```bash
# 创建别名
echo "alias openclaw='/usr/bin/openclaw'" >> ~/.bashrc
source ~/.bashrc

# 验证
openclaw --version
# 应显示：2026.3.8
```

---

## 📊 当前状态总结

| 版本 | 位置 | 状态 | 建议 |
|------|------|------|------|
| **2026.3.8** | `/usr/lib/node_modules/openclaw/` | ✅ 运行中 | **推荐使用** |
| **2026.2.9** | `/home/admin/.local/share/pnpm/openclaw/` | ⚠️ 命令行使用 | 升级或卸载 |
| **2026.2.9** | `/opt/openclaw/` | ⏸️ 备份 | 保留 |

---

## 🧹 清理建议

```bash
# 1. 检查当前使用的版本
openclaw --version

# 2. 如果是 2026.2.9，卸载 pnpm 版本
pnpm uninstall -g openclaw

# 3. 验证使用 npm 版本
openclaw --version
# 应显示：2026.3.8

# 4. 验证服务正常
openclaw gateway status
curl http://localhost:8890/health
```

---

## ⚠️ 注意事项

1. **不要同时运行多个版本**
   - 可能导致配置冲突
   - 可能导致端口占用

2. **统一使用一个版本**
   - 推荐：npm 全局安装 (2026.3.8)
   - 原因：更新及时，管理方便

3. **备份配置**
   - 卸载前备份配置
   - `/home/admin/.openclaw/config.json`

---

**报告生成时间**: 2026-03-17 17:40  
**问题**: PATH 优先级导致版本不一致  
**解决**: 统一使用 npm 版本 (2026.3.8)
