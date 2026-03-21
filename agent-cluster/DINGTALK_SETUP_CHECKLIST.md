# 钉钉双向通知 - 快速配置清单

## ✅ 已完成的配置

### 1. 代码层面
- [x] `web_app_v2.py` 添加钉钉回调端点
  - GET `/api/dingtalk/callback` - 回调验证
  - POST `/api/dingtalk/callback` - 消息接收
- [x] 签名验证逻辑
- [x] 消息解析和处理
- [x] 部署确认/取消处理
- [x] 配置文件更新 (`cluster_config_v2.json`)

### 2. 配置文件
- [x] `cluster_config_v2.json` 添加 `callback_token`
- [x] Webhook 和 Secret 已配置
- [x] 默认 Token: `openclaw_callback_token_2026`

### 3. 文档
- [x] `DINGTALK_CALLBACK_GUIDE.md` - 完整配置指南
- [x] `test_dingtalk_callback.sh` - 测试脚本

---

## 📋 你需要做的事

### 步骤 1: 创建钉钉企业自建应用

1. 访问 https://open.dingtalk.com/
2. 登录企业管理员账号
3. 进入 **企业应用** → **创建应用**
4. 选择 **企业内部开发** → **H5 微应用**
5. 填写应用信息：
   - 应用名称：Agent 集群助手
   - 应用图标：（可选）
   - 应用描述：Agent 集群部署确认和任务通知

### 步骤 2: 配置事件订阅

1. 在应用管理页面，点击左侧 **事件订阅**
2. 点击 **开通事件订阅**
3. 配置回调地址：

   **本地测试**:
   ```
   http://服务器 IP:8890/api/dingtalk/callback
   ```

   **生产环境** (推荐，需配置 Nginx HTTPS):
   ```
   https://你的域名/api/dingtalk/callback
   ```

4. 设置 Token（回调验证 token）:
   ```
   openclaw_callback_token_2026
   ```
   或修改 `cluster_config_v2.json` 中的 `callback_token`

5. 开启 **签名验证**（推荐），复制签名密钥

6. 订阅事件类型:
   - ✅ 群消息
   - ✅ 机器人消息
   - ✅ 应用通知

7. 点击 **保存**，钉钉会发送验证请求

### 步骤 3: 配置 Nginx 反向代理（生产环境）

如果通过公网访问，配置 Nginx:

```nginx
server {
    listen 443 ssl;
    server_name 你的域名;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /api/dingtalk/callback {
        proxy_pass http://127.0.0.1:8890/api/dingtalk/callback;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

然后重启 Nginx:
```bash
nginx -t && systemctl reload nginx
```

### 步骤 4: 添加机器人到钉钉群

1. 打开钉钉群
2. 群设置 → **智能群助手**
3. 添加机器人 → 选择你创建的企业应用
4. 设置机器人名称和头像

### 步骤 5: 重启 Web 服务

```bash
# 停止旧服务
pkill -f "python3 web_app_v2.py"

# 启动新服务
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app_v2.py --port 8890 &

# 或使用 systemd（如果已配置）
systemctl restart agent-cluster-web
```

### 步骤 6: 测试

#### 方法 1: 使用测试脚本

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./test_dingtalk_callback.sh
```

#### 方法 2: 手动测试

1. 在钉钉群发送消息："部署"
2. 查看日志：
   ```bash
   tail -f /home/admin/.openclaw/workspace/agent-cluster/logs/web_app.log
   ```
3. 应看到类似输出：
   ```
   📱 收到钉钉消息：部署 (from 老五)
   ✅ 收到部署确认：老五
   ```

---

## 🔧 故障排查

### 问题 1: 回调验证失败

**症状**: 钉钉开放平台显示 "回调失败"

**解决**:
```bash
# 1. 检查服务是否运行
curl http://localhost:8890/api/health/v24

# 2. 检查防火墙
ufw status | grep 8890

# 3. 检查日志
tail -f logs/web_app.log

# 4. 测试回调端点
./test_dingtalk_callback.sh
```

### 问题 2: 消息未收到

**症状**: 钉钉发送消息后无日志

**解决**:
1. 确认机器人已添加到群
2. 检查事件订阅是否开启 "群消息"
3. 确认应用有权限接收群消息

### 问题 3: 签名验证失败

**症状**: 日志显示 "签名验证失败"

**解决**:
1. 确认 `callback_token` 与钉钉配置一致
2. 检查服务器时间是否同步：
   ```bash
   date  # 应与钉钉服务器时间误差 < 5 分钟
   ntpdate pool.ntp.org  # 同步时间
   ```

---

## 📊 配置检查清单

完成后确认以下项:

- [ ] 钉钉企业应用已创建
- [ ] 事件订阅已开通
- [ ] 回调地址配置正确（公网可访问）
- [ ] Token 配置一致
- [ ] 签名密钥已配置（可选但推荐）
- [ ] 机器人已添加到群
- [ ] Web 服务已重启
- [ ] 测试脚本通过
- [ ] 实际消息能收到

---

## 🎯 下一步功能

### 已实现 ✅
- [x] 钉钉回调接收
- [x] 部署确认处理
- [x] 签名验证
- [x] 消息解析

### 待扩展 📋
- [ ] 自然语言任务创建（"@Agent 创建任务：..."）
- [ ] 任务状态查询
- [ ] PR Review 通知
- [ ] 多群支持
- [ ] 消息命令帮助（发送 "帮助" 显示可用命令）

---

## 📖 相关文档

- [DINGTALK_CALLBACK_GUIDE.md](./DINGTALK_CALLBACK_GUIDE.md) - 详细配置指南
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API 文档
- [README.md](./README.md) - 项目说明

---

**配置时间**: 2026-03-21  
**版本**: V2.2.0  
**状态**: ✅ 代码就绪，等待钉钉配置
