# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Agent Cluster V2.1

**管理后台**:
- HTTPS: `https://服务器 IP` (标准 443 端口，默认)
- 后端：`python3 web_app_v2.py --port 8890`
- 工作目录：`/home/admin/.openclaw/workspace/agent-cluster`
- GitHub: `phoenixbull/agent-cluster-test`

**监控**:
- Crontab: `*/10 * * * *` (每 10 分钟)
- 日志：`monitor.log`, `monitor_tasks.log`
- 钉钉通知：已配置 (webhook + 加签密钥)

**Web 服务看门狗**:
- 脚本：`watchdog_web.sh` (每 5 分钟自动检查)
- 功能：检测 Web 服务健康状态，异常时自动重启
- 冷却期：60 秒 (防止频繁重启)
- 日志：`logs/watchdog_web.log`

**通知事件**:
- ✅ pr_ready - PR 就绪，可 Review
- ✅ task_complete - 任务完成
- ✅ task_failed - 任务失败 (@所有人)
- ✅ human_intervention_needed - 需要人工介入 (@所有人)

## Skills 配置

| Skill | 配置/备注 |
|-------|----------|
| searxng | 优先使用的搜索引擎 (本地部署) |
| stock-data | 默认使用腾讯财经 HTTP API |
| xhs-note-creator | 小红书笔记限流检测 |
| huamanizer-zh | 中文文本 AI 痕迹去除 |
| agent-browser | 基于 Rust 的无头浏览器 |

## 环境信息

- **时区**: Asia/Shanghai (GMT+8)
- **主机**: iZ2ze3xu6p7e8obt25mlz3Z
- **Node**: v24.13.0
- **默认模型**: alibaba-cloud/qwen3.5-plus

---

Add whatever helps you do your job. This is your cheat sheet.
