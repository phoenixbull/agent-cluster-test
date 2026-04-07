# 📊 指标埋点使用指南

## 快速开始

### 1. 访问 Dashboard

**Web 界面**: `https://服务器 IP/metrics.html`

或本地访问：`http://localhost:8890/metrics.html`

### 2. API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/metrics/summary` | GET | 获取汇总统计 |
| `/api/metrics/agents` | GET | 获取 Agent 统计 |
| `/api/metrics/tasks` | GET | 获取任务历史 |
| `/api/metrics/failures` | GET | 获取失败分析 |
| `/api/metrics/report` | GET | 获取完整报告 |
| `/api/metrics/export` | POST | 导出报告到文件 |

---

## 核心指标说明

### 任务效率指标

| 指标 | 说明 | 计算方式 |
|------|------|---------|
| `total_tasks` | 总任务数 | 累计创建的任务数量 |
| `completed_tasks` | 完成数 | 成功完成的任务数量 |
| `avg_duration_seconds` | 平均完成时间 | 所有完成任务的平均耗时 |
| `ci_pass_rate` | CI 通过率 | CI 通过数 / 总 PR 数 |

### 质量指标

| 指标 | 说明 | 健康值 |
|------|------|--------|
| `ci_pass_rate` | CI 通过率 | > 80% |
| `human_intervention_rate` | 人工介入率 | < 20% |
| `review_approved` | Review 通过率 | > 90% |

### 成本指标

| 指标 | 说明 | 说明 |
|------|------|------|
| `total_cost` | 总成本 | 累计 API 调用成本 (元) |
| `today.cost` | 今日成本 | 当日 API 调用成本 |
| `by_model` | 模型成本分布 | 各模型的成本占比 |

### 稳定性指标

| 指标 | 说明 | 健康值 |
|------|------|--------|
| `agent.success_rate` | Agent 成功率 | > 85% |
| `failed_tasks` | 失败任务数 | 越少越好 |
| 失败原因分布 | 识别主要问题 | 针对性优化 |

---

## 代码集成

### 在任务开始时埋点

```python
from utils.metrics_collector import start_task, complete_task, fail_task, FailureReason

# 任务开始
metrics = start_task(
    task_id="task-001",
    workflow_id="wf-001",
    agent_id="codex",
    model="qwen-coder-plus",
    phase="3_development"
)
```

### 任务完成时埋点

```python
# 任务成功完成
complete_task(
    task_id="task-001",
    pr_number=123,
    ci_passed=True,
    review_approved=True,
    input_tokens=5000,
    output_tokens=2000,
    cost=0.05
)
```

### 任务失败时埋点

```python
# 任务失败
fail_task(
    task_id="task-001",
    reason=FailureReason.CI_FAILED,  # 或 MODEL_ERROR, TIMEOUT 等
    retry_count=2,
    cost=0.03
)
```

### 需要人工介入

```python
from utils.metrics_collector import get_metrics_collector

collector = get_metrics_collector()
collector.human_intervention(
    task_id="task-001",
    reason="复杂业务逻辑需要人工确认"
)
```

---

## 失败原因分类

| 枚举值 | 说明 | 触发条件 |
|--------|------|---------|
| `PROMPT_ERROR` | Prompt 质量问题 | 模型理解偏差 |
| `MODEL_ERROR` | 模型输出异常 | 格式错误、乱码等 |
| `CI_FAILED` | CI 检查失败 | lint/typecheck/tests 失败 |
| `REVIEW_REJECTED` | Code Review 不通过 | Reviewer 要求修改 |
| `TIMEOUT` | 超时 | 超过设定时间 |
| `ENVIRONMENT` | 环境问题 | tmux/git/网络等 |
| `UNKNOWN` | 未知原因 | 其他未分类问题 |

---

## 数据查询示例

### 获取汇总统计

```bash
curl http://localhost:8890/api/metrics/summary
```

响应示例:
```json
{
  "success": true,
  "data": {
    "total_tasks": 150,
    "completed_tasks": 128,
    "failed_tasks": 22,
    "total_cost": 45.67,
    "avg_duration_seconds": 1820.5,
    "ci_pass_rate": 0.87,
    "human_intervention_rate": 0.15,
    "today": {
      "tasks": 12,
      "cost": 3.45,
      "date": "2026-03-19"
    }
  },
  "timestamp": "2026-03-19T09:30:00"
}
```

### 获取 Agent 统计

```bash
curl http://localhost:8890/api/metrics/agents
```

### 获取失败分析

```bash
curl http://localhost:8890/api/metrics/failures?days=7
```

### 导出完整报告

```bash
curl -X POST http://localhost:8890/api/metrics/export \
  -H "Content-Type: application/json" \
  -d '{"output_path": "report.json"}'
```

---

## 数据存储

### 文件位置

