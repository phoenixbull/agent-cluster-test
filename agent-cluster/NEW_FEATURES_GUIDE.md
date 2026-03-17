# 🆕 新功能快速上手指南

**更新时间**: 2026-03-06  
**版本**: v2.0

---

## 🚀 5 分钟快速体验

### 第 1 步：启动 Web 界面

```bash
cd /home/admin/.openclaw/workspace/agent-cluster
./start_web.sh
```

或者直接运行：
```bash
python3 web_app.py --port 8889
```

### 第 2 步：访问 Web 界面

打开浏览器访问：**http://localhost:8889**

### 第 3 步：提交你的第一个任务

1. 在"提交新任务"表单中输入需求
2. 选择项目（默认/电商/博客/CRM）
3. 点击"提交任务"按钮

### 第 4 步：查看工作流状态

- 概览页面显示实时状态
- 工作流页面查看历史记录
- 钉钉接收完成通知

---

## 📝 使用模板库

### 使用预置模板

1. 访问 `/templates` 页面
2. 找到需要的模板（如"用户登录系统"）
3. 点击"使用"按钮
4. 自动跳转到提交页面，需求已填充

### 创建自定义模板

1. 在模板库页面填写表单：
   - 模板名称：如"API 接口开发"
   - 描述：如"RESTful API 标准模板"
   - 需求内容：详细描述
   - 项目：选择对应项目
2. 点击"保存模板"

---

## 📁 多项目开发

### 方式 1：前缀标记（推荐）

```bash
# 电商项目
python3 orchestrator.py "[电商] 添加商品收藏功能"

# 博客项目
python3 orchestrator.py "[博客] 实现文章点赞功能"

# CRM 项目
python3 orchestrator.py "[CRM] 添加客户跟进提醒"
```

### 方式 2：关键词自动识别

```bash
# 自动识别为电商项目（包含"购物车"关键词）
python3 orchestrator.py "优化购物车结算流程"

# 自动识别为博客项目（包含"文章"关键词）
python3 orchestrator.py "添加文章搜索功能"
```

### 查看项目配置

```bash
cat projects.json | python3 -m json.tool
```

---

## 💰 查看成本统计

### Web 界面

访问 `/costs` 页面查看：
- 今日/本周/本月成本
- 按模型统计
- 平均单次成本

### API 调用

```bash
curl http://localhost:8889/api/costs | python3 -m json.tool
```

### Python 代码

```python
from utils.cost_tracker import get_cost_stats

stats = get_cost_stats()
print(f"今日成本：¥{stats['today']['total']:.2f}")
print(f"平均单次：¥{stats['average_per_workflow']:.2f}")
```

---

## 🔧 常见问题

### Q: Web 界面无法启动？

**A**: 检查端口是否被占用
```bash
# 查看端口占用
netstat -tlnp | grep 8889

# 更换端口
python3 web_app.py --port 9999
```

### Q: 模板保存后看不到？

**A**: 刷新页面或检查文件权限
```bash
# 检查文件
ls -la memory/templates.json

# 查看内容
cat memory/templates.json | python3 -m json.tool
```

### Q: 如何添加新项目？

**A**: 编辑 `projects.json`
```json
{
  "id": "newproject",
  "name": "新项目",
  "keywords": ["关键词 1", "关键词 2"],
  "prefix": "[新项目]",
  "github": {
    "user": "yourname",
    "repo": "new-project-repo",
    "branch_prefix": "feature/"
  },
  "workspace": "~/.openclaw/workspace/newproject"
}
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| `QUICKSTART.md` | 完整使用指南 |
| `README.md` | 系统架构说明 |
| `LONG_TERM_IMPROVEMENTS_COMPLETE.md` | 改进完成报告 |
| `MULTI_PROJECT_INTEGRATION.md` | 多项目集成详情 |

---

## 🎯 下一步

1. **探索 Web 界面**: 熟悉各个页面和功能
2. **创建模板**: 将常用需求保存为模板
3. **配置项目**: 根据实际项目修改 `projects.json`
4. **监控成本**: 定期查看成本统计，优化使用

---

**祝你使用愉快！** 🎉
