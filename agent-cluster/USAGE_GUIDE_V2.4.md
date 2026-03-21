# 📘 AI 产品开发智能体 - 使用指南

**版本**: v2.4.0 告警增强版  
**更新日期**: 2026-03-19  
**适用对象**: 开发者、产品经理、技术负责人

---

## 🚀 快速开始

### 5 分钟上手

```bash
# 1. 访问控制台
http://服务器 IP:8890/

# 2. 登录
账号：admin
密码：admin123

# 3. 提交任务
在"提交新任务"框中填写需求

# 4. 等待完成
通常 30-60 分钟

# 5. 审查 PR
查看 GitHub PR 并合并
```

---

## 📋 详细使用流程

### 步骤 1: 准备工作

#### 1.1 环境检查

```bash
# 检查服务状态
curl http://localhost:8890/health

# 查看集群状态
cd /home/admin/.openclaw/workspace/agent-cluster
python3 cluster_manager.py status
```

**预期输出**:
```
✅ Web 服务正常
✅ 监控脚本运行中
✅ 钉钉通知器已初始化
✅ 告警管理器已初始化
```

#### 1.2 配置钉钉通知 (可选)

编辑 `cluster_config_v2.json`:

```json
{
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
      "secret": "YOUR_SECRET",
      "events": [
        "pr_ready",
        "task_complete",
        "task_failed",
        "human_intervention_needed"
      ]
    }
  }
}
```

**获取钉钉 Token**:
1. 打开钉钉群
2. 群设置 → 智能群助手 → 添加机器人
3. 选择"自定义"机器人
4. 复制 Webhook 地址和密钥

---

### 步骤 2: 提交任务

#### 方式 1: Web 界面 (推荐)

1. **访问控制台**
   ```
   http://服务器 IP:8890/
   ```

2. **填写需求**
   ```
   产品名称：用户登录功能
   
   需求描述：
   实现用户登录功能，要求：
   1. 支持邮箱和密码登录
   2. 密码加密存储（bcrypt）
   3. 登录失败 5 次锁定 30 分钟
   4. 生成 JWT token（有效期 24 小时）
   5. 编写单元测试（覆盖率≥80%）
   
   技术栈：Python 3.8 + FastAPI + PostgreSQL
   ```

3. **选择项目**
   - 默认项目
   - 电商项目
   - 博客系统
   - CRM 系统

4. **启动工作流**
   - 点击"🚀 启动工作流"按钮
   - 等待确认提示
   - 系统开始执行

#### 方式 2: 命令行

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 提交任务
python3 orchestrator.py "实现用户登录功能，要求支持邮箱和密码登录..."

# 查看进度
python3 cluster_manager.py status
```

#### 方式 3: API 调用

```bash
curl -X POST http://localhost:8890/api/submit \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "requirement": "实现用户登录功能...",
    "project": "default"
  }'
```

---

### 步骤 3: 监控进度

#### Web 界面监控

访问：`http://服务器 IP:8890/`

**查看内容**:
- 进行中的工作流数量
- 今日完成/失败统计
- 最近工作流列表
- Agent 状态

#### 命令行监控

```bash
# 查看集群状态
python3 cluster_manager.py status

# 查看子代理
python3 cluster_manager.py subagents list

# 查看监控日志
tail -f monitor.log
```

#### 指标 Dashboard

访问：`http://服务器 IP:8890/metrics.html`

**查看内容**:
- 核心指标卡片 (6 个)
- Agent 性能统计
- 任务历史
- 失败分析

#### 告警通知

**钉钉通知类型**:

| 事件 | 通知内容 | @所有人 |
|------|---------|--------|
| PR 就绪 | PR 链接、审查状态 | ❌ |
| 任务完成 | 任务描述、PR 链接 | ❌ |
| 任务失败 | 失败原因、重试次数 | ✅ |
| 人工介入 | 介入原因、任务详情 | ✅ |

**告警通知**:
- CI 通过率 < 70%
- 失败任务 > 5 个/天
- 单日成本 > ¥50
- Agent 成功率 < 60%
- 人工介入率 > 30%

---

### 步骤 4: 审查 PR

#### GitHub 审查

1. **收到通知**
   ```
   ✅ 任务完成
   
   任务：实现用户登录功能
   PR: #123
   状态：ready_for_merge
   CI: success
   审查通过：3
   
   可以 Review 并合并了。
   ```