```
agent-cluster/metrics/
├── tasks_metrics.jsonl      # 任务指标记录 (JSONL 格式)
├── summary_stats.json       # 汇总统计
├── agents_metrics.json      # Agent 指标
├── hourly_stats.jsonl       # 小时级聚合 (待实现)
└── cost_records.jsonl       # 成本记录 (与 cost_tracker 共享)
```

### 数据保留策略

| 数据类型 | 保留期限 | 清理策略 |
|---------|---------|---------|
| 任务明细 | 30 天 | 自动清理 |
| 汇总统计 | 永久 | 滚动聚合 |
| Agent 指标 | 永久 | 累积更新 |
| 小时级统计 | 90 天 | 自动清理 |

---

## Dashboard 使用

### 核心指标卡片

- **总任务数**: 累计处理的任务数量
- **平均完成时间**: 任务平均耗时
- **CI 通过率**: 质量指标
- **总成本**: 累计 API 成本
- **人工介入率**: 自动化程度
- **失败任务**: 需关注的问题

### Agent 性能统计

展示每个 Agent 的:
- 分配/完成/失败任务数
- 成功率
- 平均耗时
- 总成本

### 失败原因分析

按失败原因分类统计:
- 次数
- 占比
- 趋势 (待实现)

### 最近任务列表

显示最近 20 个任务的:
- 任务 ID
- 使用 Agent
- 所属阶段
- 状态
- 耗时
- 成本

---

## 告警配置 (待实现)

### 阈值告警

| 指标 | 阈值 | 动作 |
|------|------|------|
| CI 通过率 | < 70% | 钉钉通知 |
| 人工介入率 | > 30% | 钉钉通知 |
| 失败任务数 | > 10/天 | 钉钉通知 (@所有人) |
| 单日成本 | > ¥50 | 钉钉通知 |

### 配置方式

在 `cluster_config_v2.json` 中添加:

```json
{
  "metrics": {
    "alerts": {
      "enabled": true,
      "ci_pass_rate_threshold": 0.7,
      "human_intervention_threshold": 0.3,
      "daily_failure_threshold": 10,
      "daily_cost_threshold": 50.0
    }
  }
}
```

---

## 最佳实践

### 1. 定期检查指标

- **每日**: 查看 Dashboard 核心指标
- **每周**: 分析失败原因，优化 Prompt
- **每月**: 评估 Agent 性能，调整配置

### 2. 基于指标优化

| 问题 | 指标表现 | 优化方案 |
|------|---------|---------|
| Prompt 质量差 | `PROMPT_ERROR` 占比高 | 改进 Prompt 模板 |
| 模型选择不当 | 某 Agent 成功率低 | 调整 Agent 选择策略 |
| CI 配置问题 | `CI_FAILED` 占比高 | 优化 CI 配置 |
| 成本过高 | 单任务成本 > ¥0.5 | 使用更经济的模型 |

### 3. 数据驱动决策

- 根据成功率调整 Agent 权重
- 根据耗时优化任务拆解策略
- 根据失败原因针对性改进

---

## 故障排查

### 指标未更新

1. 检查 `monitor.py` 是否正常执行
2. 查看 `metrics/tasks_metrics.jsonl` 是否有新记录
3. 重启 Web 服务：`python3 web_app_v2.py --port 8890`

### Dashboard 无法访问

1. 确认 Web 服务运行：`curl http://localhost:8890/api/metrics/health`
2. 检查 Nginx 配置是否正确
3. 查看日志：`tail -f logs/web_app.log`

### 数据丢失

1. 检查 `metrics/` 目录权限
2. 查看备份文件 (如有)
3. 从 `tasks.json` 恢复基础数据

---

## 扩展开发

### 添加新指标

1. 在 `TaskMetrics` dataclass 中添加字段
2. 在 `complete_task`/`fail_task` 中更新统计
3. 在 Dashboard 中添加展示

### 自定义报告

```python
from utils.metrics_collector import get_metrics_collector

collector = get_metrics_collector()
report = collector.export_report(output_path='custom_report.json')

# 自定义分析
print(f"本周平均成本：¥{report['summary']['today']['cost']}")
```

### 集成外部系统

```python
# 发送到监控系统
import requests

stats = collector.get_summary()
requests.post('http://grafana/api/datasources/proxy/1/api/write', json={
    'metrics': stats
})
```

---

## 更新日志

### v1.0 (2026-03-19)

- ✅ 基础指标收集器实现
- ✅ Monitor.py 集成埋点
- ✅ API 端点开发
- ✅ Dashboard 页面
- ✅ 失败原因分类
- ⏳ 小时级聚合统计 (待实现)
- ⏳ 告警系统 (待实现)
- ⏳ 趋势分析图表 (待实现)

---

**维护者**: Agent 集群团队  
**最后更新**: 2026-03-19
