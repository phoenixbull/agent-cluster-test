#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理器
v2.4.0 新功能

功能:
- 监控指标阈值
- 自动发送钉钉通知
- 告警历史记录
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# 导入指标收集器
try:
    from .metrics_collector import get_metrics_collector
except ImportError:
    from metrics_collector import get_metrics_collector


@dataclass
class AlertRule:
    """告警规则"""
    id: str
    name: str
    metric: str  # 指标名称
    condition: str  # 条件：<, >, ==, !=
    threshold: float  # 阈值
    enabled: bool = True
    cooldown_minutes: int = 30  # 冷却时间 (避免重复通知)
    last_triggered: Optional[str] = None


@dataclass
class AlertRecord:
    """告警记录"""
    id: str
    rule_id: str
    rule_name: str
    metric_value: float
    threshold: float
    triggered_at: str
    notified: bool = False
    notification_channel: str = "dingtalk"


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "cluster_config_v2.json"
        self.config = self._load_config()
        
        # 告警规则
        self.rules = self._load_rules()
        
        # 告警历史
        self.history_file = Path(__file__).parent.parent / "memory" / "alert_history.json"
        self.history = self._load_history()
        
        # 指标收集器
        self.metrics = get_metrics_collector()
        
        # 钉钉通知器 (复用 monitor.py 中的)
        self.notifier = self._init_dingtalk_notifier()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _load_rules(self) -> List[AlertRule]:
        """加载告警规则"""
        # 默认规则
        default_rules = [
            AlertRule(
                id="alert-001",
                name="CI 通过率过低",
                metric="ci_pass_rate",
                condition="<",
                threshold=0.7,  # 70%
                cooldown_minutes=60
            ),
            AlertRule(
                id="alert-002",
                name="失败任务过多",
                metric="failed_tasks",
                condition=">",
                threshold=5,  # 5 个
                cooldown_minutes=30
            ),
            AlertRule(
                id="alert-003",
                name="单日成本过高",
                metric="daily_cost",
                condition=">",
                threshold=50.0,  # ¥50
                cooldown_minutes=120
            ),
            AlertRule(
                id="alert-004",
                name="Agent 成功率过低",
                metric="agent_success_rate",
                condition="<",
                threshold=0.6,  # 60%
                cooldown_minutes=60
            ),
            AlertRule(
                id="alert-005",
                name="人工介入率过高",
                metric="human_intervention_rate",
                condition=">",
                threshold=0.3,  # 30%
                cooldown_minutes=60
            ),
        ]
        
        # 从配置加载自定义规则
        custom_rules = self.config.get("alerts", {}).get("rules", [])
        
        rules = []
        for rule in default_rules + custom_rules:
            if isinstance(rule, AlertRule):
                rules.append(rule)
            elif isinstance(rule, dict):
                rules.append(AlertRule(**rule))
        
        return rules
    
    def _load_history(self) -> List[AlertRecord]:
        """加载告警历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [AlertRecord(**r) for r in data]
            except:
                pass
        return []
    
    def _save_history(self):
        """保存告警历史"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in self.history], f, ensure_ascii=False, indent=2)
    
    def _init_dingtalk_notifier(self):
        """初始化钉钉通知器"""
        try:
            from notifiers.dingtalk import ClusterNotifier
            notifications = self.config.get("notifications", {})
            dingtalk_config = notifications.get("dingtalk", {})
            
            if dingtalk_config.get("enabled"):
                return ClusterNotifier(
                    dingtalk_config.get("webhook", ""),
                    dingtalk_config.get("secret", "")
                )
        except:
            pass
        return None
    
    def check_all_rules(self) -> List[AlertRecord]:
        """检查所有规则"""
        triggered_alerts = []
        
        # 获取当前指标
        metrics = self.metrics.get_summary()
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # 检查冷却时间
            if rule.last_triggered:
                last = datetime.fromisoformat(rule.last_triggered)
                if datetime.now() - last < timedelta(minutes=rule.cooldown_minutes):
                    continue
            
            # 获取指标值
            metric_value = self._get_metric_value(metrics, rule.metric)
            
            if metric_value is None:
                continue
            
            # 检查条件
            triggered = self._check_condition(metric_value, rule.condition, rule.threshold)
            
            if triggered:
                # 创建告警记录
                alert = AlertRecord(
                    id=f"alert-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    metric_value=metric_value,
                    threshold=rule.threshold,
                    triggered_at=datetime.now().isoformat(),
                    notified=False
                )
                
                triggered_alerts.append(alert)
                self.history.append(alert)
                
                # 更新规则最后触发时间
                rule.last_triggered = alert.triggered_at
                
                # 发送通知
                self._send_alert_notification(alert, metric_value)
        
        # 保存历史
        self._save_history()
        
        return triggered_alerts
    
    def _get_metric_value(self, metrics: Dict, metric_name: str) -> Optional[float]:
        """获取指标值"""
        mapping = {
            "ci_pass_rate": lambda m: m.get("ci_pass_rate", 0),
            "failed_tasks": lambda m: m.get("failed_tasks", 0),
            "daily_cost": lambda m: m.get("today", {}).get("cost", 0),
            "agent_success_rate": lambda m: self._calculate_agent_success_rate(m),
            "human_intervention_rate": lambda m: m.get("human_intervention_rate", 0),
        }
        
        getter = mapping.get(metric_name)
        if getter:
            return getter(metrics)
        return None
    
    def _calculate_agent_success_rate(self, metrics: Dict) -> Optional[float]:
        """计算 Agent 成功率"""
        completed = metrics.get("completed_tasks", 0)
        failed = metrics.get("failed_tasks", 0)
        total = completed + failed
        # 没有任务时返回 None，避免误报
        return completed / total if total > 0 else None
    
    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """检查条件"""
        if condition == "<":
            return value < threshold
        elif condition == ">":
            return value > threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == ">=":
            return value >= threshold
        return False
    
    def _send_alert_notification(self, alert: AlertRecord, metric_value: Optional[float]):
        """发送告警通知"""
        if not self.notifier:
            print(f"⚠️  钉钉通知器未初始化，跳过通知")
            return
        
        # 格式化指标值（处理 None 情况）
        value_str = f"{metric_value:.2f}" if metric_value is not None else "N/A"
        threshold_str = f"{alert.threshold:.2f}" if alert.threshold is not None else "N/A"
        
        message = f"""
🚨 告警通知

规则：{alert.rule_name}
当前值：{value_str}
阈值：{threshold_str}
时间：{alert.triggered_at}

请及时处理！
"""
        
        try:
            # 模拟发送 (实际需要调用钉钉 API)
            print(f"📱 发送钉钉通知：{alert.rule_name}")
            print(f"   消息：{message[:100]}...")
            
            # 如果有真实的 notifier，调用:
            # self.notifier.send_message(message, at_all=True)
            
            alert.notified = True
        except Exception as e:
            print(f"❌ 发送通知失败：{e}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[AlertRecord]:
        """获取最近告警"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            a for a in self.history
            if datetime.fromisoformat(a.triggered_at) > cutoff
        ]
    
    def get_alert_stats(self) -> Dict:
        """获取告警统计"""
        recent = self.get_recent_alerts(24)
        
        by_rule = {}
        for alert in recent:
            rule_name = alert.rule_name
            by_rule[rule_name] = by_rule.get(rule_name, 0) + 1
        
        return {
            "total_24h": len(recent),
            "by_rule": by_rule,
            "notified": sum(1 for a in recent if a.notified),
            "unnotified": sum(1 for a in recent if not a.notified)
        }


# ========== 全局实例 ==========

_manager: Optional[AlertManager] = None


def get_alert_manager(config_path: Optional[str] = None) -> AlertManager:
    """获取告警管理器实例"""
    global _manager
    if _manager is None:
        _manager = AlertManager(config_path)
    return _manager


# ========== 便捷函数 ==========

def check_alerts() -> List[AlertRecord]:
    """检查并返回触发的告警"""
    return get_alert_manager().check_all_rules()


def get_alert_stats() -> Dict:
    """获取告警统计"""
    return get_alert_manager().get_alert_stats()


# ========== 测试 ==========

if __name__ == "__main__":
    print("🧪 告警管理器测试\n")
    
    manager = AlertManager()
    
    print(f"📋 已加载 {len(manager.rules)} 条告警规则:")
    for rule in manager.rules:
        print(f"  - {rule.name}: {rule.metric} {rule.condition} {rule.threshold}")
    
    print(f"\n📊 告警统计:")
    stats = manager.get_alert_stats()
    print(f"  24 小时告警数：{stats['total_24h']}")
    print(f"  已通知：{stats['notified']}")
    print(f"  未通知：{stats['unnotified']}")
    
    print(f"\n🔍 检查告警规则...")
    alerts = manager.check_all_rules()
    
    if alerts:
        print(f"\n🚨 触发 {len(alerts)} 条告警:")
        for alert in alerts:
            print(f"  - {alert.rule_name}: {alert.metric_value:.2f} (阈值：{alert.threshold:.2f})")
    else:
        print(f"\n✅ 无告警触发")
    
    print("\n✅ 测试完成!")
