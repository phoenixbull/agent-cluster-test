# 🚀 Agent 集群自动化流水线 - 使用指南

## 📋 快速开始

### 方式 1: 命令行直接触发

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 启动工作流
python3 orchestrator.py "创建一个用户登录系统，包含注册、登录、密码找回功能"
```

**输出示例**:
```
📥 接收到产品需求 (来源：manual)
   需求：创建一个用户登录系统...

🔄 开始执行工作流：wf-20260305-092029-32bb

📊 阶段 1/6: 需求分析
   ✅ 分解为 3 个任务

🎨 阶段 2/6: UI/UX 设计
   ✅ 设计完成

💻 阶段 3/6: 编码实现
   ✅ 编码完成

🧪 阶段 4/6: 测试
   ✅ 测试通过

🔍 阶段 5/6: AI Review
   ✅ Review 通过

📦 阶段 6/6: 创建 PR
   ✅ PR 创建完成：#1

✅ 工作流 wf-20260305-092029-32bb 完成！
```

---

### 方式 2: 钉钉机器人触发

#### 第 1 步：启动 Webhook 服务器

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 启动钉钉 Webhook 服务器 (默认端口 8888)
python3 webhooks/dingtalk_webhook.py --port 8888
```

#### 第 2 步：配置钉钉机器人

1. **获取服务器 IP**
   ```bash
   # 查看服务器公网 IP
   curl ifconfig.me
   ```

2. **在钉钉群配置机器人**
   - 打开钉钉群 → 群设置 → 智能群助手
   - 添加机器人 → 自定义
   - 配置 HTTP POST 地址：`http://<你的服务器 IP>:8888/dingtalk`
   - 安全设置：选择"加签密钥"（推荐）

3. **测试连接**
   在群里发送消息，查看 Webhook 服务器日志是否有输出

#### 第 3 步：在钉钉发送需求

在钉钉群里@机器人并发送产品需求：

```
@Agent 集群助手 创建一个电商小程序的购物车功能，包括：
1. 添加商品到购物车
2. 修改商品数量
3. 删除商品
4. 计算总价
5. 结算功能
```

**自动回复**:
```
✅ 需求已接收，工作流已启动
预计完成时间：60-90 分钟
完成后会收到通知。
```

---

## 🔄 完整工作流程

```
用户发送需求
    ↓
┌─────────────────────────────────────┐
│ 1. 需求分析 (自动)                   │
│    - 解析需求                        │
│    - 分解任务                        │
│    - 评估依赖                        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. UI/UX 设计 (Designer Agent)       │
│    - 线框图                          │
│    - 设计规范                        │
│    - HTML 原型                         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 编码实现 (并行)                   │
│    ├─ 后端 (Codex)                  │
│    │  - API 设计                     │
│    │  - 数据库                       │
│    │  - 业务逻辑                     │
│    └─ 前端 (Claude Code)            │
│       - 组件开发                     │
│       - 页面集成                     │
│       - 样式实现                     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. 测试循环 (自动修复)               │
│    - 运行测试                        │
│    - 失败 → 分析错误 → 修复 → 重测   │
│    - 直到通过或达到最大重试次数      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. AI Review (3 个 Reviewer)          │
│    - Codex Reviewer: 逻辑/边界       │
│    - Gemini Reviewer: 安全/扩展      │
│    - Claude Reviewer: 基础检查       │
│    - 必须全部通过                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 6. 创建 Pull Request                 │
│    - 创建功能分支                    │
│    - 提交代码到 GitHub               │
│    - 创建 PR                         │
│    - 触发 CI/CD                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 7. 钉钉通知                          │
│    - 发送 PR 就绪通知                 │
│    - 附 PR 链接和检查清单            │
└─────────────────────────────────────┘
    ↓
人工 Review & 合并
```

---

## 📱 钉钉通知示例

### 工作流启动通知
```markdown
## 🚀 产品需求已接收

**工作流 ID**: wf-20260305-092029-32bb

**需求**: 创建电商小程序购物车功能...

**时间**: 2026-03-05 09:20

---

### 📋 预计流程

1. ⏳ 需求分析
2. ⏳ UI/UX 设计
3. ⏳ 编码实现 (前后端并行)
4. ⏳ 测试 (自动修复)
5. ⏳ AI Review
6. ⏳ 创建 PR

---

⏱️ **预计完成时间**: 60-90 分钟

完成后会收到钉钉通知。
```

### PR 就绪通知
```markdown
## 🎉 PR 已就绪，可以 Review！

**任务**: 电商小程序购物车功能

**Agent**: cluster

**PR**: #42

---

### ✅ 检查清单

- ✅ UI 设计完成
- ✅ 后端 API 实现 (5 个接口)
- ✅ 前端组件实现
- ✅ 单元测试通过 (23/23)
- ✅ 集成测试通过
- ✅ AI Review 通过 (3/3)
- ✅ CI 全绿

---

🔗 https://github.com/phoenixbull/agent-cluster-test/pull/42

⏱️ Review 预计需要 10-15 分钟
```

### 需要人工介入通知
```markdown
## 🚨 需要人工介入

**任务**: 电商小程序购物车功能

**失败原因**: 测试失败，已重试 3 次

**错误**: 支付接口调用超时

---

⚠️ 请检查并决定下一步操作。
```

---

## 🔍 监控和调试

### 查看工作流状态

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 查看最近的工作流状态
cat memory/workflow_state.json | python3 -m json.tool
```

### 查看运行日志

```bash
# 查看 orchestrator 日志
tail -f logs/orchestrator.log

