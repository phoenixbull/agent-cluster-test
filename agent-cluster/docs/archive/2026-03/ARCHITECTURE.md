# Agent 集群系统架构设计

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Agent Cluster System                             │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        Cluster Manager                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │   Agent     │  │   Session   │  │    Protocol Manager     │   │  │
│  │  │   Registry  │  │   Manager   │  │  (MCP/A2A/ANP)          │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Main Agent    │  │   Coder Agent   │  │  Writer Agent   │         │
│  │   (Supervisor)  │  │   (Specialist)  │  │   (Specialist)  │         │
│  │                 │  │                 │  │                 │         │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │         │
│  │ │  SOUL.md    │ │  │ │  SOUL.md    │ │  │ │  SOUL.md    │ │         │
│  │ │  IDENTITY   │ │  │ │  IDENTITY   │ │  │ │  IDENTITY   │ │         │
│  │ │  MEMORY.md  │ │  │ │  MEMORY.md  │ │  │ │  MEMORY.md  │ │         │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        Tool Layer                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │   MCP       │  │   Native    │  │    Sub-Agent            │   │  │
│  │  │   Tools     │  │   Tools     │  │    Spawner              │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. 三层物理隔离

### 2.1 认证与模型隔离
每个 Agent 有独立的：
- API Key 配置
- 模型选择 (qwen3.5-plus / qwen3.5-vision / etc.)
- 温度/最大 token 等参数

### 2.2 记忆隔离
- 独立的 sessions 目录
- 独立的上下文序列
- 独立的 memory 文件

### 2.3 灵魂隔离
- 独立的 SOUL.md (人格定义)
- 独立的 IDENTITY.md (身份定义)
- 独立的 USER.md (用户信息)

## 3. 协作模式

### 3.1 Supervisor 模式
```
                    ┌─────────────┐
                    │   User      │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Main      │
                    │   Agent     │
                    │ (Supervisor)│
                    └──────┬──────┘
                           │ 分发任务
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │   Coder     │ │   Writer    │ │Researcher   │
    │   Agent     │ │   Agent     │ │   Agent     │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │ 汇总结果
                    ┌──────▼──────┐
                    │   Main      │
                    │   Agent     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   User      │
                    └─────────────┘
```

### 3.2 Router 模式
```
                    ┌─────────────┐
                    │   User      │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Router    │
                    │   Agent     │
                    └──────┬──────┘
                           │ 智能路由
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │   Code      │ │   Writing   │ │  Research   │
    │   Task      │ │   Task      │ │   Task      │
    └─────────────┘ └─────────────┘ └─────────────┘
```

### 3.3 Pipeline 模式
```
User → [Researcher] → [Writer] → [Reviewer] → [Editor] → User
           ↓              ↓            ↓           ↓
        收集信息      撰写初稿      审核内容     最终编辑
```

### 3.4 Parallel 模式 (子代理)
```
                    ┌─────────────┐
                    │   Main      │
                    │   Agent     │
                    └──────┬──────┘
                           │ 并行分发
    ┌──────────────┬───────┼───────┬──────────────┐
    │              │       │       │              │
┌───▼───┐    ┌────▼────┐ ┌─▼────┐ ┌─▼────┐ ┌────▼────┐
│ Sub-1 │    │  Sub-2  │ │Sub-3 │ │Sub-4 │ │  Sub-5  │
│ Blog A│    │ Blog B  │ │Blog C│ │Blog D│ │ Blog E  │
└───┬───┘    └────┬────┘ └─┬────┘ └─┬────┘ └────┬────┘
    │              │       │       │              │
    └──────────────┴───────┴───────┴──────────────┘
                           │ 汇总
                    ┌──────▼──────┐
                    │   Main      │
                    │   Agent     │
                    └─────────────┘
```

## 4. 通信协议

### 4.1 MCP (Model Context Protocol)
**用途**: 智能体与工具/资源的标准化通信

**核心能力**:
- Tools: 执行操作 (读文件、搜索、计算等)
- Resources: 提供数据 (文件内容、数据库记录等)
- Prompts: 提供模板 (代码审查、文档生成等)

**传输方式**:
- Memory: 内存传输 (测试用)
- Stdio: 标准输入输出 (本地开发)
- HTTP/SSE: 远程服务

### 4.2 A2A (Agent-to-Agent Protocol)
**用途**: 智能体间点对点通信

**核心概念**:
- Task: 任务单元，有完整生命周期
- Artifact: 任务产出物
- Message: 智能体间通信消息

**任务生命周期**:
Created → Negotiating → Working → Completed/Failed

### 4.3 ANP (Agent Network Protocol)
**用途**: 大规模智能体网络服务发现

**核心功能**:
- 服务注册
- 服务发现
- 路由管理

## 5. 数据流

### 5.1 用户请求处理流程
```
1. 用户发送消息
        ↓
2. Cluster Manager 接收
        ↓
3. 根据模式路由:
   - Supervisor: Main Agent 处理并分发
   - Router: 根据任务类型选择 Agent
   - Pipeline: 按顺序传递给各 Agent
   - Parallel: 创建子代理并行处理
        ↓
4. Agent 执行任务 (可能调用 MCP 工具)
        ↓
5. 结果汇总
        ↓
6. 返回给用户
```

### 5.2 Agent 间通信流程
```
Agent A                    A2A Protocol              Agent B
   │                           │                        │
   │─── Task Request ─────────>│                        │
   │                           │─── Task Request ──────>│
   │                           │                        │
   │                           │<── Task Accept ────────│
   │<── Task Accept ──────────│                        │
   │                           │                        │
   │                           │<── Progress Update ────│
   │<── Progress Update ──────│                        │
   │                           │                        │
   │                           │<── Task Complete ──────│
   │<── Task Complete ────────│                        │
   │                           │                        │
```

## 6. 配置管理

### 6.1 集群配置 (cluster_config.json)
```json
{
  "cluster": {
    "name": "my-cluster",
    "mode": "supervisor",
    "max_parallel_agents": 10,
    "timeout_seconds": 300
  },
  "agents": [...],
  "protocols": {...},
  "tools": {...}
}
```

### 6.2 Agent 配置 (agents/<id>/config.json)
```json
{
  "id": "coder",
  "name": "代码专家",
  "workspace": "~/.openclaw/workspace/agents/coder",
  "model": {
    "provider": "alibaba-cloud",
    "model": "qwen3.5-plus",
    "temperature": 0.7
  },
  "role": "specialist",
  "skills": ["code_review", "debugging", "refactoring"],
  "mcp_servers": ["filesystem", "github"]
}
```

## 7. 扩展性设计

### 7.1 添加新 Agent
1. 创建 agent 目录
2. 配置 SOUL.md/IDENTITY.md
3. 注册到 cluster_config.json
4. 重启集群

### 7.2 添加新工具
1. 实现 MCP Server 或 Native Tool
2. 注册到工具注册表
3. 配置到 Agent 的 mcp_servers

### 7.3 添加新协议
1. 实现 Protocol Handler 接口
2. 注册到 Protocol Manager
3. 配置到 protocols 配置
