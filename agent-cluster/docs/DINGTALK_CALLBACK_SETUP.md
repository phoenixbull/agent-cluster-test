# 📱 钉钉开放平台回调配置完整指南

**适用版本**: v2.4.1+  
**配置时间**: 约 15-20 分钟  
**难度**: ⭐⭐⭐ 中等

---

## 🎯 配置目标

让钉钉群消息能实时推送到 Agent 集群，实现：
- ✅ 回复"部署"自动确认部署
- ✅ 回复"取消"自动取消部署
- ✅ 实时接收，无需轮询

---

## 📋 前置要求

| 要求 | 说明 |
|------|------|
| 钉钉管理员账号 | 需要企业管理员权限 |
| 企业组织 | 已创建钉钉企业组织 |
| 服务器 | 公网可访问（阿里云/腾讯云等） |
| 端口开放 | 8891 端口可访问 |

---

## 🚀 配置步骤

### 步骤 1: 访问钉钉开放平台

1. 打开浏览器访问：https://open.dingtalk.com
2. 点击右上角「登录」
3. 使用**企业管理员账号**登录

![登录页面](https://img.alicdn.com/imgextra/i1/O1CN01XQy1Y11Vw8Z9Z9Z9Z_!!6000000002691-0-tps-800-600.jpg)

---

### 步骤 2: 进入控制台

1. 登录后，点击右上角「控制台」
2. 进入「应用开发」→「自建应用」

![控制台](https://img.alicdn.com/imgextra/i2/O1CN01YQy2Y21Vw8Z9Z9Z9Z_!!6000000002692-0-tps-800-600.jpg)

---

### 步骤 3: 创建自建应用

1. 点击「创建应用」
2. 选择「企业内部开发」
3. 填写应用信息：

```
应用名称：Agent 集群部署助手
应用图标：🤖 (可选)
应用描述：自动接收部署确认消息
```

4. 点击「创建」

![创建应用](https://img.alicdn.com/imgextra/i3/O1CN01ZQy3Y31Vw8Z9Z9Z9Z_!!6000000002693-0-tps-800-600.jpg)

---

### 步骤 4: 添加应用权限

1. 在应用管理页面，点击左侧「权限管理」
2. 点击「申请权限」
3. 搜索并添加以下权限：

| 权限名称 | 权限码 | 用途 |
|---------|--------|------|
| **群会话消息** | `im:chat` | 接收群消息 |
| **机器人消息** | `robot` | 发送消息 |
| **通讯录只读** | `contact:readonly` | 获取用户信息 (可选) |

4. 点击「确定」提交申请

![权限管理](https://img.alicdn.com/imgextra/i4/O1CN01AQy4Y41Vw8Z9Z9Z9Z_!!6000000002694-0-tps-800-600.jpg)

**注意**: 部分权限可能需要管理员审批，通常 1-5 分钟内通过。

---

### 步骤 5: 配置事件订阅（关键步骤）

#### 5.1 进入事件订阅页面

1. 在应用管理页面，点击左侧「事件订阅」
2. 点击「开通事件订阅」

![事件订阅](https://img.alicdn.com/imgextra/i5/O1CN01BQy5Y51Vw8Z9Z9Z9Z_!!6000000002695-0-tps-800-600.jpg)

#### 5.2 选择订阅模式

选择「**HTTP 回调模式**」（不是 AE 加密模式）

![订阅模式](https://img.alicdn.com/imgextra/i6/O1CN01CQy6Y61Vw8Z9Z9Z9Z_!!6000000002696-0-tps-800-600.jpg)

#### 5.3 配置回调地址

填写以下信息：

```
回调地址：http://服务器 IP:8891/dingtalk/callback
Token: (随机生成一个，例如：agent_cluster_2026_token)
Encoding AES Key: (点击随机生成，保留默认)
```

**重要说明**:

| 字段 | 说明 | 示例 |
|------|------|------|
| **回调地址** | 接收消息的 URL | `http://1.2.3.4:8891/dingtalk/callback` |
| **Token** | 验证令牌（自定义） | `agent_cluster_2026_token` |
| **AES Key** | 消息加密密钥 | 点击随机生成 |

![回调配置](https://img.alicdn.com/imgextra/i7/O1CN01DQy7Y71Vw8Z9Z9Z9Z_!!6000000002697-0-tps-800-600.jpg)

#### 5.4 保存配置

点击「保存」按钮，系统会自动发送验证请求。

**验证成功**后会显示「验证通过」✅

---

### 步骤 6: 选择订阅事件类型

1. 在事件订阅页面，展开「事件类型」
2. 搜索并订阅以下事件：

| 事件分类 | 事件名称 | 事件码 |
|---------|---------|--------|
| **消息类** | 接收消息 | `im:chat` |
| **机器人** | 机器人消息 | `robot` |
| **群组类** | 群添加/移除 (可选) | `bpms:group` |

3. 勾选后点击「保存」

![事件类型](https://img.alicdn.com/imgextra/i8/O1CN01EQy8Y81Vw8Z9Z9Z9Z_!!6000000002698-0-tps-800-600.jpg)

---

### 步骤 7: 发布应用

1. 点击左侧「版本管理与发布」
2. 点击「创建版本」
3. 填写版本信息：

```
版本号：1.0.0
更新说明：初始版本，支持部署确认
```

4. 点击「提交发布」

![版本发布](https://img.alicdn.com/imgextra/i9/O1CN01FQy9Y91Vw8Z9Z9Z9Z_!!6000000002699-0-tps-800-600.jpg)

---

### 步骤 8: 添加应用到钉钉群

#### 8.1 获取应用二维码

1. 点击左侧「开发管理」→「基本信息」
2. 找到「机器人二维码」或「应用二维码」
3. 保存二维码图片

#### 8.2 添加到群聊

1. 打开钉钉 PC 或手机端
2. 进入目标群聊
3. 点击右上角「...」→「添加机器人」
4. 选择「自定义机器人」或找到你的应用
5. 扫描步骤 8.1 的二维码

或者：

1. 在群聊中点击「+」→「添加应用」
2. 搜索应用名称「Agent 集群部署助手」
3. 点击「添加」

![添加到群](https://img.alicdn.com/imgextra/i10/O1CN01GQy1Y01Vw8Z9Z9Z9Z_!!6000000002700-0-tps-800-600.jpg)

---

## 🔧 启动监听器

配置完成后，启动 Agent 集群监听器：

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 使用步骤 5.3 配置的 Token
./start_deploy_listener.sh callback 8891 agent_cluster_2026_token
```

---

## 🧪 验证配置

### 测试 1: 检查监听器状态

```bash
# 查看进程
ps aux | grep deploy_listener

# 查看端口
netstat -tlnp | grep 8891

# 查看日志
tail -f logs/deploy_listener.log
```

**预期输出**:
```
✅ 钉钉消息接收器已初始化 (端口：8891)
📱 钉钉消息接收器已启动
   监听端口：8891
   回调 URL: http://服务器 IP:8891/dingtalk/callback
```

---

### 测试 2: 发送测试消息

在钉钉群发送：
```
部署
```

**预期日志**:
```
[2026-03-20T17:15:00] POST /dingtalk/callback
📱 收到钉钉消息：部署 (from 老五)
✅ 老五 确认部署
🚀 开始部署...
```

---

### 测试 3: 检查钉钉开放平台

1. 返回钉钉开放平台控制台
2. 进入「事件订阅」页面
3. 查看「调用统计」

应该有请求记录显示。

![调用统计](https://img.alicdn.com/imgextra/i11/O1CN01HQy2Y11Vw8Z9Z9Z9Z_!!6000000002701-0-tps-800-600.jpg)

---

## ❌ 常见问题排查

### 问题 1: 回调验证失败

**错误**: `❌ 钉钉回调验证失败`

**原因**:
- Token 不匹配
- 回调地址错误
- 服务器时间不同步

**解决**:
```bash
# 1. 检查 Token 是否一致
# 钉钉开放平台配置的 Token 必须与启动命令一致

# 2. 检查回调地址
# 必须是 http://服务器 IP:8891/dingtalk/callback

# 3. 同步服务器时间
sudo ntpdate ntp.aliyun.com
```

---

### 问题 2: 无法接收消息

**错误**: 发送消息后无响应

**检查清单**:
- [ ] 应用已添加到群聊
- [ ] 事件订阅已开通
- [ ] 监听器正在运行
- [ ] 端口 8891 可访问
- [ ] 防火墙已开放

**防火墙开放**:
```bash
# 阿里云安全组
# 访问 https://ecs.console.aliyun.com
# 安全组 → 添加规则 → TCP 8891

# 或使用 iptables
sudo iptables -A INPUT -p tcp --dport 8891 -j ACCEPT
```

---

### 问题 3: 权限不足

**错误**: `权限申请被拒绝`

**解决**:
1. 确认使用企业管理员账号
2. 联系企业超级管理员审批
3. 检查企业认证状态

---

### 问题 4: 回调地址无法访问

**错误**: 钉钉开放平台提示「回调地址不可达」

**解决**:
```bash
# 1. 检查服务器公网 IP
curl ifconfig.me

# 2. 测试端口可访问性
telnet 服务器 IP 8891

# 3. 使用内网穿透（开发环境）
# 安装 ngrok
ngrok http 8891

# 回调地址改为：https://xxx.ngrok.io/dingtalk/callback
```

---

## 🔐 安全建议

### 生产环境配置

1. **使用 HTTPS**
   ```bash
   # 配置 Nginx 反向代理
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location /dingtalk/callback {
           proxy_pass http://127.0.0.1:8891;
       }
   }
   ```

2. **Token 保护**
   ```bash
   # 不要硬编码在代码中
   # 使用环境变量
   export DINGTALK_TOKEN="your_secure_token"
   ./start_deploy_listener.sh callback 8891 $DINGTALK_TOKEN
   ```

3. **IP 白名单**
   - 在钉钉开放平台配置 IP 白名单
   - 仅允许钉钉服务器访问

---

## 📊 配置检查清单

配置完成后，逐项检查：

- [ ] 钉钉企业自建应用已创建
- [ ] 应用权限已申请（群会话消息、机器人）
- [ ] 事件订阅已开通（HTTP 回调模式）
- [ ] 回调地址配置正确
- [ ] Token 已记录
- [ ] 应用已发布
- [ ] 应用已添加到群聊
- [ ] 监听器已启动
- [ ] 端口 8891 可访问
- [ ] 测试消息「部署」有响应

---

## 📞 获取帮助

### 钉钉官方文档

- [事件订阅指南](https://open.dingtalk.com/document/orgapp/event-subscription)
- [回调配置](https://open.dingtalk.com/document/orgapp/configure-the-event-subscription-interface)
- [权限列表](https://open.dingtalk.com/document/orgapp/permission-list)

### Agent 集群文档

- [DINGTALK_RECEIVER_GUIDE.md](docs/DINGTALK_RECEIVER_GUIDE.md)
- [DINGTALK_INTEGRATION_REPORT.md](DINGTALK_INTEGRATION_REPORT.md)

### 技术支持

- GitHub: phoenixbull/agent-cluster-test
- 钉钉群：Agent 集群技术支持

---

**最后更新**: 2026-03-20 17:10  
**维护者**: 老五
