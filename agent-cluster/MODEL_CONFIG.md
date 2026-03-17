# 🤖 Agent 集群 V2.0 - 模型配置信息

**配置版本**: v2.0  
**更新时间**: 2026-03-05

---

## 📊 模型配置总览

| Agent | 模型 | Provider | Temperature | Max Tokens | 角色 |
|-------|------|----------|-------------|------------|------|
| **Zoe (编排者)** | qwen-max | alibaba-cloud | 0.7 | 4096 | orchestrator |
| **Codex (后端)** | qwen-coder-plus | alibaba-cloud | 0.3 | 8192 | backend_specialist |
| **Claude Code (前端)** | kimi-k2.5 | alibaba-cloud | 0.5 | 4096 | frontend_specialist |
| **Designer (设计)** | qwen-vl-plus | alibaba-cloud | 0.6 | 4096 | design_specialist |
| **Codex Reviewer** | glm-4.7 | alibaba-cloud | - | - | code_reviewer |
| **Gemini Reviewer** | qwen-plus | alibaba-cloud | - | - | code_reviewer |
| **Claude Reviewer** | MiniMax-M2.5 | alibaba-cloud | - | - | code_reviewer |

**所有 Agent 均使用 Alibaba Cloud (通义千问) 模型系列**

---

## 🎯 详细配置

### 1. Zoe 编排者 (Orchestrator)

```json
{
  "id": "zoe",
  "name": "Zoe 编排者",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-max",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "role": "orchestrator",
  "skills": [
    "task_decomposition",
    "agent_selection",
    "prompt_engineering",
    "failure_analysis",
    "context_management"
  ]
}
```

**职责**:
- 需求分析和任务分解
- Agent 选择和调度
- 工作流控制和协调
- 异常处理和重试

**模型特点**:
- `qwen-max`: 通义千问最强模型，适合复杂推理和决策
- `temperature: 0.7`: 平衡创造性和准确性
- `max_tokens: 4096`: 足够的上下文长度

---

### 2. Codex 后端专家 (Backend Specialist)

```json
{
  "id": "codex",
  "name": "Codex 后端专家",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-coder-plus",
    "temperature": 0.3,
    "max_tokens": 8192
  },
  "role": "backend_specialist",
  "skills": [
    "backend_logic",
    "bug_fixing",
    "refactoring",
    "cross_file_reasoning",
    "api_design"
  ],
  "task_types": [
    "backend_logic",
    "bug_fix",
    "refactoring",
    "api_design",
    "database"
  ]
}
```

**职责**:
- 后端 API 开发
- 数据库设计
- 业务逻辑实现
- Bug 修复和重构

**模型特点**:
- `qwen-coder-plus`: 通义千问代码专用模型，擅长编程
- `temperature: 0.3`: 低温度，保证代码准确性和一致性
- `max_tokens: 8192`: 长上下文，适合跨文件推理

**生成代码示例**:
- Python Flask/FastAPI API
- SQLAlchemy 数据模型
- RESTful 接口设计
- 单元测试

---

### 3. Claude Code 前端专家 (Frontend Specialist)

```json
{
  "id": "claude-code",
  "name": "Claude Code 前端专家",
  "model": {
    "provider": "alibaba-cloud",
    "model": "kimi-k2.5",
    "temperature": 0.5,
    "max_tokens": 4096
  },
  "role": "frontend_specialist",
  "skills": [
    "frontend_development",
    "git_operations",
    "component_development",
    "rapid_iteration"
  ],
  "task_types": [
    "frontend",
    "ui_component",
    "git_operation",
    "quick_fix"
  ]
}
```

**职责**:
- React/Vue组件开发
- HTML/CSS/JavaScript实现
- 前端样式和交互
- Git 操作

**模型特点**:
- `kimi-k2.5`: 月之暗面长上下文模型，擅长文档分析和多模态
- `temperature: 0.5`: 中等温度，兼顾创造性和规范性
- `max_tokens: 4096`: 标准上下文长度（实际支持 262K）

**生成代码示例**:
- React 组件 (JSX)
- CSS 样式文件
- JavaScript 交互逻辑
- 响应式设计

---

### 4. Designer 设计专家 (Design Specialist)

```json
{
  "id": "designer",
  "name": "设计专家 (Gemini)",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-vl-plus",
    "temperature": 0.6,
    "max_tokens": 4096
  },
  "role": "design_specialist",
  "skills": [
    "ui_design",
    "wireframe",
    "prototype",
    "design_system",
    "visual_system",
    "html_css",
    "design_spec"
  ],
  "task_types": [
    "ui_design",
    "visual",
    "html_css",
    "design_spec",
    "mockup",
    "prototype"
  ]
}
```

**职责**:
- UI/UX设计
- 线框图和原型
- 设计规范制定
- HTML/CSS原型实现

**模型特点**:
- `qwen-vl-plus`: 通义千问视觉语言模型，擅长图像理解和设计
- `temperature: 0.6`: 较高温度，鼓励创意设计
- `max_tokens: 4096`: 标准上下文长度

