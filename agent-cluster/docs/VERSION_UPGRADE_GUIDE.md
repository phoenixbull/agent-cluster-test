# 📦 版本升级指南

**适用范围**: Agent 集群系统 v2.0+  
**最后更新**: 2026-03-19

---

## 📋 版本规范

### SemVer 版本格式

```
vX.Y.Z
│ │ │
│ │ └─ 修订版本号 (Patch) - Bug 修复、小优化
│ └─── 次版本号 (Minor) - 新功能、向后兼容
└───── 主版本号 (Major) - 破坏性变更、架构调整
```

### 版本类型

| 类型 | 版本号变化 | 适用场景 | 示例 |
|------|----------|---------|------|
| **修订版本** | Z +1 | Bug 修复、性能优化、文档更新 | v2.2.0 → v2.2.1 |
| **次版本** | Y +1, Z=0 | 新功能 (向后兼容) | v2.2.0 → v2.3.0 |
| **主版本** | X +1, Y=0, Z=0 | 破坏性变更、架构重构 | v2.2.0 → v3.0.0 |

---

## 🚀 发布新版本

### 方法 1: 使用发布脚本 (推荐)

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 发布修订版本 (Bug 修复)
./scripts/release.sh 2.2.1 patch

# 发布次版本 (新功能)
./scripts/release.sh 2.3.0 minor

# 发布主版本 (架构重构)
./scripts/release.sh 3.0.0 major
```

**脚本会自动**:
1. ✅ 备份当前版本
2. ✅ 更新配置文件
3. ✅ 更新 Web 界面
4. ✅ 语法检查
5. ✅ 创建 Git 标签

### 方法 2: 手动发布

#### 步骤 1: 确定版本号

```bash
# 查看当前版本
cat cluster_config_v2.json | grep version
# 输出："version": "2.2.0"

# 决定新版本号
# - Bug 修复：2.2.0 → 2.2.1
# - 新功能：2.2.0 → 2.3.0
# - 破坏性变更：2.2.0 → 3.0.0
```

#### 步骤 2: 备份当前版本

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份关键文件
cp cluster_config_v2.json "$BACKUP_DIR/"
cp monitor.py "$BACKUP_DIR/"
cp web_app_v2.py "$BACKUP_DIR/"
cp VERSION.md "$BACKUP_DIR/"

echo "✅ 备份完成：$BACKUP_DIR"
```

#### 步骤 3: 更新版本号

**更新配置文件**:
```bash
# 编辑 cluster_config_v2.json
{
  "cluster": {
    "version": "2.3.0",           # ← 更新这里
    "release_date": "2026-03-19", # ← 更新这里
    "codename": "功能增强版"       # ← 更新这里
  }
}
```

**更新 Web 界面**:
```bash
# 编辑 web_app_v2.py
# 第 5 行：Agent 集群 Web 界面 V2.3.0
# 登录页面：<span class="version">V2.3.0 功能增强版</span>
# 主页面：<span class="version">V2.3.0 功能增强版</span>
```

#### 步骤 4: 更新 VERSION.md

```markdown
### v2.3.0 (2026-03-19) - 功能增强版

**类型**: 次版本发布 (新功能)

#### ✨ 新增功能

1. **功能名称**
   - ✅ 功能点 1
   - ✅ 功能点 2

#### 📁 新增文件

```
文件名                       # 说明
```

#### 🔧 修改文件

```
文件名                       # 修改说明
```

#### 📈 性能提升

| 指标 | 之前 | 之后 | 提升 |
|------|------|------|------|
| XXX  | -    | -    | -    |
```

#### 步骤 5: 语法检查

```bash
python3 -m py_compile web_app_v2.py
python3 -m py_compile monitor.py
echo "✅ 语法检查通过"
```

#### 步骤 6: 创建 Git 标签

```bash
git add cluster_config_v2.json web_app_v2.py VERSION.md
git commit -m "chore: 发布 v2.3.0 - 功能增强版"
git tag v2.3.0
git push origin main --tags
```

---

## 🔄 版本回滚

### 回滚到上一个版本

