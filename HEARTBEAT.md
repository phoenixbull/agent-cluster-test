# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## 定期检查项

- **Agent 集群状态** - 检查管理后台是否正常运行 (443 端口)
- **监控脚本状态** - 确认 monitor.py 无报错
- **钉钉通知** - 验证通知是否送达

## 检查频率

- **建议频率**: 每 30-60 分钟一次（活跃时段）
- **每日次数**: 2-4 次 (早、中、晚 + 必要时)
- **深夜避免**: 23:00-08:00 期间不主动检查
- **频率控制**: 若收到密集心跳请求，合并处理或降低响应频率

## 自动监控

- **Web 服务看门狗**: `watchdog_web.sh` (每 5 分钟自动检查)
- **自动重启**: 服务异常时自动重启，带 60 秒冷却期
- **日志位置**: `logs/watchdog_web.log`

## 健康检查脚本

使用标准化脚本执行检查，正确识别 302 重定向为正常状态：

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./health_check.sh
```

### 检查项说明

| 检查项 | 正常状态 | 说明 |
|--------|----------|------|
| HTTPS (443) | 200 或 302 | 302 重定向到登录页为正常 |
| Web 服务 (8890) | 200 或 302 | 后端 Python 应用响应 |
| 监控日志 | 无 ERROR/错误 | monitor.log 无报错 |
| nginx 服务 | active | systemctl 状态正常 |

### 手动验证命令

```bash
# HTTPS 检查 (接受 200/302)
curl -sk -o /dev/null -w "%{http_code}" https://localhost:443

# Web 服务检查
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8890

# 查看最近检查日志
tail -20 logs/health_check.log
```
