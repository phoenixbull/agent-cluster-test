# MEMORY.md - 长期记忆

## 重要偏好

**🔍 搜索**: 联网搜索优先使用 `searxng` skill (隐私保护、本地部署)

---

## Agent 集群 V2.1

**位置**: `/home/admin/.openclaw/workspace/agent-cluster/`

**GitHub 仓库**: phoenixbull/agent-cluster-test

**架构**:
- nginx HTTPS 443 → web_app_v2.py 8890 (默认)
- 访问地址：`https://服务器 IP` (标准 HTTPS 端口)

**钉钉通知配置**:
- Webhook 和加签密钥已配置在 `cluster_config_v2.json`
- 通知模块：`notifiers/dingtalk.py` (ClusterNotifier 类)
- 监控脚本：`monitor.py` (已集成钉钉通知，每 10 分钟自动运行)
- Crontab: `*/10 * * * *` 自动监控任务状态

**通知事件**:
- ✅ pr_ready - PR 就绪，可 Review (不@所有人)
- ✅ task_complete - 任务完成 (不@所有人)
- ✅ task_failed - 任务失败 (@所有人)
- ✅ human_intervention_needed - 需要人工介入 (@所有人)

**启动命令**:
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app_v2.py --port 8890
python3 cluster_manager.py parallel test_tasks.json
```

**监控命令**:
```bash
python3 cluster_manager.py status
tail -f monitor.log
```

**Web 服务看门狗**:
- 自动监控：`watchdog_web.sh` (每 5 分钟)
- 日志：`logs/watchdog_web.log`
- 功能：服务异常自动重启 (60 秒冷却期)

---

## 已安装 Skills (2026-03-11)

| Skill | 用途 |
|-------|------|
| system-prompt-writer | AI 提示词生成和优化 |
| stock-data | 股票行情数据查询 |
| ai-daily-brief | 每日任务简报 |
| isearch | 联网搜索 |
| xhs-note-creator | 小红书笔记限流检测 |
| huamanizer-zh | 中文文本去 AI 化 |
| agent-browser | 浏览器自动化 |

---

## 环境信息

- **主机**: iZ2ze3xu6p7e8obt25mlz3Z (阿里云)
- **Node**: v24.13.0
- **默认模型**: alibaba-cloud/qwen3.5-plus
- **时区**: Asia/Shanghai (GMT+8)