# 查看 webhook 日志
tail -f logs/webhook.log
```

### 测试工作流

```bash
# 运行测试工作流
python3 orchestrator.py "测试需求：创建一个简单的 TODO 应用"
```

---

## ⚙️ 配置选项

### cluster_config.json

```json
{
  "workflow": {
    "auto_start": true,
    "max_retries": 3,
    "timeout_hours": 4,
    "parallel_agents": 3
  },
  "notifications": {
    "dingtalk": {
      "enabled": true,
      "notify_on": ["start", "complete", "failed", "human_needed"]
    }
  },
  "review": {
    "required_reviewers": 2,
    "auto_merge": false,
    "require_ci": true
  }
}
```

---

## 🛠️ 常见问题

### Q: Webhook 服务器无法启动？
**A**: 检查端口是否被占用
```bash
# 查看端口占用
netstat -tlnp | grep 8888

# 更换端口
python3 webhooks/dingtalk_webhook.py --port 9999
```

### Q: 钉钉收不到通知？
**A**: 检查以下配置
1. Webhook URL 是否正确
2. 加签密钥是否配置
3. 服务器防火墙是否开放端口
4. 钉钉机器人是否启用

### Q: 工作流执行失败？
**A**: 查看日志定位问题
```bash
cat memory/workflow_state.json | python3 -m json.tool
```

---

## 📊 工作流状态说明

| 状态 | 说明 |
|------|------|
| started | 工作流已启动 |
| analysis | 需求分析中 |
| design | UI 设计中 |
| coding | 编码实现中 |
| testing | 测试中 |
| review | AI Review 中 |
| pr | 创建 PR 中 |
| completed | 完成 |
| failed | 失败 |

---

## 🎯 优化进度

### ✅ 已完成

#### 近期 (本周)
- [x] 集成真实 LLM API 进行需求分析
- [x] 实现 Designer Agent 调用
- [x] 实现 Codex/Claude Agent 调度
- [x] 集成 GitHub API 创建 PR

#### 中期 (下周)
- [x] 实现测试循环自动修复
- [x] 集成 3 个 Reviewer Agent
- [x] 添加工作流进度查询
- [x] 添加人工介入接口

#### 长期 (后续)
- [x] Web 界面
- [x] 工作流模板库
- [x] 多项目支持
- [x] 成本统计

---

## 🆕 新增功能使用指南

### 1. Web 界面

**启动 Web 服务**:
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app.py --port 8889
```

**访问地址**: http://localhost:8889

**功能**:
- 📊 系统状态概览（运行状态、活跃工作流、今日完成/失败）
- 🚀 在线提交任务（选择项目、输入需求）
- 📋 工作流历史记录
- 📝 模板库管理
- 💰 成本统计

### 2. 工作流模板库

**位置**: `memory/templates.json`

**使用方式**:

1. **Web 界面管理**
   - 访问 `/templates` 页面
   - 创建新模板（名称、描述、需求内容、项目）
   - 使用模板（一键填充需求到提交表单）
   - 删除模板

2. **API 调用**
   ```bash
   # 获取模板列表
   curl http://localhost:8889/api/templates
   
   # 保存模板
   curl -X POST http://localhost:8889/api/template/save \
     -H "Content-Type: application/json" \
     -d '{"name":"示例模板","description":"描述","requirement":"需求内容","project":"default"}'
   
   # 删除模板
   curl -X POST http://localhost:8889/api/template/delete \
     -H "Content-Type: application/json" \
     -d '{"id":"tpl_xxx"}'
   ```

**预置模板**:
- 用户登录系统
- 电商购物车
- 博客文章系统
- CRM 客户管理
- TODO 待办事项

### 3. 多项目支持

**配置文件**: `projects.json`

**使用方式**:

```bash
# 指定项目前缀
python3 orchestrator.py "[电商] 添加购物车功能"
python3 orchestrator.py "[博客] 实现文章评论功能"
python3 orchestrator.py "[CRM] 添加客户管理功能"

# 或使用关键词自动识别
python3 orchestrator.py "实现购物车和订单管理"  # 自动识别为电商项目
```

**项目隔离**:
- 独立工作区目录
- 独立 GitHub 仓库
- 独立分支前缀
- 独立 Agent 会话

### 4. 成本统计

**数据文件**: `memory/cost_stats.json`

**查看方式**:

1. **Web 界面**: 访问 `/costs` 页面
2. **API**: `curl http://localhost:8889/api/costs`
3. **Python**:
   ```python
   from utils.cost_tracker import get_cost_stats
   stats = get_cost_stats()
   print(f"今日成本：¥{stats['today']['total']:.2f}")
   ```

**统计维度**:
- 今日/本周/本月成本
- 按模型统计（调用次数、Token 消耗、成本）
- 平均单次工作流成本
- 工作流级别成本追踪

**集成到 Orchestrator**:
```python
from utils.cost_tracker import record_api_call

# 在 API 调用后记录
cost = record_api_call(
    model="qwen-plus",
    input_tokens=1500,
    output_tokens=800,
    workflow_id="wf-20260306-xxx"
)
```

---

## 📊 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                      Web 界面 (web_app.py)                    │
│  概览 · 工作流 · 模板库 · 成本统计 · 设置                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    编排层 (orchestrator.py)                   │
│  需求分析 · 任务分解 · Agent 调度 · 工作流管理                  │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Codex Agent    │ │ Claude Code     │ │  Gemini         │
│  后端专家       │ │ 前端专家        │ │ 设计专家        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
                    GitHub CI/CD + AI Reviewers
                              │
                              ▼
                       钉钉通知 + 成本统计
```

---

**文档更新时间**: 2026-03-05  
**版本**: v1.0  
**状态**: 核心框架已完成，待集成真实 Agent
