#!/usr/bin/env node
/**
 * Xcode MCP Server
 * 支持 iOS 构建、签名、模拟器管理
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";
import { join } from "path";

const server = new Server(
  {
    name: "xcode-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 工具定义
const tools = [
  {
    name: "xcode_select",
    description: "选择 Xcode 版本",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Xcode 路径" },
      },
    },
  },
  {
    name: "xcode_build",
    description: "构建 iOS 项目",
    inputSchema: {
      type: "object",
      properties: {
        workspace: { type: "string", description: ".xcworkspace 路径" },
        scheme: { type: "string", description: "Scheme 名称" },
        configuration: { type: "string", description: "配置 (Debug/Release)" },
        destination: { type: "string", description: "目标设备" },
      },
      required: ["workspace", "scheme"],
    },
  },
  {
    name: "xcode_test",
    description: "运行 iOS 测试",
    inputSchema: {
      type: "object",
      properties: {
        workspace: { type: "string", description: ".xcworkspace 路径" },
        scheme: { type: "string", description: "Scheme 名称" },
        destination: { type: "string", description: "目标设备" },
      },
      required: ["workspace", "scheme"],
    },
  },
  {
    name: "simulator_list",
    description: "列出可用的 iOS 模拟器",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "simulator_launch",
    description: "启动 iOS 模拟器",
    inputSchema: {
      type: "object",
      properties: {
        device_id: { type: "string", description: "设备 ID" },
      },
      required: ["device_id"],
    },
  },
  {
    name: "simulator_screenshot",
    description: "截取模拟器屏幕",
    inputSchema: {
      type: "object",
      properties: {
        device_id: { type: "string", description: "设备 ID" },
        output: { type: "string", description: "输出文件路径" },
      },
      required: ["device_id"],
    },
  },
  {
    name: "pod_install",
    description: "安装 CocoaPods 依赖",
    inputSchema: {
      type: "object",
      properties: {
        directory: { type: "string", description: "项目目录" },
      },
      required: ["directory"],
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "xcode_select": {
        const cmd = `sudo xcode-select -s ${args.path}`;
        execSync(cmd, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ Xcode 已选择：${args.path}` }] };
      }

      case "xcode_build": {
        const cmd = `xcodebuild -workspace "${args.workspace}" -scheme "${args.scheme}" -configuration ${args.configuration || "Release"} -destination '${args.destination || "generic/platform=iOS"}' clean build`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 构建成功\n${output}` }] };
      }

      case "xcode_test": {
        const cmd = `xcodebuild test -workspace "${args.workspace}" -scheme "${args.scheme}" -destination '${args.destination || "platform=iOS Simulator,name=iPhone 15"}'`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 测试成功\n${output}` }] };
      }

      case "simulator_list": {
        const output = execSync("xcrun simctl list devices available", { encoding: "utf-8" });
        return { content: [{ type: "text", text: `可用的模拟器:\n${output}` }] };
      }

      case "simulator_launch": {
        execSync(`xcrun simctl boot ${args.device_id}`, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ 模拟器已启动：${args.device_id}` }] };
      }

      case "simulator_screenshot": {
        const output = args.output || `/tmp/simulator_${Date.now()}.png`;
        execSync(`xcrun simctl io ${args.device_id} screenshot "${output}"`, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ 截图已保存：${output}` }] };
      }

      case "pod_install": {
        const dir = args.directory || ".";
        execSync(`cd ${dir} && pod install`, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ CocoaPods 依赖已安装` }] };
      }

      default:
        return { content: [{ type: "text", text: `❌ 未知工具：${name}` }], isError: true };
    }
  } catch (error) {
    return { 
      content: [{ type: "text", text: `❌ 执行失败：${error.message}` }], 
      isError: true 
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Xcode MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
