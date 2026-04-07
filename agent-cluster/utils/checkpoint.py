"""
断点续传模块
支持工作流中断后从断点恢复执行
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from .config_loader import config
from .database import get_database
from typing import Tuple


class CheckpointStatus(Enum):
    """检查点状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, checkpoint_dir: str = None):
        if checkpoint_dir:
            self.checkpoint_dir = Path(checkpoint_dir)
        else:
            self.checkpoint_dir = Path(config.base_path) / 'checkpoints'
        
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.db = get_database()
    
    def create_checkpoint(self, workflow_id: str, phase: int, data: Dict[str, Any]) -> str:
        """
        创建检查点
        
        Args:
            workflow_id: 工作流 ID
            phase: 阶段号 (1-6)
            data: 检查点数据
        
        Returns:
            检查点文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_file = self.checkpoint_dir / f'{workflow_id}_phase{phase}_{timestamp}.json'
        
        checkpoint_data = {
            'workflow_id': workflow_id,
            'phase': phase,
            'status': CheckpointStatus.COMPLETED.value,
            'created_at': datetime.now().isoformat(),
            'data': data
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        # 同时在数据库中记录
        self._save_checkpoint_to_db(workflow_id, phase, checkpoint_data)
        
        return str(checkpoint_file)
    
    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流的最新检查点
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            检查点数据，不存在返回 None
        """
        # 先从数据库获取
        checkpoint = self._get_checkpoint_from_db(workflow_id)
        if checkpoint:
            return checkpoint
        
        # 从文件获取
        pattern = f'{workflow_id}_phase*.json'
        checkpoints = list(self.checkpoint_dir.glob(pattern))
        
        if not checkpoints:
            return None
        
        # 按时间排序，获取最新的
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def get_checkpoint_for_phase(self, workflow_id: str, phase: int) -> Optional[Dict[str, Any]]:
        """
        获取指定阶段的检查点
        
        Args:
            workflow_id: 工作流 ID
            phase: 阶段号
        
        Returns:
            检查点数据
        """
        pattern = f'{workflow_id}_phase{phase}_*.json'
        checkpoints = list(self.checkpoint_dir.glob(pattern))
        
        if not checkpoints:
            return None
        
        # 获取最新的
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def resume_from_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        从检查点恢复工作流
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            恢复的检查点数据，包括下一阶段信息
        """
        checkpoint = self.get_latest_checkpoint(workflow_id)
        
        if not checkpoint:
            return None
        
        # 计算下一阶段
        current_phase = checkpoint.get('phase', 0)
        next_phase = current_phase + 1
        
        return {
            'workflow_id': workflow_id,
            'current_phase': current_phase,
            'next_phase': next_phase,
            'checkpoint_data': checkpoint.get('data', {}),
            'can_resume': next_phase <= 6
        }
    
    def delete_checkpoints(self, workflow_id: str) -> int:
        """
        删除工作流的所有检查点
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            删除的检查点数量
        """
        pattern = f'{workflow_id}_phase*.json'
        checkpoints = list(self.checkpoint_dir.glob(pattern))
        
        count = 0
        for checkpoint in checkpoints:
            try:
                checkpoint.unlink()
                count += 1
            except Exception:
                pass
        
        return count
    
    def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """
        清理旧检查点
        
        Args:
            days: 保留天数
        
        Returns:
            清理的检查点数量
        """
        current_time = time.time()
        max_age_seconds = days * 24 * 3600
        
        count = 0
        for checkpoint in self.checkpoint_dir.glob('*.json'):
            age = current_time - checkpoint.stat().st_mtime
            if age > max_age_seconds:
                try:
                    checkpoint.unlink()
                    count += 1
                except Exception:
                    pass
        
        return count
    
    def _save_checkpoint_to_db(self, workflow_id: str, phase: int, data: Dict[str, Any]):
        """保存检查点到数据库"""
        try:
            # 更新工作流元数据
            workflow = self.db.get_workflow(workflow_id)
            if workflow:
                metadata = json.loads(workflow.get('metadata') or '{}')
                metadata['last_checkpoint'] = {
                    'phase': phase,
                    'created_at': data.get('created_at'),
                    'status': data.get('status')
                }
                self.db.update_workflow_status(workflow_id, workflow['status'], phase)
        except Exception as e:
            print(f"⚠️ 保存检查点到数据库失败：{e}")
    
    def _get_checkpoint_from_db(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取检查点"""
        try:
            workflow = self.db.get_workflow(workflow_id)
            if workflow:
                metadata = json.loads(workflow.get('metadata') or '{}')
                last_checkpoint = metadata.get('last_checkpoint')
                
                if last_checkpoint:
                    # 尝试从文件加载完整数据
                    return self.get_checkpoint_for_phase(workflow_id, last_checkpoint['phase'])
        except Exception:
            pass
        
        return None


