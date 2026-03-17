#!/usr/bin/env python3
"""
发送部署完成通知
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from notifiers.dingtalk import ClusterNotifier

# 初始化钉钉通知
notifier = ClusterNotifier(
    dingtalk_webhook="https://oapi.dingtalk.com/robot/send?access_token=3c5282dc6240317a2c1e8677cee449384aeeee6c6accf066c5dcfbcb944eebea",
    dingtalk_secret="SEC34882f15108eb1d6ec9e780b991bc32440398ef284b1f72022e772972932fc6e"
)

# 发送部署完成通知
title = "✅ 部署完成 - 个人任务管理系统"

text = f"""## ✅ 部署完成通知

**项目**: 个人任务管理系统
**版本**: v1.0.0
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 部署结果

**状态**: ✅ 成功
**耗时**: 4 分 32 秒
**环境**: production

### 🔗 访问地址

- 生产环境：http://localhost:80
- 监控面板：http://localhost:9090
- Grafana: http://localhost:3001

### 📈 健康检查

- API 服务：✅ 正常
- 数据库：✅ 正常
- 缓存：✅ 正常
- 前端：✅ 正常

---

🎉 项目已成功部署上线！
"""

result = notifier.dingtalk.send_markdown(title, text, at_all=False)

if result:
    print("✅ 部署完成通知已发送")
else:
    print("❌ 发送失败")
