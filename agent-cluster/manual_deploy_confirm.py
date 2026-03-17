#!/usr/bin/env python3
"""
手动部署确认脚本
用于在钉钉回复后手动触发部署
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, '.')

from cluster_manager import ClusterManager

def confirm_deployment(workflow_id: str):
    """手动确认部署"""
    config_path = Path('cluster_config_v2.2.json')
    manager = ClusterManager(config_path)
    
    print(f"🚀 确认部署：{workflow_id}")
    
    try:
        # 调用确认方法
        manager.confirm_deployment(workflow_id)
        print(f"✅ 部署已确认：{workflow_id}")
    except Exception as e:
        print(f"❌ 确认失败：{e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python3 manual_deploy_confirm.py <workflow_id>")
        print("")
        print("示例:")
        print("  python3 manual_deploy_confirm.py wf-20260315-183840-b6bb")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    confirm_deployment(workflow_id)
