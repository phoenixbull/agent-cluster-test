#!/usr/bin/env node
/**
 * Gradle MCP Server
 * 支持 Android 构建、测试、打包
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";

const server = new Server(
  {
    name: "gradle-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const tools = [
  {
    name: "gradle_build",
    description: "构建 Android 项目",
    inputSchema: {
      type: "object",
      properties: {
        directory: { type: "string", description: "项目目录" },
        task: { type: "string", description: "Gradle 任务" },
        variant: { type: "string", description: "构建变体 (debug/release)" },
      },
      required: ["directory"],
    },
  },
  {
    name: "gradle_test",
    description: "运行 Android 测试",
    inputSchema: {
      type: "object",
      properties: {
        directory: { type: "string", description: "项目目录" },
      },
      required: ["directory"],
    },
  },
  {
    name: "gradle_dependencies",
    description: "查看依赖树",
    inputSchema: {
      type: "object",
      properties: {
        directory: { type: "string", description: "项目目录" },
        configuration: { type: "string", description: "配置名称" },
      },
      required: ["directory"],
    },
  },
  {
    name: "avd_list",
    description: "列出 Android 虚拟设备",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "avd_create",
    description: "创建 Android 虚拟设备",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "AVD 名称" },
        device: { type: "string", description: "设备 ID" },
        api: { type: "string", description: "API 级别" },
      },
      required: ["name"],
    },
  },
  {
    name: "avd_launch",
    description: "启动 Android 模拟器",
    inputSchema: {
      type: "object",
      properties: {
        avd_name: { type: "string", description: "AVD 名称" },
      },
      required: ["avd_name"],
    },
  },
  {
    name: "adb_devices",
    description: "列出连接的 Android 设备",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "adb_install",
    description: "安装 APK 到设备",
    inputSchema: {
      type: "object",
      properties: {
        apk_path: { type: "string", description: "APK 文件路径" },
        device_id: { type: "string", description: "设备 ID" },
      },
      required: ["apk_path"],
    },
  },
  {
    name: "adb_screenshot",
    description: "截取设备屏幕",
    inputSchema: {
      type: "object",
      properties: {
        output: { type: "string", description: "输出文件路径" },
        device_id: { type: "string", description: "设备 ID" },
      },
      required: ["output"],
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
      case "gradle_build": {
        const dir = args.directory || ".";
        const task = args.task || `assemble${args.variant === "release" ? "Release" : "Debug"}`;
        const cmd = `cd ${dir} && ./gradlew ${task}`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 构建成功\n${output}` }] };
      }

      case "gradle_test": {
        const dir = args.directory || ".";
        const cmd = `cd ${dir} && ./gradlew test`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `✅ 测试完成\n${output}` }] };
      }

      case "gradle_dependencies": {
        const dir = args.directory || ".";
        const config = args.configuration || "dependencies";
        const cmd = `cd ${dir} && ./gradlew ${config}`;
        const output = execSync(cmd, { stdio: "pipe", encoding: "utf-8" });
        return { content: [{ type: "text", text: `依赖树:\n${output}` }] };
      }

      case "avd_list": {
        const output = execSync("avdmanager list avd", { encoding: "utf-8" });
        return { content: [{ type: "text", text: `可用的 AVD:\n${output}` }] };
      }

      case "avd_create": {
        const cmd = `avdmanager create avd -n ${args.name} -k "system-images;android-${args.api || "30"};google_apis_playstore;x86_64" -d "${args.device || "pixel_4"}"`;
        execSync(cmd, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ AVD 已创建：${args.name}` }] };
      }

      case "avd_launch": {
        execSync(`emulator -avd ${args.avd_name} &`, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ 模拟器启动中：${args.avd_name}` }] };
      }

      case "adb_devices": {
        const output = execSync("adb devices", { encoding: "utf-8" });
        return { content: [{ type: "text", text: `连接的设备:\n${output}` }] };
      }

      case "adb_install": {
        const cmd = args.device_id 
          ? `adb -s ${args.device_id} install -r ${args.apk_path}`
          : `adb install -r ${args.apk_path}`;
        execSync(cmd, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ APK 已安装：${args.apk_path}` }] };
      }

      case "adb_screenshot": {
        const output = args.output || `/tmp/screenshot_${Date.now()}.png`;
        const cmd = args.device_id
          ? `adb -s ${args.device_id} shell screencap -p /sdcard/screenshot.png && adb -s ${args.device_id} pull /sdcard/screenshot.png ${output}`
          : `adb shell screencap -p /sdcard/screenshot.png && adb pull /sdcard/screenshot.png ${output}`;
        execSync(cmd, { stdio: "pipe" });
        return { content: [{ type: "text", text: `✅ 截图已保存：${output}` }] };
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
  console.error("Gradle MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
