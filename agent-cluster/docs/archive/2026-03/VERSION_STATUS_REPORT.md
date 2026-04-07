# OpenClaw 多版本状态报告

**报告时间**: 2026-03-17 17:30 (Asia/Shanghai)

---

## 📊 当前状态

### 发现的 OpenClaw 实例

| 位置 | 版本 | 状态 | 用途 |
|------|------|------|------|
| **/opt/openclaw** | 2026.2.9 | ✅ 已安装 | 系统版本（旧） |
| **/usr/bin/openclaw** | 2026.3.8 | ✅ 运行中 | **当前使用** |
| **/tmp/openclaw-new** | 2026.3.14 | ⏸️ 源码 | 临时升级文件 |
| **~/.local/pnpm/openclaw** | 未知 | ⏸️ pnpm | Node.js 版本 |

---

## ✅ 当前使用的版本

### 活跃版本：**2026.3.8 (3caab92)**

**验证命令**:
```bash
openclaw --version
# 输出：OpenClaw 2026.3.8 (3caab92)
```

**安装位置**:
```bash
which openclaw
# 输出：/usr/bin/openclaw（优先使用）
```

**运行进程**:
```bash
ps aux | grep "openclaw" | grep -v grep
# 输出：admin 139440 ... openclaw-gateway
```

---

## 📁 各版本详情

### 1. /opt/openclaw (2026.2.9)

| 项目 | 详情 |
|------|------|
| **版本** | 2026.2.9 |
| **位置** | /opt/openclaw/ |
| **状态** | 已安装（旧版本） |
| **用途** | 系统目录，可能是初始安装 |
| **建议** | 可以保留作为备份 |

**查看版本**:
```bash
head -5 /opt/openclaw/CHANGELOG.md | grep "## 2026.2.9"
```

---

### 2. /usr/bin/openclaw (2026.3.8) ⭐ 当前使用

| 项目 | 详情 |
|------|------|
| **版本** | 2026.3.8 (3caab92) |
| **位置** | /usr/bin/openclaw |
| **状态** | ✅ **运行中** |
| **用途** | **当前活跃版本** |
| **建议** | 继续使用 |

**验证**:
```bash
openclaw --version
# OpenClaw 2026.3.8 (3caab92)
```

---

### 3. /tmp/openclaw-new (2026.3.14)

| 项目 | 详情 |
|------|------|
| **版本** | 2026.3.14 |
| **位置** | /tmp/openclaw-new/ |
| **状态** | 源码目录（未安装） |
| **用途** | 升级时下载的临时文件 |
| **建议** | 可以删除或保留参考 |

**查看版本**:
```bash
cat /tmp/openclaw-new/package.json | grep version
# "version": "2026.3.14"
```

---

### 4. ~/.local/pnpm/openclaw

| 项目 | 详情 |
|------|------|
| **版本** | 未知 |
| **位置** | /home/admin/.local/share/pnpm/openclaw |
| **状态** | pnpm 安装的 Node.js 版本 |
| **用途** | 可能是前端工具链 |
| **建议** | 保留（前端开发用） |

---

## 🔍 为什么会有多个版本？

### 原因分析

1. **/opt/openclaw** - 初始安装版本 (2026.2.9)
2. **/usr/bin/openclaw** - pip 安装版本 (2026.3.8) ← **当前使用**
3. **/tmp/openclaw-new** - 刚才升级时下载的源码 (2026.3.14)
4. **~/.local/pnpm/openclaw** - pnpm 安装的 Node.js 版本

### 版本优先级

```bash
# shell 查找命令的顺序（PATH 环境变量）
1. /usr/bin/openclaw      ← 优先使用（当前版本）
2. /bin/openclaw          ← 通常是 /usr/bin 的软链接
3. ~/.local/bin/openclaw  ← 用户级安装
```

---

## ✅ 结论

### 当前使用的版本

**OpenClaw 2026.3.8 (3caab92)**

**安装位置**: `/usr/bin/openclaw`

**运行状态**: ✅ 正常运行（进程 139440）

### 其他版本

| 版本 | 位置 | 状态 | 建议 |
|------|------|------|------|
| 2026.2.9 | /opt/openclaw | 旧版本 | 保留作备份 |
| 2026.3.14 | /tmp/openclaw-new | 源码 | 可删除 |
| unknown | ~/.local/pnpm | Node.js | 保留 |

---

## 🧹 清理建议（可选）

### 可以删除的

```bash
# 删除临时源码目录（已完成升级）
rm -rf /tmp/openclaw-new

# 验证删除
ls -la /tmp/openclaw-new 2>/dev/null || echo "✅ 已删除"
```

### 建议保留的

```bash
# /opt/openclaw - 旧版本备份
# ~/.local/pnpm/openclaw - Node.js 工具链
```

---

## 📋 验证当前版本

```bash
# 1. 检查版本
openclaw --version
# 应显示：OpenClaw 2026.3.8 (3caab92)

# 2. 检查安装位置
which openclaw
# 应显示：/usr/bin/openclaw

# 3. 检查运行进程
ps aux | grep "openclaw-gateway" | grep -v grep
# 应显示运行中的进程

# 4. 检查服务状态
openclaw gateway status
# 应显示：running
```

---

## 🎯 总结

### 是否存在两个版本？
**是的**，机器上有多个 OpenClaw 版本，但**只有一个在运行**。

### 当前使用的是哪个？
**OpenClaw 2026.3.8 (3caab92)**，安装在 `/usr/bin/openclaw`

### 是否需要清理？
- ✅ **当前版本**: 2026.3.8（正常使用）
- ⚠️ **临时文件**: /tmp/openclaw-new（可删除）
- ✅ **旧版本**: /opt/openclaw（建议保留作备份）

---

**报告生成时间**: 2026-03-17 17:30  
**当前版本**: 2026.3.8 (3caab92)  
**状态**: ✅ 正常运行
