"""
备份管理器
提供工作流状态的定期备份与恢复功能
"""

import json
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

from .config_loader import config


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = None):
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path(config.base_path) / 'backups'
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份配置
        self.max_backups = 10  # 最多保留 10 个备份
        self.backup_interval_hours = 6  # 每 6 小时备份一次
    
    def create_backup(self, data: Dict[str, Any], name: str = None) -> str:
        """
        创建备份
        
        Args:
            data: 要备份的数据
            name: 备份名称（可选）
        
        Returns:
            备份文件路径
        """
        if not name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f'backup_{timestamp}'
        
        # 生成备份文件名（带压缩）
        backup_file = self.backup_dir / f'{name}.json.gz'
        
        # 添加元数据
        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'name': name,
                'checksum': None  # 稍后计算
            },
            'data': data
        }
        
        # 写入压缩文件
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')
        
        # 计算 checksum
        checksum = hashlib.md5(json_bytes).hexdigest()
        backup_data['metadata']['checksum'] = checksum
        
        # 重新生成带 checksum 的内容
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
            f.write(json_str)
        
        # 清理旧备份
        self._cleanup_old_backups()
        
        return str(backup_file)
    
    def restore_backup(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """
        恢复备份
        
        Args:
            backup_file: 备份文件路径
        
        Returns:
            恢复的数据，失败返回 None
        """
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            return None
        
        try:
            # 读取压缩文件
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 验证 checksum
            stored_checksum = backup_data['metadata'].get('checksum')
            if stored_checksum:
                # 重新计算 checksum（不包含 checksum 字段本身）
                data_copy = backup_data.copy()
                data_copy['metadata']['checksum'] = None
                json_str = json.dumps(data_copy, ensure_ascii=False, indent=2)
                calculated_checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
                
                if stored_checksum != calculated_checksum:
                    print(f"⚠️ 备份文件 checksum 不匹配，可能已损坏")
            
            return backup_data['data']
        
        except Exception as e:
            print(f"❌ 恢复备份失败：{e}")
            return None
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for file in sorted(self.backup_dir.glob('*.json.gz')):
            try:
                with gzip.open(file, 'rt', encoding='utf-8') as f:
                    metadata = json.load(f).get('metadata', {})
                
                backups.append({
                    'name': file.stem,
                    'path': str(file),
                    'size': file.stat().st_size,
                    'created_at': metadata.get('created_at'),
                    'checksum': metadata.get('checksum')
                })
            except Exception as e:
                backups.append({
                    'name': file.stem,
                    'path': str(file),
                    'size': file.stat().st_size,
                    'error': str(e)
                })
        
        return backups
    
    def get_latest_backup(self) -> Optional[str]:
        """获取最新备份文件路径"""
        backups = self.list_backups()
        if backups:
            return backups[0]['path']
        return None
    
    def delete_backup(self, backup_file: str) -> bool:
        """删除备份"""
        try:
            Path(backup_file).unlink()
            return True
        except Exception:
            return False
    
    def _cleanup_old_backups(self):
        """清理旧备份，保留最近的 max_backups 个"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # 删除最旧的备份
            for backup in backups[self.max_backups:]:
                self.delete_backup(backup['path'])
                print(f"🗑️ 已删除旧备份：{backup['name']}")
    
    def auto_backup(self, workflow_state: Dict[str, Any]) -> Optional[str]:
        """
        自动备份（检查是否需要备份）
        
        Args:
            workflow_state: 工作流状态数据
        
        Returns:
            备份文件路径，如果不需要备份返回 None
        """
        # 检查上次备份时间
        latest = self.get_latest_backup()
        
        if latest:
            try:
                with gzip.open(latest, 'rt', encoding='utf-8') as f:
                    metadata = json.load(f).get('metadata', {})
                
                created_at = datetime.fromisoformat(metadata.get('created_at'))
                hours_since_backup = (datetime.now() - created_at).total_seconds() / 3600
                
                if hours_since_backup < self.backup_interval_hours:
                    return None  # 不需要备份
            
            except Exception:
                pass  # 如果读取失败，创建新备份
        
        # 创建新备份
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return self.create_backup(workflow_state, f'workflow_{timestamp}')


# 全局备份管理器实例
backup_manager = BackupManager()


def get_backup_manager() -> BackupManager:
    """获取备份管理器实例"""
    return backup_manager
