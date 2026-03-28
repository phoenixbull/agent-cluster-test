# 🔧 设置保存功能修复报告

**修复时间**: 2026-03-25  
**问题**: 配置保存后不生效，重新进入后配置丢失

---

## 🐛 问题原因

### 1. 单例模式缓存问题
`settings_manager.py` 使用单例模式，在 Web 服务启动时加载一次设置后就不会重新读取文件。

```python
# 问题代码
class SettingsManager:
    _instance = None
    
    def __init__(self):
        if self._initialized:
            return  # 直接返回，不重新加载
        self.settings = self._load_settings()  # 只加载一次
```

### 2. 保存后未重新加载
保存设置后，内存中的 `self.settings` 已更新，但没有持久化到文件或同步后重新加载。

### 3. 前端表单处理不完整
只有 GitHub 表单有完整的提交代码，其他表单（App Store、Google Play、钉钉、集群配置）的提交代码未实现。

---

## ✅ 修复方案

### 1. 深度合并设置

```python
def save_settings(self, settings: Dict) -> bool:
    # 深度合并设置
    self._deep_merge(self.settings, settings)
    
    # 保存到文件
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(self.settings, f, indent=2, ensure_ascii=False)
    
    # 同步更新 cluster_config_v2.json
    self._sync_to_cluster_config()
    
    # 重新加载确保数据一致 ✅ 新增
    self.settings = self._load_settings()
    
    return True
```

### 2. 添加深度合并函数

```python
def _deep_merge(self, base: Dict, update: Dict):
    """深度合并字典"""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            self._deep_merge(base[key], value)
        else:
            base[key] = value
```

### 3. 完善前端表单提交

为所有 6 个配置模块添加了完整的提交处理：

```javascript
// GitHub 表单
document.getElementById('githubForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = { github: { ... } };
    const res = await fetch('/api/settings/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'  // 新增：携带认证
    }, body: JSON.stringify(data));
    // 处理结果...
});

// App Store 表单 ✅ 新增
document.getElementById('appstoreForm').addEventListener('submit', async function(e) { ... });

// Google Play 表单 ✅ 新增
document.getElementById('googleplayForm').addEventListener('submit', async function(e) { ... });

// 钉钉表单 ✅ 新增
document.getElementById('dingtalkForm').addEventListener('submit', async function(e) { ... });

// 集群配置表单 ✅ 新增
document.getElementById('clusterForm').addEventListener('submit', async function(e) { ... });
```

### 4. 添加测试连接功能

```javascript
async function testGithub() {
    showMessage('🔄 正在测试 GitHub 连接...', 'success');
    const res = await fetch('/api/settings/test/github', {
        method: 'POST',
        credentials: 'same-origin'
    });
    const result = await res.json();
    if (result.success) {
        showMessage('✅ ' + result.message);
        document.getElementById('githubStatus').className = 'status-badge configured';
    }
}
```

---

## 📁 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `utils/settings_manager.py` | 添加 `_deep_merge` 方法，保存后重新加载 |
| `templates/settings.html` | 完善所有表单提交，添加测试连接功能 |

---

## 🧪 测试步骤

### 1. 保存配置测试

1. 访问 `https://39.107.101.25/settings`
2. 登录 (admin / admin123)
3. 点击左侧 "🐙 GitHub"
4. 填写配置:
   - Token: `ghp_xxx`
   - 用户名：`yourname`
   - 仓库：`your-repo`
5. 点击 "💾 保存配置"
6. 应该显示 "✅ GitHub 配置已保存"
7. 刷新页面或重新进入设置
8. **验证**: 配置应该仍然存在

### 2. 其他配置测试

重复上述步骤测试:
- 🍎 App Store Connect
- 🤖 Google Play
- 📱 钉钉通知
- ⚙️ 集群配置

### 3. 验证文件保存

```bash
# 查看设置文件
cat /home/admin/.openclaw/workspace/agent-cluster/memory/settings.json

# 应该看到保存的配置
{
  "github": {
    "token": "ghp_xxx",
    "user": "yourname",
    ...
  },
  ...
}
```

### 4. 验证同步

```bash
# 查看 cluster_config_v2.json 是否同步
grep -A 5 '"github"' /home/admin/.openclaw/workspace/agent-cluster/cluster_config_v2.json
```

---

## ✅ 预期效果

### 保存前
```
GitHub 状态：🔴 未配置
Token: (空)
```

### 保存后
```
✅ GitHub 配置已保存

GitHub 状态：🟢 已配置
Token: ghp_xxx... (隐藏)
```

### 刷新页面后
```
GitHub 状态：🟢 已配置
Token: ghp_xxx... (隐藏)  ← 配置保留
```

---

## 🔍 故障排除

### 问题 1: 保存后仍然丢失

**检查**:
```bash
# 1. 查看设置文件是否存在
ls -la memory/settings.json

# 2. 查看文件权限
chmod 644 memory/settings.json

# 3. 查看 Web 服务日志
tail -f logs/web_app_v2.log | grep -i settings
```

### 问题 2: 保存时报错

**检查浏览器控制台**:
```
F12 → Console → 查看错误信息
```

**常见错误**:
- `401 Unauthorized`: 未登录或会话过期 → 重新登录
- `500 Internal Server Error`: 后端错误 → 查看 Web 日志
- `Network Error`: 网络问题 → 检查连接

### 问题 3: 配置不同步

**手动同步**:
```bash
cd /home/admin/.openclaw/workspace/agent-cluster
python3 -c "from utils.settings_manager import get_settings_manager; m = get_settings_manager(); m._sync_to_cluster_config()"
```

---

## 📝 注意事项

1. **首次保存**: 会创建 `memory/settings.json` 文件
2. **权限**: 确保 Web 服务有写入权限
3. **认证**: 所有设置 API 需要 JWT 认证
4. **同步**: 保存后自动同步到 `cluster_config_v2.json`
5. **重启**: 修改集群配置后可能需要重启服务

---

## 🚀 下一步

1. **测试配置保存**: 验证所有 6 个配置模块
2. **配置 GitHub Secrets**: 在 GitHub 后台设置
3. **测试连接**: 使用"🧪 测试连接"按钮
4. **集成 CI/CD**: 使用保存的配置触发构建

---

**修复完成时间**: 2026-03-25 14:31  
**修复版本**: v1.1
