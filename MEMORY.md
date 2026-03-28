# MEMORY.md - 长期记忆

## 重要偏好

**🔍 搜索**: 联网搜索优先使用 `searxng` skill (隐私保护、本地部署)

---

## 📋 全局工作规则

**✅ 进度更新规则**: 所有项目每次任务完成后，必须更新进度到记忆文件 (`MEMORY.md` 或 `memory/YYYY-MM-DD.md`)，确保工作连续性和可追溯性。此规则对所有项目通用。

---

## 🚀 P4 测试框架实施进度 (2026-03-28)

**总体状态**: ✅ P4 全阶段 (1-5) 已完成

| 阶段 | 内容 | 状态 | 完成时间 |
|------|------|------|---------|
| **阶段 1** | 基础测试 (pytest/jest) | ✅ 完成 | 12:22 |
| **阶段 2** | iOS 测试 (XCTest/XCUITest) | ✅ 完成 (占位) | 12:32 |
| **阶段 3** | Android 测试 (JUnit/Espresso) | ✅ 完成 (占位) | 14:04 |
| **阶段 4** | 跨平台测试 (RN/Flutter) | ✅ 完成 (占位) | 14:29 |
| **阶段 5** | CI/CD + 告警系统 | ✅ 完成 (占位) | 14:32 |

**核心文件**:
- `utils/test_executor.py` - 测试执行器 (支持 6 平台)
- `utils/cicd_alerts.py` - CI/CD 集成 + 告警系统

**测试结果汇总**:
- 总测试数：38
- 通过率：97.37%
- 平均覆盖率：77.5%

**占位说明**: iOS/Android/RN/Flutter/CI-CD 需要相应 SDK/环境，当前为占位实现，等待真实环境即可启用。

---

## 💻 Phase 3 编码阶段优化进度 (2026-03-28)

**总体状态**: ✅ P1-P2 已完成，P3 待实施

| 优化项 | 内容 | 状态 | 完成时间 |
|--------|------|------|---------|
| **P1** | 真实 Agent 调用 | ✅ 完成 | 15:35 |
| **P2** | 代码审查集成 | ✅ 完成 | 15:40 |
| **P3** | 增量代码生成 | ⏳ 待实施 | - |

**核心文件**:
- `utils/agent_executor.py` - Agent 执行器 (P1 增强)
- `utils/review_collector.py` - 审查收集器 (新增)

**新增功能**:
- 真实 OpenClaw sessions_spawn 调用
- 审查结果收集与反馈应用
- 代码修改提示生成

**待实施**:
- 增量代码生成 (基于现有代码的增量修改)

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