2. **查看 PR**
   - 打开 GitHub PR 链接
   - 查看代码变更
   - 查看 CI 状态
   - 查看 AI 审查意见

3. **审查要点**
   - ✅ 代码逻辑正确
   - ✅ 测试覆盖率 ≥ 80%
   - ✅ 无安全漏洞
   - ✅ 符合代码规范
   - ✅ 文档完整

4. **合并代码**
   - 点击"Merge pull request"
   - 选择"Squash and merge"或"Create a merge commit"
   - 确认合并

#### 本地审查 (可选)

```bash
# 克隆仓库
git clone https://github.com/phoenixbull/agent-cluster-test.git
cd agent-cluster-test

# 切换到 PR 分支
git fetch origin pull/123/head:pr-123
git checkout pr-123

# 运行测试
python3 -m pytest tests/

# 查看代码
code .
```

---

### 步骤 5: 部署上线

#### 自动部署 (推荐)

**配置 CI/CD**:

`.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  pull_request:
    types: [closed]

jobs:
  deploy:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Production
        run: |
          # 部署脚本
          docker-compose up -d
```

#### 手动部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 构建 Docker 镜像
docker build -t myapp:latest .

# 3. 停止旧容器
docker-compose down

# 4. 启动新容器
docker-compose up -d

# 5. 验证部署
curl http://localhost:8080/health
```

---

## 📖 进阶使用

### 场景 1: 多项目并行

**问题**: 同时开发多个功能

**解决方案**:

```bash
# 项目 A: 用户登录
python3 orchestrator.py "[电商] 实现用户登录功能"

# 项目 B: 购物车
python3 orchestrator.py "[电商] 实现购物车功能"

# 项目 C: 文章评论
python3 orchestrator.py "[博客] 实现文章评论功能"
```

**隔离机制**:
- 每个项目独立 worktree
- 独立 tmux 会话
- 独立 Git 分支

### 场景 2: 紧急 Bug 修复

**问题**: 生产环境出现 Bug

**解决方案**:

```bash
# 提交紧急 Bug 修复任务
python3 orchestrator.py "🐛 紧急 Bug：用户无法登录，错误信息：..."

# 设置高优先级
# 在 Web 界面选择"高"优先级

# 监控进度
tail -f monitor.log | grep "BUG"
```

**预期时间**: 30-60 分钟

### 场景 3: 大型重构

**问题**: 需要重构整个模块

**解决方案**:

```bash
# 1. 提交重构需求
python3 orchestrator.py "重构用户模块，提升可维护性，要求：
1. 拆分大文件
2. 提取公共函数
3. 添加类型注解
4. 保持测试覆盖"

# 2. 系统自动拆解为子任务
# - 分析现有代码
# - 设计新结构
# - 分步重构
# - 运行测试

# 3. 审查每个子任务的 PR
```

**预期时间**: 2-4 小时

---

## 🔧 常用命令

### 集群管理

```bash
# 启动集群
python3 cluster_manager.py start

# 停止集群
python3 cluster_manager.py stop

# 查看状态
python3 cluster_manager.py status

# 查看子代理
python3 cluster_manager.py subagents list

# 查看任务
python3 cluster_manager.py tasks list
```

### 监控命令

```bash
# 运行监控脚本
python3 monitor.py

# 查看监控日志
tail -f monitor.log

# 查看 Web 日志
tail -f logs/web_app.log

# 查看告警历史
cat memory/alert_history.json
```

### 指标查询

```bash
# 汇总统计
curl http://localhost:8890/api/metrics/summary

# Agent 统计
curl http://localhost:8890/api/metrics/agents

# 任务历史
curl http://localhost:8890/api/metrics/tasks

# 失败分析
curl http://localhost:8890/api/metrics/failures
```

---

## ⚠️ 常见问题

### Q1: Agent 不响应

**现象**: 任务提交后长时间无反应

**排查步骤**:
```bash
# 1. 检查 tmux 会话
tmux list-sessions

# 2. 检查日志
tail -f monitor.log

# 3. 重启集群
python3 cluster_manager.py stop
python3 cluster_manager.py start
```

**解决方案**:
- 重启 tmux 会话
- 检查网络连接
- 查看模型配额

### Q2: CI 一直失败

**现象**: PR 创建但 CI 始终红色

**排查步骤**:
```bash
# 1. 查看 CI 日志
# GitHub Actions → 查看具体失败步骤

