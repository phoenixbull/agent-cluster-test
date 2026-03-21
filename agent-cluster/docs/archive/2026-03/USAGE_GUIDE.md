# AI 产品开发智能体 V2.2 - 使用指南

**版本**: v2.2.0  
**更新时间**: 2026-03-15  
**访问地址**: http://39.107.101.25:8890

---

## 🚀 快速开始

### 1. 登录系统

**地址**: http://39.107.101.25:8890  
**账号**: `admin` / `admin123`

### 2. 功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 📊 概览 | `/` | 系统状态、快捷操作 |
| 🔄 开发流程 | `/phases` | 6 阶段开发流程 |
| 🤖 AI 智能体 | `/agents` | 10 个专业智能体 |
| 📋 工作流 | `/workflows` | 任务工作流管理 |
| 🚦 质量门禁 | `/quality` | 质量标准配置 |
| 🐛 Bug 管理 | `/bugs` | Bug 提交与追踪 |
| 📋 项目看板 | `/kanban` | Kanban 任务管理 |
| 📝 模板库 | `/templates` | 需求模板管理 |
| 💰 成本统计 | `/costs` | API 成本分析 |
| ⚙️ 设置 | `/settings` | 系统配置 |

---

## 📋 功能使用指南

### 1. 项目看板管理

**访问**: http://39.107.101.25:8890/kanban

**功能**:
- 5 列 Kanban 面板（待办/准备做/进行中/审查中/已完成）
- 任务状态快速切换
- 项目进度追踪
- 任务优先级管理

**使用步骤**:
1. 访问项目看板页面
2. 点击"添加任务"
3. 填写任务信息：
   - 任务标题
   - 优先级（高/中/低）
   - 阶段（需求/设计/开发/测试/审查/部署）
   - 预估工时
   - 任务描述
4. 点击"保存"
5. 拖拽任务卡片切换状态

---

### 2. 工作流管理

**访问**: http://39.107.101.25:8890/workflows

**功能**:
- 提交新任务
- 查看工作流状态
- 追踪任务进度

**使用步骤**:
1. 访问概览页面或工作流页面
2. 在"提交新任务"表单中填写：
   - 产品需求描述（详细描述功能需求）
   - 选择项目
3. 点击"启动工作流"
4. 系统将自动执行 6 阶段开发流程：
   - Phase 1: 需求分析
   - Phase 2: 技术设计
   - Phase 3: 开发实现
   - Phase 4: 测试验证
   - Phase 5: 代码审查
   - Phase 6: 部署上线

---

### 3. Bug 管理

**访问**: http://39.107.101.25:8890/bugs

**功能**:
- 提交 Bug
- Bug 状态追踪
- 自动修复流程

**使用步骤**:
1. 访问 Bug 管理页面
2. 点击"提交 Bug"
3. 填写 Bug 信息：
   - Bug 标题
   - 优先级（高/中/低）
   - 详细描述（现象、复现步骤、预期行为）
   - 相关文件路径
   - 关联项目
4. 点击"提交并启动修复流程"
5. 系统将自动：
   - 分析 Bug 原因
   - 修复代码
   - 运行测试
   - 代码审查
   - 创建 PR

---

### 4. 模板库管理

**访问**: http://39.107.101.25:8890/templates

**功能**:
- 保存常用需求模板
- 快速复用模板
- 模板分类管理

**使用步骤**:
1. 访问模板库页面
2. 点击"新建模板"
3. 填写模板信息：
   - 模板名称
   - 描述
   - 需求内容
   - 项目分类
4. 点击"保存模板"
5. 使用时点击"使用"按钮快速加载

---

### 5. AI 智能体阵容

**访问**: http://39.107.101.25:8890/agents

**智能体列表**:

#### 执行智能体（7 个）
| 智能体 | 角色 | 阶段 | 模型 |
|--------|------|------|------|
| Product Manager | 产品经理 | Phase 1 | qwen-max |
| Tech Lead | 技术负责人 | Phase 2 | qwen-max |
| Designer | 设计师 | Phase 2 | qwen-vl-plus |
| DevOps | 运维工程师 | Phase 2/6 | qwen-plus |
| Codex | 后端专家 | Phase 3 | qwen-coder-plus |
| Claude-Code | 前端专家 | Phase 3 | kimi-k2.5 |
| Tester | 测试工程师 | Phase 4 | qwen-coder-plus |

#### 审查智能体（3 个）
| 智能体 | 角色 | 阶段 | 模型 |
|--------|------|------|------|
| Codex Reviewer | 逻辑审查 | Phase 5 | glm-4.7 |
| Gemini Reviewer | 安全审查 | Phase 5 | qwen-plus |
| Claude Reviewer | 基础审查 | Phase 5 | MiniMax-M2.5 |

---

### 6. 开发流程

**访问**: http://39.107.101.25:8890/phases

**6 阶段开发流程**:

```
Phase 1: 需求分析
  - 产品经理分析需求
  - 输出：PRD 文档、用户故事、验收标准

Phase 2: 技术设计
  - 技术负责人架构设计
  - 设计师 UI/UX 设计
  - DevOps 部署规划
  - 输出：架构文档、UI 设计、部署配置

Phase 3: 开发实现
  - Codex 后端开发
  - Claude-Code 前端开发
  - 输出：后端代码、前端代码

Phase 4: 测试验证 🔒 质量门禁
  - Tester 编写测试
  - 输出：测试报告、Bug 列表
  - 要求：测试覆盖率 > 80%

Phase 5: 代码审查 🔒 质量门禁
  - 3 个审查智能体审查
  - 输出：审查报告
  - 要求：审查评分 > 80 分

Phase 6: 部署上线 🔐 需要确认
  - DevOps 部署
  - 输出：运行中的系统
  - 需要人工确认
```

---

## 🔧 API 使用示例

### 认证登录
```bash
curl -X POST "http://39.107.101.25:8890/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 获取项目看板
```bash
curl "http://39.107.101.25:8890/api/kanban" \
  -H "Cookie: auth_token=YOUR_TOKEN"
```

### 提交任务
```bash
curl -X POST "http://39.107.101.25:8890/api/submit" \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{"requirement":"实现用户登录功能","project":"default"}'
```

### 提交 Bug
```bash
curl -X POST "http://39.107.101.25:8890/api/bugs/submit" \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "title":"登录页面报错",
    "priority":"high",
    "description":"点击登录按钮后页面无响应",
    "files":"src/pages/login.py",
    "project":"ecommerce"
  }'
```

---

## 📊 系统状态监控

### 检查服务状态
```bash
curl http://39.107.101.25:8890/api/status
```

### 查看智能体状态
```bash
curl "http://39.107.101.25:8890/api/agents" \
  -H "Cookie: auth_token=YOUR_TOKEN"
```

### 查看工作流状态
```bash
curl "http://39.107.101.25:8890/api/workflows" \
  -H "Cookie: auth_token=YOUR_TOKEN"
```

---

## ⚠️ 常见问题

### Q1: 页面显示"暂无数据"
**A**: 这是正常的，系统刚安装还没有创建数据。请按照上述指南创建项目、任务或模板。

### Q2: 外网无法访问
**A**: 请检查阿里云安全组是否开放 8890 端口。
- 登录阿里云控制台
- 进入 ECS → 安全组
- 添加入站规则：端口 8890/TCP，授权对象 0.0.0.0/0

### Q3: 工作流执行失败
**A**: 检查以下项：
1. orchestrator.py 是否运行
2. 查看 logs/web.log 日志
3. 确认模型 API 配置正确

### Q4: Bug 修复流程未启动
**A**: 检查以下项：
1. 查看 logs/bug_*.log 日志
2. 确认 orchestrator.py 正常运行
3. 检查钉钉通知配置

---

## 📞 技术支持

**GitHub**: https://github.com/phoenixbull/ai-product-dev-agents  
**文档**: USAGE_GUIDE.md  
**版本**: v2.2.0

---

**最后更新**: 2026-03-15 15:10
