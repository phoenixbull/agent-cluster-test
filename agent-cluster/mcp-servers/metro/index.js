#!/usr/bin/env node
/**
 * Metro MCP Server (React Native)
 * 支持 React Native 打包、热重载、测试
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";

const server = new Server(
  { name: "metro-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

const tools = [
  {
    name: "rn_bundle",
    description: "打包 React Native 应用",
    inputSchema: {
      type: "object",
      properties: {
        platform: { type: "string", enum: ["ios", "android"], description: "平台" },
        dev: { type: "boolean", description: "开发模式" },
        minify: { type: "boolean", description: "压缩代码" },
      },
      required: ["platform"],
    },
  },
  {
    name: "rn_start",
    description: "启动 Metro 开发服务器",
    inputSchema: {
      type: "object",
      properties: {
        port: { type: "number", description: "端口号" },
        resetCache: { type: "boolean", description: "重置缓存" },
      },
    },
  },
  {
    name: "rn_run_ios",
    description: "在 iOS 上运行 React Native",
    inputSchema: {
      type: "object",
      properties: {
        device: { type: "string", description: "设备名称" },
        configuration: { type: "string", description: "配置" },
      },
    },
  },
  {
    name: "rn_run_android",
    description: "在 Android 上运行 React Native",
    inputSchema: {
      type: "object",
      properties: {
        deviceId: { type: "string", description: "设备 ID" },
        variant: { type: "string", description: "构建变体" },
      },
    },
  },
  {
    name: "rn_test",
    description: "运行 React Native 测试",
    inputSchema: {
      type: "object",
      properties: {
        testPathPattern: { type: "string", description: "测试文件匹配" },
        coverage: { type: "boolean", description: "生成覆盖率报告" },
      },
    },
  },
  {
    name: "rn_doctor",
    description: "检查 React Native 开发环境",
    inputSchema: { type: "object", properties: {} },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "rn_bundle": {
        const cmd = `npx react-native bundle --platform ${args.platform} --dev ${args.dev ? "true" : "false"} --minify ${args.minify ? "true" : "false"} --entry-file index.js --bundle-output bundle.${args.platform}.js`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 打包成功` }] };
      }
      case "rn_start": {
        const cmd = `npx react-native start --port ${args.port || 8081} ${args.resetCache ? "--reset-cache" : ""}`;
        execSync(cmd + " &", { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ Metro 服务器已启动` }] };
      }
      case "rn_run_ios": {
        const cmd = `npx react-native run-ios ${args.device ? `--device "${args.device}"` : ""} ${args.configuration ? `--configuration ${args.configuration}` : ""}`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ iOS 应用已启动` }] };
      }
      case "rn_run_android": {
        const cmd = `npx react-native run-android ${args.deviceId ? `--deviceId ${args.deviceId}` : ""} ${args.variant ? `--variant ${args.variant}` : ""}`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ Android 应用已启动` }] };
      }
      case "rn_test": {
        const cmd = `npx jest ${args.testPathPattern ? args.testPathPattern : ""} ${args.coverage ? "--coverage" : ""}`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 测试完成\n${output}` }] };
      }
      case "rn_doctor": {
        const output = execSync("npx react-native doctor", { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `环境检查:\n${output}` }] };
      }
      default:
        return { content: [{ type: "text", text: `❌ 未知工具：${name}` }], isError: true };
    }
  } catch (error) {
    return { content: [{ type: "text", text: `❌ 执行失败：${error.message}` }], isError: true };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Metro MCP Server running on stdio");
}

main().catch(console.error);
