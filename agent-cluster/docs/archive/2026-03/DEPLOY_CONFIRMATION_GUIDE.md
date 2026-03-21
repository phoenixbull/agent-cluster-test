# 部署确认功能完整指南

**更新时间**: 2026-03-15 18:45  
**状态**: ✅ 核心功能完成

---

## ✅ 已完成的功能

### 1. Phase 6 部署确认触发
- ✅ 工作流 Phase 1-5 完成后自动触发
- ✅ 发送钉钉部署确认通知 (@所有人)
- ✅ 工作流状态标记为 `waiting_confirmation`
- ✅ 30 分钟超时机制

### 2. 钉钉通知发送
- ✅ 通知内容包含 PR 链接、部署前检查清单
- ✅ @所有人 确保引起注意
- ✅ 30 分钟超时提醒

### 3. 部署确认处理
- ✅ `cluster_manager.py` 已有 `confirm_deployment()` 方法
- ✅ `deploy_listener.py` 已有钉钉消息监听框架
- ✅ 手动确认脚本 `manual_deploy_confirm.py`

---

## ⏳ 待实现的功能

### 1. 钉钉 webhook 接口
需要在 Web 界面添加钉钉回调接口：

```python
# web_app_v2.py 中添加
elif path == '/api/dingtalk/callback':
    # 接收钉钉消息
    data = json.loads(self.rfile.read(cl).decode('utf-8'))
    # 解析回复内容
    if '确认部署' in data.get('text', {}).get('content', ''):
        # 触发部署确认
        manager.confirm_deployment(workflow_id)
```

### 2. 钉钉回复解析
需要解析钉钉消息中的关键词：
- "确认部署" → 触发部署
- "取消部署" → 取消部署
- "查看状态" → 返回部署状态

### 3. 部署执行
需要实现实际部署逻辑：
- Docker 部署
- Kubernetes 部署
- 或简单的文件同步

---

## 🔧 当前使用方法

### 方法 1: 手动确认部署

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 找到工作流 ID
python3 -c "
import json
with open('memory/workflow_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    for wf_id, wf in data.get('workflows', {}).items():
        if wf.get('deployment_status') == 'waiting_confirmation':
            print(f'{wf_id}: {wf.get(\"project\")}')
"

# 手动确认部署
python3 manual_deploy_confirm.py <workflow_id>
```

### 方法 2: 通过钉钉回复（待实现）

在钉钉群回复：
```
确认部署 wf-20260315-183840-b6bb
```

系统会自动：
1. 解析消息
2. 提取工作流 ID
3. 触发 `confirm_deployment()`
4. 执行部署
5. 发送完成通知

---

## 📱 钉钉通知内容示例

```
## 🚀 部署确认通知

**工作流**: wf-20260315-183840-b6bb
**需求**: 测试钉钉部署通知 - 第八次尝试
**PR**: #N/A
**PR 链接**: N/A

---

### 📋 部署信息

- **项目**: notify-test-8
- **环境**: 生产环境
- **提交**: N/A

---

### ⚠️ 部署前检查

- [ ] 代码审查通过
- [ ] 测试覆盖率 ≥ 80%
- [ ] 无高危 Bug
- [ ] CI/CD 通过

---

### 📌 操作指引

请在 30 分钟 内确认是否部署：

回复 "确认部署" 触发部署
回复 "取消部署" 取消部署

---

🤖 AI 产品开发智能体
```

---

## 🎯 下一步开发计划

### 短期（本周）
- [ ] 添加钉钉 webhook 接口到 web_app_v2.py
- [ ] 实现钉钉消息解析
- [ ] 测试完整流程

### 中期（本月）
- [ ] 实现实际部署逻辑（Docker/K8s）
- [ ] 添加部署进度监控
- [ ] 添加部署回滚功能

### 长期（下季度）
- [ ] 多环境部署支持
- [ ] 蓝绿部署
- [ ] 金丝雀发布

---

## 📞 技术支持

**相关文档**:
- `DEPLOY_CONFIRMATION_FEATURE.md` - 功能说明
- `DEPLOY_PHASE_FIX_SUMMARY.md` - 修复总结
- `manual_deploy_confirm.py` - 手动确认脚本

**代码位置**:
- `cluster_manager.py` - 部署确认逻辑
- `deploy_listener.py` - 钉钉监听器
- `notifiers/dingtalk.py` - 钉钉通知

---

**指南更新时间**: 2026-03-15 18:45
