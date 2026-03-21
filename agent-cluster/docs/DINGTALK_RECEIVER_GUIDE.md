# 📱 钉钉消息接收配置指南

**版本**: v2.4.0  
**更新日期**: 2026-03-20

---

## 🎯 功能说明

通过钉钉消息实时接收部署确认命令，支持：
- ✅ "部署" / "deploy" - 批准部署
- ✅ "取消" / "cancel" - 取消部署

---

## 📋 两种监听模式

### 模式对比

| 特性 | 轮询模式 | 回调模式 (推荐) |
|------|---------|---------------|
| 实时性 | 30 秒延迟 | 实时 |
| 配置复杂度 | 简单 | 中等 |
| 钉钉要求 | 群机器人 | 企业自建应用 |
| 消息接收 | ❌ 不支持 | ✅ 支持 |
| 适用场景 | 测试/临时 | 生产环境 |

---

## 🚀 快速开始

### 方式 1: 回调模式（推荐）

#### 步骤 1: 创建钉钉企业自建应用

1. 访问 [钉钉开放平台](https://open.dingtalk.com)
2. 登录企业管理员账号
3. 点击「控制台」→「应用开发」→「自建应用」
4. 创建应用，填写基本信息

#### 步骤 2: 添加权限

在应用配置中添加以下权限：
- ✅ **群会话消息** - 接收群消息
- ✅ **机器人消息** - 发送消息

#### 步骤 3: 配置事件订阅

1. 进入「事件订阅」页面
2. 开启「事件订阅」开关
3. 配置回调地址：
   ```
   http://服务器 IP:8891/dingtalk/callback
   ```
4. 复制 **Token**（用于验证回调）

#### 步骤 4: 选择事件类型

订阅以下事件：
- ✅ **消息接收** - im/chat
- ✅ **机器人消息** - robot

#### 步骤 5: 启动监听器

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 方式 A: 使用启动脚本
./start_deploy_listener.sh callback 8891 your_token

# 方式 B: 直接运行
python3 deploy_listener.py --mode callback --port 8891 --token your_token
```

#### 步骤 6: 验证配置

在钉钉群中发送消息：
```
部署
```

查看日志输出：
```
📱 收到钉钉消息：部署 (from 老五)
✅ 老五 确认部署
🚀 开始部署...
```

---

### 方式 2: 轮询模式（简单）

**注意**: 轮询模式无法接收钉钉消息，仅检查待确认部署状态。

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 启动轮询模式
./start_deploy_listener.sh poll

# 或直接运行
python3 deploy_listener.py --mode poll
```

---

## 🔧 高级配置

### 修改端口

```bash
./start_deploy_listener.sh callback 9000 your_token
```

### 后台运行

```bash
nohup ./start_deploy_listener.sh callback 8891 your_token > logs/deploy_listener.log 2>&1 &
```

### 开机自启（systemd）

创建服务文件 `/etc/systemd/system/dingtalk-deploy.service`:

```ini
[Unit]
Description=DingTalk Deployment Listener
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/agent-cluster
ExecStart=/home/admin/.openclaw/workspace/agent-cluster/start_deploy_listener.sh callback 8891 your_token
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable dingtalk-deploy
sudo systemctl start dingtalk-deploy
sudo systemctl status dingtalk-deploy
```

---

## 📁 文件结构

```
agent-cluster/
├── notifiers/
│   ├── dingtalk.py              # 钉钉发送模块
│   └── dingtalk_receiver.py     # 钉钉接收模块 (新增)
├── deploy_listener.py           # 部署监听器 (已更新)
├── start_deploy_listener.sh     # 启动脚本 (新增)
└── docs/
    └── DINGTALK_RECEIVER_GUIDE.md  # 本文档
```

---

## 🔍 故障排查

### 问题 1: 回调验证失败

**错误**: `❌ 钉钉回调验证失败`

**原因**: Token 不匹配或签名错误

**解决**:
1. 检查启动命令中的 Token 是否与钉钉开放平台一致
2. 确认回调地址配置正确
3. 检查服务器时间是否同步

### 问题 2: 无法接收消息

**错误**: 发送"部署"无响应

**解决**:
1. 检查监听器是否运行：`ps aux | grep deploy_listener`
2. 查看日志：`tail -f logs/deploy_listener.log`
3. 确认钉钉应用已添加到目标群聊
4. 检查防火墙是否开放端口：`netstat -tlnp | grep 8891`

### 问题 3: 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8891

# 杀死进程
kill -9 <PID>

# 或使用其他端口
./start_deploy_listener.sh callback 9000 your_token
```

---

## 📊 测试验证

### 测试命令

```bash
# 1. 启动监听器
./start_deploy_listener.sh callback 8891 your_token

# 2. 在钉钉群发送测试消息
部署

# 3. 查看日志确认
tail -f logs/deploy_listener.log
```

### 预期输出

```
============================================================
📱 钉钉部署确认监听器 - 回调模式
============================================================

✅ 钉钉消息接收器已初始化 (端口：8891)

📱 钉钉消息接收器已启动
   监听端口：8891
   回调 URL: http://服务器 IP:8891/dingtalk/callback
   消息处理：已注册 deploy_listener.on_dingtalk_message()

⚠️  需要在钉钉开放平台配置回调地址:
   http://服务器 IP:8891/dingtalk/callback

[2026-03-20T17:05:00] POST /dingtalk/callback
📱 收到钉钉消息：部署 (from 老五)
✅ 老五 确认部署
🚀 开始部署...
```

---

## 🔗 相关文档

- [钉钉开放平台](https://open.dingtalk.com)
- [事件订阅文档](https://open.dingtalk.com/document/orgapp/event-subscription)
- [回调配置指南](https://open.dingtalk.com/document/orgapp/configure-the-event-subscription-interface)
- [Agent 集群文档](../README.md)

---

## 📝 更新日志

### v2.4.0 (2026-03-20)

- ✅ 新增 `dingtalk_receiver.py` - 钉钉消息接收模块
- ✅ 更新 `deploy_listener.py` - 支持回调模式
- ✅ 新增 `start_deploy_listener.sh` - 启动脚本
- ✅ 支持轮询/回调双模式
- ✅ 添加 systemd 开机自启配置

---

**维护者**: 老五  
**最后更新**: 2026-03-20 17:05
