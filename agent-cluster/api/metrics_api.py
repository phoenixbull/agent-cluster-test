#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指标 API 端点
提供指标数据的 HTTP 查询接口
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from flask import Blueprint, jsonify, request

# 添加父目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from utils.metrics_collector import get_metrics_collector, FailureReason


# 创建 Blueprint
metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')


@metrics_bp.route('/summary', methods=['GET'])
def get_summary():
    """获取汇总统计"""
    try:
        collector = get_metrics_collector()
        stats = collector.get_summary()
        
        return jsonify({
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@metrics_bp.route('/agents', methods=['GET'])
def get_agents():
    """获取 Agent 统计"""
    try:
        agent_id = request.args.get('agent_id')
        collector = get_metrics_collector()
        
        stats = collector.get_agent_stats(agent_id)
        
        return jsonify({
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@metrics_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取任务历史"""
    try:
        limit = int(request.args.get('limit', 100))
        status = request.args.get('status')
        
        collector = get_metrics_collector()
        tasks = collector.get_task_history(limit=limit, status=status)
        
        return jsonify({
            "success": True,
            "data": tasks,
            "total": len(tasks),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@metrics_bp.route('/failures', methods=['GET'])
def get_failures():
    """获取失败分析"""
    try:
        days = int(request.args.get('days', 7))
        collector = get_metrics_collector()
        
        analysis = collector.get_failure_analysis(days=days)
        
        return jsonify({
            "success": True,
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@metrics_bp.route('/report', methods=['GET'])
def get_report():
    """获取完整报告"""
    try:
        collector = get_metrics_collector()
        report = collector.export_report()
        
        return jsonify({
            "success": True,
            "data": report,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@metrics_bp.route('/export', methods=['POST'])
def export_report():
    """导出报告到文件"""
    try:
        data = request.get_json() or {}
        output_path = data.get('output_path', 'metrics_report.json')
        
        collector = get_metrics_collector()
        report = collector.export_report(output_path=Path(output_path))
        
        return jsonify({
            "success": True,
            "message": f"报告已导出到 {output_path}",
            "data": report,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@metrics_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        collector = get_metrics_collector()
        stats = collector.get_summary()
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "metrics_loaded": stats.get('total_tasks', 0) > 0,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500


# ========== 注册到主应用 ==========

def register_metrics_api(app):
    """注册指标 API 到 Flask 应用"""
    app.register_blueprint(metrics_bp)
    print("✅ 指标 API 已注册：/api/metrics/*")


if __name__ == '__main__':
    # 测试
    from flask import Flask
    app = Flask(__name__)
    register_metrics_api(app)
    
    with app.test_client() as client:
        # 测试汇总接口
        response = client.get('/api/metrics/summary')
        print("汇总接口响应:", response.get_json())
        
        # 测试 Agent 接口
        response = client.get('/api/metrics/agents')
        print("Agent 接口响应:", response.get_json())
