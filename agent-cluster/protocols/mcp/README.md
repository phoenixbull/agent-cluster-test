# MCP 协议实现 (Model Context Protocol)

MCP 用于智能体与工具/资源的标准化通信。

## 使用示例

### 连接到 MCP 服务器

```python
from protocols.mcp.client import MCPClient

# 连接到文件系统 MCP 服务器
client = MCPClient([
    "npx", "-y",
    "@modelcontextprotocol/server-filesystem",
    "."
])

# 列出可用工具
tools = await client.list_tools()

# 调用工具
result = await client.call_tool("read_file", {"path": "README.md"})
```

### 在 Agent 中使用 MCP 工具

```python
from cluster_manager import ClusterManager

cluster = ClusterManager()

# 为 Agent 添加 MCP 工具
agent = cluster.agents["main"]
agent.add_mcp_server("filesystem")

# Agent 现在可以自动使用 MCP 工具
session_id = cluster.create_session("main", "读取并分析 README.md 文件")
```

## 支持的 MCP 服务器

### 官方服务器
- `@modelcontextprotocol/server-filesystem` - 文件系统访问
- `@modelcontextprotocol/server-github` - GitHub API
- `@modelcontextprotocol/server-postgres` - PostgreSQL 数据库
- `@modelcontextprotocol/server-slack` - Slack 集成

### 社区服务器
- `@playwright/mcp` - 浏览器自动化
- `@mcp/server-obsidian` - Obsidian 笔记
- `@mcp/server-notion` - Notion 集成

## 传输方式

1. **Memory** - 内存传输 (测试用)
2. **Stdio** - 标准输入输出 (本地进程)
3. **HTTP** - HTTP 远程服务
4. **SSE** - Server-Sent Events (实时流)
5. **StreamableHTTP** - 流式 HTTP