# 2. 本地运行测试
python3 -m pytest tests/ -v

# 3. 检查依赖
pip install -r requirements.txt
```

**解决方案**:
- 修复测试错误
- 更新依赖版本
- 调整 CI 配置

### Q3: 成本过高

**现象**: 单日成本超过预算

**排查步骤**:
```bash
# 1. 查看成本统计
curl http://localhost:8890/api/metrics/costs

# 2. 查看各模型使用情况
curl http://localhost:8890/api/metrics/by_model
```

**解决方案**:
- 调整模型选择策略
- 优化 Prompt 减少 token 使用
- 设置成本告警阈值

### Q4: 告警误报

**现象**: 无问题时触发告警

**排查步骤**:
```bash
# 1. 查看告警历史
cat memory/alert_history.json

# 2. 检查阈值配置
cat cluster_config_v2.json | grep -A5 "alerts"
```

**解决方案**:
- 调整告警阈值
- 增加冷却时间
- 优化指标计算逻辑

---

## 📊 最佳实践

### 需求描述模板

```markdown
# 功能名称

## 背景
[为什么要做这个功能]

## 目标
[期望达到什么效果]

## 详细需求
1. [需求点 1]
2. [需求点 2]
3. [需求点 3]

## 技术约束
- 语言：Python 3.8+
- 框架：FastAPI
- 数据库：PostgreSQL

## 验收标准
- [ ] 功能正常工作
- [ ] 测试覆盖率 ≥ 80%
- [ ] 通过所有 CI 检查
- [ ] 代码审查通过
```

### 审查清单

**代码审查**:
- [ ] 代码逻辑正确
- [ ] 无安全漏洞
- [ ] 符合代码规范
- [ ] 异常处理完善
- [ ] 日志记录完整

**测试审查**:
- [ ] 单元测试覆盖 ≥ 80%
- [ ] 集成测试通过
- [ ] 边界条件测试
- [ ] 异常场景测试

**文档审查**:
- [ ] README 更新
- [ ] API 文档完整
- [ ] 注释清晰
- [ ] 变更记录

### 成本控制

**模型选择策略**:
```python
# 简单任务 → qwen-turbo (便宜、快速)
# 常规任务 → qwen-coder-plus (性价比高)
# 复杂任务 → qwen-max (强大、稍贵)
# 设计任务 → qwen-vl-plus (多模态)
```

**优化技巧**:
- 精简 Prompt，减少 token 使用
- 复用历史上下文
- 设置成本告警
- 定期查看成本统计

---

## 📁 文件位置

```
# 核心文件
/home/admin/.openclaw/workspace/agent-cluster/
├── cluster_config_v2.json      # 配置文件
├── monitor.py                  # 监控脚本
├── web_app_v2.py               # Web 界面
├── orchestrator.py             # 编排器
└── tasks.json                  # 任务注册表

# 日志文件
├── monitor.log                 # 监控日志
├── logs/
│   └── web_app.log            # Web 日志

# 数据文件
└── memory/
    ├── alert_history.json     # 告警历史
    ├── cost_stats.json        # 成本统计
    └── metrics/               # 指标数据
```

---

## 🔗 相关资源

### 内部文档

- [README.md](README.md) - 项目说明
- [AI_AGENT_V2.4_SUMMARY.md](AI_AGENT_V2.4_SUMMARY.md) - 系统介绍
- [VERSION.md](VERSION.md) - 版本历史
- [METRICS_GUIDE.md](docs/METRICS_GUIDE.md) - 指标使用指南

### 外部资源

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [GitHub 仓库](https://github.com/phoenixbull/agent-cluster-test)
- [阿里云百炼](https://bailian.console.aliyun.com)

---

## 📞 获取帮助

### 问题排查

1. **查看日志**: `tail -f monitor.log`
2. **检查状态**: `python3 cluster_manager.py status`
3. **查看文档**: `cat README.md`

### 联系方式

- **GitHub Issues**: 提交问题
- **钉钉群**: 实时沟通
- **邮件**: 重大问题

---

**最后更新**: 2026-03-19 16:54  
**版本**: v2.4.0 告警增强版  
**维护者**: Agent 集群团队
