# OpenClaw 手动升级完整步骤

**适用版本**: 任何版本升级到最新版  
**升级时间**: 约 20-30 分钟  
**风险等级**: 低（有备份）

---

## 📋 升级前准备

### 1. 备份工作区

```bash
# 创建工作区备份
cd /home/admin/.openclaw
tar -czf workspace_backup_$(date +%Y%m%d_%H%M%S).tar.gz workspace/

# 验证备份
ls -lh workspace_backup_*.tar.gz
```

### 2. 备份配置

```bash
# 备份 Cron 任务
crontab -l > /tmp/crontab_backup.txt

# 备份插件配置
cp -r /home/admin/.openclaw/.agent /tmp/.agent.backup
cp -r /home/admin/.openclaw/.agents /tmp/.agents.backup

# 记录已安装 skills
ls /home/admin/.openclaw/workspace/skills/ > /tmp/skills_list.txt
```

### 3. 停止服务

```bash
# 停止 Gateway 服务
openclaw gateway stop

# 停止 Agent Cluster 服务
pkill -f "web_app_v2.py"
pkill -f "dingtalk_notifier.py"

# 验证服务已停止
ps aux | grep "openclaw" | grep -v grep
ps aux | grep "web_app_v2" | grep -v grep
```

---

## 🚀 升级步骤

### 步骤 1: 克隆最新源码

```bash
# 进入临时目录
cd /tmp

# 克隆最新源码
git clone https://github.com/openclaw/openclaw.git openclaw-new

# 验证下载完成
ls -lh openclaw-new/
# 应看到约 300MB 的目录
```

### 步骤 2: 安装构建工具

```bash
# 升级 pip
pip3 install --upgrade pip -q

# 安装构建工具
pip3 install build setuptools -q

# 验证安装
pip3 list | grep -E "build|setuptools"
```

### 步骤 3: 安装新版本

```bash
# 进入源码目录
cd /tmp/openclaw-new

# 安装（使用 no-build-isolation 避免兼容性问题）
pip3 install . --no-build-isolation

# 等待安装完成（约 20-30 分钟）
# 安装过程中内存使用会达到 400-500MB，这是正常的
```

### 步骤 4: 验证安装

```bash
# 检查版本
openclaw --version
# 应显示新版本号

# 检查安装位置
which openclaw
# 应显示 /usr/bin/openclaw 或 /usr/local/bin/openclaw
```

### 步骤 5: 恢复配置

```bash
# 恢复工作区（如果升级过程被覆盖）
cd /home/admin/.openclaw
tar -xzf workspace_backup_*.tar.gz

# 恢复 Agent 配置
cp -r /tmp/.agent.backup/* /home/admin/.openclaw/.agent/ 2>/dev/null || true
cp -r /tmp/.agents.backup/* /home/admin/.openclaw/.agents/ 2>/dev/null || true

# 恢复 Cron 任务
crontab /tmp/crontab_backup.txt
```

### 步骤 6: 启动服务

```bash
# 启动 Gateway 服务
openclaw gateway start

# 等待服务启动
sleep 10

# 检查服务状态
openclaw gateway status

# 启动 Agent Cluster 服务
cd /home/admin/.openclaw/workspace/agent-cluster
nohup python3 web_app_v2.py --port 8890 > logs/web_app_v2.log 2>&1 &

# 启动钉钉通知服务
cd /home/admin/.openclaw/workspace/agent-cluster/monitoring
nohup python3 dingtalk_notifier.py > dingtalk_notifier.log 2>&1 &

# 验证服务
sleep 5
pgrep -fa "web_app_v2.py"
curl http://localhost:8890/health
```

---

## ✅ 升级后验证

### 1. 版本检查

```bash
openclaw --version
# 应显示新版本号
```

### 2. 服务状态

```bash
openclaw gateway status
# 应显示 running
```

### 3. Web 服务

```bash
curl http://localhost:8890/health
# 应返回 JSON 格式的健康状态
```

### 4. Agent Cluster

```bash
pgrep -fa "web_app_v2.py"
# 应显示进程 ID
```

### 5. Skills 检查

```bash
# 列出已安装的 skills
ls /home/admin/.openclaw/workspace/skills/

# 对比升级前
diff /tmp/skills_list.txt <(ls /home/admin/.openclaw/workspace/skills/)
# 无输出表示 skills 完整
```

