# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## 定期检查项

- **Agent 集群状态** - 检查管理后台是否正常运行 (443 端口)
- **监控脚本状态** - 确认 monitor.py 无报错
- **钉钉通知** - 验证通知是否送达

## 检查频率

- 每日 2-4 次 (早、中、晚 + 必要时)
- 避免深夜打扰 (23:00-08:00)

## 自动监控

- **Web 服务看门狗**: `watchdog_web.sh` (每 5 分钟自动检查)
- **自动重启**: 服务异常时自动重启，带 60 秒冷却期
- **日志位置**: `logs/watchdog_web.log`