class WorkflowResumer:
    """工作流恢复器"""
    
    def __init__(self):
        self.checkpoint_manager = CheckpointManager()
        self.db = get_database()
    
    def can_resume(self, workflow_id: str) -> Tuple[bool, str]:
        """
        检查工作流是否可以恢复
        
        Returns:
            (是否可以恢复，原因)
        """
        workflow = self.db.get_workflow(workflow_id)
        
        if not workflow:
            return False, '工作流不存在'
        
        status = workflow.get('status')
        
        if status == 'completed':
            return False, '工作流已完成，无需恢复'
        
        if status == 'failed':
            checkpoint = self.checkpoint_manager.get_latest_checkpoint(workflow_id)
            if checkpoint:
                return True, f'可从 Phase {checkpoint.get("phase", 0)} 恢复'
            else:
                return False, '工作流失败且无检查点'
        
        if status == 'running':
            # 检查是否超时
            # TODO: 实现超时检测
            return True, '工作流运行中，可继续执行'
        
        if status == 'pending':
            return True, '工作流未开始，从头执行'
        
        return False, f'未知状态：{status}'
    
    def resume(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复工作流
        
        Returns:
            恢复信息，包括下一阶段和上下文数据
        """
        can_resume, reason = self.can_resume(workflow_id)
        
        if not can_resume:
            return {
                'success': False,
                'error': reason
            }
        
        resume_info = self.checkpoint_manager.resume_from_checkpoint(workflow_id)
        
        if resume_info:
            # 更新工作流状态
            self.db.update_workflow_status(workflow_id, 'running', resume_info['next_phase'] - 1)
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'resumed_from_phase': resume_info['current_phase'],
                'next_phase': resume_info['next_phase'],
                'context': resume_info['checkpoint_data'],
                'message': f'从 Phase {resume_info["current_phase"]} 恢复，继续执行 Phase {resume_info["next_phase"]}'
            }
        else:
            # 无检查点，从头开始
            self.db.update_workflow_status(workflow_id, 'running', 0)
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'resumed_from_phase': 0,
                'next_phase': 1,
                'context': {},
                'message': '无检查点，从头开始执行'
            }
    
    def get_resume_suggestions(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取恢复建议
        
        Returns:
            恢复建议信息
        """
        can_resume, reason = self.can_resume(workflow_id)
        
        if not can_resume:
            return {
                'can_resume': False,
                'reason': reason,
                'suggestion': '建议重新创建工作流'
            }
        
        resume_info = self.checkpoint_manager.resume_from_checkpoint(workflow_id)
        
        if resume_info and resume_info['current_phase'] > 0:
            return {
                'can_resume': True,
                'reason': reason,
                'suggestion': f'建议从 Phase {resume_info["current_phase"]} 恢复',
                'next_phase': resume_info['next_phase'],
                'context_available': bool(resume_info['checkpoint_data']),
                'phase_names': {
                    1: '需求分析',
                    2: '技术设计',
                    3: '开发实现',
                    4: '测试验证',
                    5: '代码审查',
                    6: '部署上线'
                }
            }
        
        return {
            'can_resume': True,
            'reason': reason,
            'suggestion': '从头开始执行',
            'next_phase': 1,
            'context_available': False,
            'phase_names': {}
        }


# 全局实例
checkpoint_manager = CheckpointManager()
workflow_resumer = WorkflowResumer()


def get_checkpoint_manager() -> CheckpointManager:
    """获取检查点管理器实例"""
    return checkpoint_manager


def get_workflow_resumer() -> WorkflowResumer:
    """获取工作流恢复器实例"""
    return workflow_resumer
