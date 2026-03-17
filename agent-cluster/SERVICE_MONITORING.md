# 🔍 Web 服务监控配置

**配置时间**: 2026-03-06 17:49  
**状态**: ✅ 已配置

---

## 📋 监控任务

| 任务 | 频率 | 说明 |
|------|------|------|
| **Web 服务监控** | 每 5 分钟 | 检查并自动重启 Web 服务 |
| **集群监控** | 每 10 分钟 | Agent 集群状态监控 |
| **磁盘清理** | 每周日 2:00 | 清理垃圾文件 |

---

## 🔧 监控脚本

**位置**: `/home/admin/.openclaw/workspace/agent-cluster/watchdog.sh`

**功能**:
1. 检查 8889 端口是否监听
2. 如果未监听，自动重启 Web 服务
3. 记录日志到 `logs/watchdog.log`

**执行逻辑**:
```bash
# 每 5 分钟执行
*/5 * * * * /home/admin/.openclaw/workspace/agent-cluster/watchdog.sh
```

---

## 📊 日志位置

| 日志 | 路径 |
|------|------|
| **Web 监控日志** | `logs/watchdog.log` |
| **集群监控日志** | `monitor.log` |
| **磁盘清理日志** | `/var/log/cleanup_weekly.log` |

---

## 🔍 查看日志

```bash
# 查看监控日志
tail -f logs/watchdog.log

# 查看最近 10 条记录
tail -10 logs/watchdog.log

# 查看服务重启记录
grep "重启" logs/watchdog.log
```

---

## 🛠️ 手动管理

```bash
# 启动服务
cd /home/admin/.openclaw/workspace/agent-cluster
python3 web_app.py --port 8889 &

# 停止服务
pkill -f "web_app.py"

# 查看进程
pgrep -f "web_app.py"

# 查看端口
netstat -tlnp | grep 8889

# 测试访问
curl http://127.0.0.1:8889/api/status
```

---

## 📋 Crontab 任务

```bash
# 查看当前任务
crontab -l

# 编辑任务
crontab -e

# 禁用监控（临时）
# */5 * * * * /home/admin/.openclaw/workspace/agent-cluster/watchdog.sh
```

---

## ⚠️ 注意事项

1. **日志轮转**: 监控日志可能增长，建议定期清理
2. **进程冲突**: 手动启动服务前先停止旧进程
3. **端口占用**: 确保 8889 端口未被其他程序占用
4. **权限问题**: 确保脚本有执行权限 (`chmod +x`)

---

## 🎯 故障排查

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 8889

# 杀死占用进程
kill -9 <PID>

# 查看错误日志
tail logs/watchdog.log
```

### 监控不工作

```bash
# 检查 crontab
crontab -l

# 手动执行监控脚本
./watchdog.sh

# 检查脚本权限
ls -l watchdog.sh
```

---

**配置完成！Web 服务现在会自动监控和重启。** ✅