```bash
cd /home/admin/.openclaw/workspace/agent-cluster

# 1. 找到备份目录
ls -la backup_* | tail -5

# 2. 恢复文件
cp backup_20260319_130210/cluster_config_v2.json .
cp backup_20260319_130210/monitor.py .
cp backup_20260319_130210/web_app_v2.py .

# 3. 重启服务
pkill -f web_app_v2.py
python3 web_app_v2.py --port 8890 &

# 4. 验证版本
curl http://localhost:8890/health | jq .version
```

### Git 回滚

```bash
# 回滚到上一个标签
git checkout v2.2.0

# 或者回滚特定文件
git checkout v2.2.0 -- cluster_config_v2.json
```

---

## 📊 版本对比

### 查看版本差异

```bash
# 比较配置文件
diff backup_20260319_130210/cluster_config_v2.json cluster_config_v2.json

# 查看 Git 差异
git diff v2.2.0 v2.3.0

# 查看版本历史
cat VERSION.md
```

### 功能对比表

创建 `docs/VERSION_COMPARISON.md`:

```markdown
## v2.3.0 vs v2.2.0

| 功能 | v2.2.0 | v2.3.0 | 变化 |
|------|--------|--------|------|
| 功能 A | ✅ | ✅ | - |
| 功能 B | ❌ | ✅ | 新增 |
| 功能 C | ✅ | ❌ | 移除 |
```

---

## 🧪 版本测试

### 发布前测试清单

```bash
# 1. 语法检查
python3 -m py_compile web_app_v2.py
python3 -m py_compile monitor.py

# 2. 功能测试
python3 test_smart_retry.py

# 3. API 测试
curl http://localhost:8890/api/metrics/summary

# 4. 健康检查
curl http://localhost:8890/health

# 5. Dashboard 访问
# 浏览器访问：http://localhost:8890/metrics.html
```

### 发布后验证

```bash
# 1. 检查版本号
curl http://localhost:8890/health | jq .version

# 2. 查看启动日志
tail -f logs/web_app.log | grep "V2.3.0"

# 3. 验证新功能
# 根据新版本功能进行测试
```

---

## 📝 最佳实践

### 版本号命名

✅ **好的版本名**:
- `v2.2.1` - Bug 修复
- `v2.3.0` - 新功能
- `v3.0.0` - 架构重构

❌ **不好的版本名**:
- `v2.2` - 缺少修订号
- `v2.03.0` - 前导零
- `2.3.0-beta` - 预发布版本应使用 `-beta` 后缀

### 发布频率

| 版本类型 | 建议频率 | 说明 |
|---------|---------|------|
| 修订版本 | 随时 | Bug 修复、紧急优化 |
| 次版本 | 2-4 周 | 新功能累积到一定程度 |
| 主版本 | 3-6 个月 | 重大架构调整 |

### 发布说明

每个版本应包含:
1. ✅ 版本号
2. ✅ 发布日期
3. ✅ 版本代号
4. ✅ 新增功能列表
5. ✅ Bug 修复列表
6. ✅ 破坏性变更说明
7. ✅ 升级指南
8. ✅ 回滚方案

---

## 🔗 相关文档

- [VERSION.md](../VERSION.md) - 版本历史
- [release.sh](../scripts/release.sh) - 发布脚本
- [CHANGELOG 规范](https://keepachangelog.com/zh-CN/1.0.0/)
- [SemVer 规范](https://semver.org/lang/zh-CN/)

---

## 📞 问题排查

### 常见问题

**Q: 版本号更新后 Web 界面没变化？**
```bash
# 清除浏览器缓存
# 或强制刷新：Ctrl+F5

# 检查文件是否更新
grep "V2.3.0" web_app_v2.py

# 重启 Web 服务
pkill -f web_app_v2.py
python3 web_app_v2.py --port 8890 &
```

**Q: Git 标签创建失败？**
```bash
# 检查是否已存在
git tag -l | grep v2.3.0

# 删除旧标签
git tag -d v2.3.0
git push origin :refs/tags/v2.3.0

# 重新创建
git tag v2.3.0
git push origin --tags
```

**Q: 备份文件太多怎么办？**
```bash
# 保留最近 10 个备份
ls -dt backup_* | tail -n +11 | xargs rm -rf
```

---

**最后更新**: 2026-03-19  
**维护者**: Agent 集群团队
