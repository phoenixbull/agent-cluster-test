#!/usr/bin/env node
/**
 * Flutter MCP Server
 * 支持 Flutter 多平台构建、测试、发布
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";

const server = new Server(
  { name: "flutter-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

const tools = [
  {
    name: "flutter_build",
    description: "构建 Flutter 应用",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "目标平台" },
        release: { type: "boolean", description: "发布模式" },
      },
    },
  },
  {
    name: "flutter_run",
    description: "运行 Flutter 应用",
    inputSchema: {
      type: "object",
      properties: {
        device_id: { type: "string", description: "设备 ID" },
        debug: { type: "boolean", description: "调试模式" },
      },
    },
  },
  {
    name: "flutter_test",
    description: "运行 Flutter 测试",
    inputSchema: {
      type: "object",
      properties: {
        test_file: { type: "string", description: "测试文件" },
        coverage: { type: "boolean", description: "生成覆盖率" },
      },
    },
  },
  {
    name: "flutter_devices",
    description: "列出可用设备",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "flutter_doctor",
    description: "检查 Flutter 开发环境",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "flutter_build_apk",
    description: "构建 Android APK",
    inputSchema: {
      type: "object",
      properties: {
        release: { type: "boolean", description: "发布模式" },
      },
    },
  },
  {
    name: "flutter_build_ios",
    description: "构建 iOS 应用",
    inputSchema: {
      type: "object",
      properties: {
        release: { type: "boolean", description: "发布模式" },
        codesign: { type: "boolean", description: "代码签名" },
      },
    },
  },
  {
    name: "flutter_build_web",
    description: "构建 Web 版本",
    inputSchema: {
      type: "object",
      properties: {
        release: { type: "boolean", description: "发布模式" },
      },
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "flutter_build": {
        const mode = args.release ? "--release" : "--debug";
        const cmd = `flutter build ${args.target || "apk"} ${mode}`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 构建成功` }] };
      }
      case "flutter_run": {
        const cmd = `flutter run ${args.device_id ? `-d ${args.device_id}` : ""} ${args.debug ? "--debug" : "--release"}`;
        execSync(cmd + " &", { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ 应用运行中` }] };
      }
      case "flutter_test": {
        const cmd = `flutter test ${args.test_file || ""} ${args.coverage ? "--coverage" : ""}`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 测试完成\n${output}` }] };
      }
      case "flutter_devices": {
        const output = execSync("flutter devices", { encoding: "utf-8" });
        return { content: [{ type: "text", text: `可用设备:\n${output}` }] };
      }
      case "flutter_doctor": {
        const output = execSync("flutter doctor -v", { encoding: "utf-8" });
        return { content: [{ type: "text", text: `环境检查:\n${output}` }] };
      }
      case "flutter_build_apk": {
        const cmd = `flutter build apk ${args.release ? "--release" : "--debug"}`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ APK 已构建` }] };
      }
      case "flutter_build_ios": {
        const cmd = `flutter build ios ${args.release ? "--release" : "--debug"} ${!args.codesign ? "--no-codesign" : ""}`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ iOS 应用已构建` }] };
      }
      case "flutter_build_web": {
        const cmd = `flutter build web ${args.release ? "--release" : "--debug"}`;
        execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ Web 版本已构建` }] };
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
  console.error("Flutter MCP Server running on stdio");
}

main().catch(console.error);
