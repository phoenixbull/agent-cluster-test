# OpenClaw 安装位置详解

**报告时间**: 2026-03-17 17:35 (Asia/Shanghai)

---

## 📊 当前安装情况

### OpenClaw 真实安装位置

| 组件 | 位置 | 类型 | 版本 |
|------|------|------|------|
| **主程序** | `/usr/lib/node_modules/openclaw/` | npm 全局安装 | 2026.3.8 |
| **命令链接** | `/usr/bin/openclaw` | 符号链接 | → openclaw.mjs |
| **命令链接** | `/bin/openclaw` | 符号链接 | → openclaw.mjs |
| **pnpm 版本** | `/home/admin/.local/share/pnpm/openclaw/` | pnpm 安装 | 未知 |
| **旧版本** | `/opt/openclaw/` | 系统目录 | 2026.2.9 |
| **临时源码** | `/tmp/openclaw-new/` | Git 源码 | 2026.3.14 |

---

## 🔍 详细说明

### 1. 主程序位置

**路径**: `/usr/lib/node_modules/openclaw/`

**验证**:
```bash
ls -la /usr/lib/node_modules/openclaw/
# 显示：
# total 904
# drwxr-xr-x   8 root root   4096 Mar 10 12:12 .
# -rw-r--r--   1 root root 676271 Mar 10 12:12 CHANGELOG.md
```

**查看版本**:
```bash
cat /usr/lib/node_modules/openclaw/package.json | grep version
# 或
openclaw --version
# 输出：OpenClaw 2026.3.8 (3caab92)
```

---

### 2. 命令符号链接

**路径**: `/usr/bin/openclaw` → `../lib/node_modules/openclaw/openclaw.mjs`

**验证**:
```bash
ls -la /usr/bin/openclaw
# 输出：
# lrwxrwxrwx 1 root root 41 Mar 10 12:12 /usr/bin/openclaw -> ../lib/node_modules/openclaw/openclaw.mjs

file /usr/bin/openclaw
# 输出：
# /usr/bin/openclaw: symbolic link to ../lib/node_modules/openclaw/openclaw.mjs
```

**说明**:
- `/usr/bin/openclaw` 是一个**符号链接**（快捷方式）
- 实际执行的是 `/usr/lib/node_modules/openclaw/openclaw.mjs`
- 这是 npm 全局安装的标准方式

---

### 3. npm 全局安装验证

```bash
# 查看全局安装的 openclaw
npm list -g openclaw
# 输出：
# └── openclaw@2026.3.8

# 查看 npm 全局安装位置
npm root -g
# 通常输出：/usr/lib/node_modules
```

---

### 4. pnpm 版本

**路径**: `/home/admin/.local/share/pnpm/openclaw/`

**说明**:
- 这是通过 pnpm 安装的用户级版本
- 通常用于前端开发工具链
- 不影响系统级的 npm 版本

---

### 5. 旧版本备份

**路径**: `/opt/openclaw/`

**版本**: 2026.2.9

**说明**:
- 系统目录中的旧版本
- 可能是初始安装位置
- 建议保留作为备份

---

### 6. 临时源码

**路径**: `/tmp/openclaw-new/`

**版本**: 2026.3.14

**说明**:
- 升级时下载的 Git 源码
- 未安装，仅源代码
- 可以安全删除

---

## 🎯 总结

### 当前使用的版本

**OpenClaw 2026.3.8**

**真实位置**: `/usr/lib/node_modules/openclaw/`

**安装方式**: npm 全局安装 (`npm install -g openclaw`)

**命令路径**: `/usr/bin/openclaw` (符号链接)

---

### 文件结构

```
/usr/lib/node_modules/openclaw/     ← 真正的安装目录
├── openclaw.mjs                    ← 主程序入口
├── package.json                    ← 版本信息 (2026.3.8)
├── CHANGELOG.md                    ← 更新日志
└── ...

/usr/bin/openclaw                   ← 符号链接（快捷方式）
  → ../lib/node_modules/openclaw/openclaw.mjs
```

---

### 为什么 `/usr/bin/openclaw` 显示"不存在"？

**原因**: 它是一个**符号链接**，不是实际的目录或文件。

**验证方法**:
```bash
# 检查符号链接
ls -la /usr/bin/openclaw
# 显示：lrwxrwxrwx ... -> ../lib/node_modules/openclaw/openclaw.mjs

# 检查目标文件是否存在
ls -la /usr/lib/node_modules/openclaw/openclaw.mjs
# 显示：-rw-r--r-- ... openclaw.mjs
```

**符号链接是正常的**，这是 npm 全局安装的标准方式。

---

### 清理建议

```bash
# 可以删除的（临时文件）
rm -rf /tmp/openclaw-new

# 建议保留的
# /usr/lib/node_modules/openclaw/  ← 当前使用版本
# /opt/openclaw/                   ← 旧版本备份
# /home/admin/.local/pnpm/openclaw/ ← pnpm 工具链
```

---

## 📋 验证命令

```bash
# 1. 检查版本
openclaw --version
# 输出：OpenClaw 2026.3.8 (3caab92)

# 2. 检查命令位置
which openclaw
# 输出：/usr/bin/openclaw

# 3. 检查符号链接
ls -la /usr/bin/openclaw
# 输出：lrwxrwxrwx ... -> ../lib/node_modules/openclaw/openclaw.mjs

# 4. 检查真实位置
ls -la /usr/lib/node_modules/openclaw/
# 输出：目录内容

# 5. 检查 npm 安装
npm list -g openclaw
# 输出：└── openclaw@2026.3.8

# 6. 检查运行进程
ps aux | grep "openclaw-gateway" | grep -v grep
# 输出：运行中的进程
```

---

**报告生成时间**: 2026-03-17 17:35  
**当前版本**: 2026.3.8  
**安装位置**: /usr/lib/node_modules/openclaw/  
**安装方式**: npm 全局安装  
**状态**: ✅ 正常运行
