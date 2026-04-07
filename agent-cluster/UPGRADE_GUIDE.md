# OpenClaw 安全升级指南

**升级时间**: 2026-03-17  
**当前版本**: 2026.3.8  
**目标版本**: 最新版本

---

## 📋 升级前准备

### 1. 备份重要数据

```bash
# 创建工作区备份
cd /home/admin/.openclaw
tar -czf workspace_backup_$(date +%Y%m%d_%H%M%S).tar.gz workspace/

# 备份配置
cp -r /home/admin/.openclaw/.agent /home/admin/.openclaw/.agent.backup
cp -r /home/admin/.openclaw/.agents /home/admin/.openclaw/.agents.backup

# 验证备份
ls -lh /home/admin/.openclaw/workspace_backup_*.tar.gz
```

### 2. 记录当前配置

```bash
# 导出当前配置
openclaw gateway config.get > /tmp/openclaw_config_backup.json

# 记录已安装的 skills
ls /home/admin/.openclaw/workspace/skills/ > /tmp/skills_list.txt

# 记录 cron 任务
crontab -l > /tmp/crontab_backup.txt
```

---

## 🚀 升级方法

### 方法 1: 自动升级（推荐）

```bash
# 1. 停止当前服务
openclaw gateway stop

# 2. 备份工作区（如果上面没做）
cd /home/admin/.openclaw
tar -czf workspace_backup_$(date +%Y%m%d_%H%M%S).tar.gz workspace/

# 3. 执行升级
openclaw update

# 4. 等待升级完成（约 2-5 分钟）
# 升级过程会自动：
# - 下载最新版本
# - 更新依赖
# - 迁移配置
# - 保留工作区

# 5. 启动服务
openclaw gateway start

# 6. 验证升级
openclaw --version
```

### 方法 2: 手动升级（更可控）

```bash
# 1. 停止服务
openclaw gateway stop

# 2. 备份
cd /home/admin/.openclaw
mkdir -p /tmp/openclaw_backup
cp -r workspace /tmp/openclaw_backup/
cp -r .agent /tmp/openclaw_backup/
cp -r .agents /tmp/openclaw_backup/

# 3. 使用 pip 升级
pip3 install --upgrade openclaw

# 或者从源码升级
# git clone https://github.com/openclaw/openclaw.git /tmp/openclaw-new
# cd /tmp/openclaw-new
# pip3 install -e .

# 4. 恢复工作区
cp -r /tmp/openclaw_backup/workspace/* /home/admin/.openclaw/workspace/
cp -r /tmp/openclaw_backup/.agent/* /home/admin/.openclaw/.agent/
cp -r /tmp/openclaw_backup/.agents/* /home/admin/.openclaw/.agents/

# 5. 启动服务
openclaw gateway start

# 6. 验证
openclaw --version
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

### 3. 工作区完整性

```bash
# 检查 Agent Cluster 代码
ls -lh /home/admin/.openclaw/workspace/agent-cluster/

# 检查配置文件
cat /home/admin/.openclaw/workspace/agent-cluster/cluster_config_v2.json | head -10

# 检查数据库
ls -lh /home/admin/.openclaw/workspace/agent-cluster/agent_cluster.db
```

### 4. 功能测试

```bash
# Web 服务访问
curl http://localhost:8890/health

# 监控页面
curl http://localhost:8890/monitoring | grep -o "监控日志" && echo "✅ 监控页面正常"

# API 测试
curl http://localhost:8890/api/status
```

### 5. Skills 检查

```bash
# 列出已安装的 skills
ls /home/admin/.openclaw/workspace/skills/

# 对比升级前
diff /tmp/skills_list.txt <(ls /home/admin/.openclaw/workspace/skills/)
# 无输出表示 skills 完整
```

---

## ⚠️ 注意事项

### 1. 保留的数据

升级过程会**自动保留**：
- ✅ `/home/admin/.openclaw/workspace/` - 所有工作区代码
- ✅ `/home/admin/.openclaw/.agent/` - Agent 配置
- ✅ `/home/admin/.openclaw/.agents/` - Agents 配置
- ✅ Cron 任务
- ✅ 环境变量配置

### 2. 可能被覆盖的文件

以下文件**可能被更新**：
- ⚠️ `/opt/openclaw/` - OpenClaw 核心程序
- ⚠️ `/opt/openclaw/skills/` - 系统 skills（自定义 skills 不受影响）
- ⚠️ 配置文件（会自动迁移）

### 3. 升级失败处理

```bash
# 如果升级失败，回滚到备份
cd /home/admin/.openclaw
tar -xzf workspace_backup_YYYYMMDD_HHMMSS.tar.gz

# 恢复配置
cp -r /tmp/openclaw_backup/.agent/* /home/admin/.openclaw/.agent/
cp -r /tmp/openclaw_backup/.agents/* /home/admin/.openclaw/.agents/

# 重启服务
openclaw gateway restart
```

---

## 📊 升级检查清单

### 升级前
- [ ] 备份工作区
- [ ] 备份配置
- [ ] 记录已安装 skills
- [ ] 记录 cron 任务
- [ ] 停止服务

### 升级中
- [ ] 执行升级命令
- [ ] 等待升级完成
- [ ] 检查升级日志

### 升级后
- [ ] 验证版本号
- [ ] 检查服务状态
- [ ] 验证工作区完整性
- [ ] 测试 Web 服务
- [ ] 检查 skills
- [ ] 验证 cron 任务
- [ ] 测试钉钉通知

---

## 🔧 常见问题

### Q1: 升级后服务无法启动

```bash
# 检查日志
openclaw gateway logs | tail -50

# 重新安装依赖
pip3 install --upgrade openclaw --force-reinstall

# 重启服务
openclaw gateway restart
```

### Q2: Skills 丢失

```bash
# 从备份恢复
cp /tmp/skills_list.txt /tmp/current_skills.txt
# 对比差异
diff /tmp/skills_list.txt /tmp/current_skills.txt

# 重新安装缺失的 skills
openclaw skill install <skill-name>
```

### Q3: 配置不兼容

```bash
# 恢复旧配置
cp /tmp/openclaw_config_backup.json /home/admin/.openclaw/config.json

# 或者手动迁移配置
# 参考升级日志中的迁移提示
```

---

## 📈 升级收益

### 新功能
- ✨ 最新的 AI 模型支持
- ✨ 改进的 UI 界面
- ✨ 性能优化
- ✨ 安全补丁

### 修复问题
- 🐛 已知的 Bug 修复
- 🐛 兼容性问题修复
- 🐛 性能问题优化

---

## 🎯 推荐升级流程

**最简单安全的方案**:

```bash
# 1. 一键备份
cd /home/admin/.openclaw && tar -czf workspace_backup_$(date +%Y%m%d_%H%M%S).tar.gz workspace/

# 2. 一键升级
openclaw gateway stop && openclaw update && openclaw gateway start

# 3. 一键验证
openclaw --version && openclaw gateway status && curl -s http://localhost:8890/health | head -1
```

**预计时间**: 5-10 分钟  
**风险等级**: 低（有备份）  
**影响范围**: 无（工作区保留）

---

**文档生成时间**: 2026-03-17 15:25  
**适用版本**: 2026.3.8 → Latest  
**回滚方案**: 有备份可随时回滚