### 6. Cron 任务

```bash
crontab -l
# 应显示所有定时任务
```

### 7. 钉钉通知

```bash
# 检查钉钉通知服务
pgrep -fa "dingtalk_notifier.py"

# 测试通知
curl -X POST http://localhost:5001/alerts \
  -H "Content-Type: application/json" \
  -d '{"alerts": [{"status": "firing", "labels": {"alertname": "Test"}}]}'
```

---

## ⚠️ 常见问题

### Q1: pip 安装报错 "Directory '.' is not installable"

**原因**: 缺少构建工具或使用了旧版 pip

**解决**:
```bash
pip3 install --upgrade pip
pip3 install build setuptools
pip3 install . --no-build-isolation
```

### Q2: 升级后服务无法启动

**解决**:
```bash
# 查看日志
openclaw gateway logs | tail -50

# 重新安装依赖
pip3 install -e /tmp/openclaw-new --no-build-isolation

# 重启服务
openclaw gateway restart
```

### Q3: Skills 丢失

**解决**:
```bash
# 从备份恢复
cd /home/admin/.openclaw
tar -xzf workspace_backup_*.tar.gz

# 或重新安装 skills
openclaw skill install <skill-name>
```

### Q4: 配置不兼容

**解决**:
```bash
# 查看配置警告
openclaw gateway status

# 编辑配置文件，移除无效插件
vim /home/admin/.openclaw/config.json

# 重启服务
openclaw gateway restart
```

---

## 🔄 回滚方案

如果升级失败，可以回滚到升级前状态：

```bash
# 1. 停止服务
openclaw gateway stop
pkill -f "web_app_v2.py"

# 2. 恢复备份
cd /home/admin/.openclaw
tar -xzf workspace_backup_*.tar.gz

# 3. 恢复配置
cp -r /tmp/.agent.backup/* /home/admin/.openclaw/.agent/
cp -r /tmp/.agents.backup/* /home/admin/.openclaw/.agents/
crontab /tmp/crontab_backup.txt

# 4. 重启服务
openclaw gateway start
cd /home/admin/.openclaw/workspace/agent-cluster
nohup python3 web_app_v2.py --port 8890 > logs/web_app_v2.log 2>&1 &

# 5. 验证
openclaw --version
curl http://localhost:8890/health
```

---

## 📊 升级检查清单

### 升级前
- [ ] 备份工作区
- [ ] 备份配置
- [ ] 记录 Skills 列表
- [ ] 停止服务

### 升级中
- [ ] 克隆源码（约 300MB）
- [ ] 安装构建工具
- [ ] pip 安装（约 20-30 分钟）
- [ ] 验证版本

### 升级后
- [ ] 恢复配置
- [ ] 启动服务
- [ ] 验证版本
- [ ] 检查服务状态
- [ ] 测试 Web 服务
- [ ] 验证 Skills
- [ ] 验证 Cron 任务
- [ ] 测试钉钉通知

---

## 🎯 快速升级命令

```bash
# 一键备份
cd /home/admin/.openclaw && tar -czf workspace_backup_$(date +%Y%m%d_%H%M%S).tar.gz workspace/

# 一键升级
cd /tmp && git clone https://github.com/openclaw/openclaw.git openclaw-new && \
cd openclaw-new && pip3 install . --no-build-isolation && \
openclaw --version && openclaw gateway restart

# 一键验证
openclaw --version && openclaw gateway status && curl -s http://localhost:8890/health | head -1
```

---

## 📈 预计时间

| 步骤 | 预计时间 |
|------|----------|
| 备份 | 2 分钟 |
| 克隆源码 | 3-5 分钟 |
| 安装构建工具 | 1 分钟 |
| pip 安装 | 20-30 分钟 |
| 验证和恢复 | 5 分钟 |
| **总计** | **30-40 分钟** |

---

## ✅ 成功标志

- [ ] `openclaw --version` 显示新版本号
- [ ] `openclaw gateway status` 显示 running
- [ ] Web 服务可访问 (端口 8890)
- [ ] Agent Cluster 运行正常
- [ ] Skills 完整无缺
- [ ] Cron 任务正常
- [ ] 钉钉通知正常

---

**文档生成时间**: 2026-03-17 16:58  
**适用版本**: 任意版本 → 最新版  
**预计时间**: 30-40 分钟  
**风险等级**: 低（有备份）
