# 代码备份策略

**生效时间**: 2026-03-15  
**版本**: v1.0

---

## 📋 备份原则

**核心原则**: 任何修改前必须先备份！

---

## 🔧 自动备份脚本

### 1. 修改前备份脚本

```bash
#!/bin/bash
# backup_before_modify.sh

FILE=$1
if [ -z "$FILE" ]; then
    echo "用法：$0 <文件名>"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp "$FILE" "${FILE}.backup.${TIMESTAMP}"
echo "✅ 已备份：${FILE}.backup.${TIMESTAMP}"
```

### 2. 完整备份脚本

```bash
#!/bin/bash
# full_backup.sh

BACKUP_DIR="/home/admin/.openclaw/workspace/agent-cluster/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR/$TIMESTAMP
cp -r web_app_v2.py utils memory $BACKUP_DIR/$TIMESTAMP/

echo "✅ 完整备份已保存到：$BACKUP_DIR/$TIMESTAMP"
```

---

## 📁 备份文件命名规范

**格式**: `<文件名>.backup.YYYYMMDD_HHMMSS`

**示例**:
- `web_app_v2.py.backup.20260315_165517`
- `utils.backup.20260315_170000`

---

## 🔄 回滚流程

### 1. 查找备份文件
```bash
ls -lh web_app_v2.py.backup.*
```

### 2. 恢复备份
```bash
# 停止服务
pkill -f web_app_v2.py

# 恢复备份
cp web_app_v2.py.backup.20260315_165517 web_app_v2.py

# 验证语法
python3 -m py_compile web_app_v2.py

# 重启服务
python3 web_app_v2.py --host 0.0.0.0 --port 8890 &
```

### 3. 验证功能
```bash
curl http://127.0.0.1:8890/api/status
```

---

## 📊 备份保留策略

| 备份类型 | 保留时间 | 说明 |
|----------|----------|------|
| 修改前备份 | 7 天 | 单个文件修改前的备份 |
| 完整备份 | 30 天 | 重大修改前的完整备份 |
| 版本备份 | 永久 | 每个正式版本的备份 |

---

## ⚠️ 注意事项

1. **修改前必须备份** - 任何代码修改前都要执行备份
2. **备份后验证** - 备份完成后检查备份文件是否存在
3. **定期清理** - 定期清理 7 天前的临时备份
4. **重要备份** - 重大修改前做完整备份

---

## 📝 备份日志

每次备份都应记录：
- 备份时间
- 备份原因
- 备份文件
- 修改内容

---

**最后更新**: 2026-03-15
