# v1.0 Designer 与 v2.0 Gemini 合并说明

## 合并背景

在 v1.0 中，我们有 `designer` Agent 负责 UI/UX 设计。
在 v2.0 架构中，对应角色是 `gemini` (设计专家)。

为了避免破坏现有工作流，同时升级能力，我们选择**合并**而非替换。

## 合并方案

### 保留项
- ✅ **Agent ID**: `designer` (保持兼容 v1.0)
- ✅ **工作区**: `~/.openclaw/workspace/agents/designer`
- ✅ **MCP 服务器**: figma, excalidraw, filesystem

### 升级项
| 项目 | v1.0 | v2.0 (合并后) |
|------|------|---------------|
| **模型** | qwen3.5-plus | qwen-vl-plus (多模态) |
| **温度** | 0.6 | 0.6 |
| **技能** | 4 个 | 7 个 (新增 3 个) |
| **任务类型** | 4 个 | 8 个 (新增 4 个) |
| **审查职责** | 无 | gemini-reviewer |
| **协作模式** | 单层 | 双层 (编排层 + 执行层) |

### 新增技能
1. **visual_system** - 视觉系统设计 (色彩、字体、间距)
2. **html_css** - 直接生成 HTML/CSS 代码
3. **design_spec** - 设计规范文档编写

### 新增任务类型
1. **visual** - 视觉设计任务
2. **html_css** - HTML/CSS 实现
3. **design_spec** - 设计规范
4. **mockup** - 设计稿/样机

## 配置文件变更

### cluster_config_v2.json

```json
{
  "id": "designer",
  "name": "设计专家 (Gemini)",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen-vl-plus",  // 升级为多模态模型
    "temperature": 0.6
  },
  "role": "design_specialist",
  "skills": [
    "ui_design",        // v1.0 保留
    "wireframe",        // v1.0 保留
    "prototype",        // v1.0 保留
    "design_system",    // v1.0 保留
    "visual_system",    // v2.0 新增
    "html_css",         // v2.0 新增
    "design_spec"       // v2.0 新增
  ],
  "task_types": [
    "ui_design",        // v1.0 保留
    "visual",           // v2.0 新增
    "html_css",         // v2.0 新增
    "design_spec",      // v2.0 新增
    "mockup",           // v2.0 新增
    "prototype",        // v1.0 保留
    "wireframe",        // v1.0 保留
    "design_system"     // v1.0 保留
  ],
  "v2_merged": true,    // 标记为 v2.0 合并版本
  "v1_compatible": true // 保持 v1.0 兼容
}
```

## SOUL.md 变更

### 核心变化
1. 添加 **v2.0 升级说明** 到角色定位
2. 整合 **v1.0 能力** 和 **v2.0 新增能力**
3. 新增 **AI Reviewer 职责** (gemini-reviewer)
4. 更新 **协作协议** (与 zoe 编排层配合)
5. 添加 **多模态视觉** 能力说明

### 新增章节
- **v1.0 → v2.0 升级说明** 对比表
- **任务类型映射** 字典
- **成功指标** 列表

## Agent 选择策略更新

### agent_selector.py

```python
TASK_TYPE_MAPPING = {
    # v1.0 保留
    "ui_design": "designer",
    "wireframe": "designer",
    "prototype": "designer",
    "design_system": "designer",
    
    # v2.0 新增
    "visual": "designer",
    "html_css": "designer",
    "design_spec": "designer",
    "mockup": "designer",
}

# 多 Agent 协作
MULTI_AGENT_TASKS = {
    "full_feature": ["designer", "claude-code", "codex"],
    "new_page": ["designer", "claude-code"],
    "design_system": ["designer", "claude-code"],
}
```

## 审查层集成

### reviewers 配置

```json
{
  "reviewers": [
    {
      "id": "codex-reviewer",
      "name": "Codex 审查者",
      "model": "qwen-coder-plus",
      "focus": "边界情况、逻辑错误、竞态条件",
      "weight": "high",
      "required": true
    },
    {
      "id": "gemini-reviewer",
      "name": "Gemini 审查者",
      "model": "qwen-plus",
      "focus": "安全问题、扩展性、代码质量",
      "weight": "medium",
      "required": true,
      "alias": "designer-reviewer"  // designer 可作为 alias
    },
    {
      "id": "claude-reviewer",
      "name": "Claude 审查者",
      "model": "qwen-turbo",
      "focus": "基础检查（仅 critical 问题）",
      "weight": "low",
      "required": false
    }
  ]
}
```

## 工作流整合

### v1.0 工作流
```
writer → designer → coder
```

### v2.0 工作流
```
zoe (编排层)
  │
  ├─→ designer (设计) ──→ claude-code (前端实现)
  │                          │
  └─→ codex (后端) ──────────┘
                              │
                              ▼
                    gemini-reviewer (设计审查)
```

## 迁移步骤

### 1. 更新配置
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
cp cluster_config_v2.json cluster_config.json
```

### 2. 更新模型
```bash
# 重新初始化 designer Agent
python3 cluster_manager.py agent add designer "设计专家 (Gemini)"
```

### 3. 验证配置
```bash
python3 cluster_manager.py agent list
python3 cluster_manager.py status
```

### 4. 测试工作流
```bash
# 运行包含设计任务的完整工作流
python3 cluster_manager.py parallel examples/full_pipeline_tasks.json
```

## 兼容性保证

### 向后兼容 (v1.0 → v2.0)
- ✅ Agent ID 保持 `designer`
- ✅ 工作区路径不变
- ✅ MCP 服务器配置兼容
- ✅ 现有任务类型继续支持

### 向前兼容 (v2.0 新特性)
- ✅ 新增技能可用
- ✅ 新增任务类型可用
- ✅ AI Reviewer 职责可用
- ✅ 与 zoe 编排层集成

## 测试清单

- [ ] designer Agent 正常启动
- [ ] qwen-vl-plus 模型调用正常
- [ ] Figma MCP 连接正常
- [ ] Excalidraw MCP 连接正常
- [ ] UI 设计任务正常执行
- [ ] HTML/CSS 生成正常
- [ ] 设计审查 (gemini-reviewer) 正常
- [ ] 与 claude-code 协作正常
- [ ] 与 zoe 编排层通信正常

## 性能对比

| 指标 | v1.0 | v2.0 (合并后) | 提升 |
|------|------|---------------|------|
| 设计理解 | 文本 | 多模态 (文本 + 图像) | ⬆️ 显著 |
| 输出格式 | 设计稿 | 设计稿 + HTML/CSS | ⬆️ 实用 |
| 审查能力 | 无 | gemini-reviewer | ⬆️ 新增 |
| 协作效率 | 单层 | 双层编排 | ⬆️ 优化 |
| 失败处理 | 重试 | Ralph Loop | ⬆️ 智能 |

## 成本影响

| 项目 | v1.0 | v2.0 | 变化 |
|------|------|------|------|
| 模型 | qwen3.5-plus | qwen-vl-plus | +¥0-50/月 |
| 调用次数 | ~100/天 | ~150/天 (新增审查) | +50% |
| **总成本** | ~¥100/月 | ~¥150/月 | +¥50/月 |

**性价比**: 多模态能力 + 审查职责 + 编排集成，性价比显著提升。

---

*合并完成日期：2026-03-04*  
*版本：v2.0*