**生成内容示例**:
- 设计规范文档
- 线框图描述
- 配色方案
- HTML/CSS原型

---

### 5. 代码审查者 (Reviewers)

#### Codex Reviewer
```json
{
  "id": "codex-reviewer",
  "name": "Codex 审查者",
  "model": "glm-4.7",
  "focus": "边界情况、逻辑错误、竞态条件",
  "weight": "high",
  "required": true
}
```

**审查重点**:
- 代码逻辑正确性
- 边界情况处理
- 竞态条件和并发问题
- 性能优化建议

**模型特点**:
- `glm-4.7`: 智谱 GLM 系列模型，擅长逻辑推理和代码理解

---

#### Gemini Reviewer
```json
{
  "id": "gemini-reviewer",
  "name": "Gemini 审查者",
  "model": "qwen-plus",
  "focus": "安全问题、扩展性、代码质量",
  "weight": "medium",
  "required": true
}
```

**审查重点**:
- 安全漏洞检查
- 代码可扩展性
- 代码质量和规范
- 最佳实践遵循

---

#### Claude Reviewer
```json
{
  "id": "claude-reviewer",
  "name": "Claude 审查者",
  "model": "MiniMax-M2.5",
  "focus": "基础检查（仅 critical 问题）",
  "weight": "low",
  "required": false
}
```

**审查重点**:
- 基础语法检查
- Critical 问题识别
- 快速反馈

**模型特点**:
- `MiniMax-M2.5`: MiniMax 最新模型，超长上下文 (204K)，适合快速扫描大文件

---

## 📈 模型选择策略

### 按任务类型

| 任务类型 | 推荐模型 | 原因 |
|----------|----------|------|
| **需求分析** | qwen-max | 复杂推理和理解 |
| **后端开发** | qwen-coder-plus | 代码专用，准确性高 |
| **前端开发** | qwen-plus | 平衡性能和成本 |
| **UI 设计** | qwen-vl-plus | 视觉理解能力强 |
| **代码审查** | qwen-coder-plus | 代码理解深入 |
| **快速修复** | qwen-turbo | 快速响应 |

### 按 Temperature 设置

| Temperature | 适用场景 | Agent |
|-------------|----------|-------|
| **0.2-0.3** | 代码生成、数学计算 | Codex |
| **0.4-0.6** | 一般任务、前端开发 | Claude Code, Designer |
| **0.7-0.8** | 创意写作、需求分析 | Zoe |
| **0.9-1.0** | 头脑风暴、创意发散 | - |

---

## 🔧 配置位置

**主配置文件**: `/home/admin/.openclaw/workspace/agent-cluster/cluster_config.json`

**修改示例**:
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
nano cluster_config.json
```

---

## 📊 性能对比

| 模型 | 推理速度 | 代码质量 | 成本 | 适用场景 |
|------|----------|----------|------|----------|
| **qwen-max** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高 | 复杂任务 |
| **qwen-coder-plus** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中高 | 代码生成 |
| **qwen-plus** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 通用任务 |
| **qwen-vl-plus** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中高 | 视觉任务 |
| **qwen-turbo** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 低 | 快速任务 |

---

## 🎯 使用建议

### 1. 代码生成任务
- **推荐**: `qwen-coder-plus`
- **Temperature**: 0.2-0.3
- **原因**: 代码准确性优先

### 2. 需求分析任务
- **推荐**: `qwen-max`
- **Temperature**: 0.7-0.8
- **原因**: 需要理解和推理

### 3. 前端开发任务
- **推荐**: `qwen-plus`
- **Temperature**: 0.5-0.6
- **原因**: 平衡创造性和规范

### 4. 设计任务
- **推荐**: `qwen-vl-plus`
- **Temperature**: 0.6-0.7
- **原因**: 视觉理解能力强

### 5. 代码审查任务
- **推荐**: `qwen-coder-plus`
- **Temperature**: 0.2-0.3
- **原因**: 准确性和一致性

---

## 📝 配置说明

### Provider
- **alibaba-cloud**: 阿里云通义千问 API
- 所有模型均来自同一 Provider，保证一致性

### Temperature
- **范围**: 0.0-1.0
- **低值 (0.1-0.3)**: 确定性强，适合代码
- **中值 (0.4-0.6)**: 平衡，适合一般任务
- **高值 (0.7-1.0)**: 创造性强，适合创意任务

### Max Tokens
- **4096**: 标准配置，适合大多数任务
- **8192**: 长上下文，适合复杂任务
- 根据任务复杂度调整

---

## 🔗 相关链接

- **配置文件**: `cluster_config.json`
- **编排器**: `orchestrator.py`
- **执行器**: `utils/agent_executor.py`
- **API 集成**: `utils/openclaw_api.py`

---

**文档更新时间**: 2026-03-05  
**版本**: v2.0  
**状态**: ✅ 配置完整
