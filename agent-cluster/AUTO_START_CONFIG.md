# 开机自启配置报告

**配置时间**: 2026-03-17 15:20 (Asia/Shanghai)  
**系统版本**: V2.7.1

---

## 📋 问题原因

每次服务器重启后钉钉消息无回复的原因：
1. ❌ **Web 服务未自启** - 没有配置开机自动启动
2. ❌ **钉钉通知未自启** - 通知服务需要手动启动
3. ❌ **服务管理缺失** - 没有 systemd 或 crontab 配置

---

## ✅ 解决方案

### 方案 1: Crontab 开机自启（✅ 已配置）

**优点**:
- ✅ 配置简单
- ✅ 无需 root 权限
- ✅ 可靠性高

**配置内容**:
```bash
@reboot /usr/local/bin/agent-cluster-start
```

**启动脚本**: `/usr/local/bin/agent-cluster-start`

**启动流程**:
```
1. 等待网络就绪 (10 秒)
2. 停止旧进程
3. 启动 Web 服务 (端口 8890)
4. 启动钉钉通知服务
5. 健康检查验证
```

---

### 方案 2: systemd 服务（备用）

**服务文件**: `/etc/systemd/system/agent-cluster.service`

**状态**: 已配置但暂未启用（端口占用问题）

**启用方法**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agent-cluster
sudo systemctl start agent-cluster
```

---

## 🔧 验证方法

### 1. 检查当前服务状态

```bash
# 检查 Web 服务
pgrep -fa "web_app_v2.py" && echo "✅ Web 服务运行中" || echo "❌ Web 服务未运行"

# 检查钉钉通知
pgrep -fa "dingtalk_notifier.py" && echo "✅ 钉钉通知运行中" || echo "❌ 钉钉通知未运行"

# 健康检查
curl http://localhost:8890/health
```

### 2. 测试开机自启

```bash
# 重启服务器（测试用）
sudo reboot

# 重启后等待 30 秒，然后检查
ssh user@server "curl -s http://localhost:8890/health"
```

### 3. 查看 crontab 配置

```bash
crontab -l | grep agent-cluster
# 应输出：@reboot /usr/local/bin/agent-cluster-start
```

---

## 📁 配置文件位置

| 文件 | 路径 | 用途 |
|------|------|------|
| 启动脚本 | `/usr/local/bin/agent-cluster-start` | 开机自启脚本 |
| systemd 服务 | `/etc/systemd/system/agent-cluster.service` | systemd 配置 |
| Crontab | 用户 crontab | `@reboot` 任务 |
| Web 服务日志 | `logs/web_app_v2.log` | Web 服务日志 |
| 钉钉通知日志 | `monitoring/dingtalk_notifier.log` | 通知服务日志 |

---

## 🚀 立即生效（无需重启）

**当前服务已启动**:
- ✅ Web 服务：端口 8890
- ✅ 钉钉通知：端口 5001

**验证钉钉消息**:
```bash
# 发送测试消息到钉钉
curl -X POST http://localhost:5001/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "status": "firing",
      "labels": {"alertname": "Test"},
      "annotations": {"summary": "测试消息"}
    }]
  }'
```

---

## ⚠️ 注意事项

### 1. 端口占用

如果 systemd 服务启动失败，可能是端口被占用：
```bash
# 查找占用 8890 端口的进程
lsof -i :8890

# 停止旧进程
pkill -f "web_app_v2.py"

# 重启服务
sudo systemctl restart agent-cluster
```

### 2. 日志查看

```bash
# Web 服务日志
tail -f /home/admin/.openclaw/workspace/agent-cluster/logs/web_app_v2.log

# 钉钉通知日志
tail -f /home/admin/.openclaw/workspace/agent-cluster/monitoring/dingtalk_notifier.log

# systemd 日志
sudo journalctl -u agent-cluster -f
```

### 3. 服务管理

```bash
# 手动启动
/usr/local/bin/agent-cluster-start

# 停止服务
pkill -f "web_app_v2.py"
pkill -f "dingtalk_notifier.py"

# 查看状态
pgrep -fa "web_app_v2.py"
pgrep -fa "dingtalk_notifier.py"
```

---

## 📊 配置总结

| 配置项 | 状态 | 说明 |
|--------|------|------|
| Crontab 自启 | ✅ 已配置 | `@reboot` 任务 |
| systemd 服务 | ⚠️ 备用 | 端口占用问题 |
| 启动脚本 | ✅ 已安装 | `/usr/local/bin/agent-cluster-start` |
| 当前服务 | ✅ 运行中 | Web + 钉钉通知 |
| 开机自启 | ✅ 已启用 | 下次重启生效 |

---

## ✅ 验证清单

- [x] 启动脚本已安装
- [x] Crontab 配置已添加
- [x] Web 服务当前运行
- [x] 钉钉通知当前运行
- [ ] 重启后验证（建议测试）

---

**配置完成时间**: 2026-03-17 15:20  
**下次重启生效**: 是  
**当前服务状态**: ✅ 运行中
