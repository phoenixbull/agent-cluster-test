# TOOLS.md - 工具速查手册

> 老五的技术环境配置大全
> 
> 快速定位、快速复制、快速执行

---

## 🚀 Agent 集群 V2.1

### 架构概览
```
用户请求 → nginx (443) → web_app_v2.py (8890) → Agent 编排器
                ↓
         监控/告警 (钉钉)
```

### 核心服务

| 服务 | 地址 | 说明 |
|------|------|------|
| **管理后台** | `https://服务器 IP` | 标准 HTTPS 443 端口 |
| **后端服务** | `python3 web_app_v2.py --port 8890` | Python FastAPI |
| **工作目录** | `/home/admin/.openclaw/workspace/agent-cluster` | 项目根目录 |
| **GitHub** | `phoenixbull/agent-cluster-test` | 代码仓库 |

### 常用命令

```bash
# 启动 Web 服务
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app_v2.py --port 8890

# 启动并行任务
python3 cluster_manager.py parallel test_tasks.json

# 查看任务状态
python3 cluster_manager.py status

# 实时监控
tail -f monitor.log
tail -f monitor_tasks.log
```

---

## 📊 监控体系

### 自动监控（已配置）

| 监控项 | 频率 | 脚本 | 日志 |
|--------|------|------|------|
| **任务监控** | 10 分钟 | `monitor.py` | `monitor.log` |
| **Web 看门狗** | 5 分钟 | `watchdog_web.sh` | `logs/watchdog_web.log` |
| **健康检查** | 按需 | `health_check.sh` | `logs/health_check.log` |

### Crontab 配置
```bash
*/10 * * * * cd /home/admin/.openclaw/workspace/agent-cluster && python3 monitor.py
*/5  * * * * cd /home/admin/.openclaw/workspace/agent-cluster && ./watchdog_web.sh
```

### 钉钉通知事件

| 事件 | 触发条件 | @所有人 |
|------|---------|--------|
| `pr_ready` | PR 就绪，可 Review | ❌ |
| `task_complete` | 任务完成 | ❌ |
| `task_failed` | 任务失败 | ✅ |
| `human_intervention_needed` | 需要人工介入 | ✅ |

---

## 🔧 健康检查

### 快速检查
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./health_check.sh
```

### 手动验证

```bash
# HTTPS 检查（接受 200/302）
curl -sk -o /dev/null -w "%{http_code}" https://localhost:443

# Web 服务检查
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8890

# nginx 状态
systemctl status nginx

# 查看最近日志
tail -20 logs/health_check.log
tail -20 logs/watchdog_web.log
```

### 检查项说明

| 检查项 | 正常状态 | 说明 |
|--------|----------|------|
| HTTPS (443) | 200 或 302 | 302 重定向到登录页为正常 |
| Web 服务 (8890) | 200 或 302 | 后端 Python 应用响应 |
| 监控日志 | 无 ERROR | monitor.log 无报错 |
| nginx 服务 | active | systemctl 状态正常 |

---

## 🛠️ Skills 配置

### 已安装 Skills

| Skill | 功能 | 配置 | 优先级 |
|-------|------|------|--------|
| **searxng** | 联网搜索 | 本地部署，隐私优先 | ⭐⭐⭐⭐⭐ |
| **stock-data** | 股票行情 | 腾讯财经 HTTP API | ⭐⭐⭐⭐☆ |
| **xhs-note-creator** | 小红书运营 | 限流检测、敏感词分析 | ⭐⭐⭐☆☆ |
| **huamanizer-zh** | 中文文本优化 | 去除 AI 痕迹 | ⭐⭐⭐☆☆ |
| **agent-browser** | 浏览器自动化 | 基于 Rust 无头浏览器 | ⭐⭐⭐⭐☆ |
| **system-prompt-writer** | AI 提示词生成 | 多平台支持 | ⭐⭐⭐⭐⭐ |
| **ai-daily-brief** | 每日任务简报 | 自动整理优先级 | ⭐⭐⭐⭐☆ |

### Skill 使用速查

```bash
# 搜索（优先 searxng）
searxng "查询内容"

# 股票查询
stock-data 000001  # 平安银行

# 小红书检测
xhs-note-creator --check-limit

# 文本优化
huamanizer-zh input.txt output.txt
```

---

## 💻 环境信息

### 系统配置

| 属性 | 值 |
|------|-----|
| **主机** | iZ2ze3xu6p7e8obt25mlz3Z |
| **系统** | Linux 5.10.134-19.2.al8.x86_64 (x64) |
| **时区** | Asia/Shanghai (GMT+8) |
| **Shell** | bash |

### 运行时

| 组件 | 版本 |
|------|------|
| **Node** | v24.13.0 |
| **Python** | 3.x |
| **默认模型** | alibaba-cloud/qwen3.5-plus |

### 关键路径

```
~/.openclaw/
├── workspace/              # 工作目录
│   ├── agent-cluster/      # Agent 集群项目
│   ├── memory/             # 每日记忆
│   ├── AGENTS.md           # 工作手册
│   ├── SOUL.md             # 人格定义
│   ├── USER.md             # 用户画像
│   ├── TOOLS.md            # 本文件
│   └── MEMORY.md           # 长期记忆
├── agents/                 # Agent 会话记录
│   └── codex/sessions/     # Codex 会话
└── config/                 # 配置文件
```

---

## 📝 常用 Snippets

### Git 操作
```bash
# 快速提交
git add . && git commit -m "feat: 描述" && git push

# 查看状态
git status

# 查看日志（图形化）
git log --oneline --graph --decorate
```

### Python 虚拟环境
```bash
# 创建
python3 -m venv venv

# 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 文件操作
```bash
# 安全删除（用 trash）
trash filename

# 查找大文件
du -sh * | sort -rh | head -10

# 批量重命名
for f in *.txt; do mv "$f" "${f%.txt}.bak"; done
```

### 网络诊断
```bash
# 端口检查
netstat -tlnp | grep 8890

# 进程检查
ps aux | grep python

# 磁盘空间
df -h
```

---

## 🚨 故障排查

### 服务起不来
1. 检查端口占用：`netstat -tlnp | grep 8890`
2. 检查日志：`tail -50 logs/error.log`
3. 检查依赖：`pip list | grep key-package`
4. 重启 nginx：`sudo systemctl restart nginx`

### Agent 无响应
1. 检查会话记录：`ls ~/.openclaw/agents/codex/sessions/`
2. 检查 API 配置：`cat ~/.openclaw/config.json`
3. 测试直连：`curl -s http://127.0.0.1:8890/health`

### 通知没收到
1. 检查 webhook 配置：`cat cluster_config_v2.json`
2. 测试钉钉：`curl -X POST webhook_url -d '{"msgtype":"text","text":{"content":"test"}}'`
3. 检查网络：`ping oapi.dingtalk.com`

---

## 🔗 相关文档

- **MEMORY.md** - 长期记忆、项目进度
- **HEARTBEAT.md** - 心跳检查配置
- **cluster_config_v2.json** - Agent 集群配置
- **SKILL.md** - Skill 使用指南（各 Skill 目录内）

---

> **速查原则**：复制即用，无需思考
> 
> **更新规则**：新工具、新路径、新配置 → 立即更新

---

**最后更新**: 2026-04-09  
**版本**: 2.0 (结构化速查手册)
