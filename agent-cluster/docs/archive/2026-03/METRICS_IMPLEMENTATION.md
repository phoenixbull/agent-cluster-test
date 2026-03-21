# 📊 指标埋点实施总结

## 已完成的工作

### 1. 核心模块

| 文件 | 路径 | 说明 |
|------|------|------|
| `metrics_collector.py` | `utils/metrics_collector.py` | 指标收集器核心模块 |
| `metrics_api.py` | `api/metrics_api.py` | HTTP API 端点 |
| `metrics_dashboard.html` | `templates/metrics_dashboard.html` | 可视化 Dashboard |
| `METRICS_GUIDE.md` | `docs/METRICS_GUIDE.md` | 使用文档 |

### 2. 集成修改

| 文件 | 修改内容 |
|------|---------|
| `monitor.py` | 导入指标模块，在任务完成/失败时自动埋点 |
| `web_app_v2.py` | 导入 metrics_api 模块 (待完成路由注册) |

---

## 核心功能

### 指标采集

- ✅ 任务开始/完成/失败自动埋点
- ✅ Agent 性能统计 (分配/完成/失败/成功率/成本)
- ✅ 失败原因分类 (7 种类型)
- ✅ 成本追踪 (与 cost_tracker 集成)
- ✅ 实时汇总统计

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/metrics/summary` | GET | 汇总统计 |
| `/api/metrics/agents` | GET | Agent 统计 |
| `/api/metrics/tasks` | GET | 任务历史 |
| `/api/metrics/failures` | GET | 失败分析 |
| `/api/metrics/report` | GET | 完整报告 |
| `/api/metrics/export` | POST | 导出报告 |

### Dashboard 功能

- 📊 核心指标卡片 (6 个)
- 🤖 Agent 性能统计
- ⚠️ 失败原因分析
- 📋 最近任务列表
- 🔄 自动刷新 (30 秒)

---

## 使用方法

### 1. 访问 Dashboard

```
https://服务器 IP/metrics.html
或
http://localhost:8890/metrics.html
```

### 2. API 查询示例

```bash
# 获取汇总统计
curl http://localhost:8890/api/metrics/summary

# 获取 Agent 统计
curl http://localhost:8890/api/metrics/agents

# 获取失败分析
curl http://localhost:8890/api/metrics/failures?days=7

# 导出报告
curl -X POST http://localhost:8890/api/metrics/export \
  -H "Content-Type: application/json" \
  -d '{"output_path": "report.json"}'
```

### 3. 代码集成

```python
from utils.metrics_collector import start_task, complete_task, fail_task, FailureReason

# 任务开始
start_task(
    task_id="task-001",
    agent_id="codex",
    model="qwen-coder-plus",
    phase="3_development"
)

# 任务完成
complete_task(
    task_id="task-001",
    pr_number=123,
    ci_passed=True,
    review_approved=True,
    input_tokens=5000,
    output_tokens=2000,
    cost=0.05
)

# 任务失败
fail_task(
    task_id="task-001",
    reason=FailureReason.CI_FAILED,
    retry_count=2,
    cost=0.03
)
```

---

## 数据存储

```
agent-cluster/metrics/
├── tasks_metrics.jsonl      # 任务指标 (JSONL)
├── summary_stats.json       # 汇总统计
├── agents_metrics.json      # Agent 指标
└── hourly_stats.jsonl       # 小时级聚合 (待实现)
```

---

## 下一步行动

### 立即可做

1. **测试埋点功能**
   ```bash
   cd /home/admin/.openclaw/workspace/agent-cluster
   python3 utils/metrics_collector.py
   ```

2. **重启 Web 服务**
   ```bash
   # 停止现有服务
   pkill -f web_app_v2.py
   
   # 启动新版本
   cd /home/admin/.openclaw/workspace/agent-cluster
   python3 web_app_v2.py --port 8890 &
   ```

3. **验证 Dashboard**
   - 访问 `http://localhost:8890/metrics.html`
   - 检查核心指标是否显示
   - 查看任务列表是否有数据

### 后续优化

| 功能 | 优先级 | 预计工时 |
|------|--------|---------|
| 在 monitor.py 中完成埋点集成 | P0 | 30 分钟 |
| 在 web_app_v2.py 中注册 API 路由 | P0 | 30 分钟 |
| 添加指标数据到现有 Dashboard | P1 | 2 小时 |
| 实现小时级聚合统计 | P2 | 4 小时 |
| 告警系统集成 | P2 | 4 小时 |
| 趋势分析图表 | P3 | 8 小时 |

---

## 关键指标定义

### 效率指标

| 指标 | 计算公式 | 健康值 |
|------|---------|--------|
| 平均完成时间 | Σ(完成时间 - 开始时间) / 完成数 | < 30 分钟 |
| 任务吞吐量 | 完成数 / 小时 | > 5/小时 |

### 质量指标

| 指标 | 计算公式 | 健康值 |
|------|---------|--------|
| CI 通过率 | CI 通过数 / 总 PR 数 | > 80% |
| 一次通过率 | 无需重试完成数 / 总完成数 | > 70% |
| 人工介入率 | 人工介入数 / 总任务数 | < 20% |

### 成本指标

| 指标 | 说明 | 参考值 |
|------|------|--------|
| 日均成本 | ΣAPI 调用成本 | ¥30-50/天 |
| 单任务成本 | 任务总成本 / 任务数 | ¥0.3-0.8/任务 |

---

## 失败原因分类

| 原因 | 说明 | 优化方向 |
|------|------|---------|
| `PROMPT_ERROR` | Prompt 质量问题 | 改进 Prompt 模板 |
| `MODEL_ERROR` | 模型输出异常 | 调整模型参数 |
| `CI_FAILED` | CI 检查失败 | 优化 CI 配置 |
| `REVIEW_REJECTED` | Code Review 不通过 | 提高代码质量 |
| `TIMEOUT` | 超时 | 增加超时时间或优化任务 |
| `ENVIRONMENT` | 环境问题 | 稳定运行环境 |
| `UNKNOWN` | 未知原因 | 加强日志记录 |

---

## 故障排查

### 问题：指标未更新

1. 检查 `monitor.py` 是否正常执行
2. 查看 `metrics/tasks_metrics.jsonl` 是否有新记录
3. 确认埋点代码已正确集成

### 问题：Dashboard 无法访问

1. 确认 Web 服务运行：`curl http://localhost:8890/api/metrics/health`
2. 检查 Nginx 配置
3. 查看日志：`tail -f logs/web_app.log`

---

## 相关文件清单

```
agent-cluster/
├── utils/
│   └── metrics_collector.py          # ✅ 新建
├── api/
│   └── metrics_api.py                # ✅ 新建
├── templates/
│   └── metrics_dashboard.html        # ✅ 新建
├── docs/
│   └── METRICS_GUIDE.md              # ✅ 新建
├── monitor.py                        # ⚠️ 已修改 (需验证)
├── web_app_v2.py                     # ⚠️ 待完成路由注册
└── metrics/                          # 📁 数据目录 (自动创建)
    ├── tasks_metrics.jsonl
    ├── summary_stats.json
    ├── agents_metrics.json
    └── hourly_stats.jsonl
```

---

**实施日期**: 2026-03-19  
**版本**: v1.0  
**状态**: 核心功能完成，待集成测试
