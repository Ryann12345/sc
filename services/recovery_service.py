import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.logger import get_logger
from utils.helpers import format_file_size

class RecoveryService:
    def __init__(self):
        self.logger = get_logger('RecoveryService')
    
    def recover_file(self, log_id: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        log_data = None
        logs = db_manager.get_operation_logs(limit=10000)
        for log in logs:
            if log.get('id') == log_id:
                log_data = log
                break
        
        if not log_data:
            return {'success': False, 'error': '未找到操作记录'}
        
        if log_data.get('is_recovered'):
            return {'success': False, 'error': '该文件已经恢复过了'}
        
        op_type = log_data.get('operation_type')
        file_path = log_data.get('file_path')
        old_path = log_data.get('old_path')
        new_path = log_data.get('new_path')
        
        result = {
            'success': False,
            'operation_type': op_type,
            'original_path': old_path or file_path,
            'new_path': None,
            'error': None
        }
        
        try:
            if op_type == 'DELETE':
                result = self._recover_deleted_file(log_data, target_path)
            elif op_type == 'OVERWRITE':
                result = self._recover_overwritten_file(log_data, target_path)
            elif op_type == 'MOVE':
                result = self._recover_moved_file(log_data, target_path)
            elif op_type == 'RENAME':
                result = self._recover_renamed_file(log_data, target_path)
            else:
                result['error'] = f"不支持恢复的操作类型: {op_type}"
            
            if result.get('success'):
                db_manager.mark_log_recovered(log_id, recovered=True)
                self.logger.info(f"成功恢复文件: {log_data.get('file_name')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"恢复文件失败: {e}")
            result['error'] = str(e)
            return result
    
    def _recover_deleted_file(self, log_data: Dict, target_path: Optional[str]) -> Dict:
        file_path = log_data.get('file_path')
        file_name = log_data.get('file_name')
        
        trash_dir = AppConfig.DATA_DIR / "trash"
        candidate = None
        
        if trash_dir.exists():
            for item in trash_dir.iterdir():
                if item.name.startswith(file_name + "_"):
                    if candidate is None or item.stat().st_mtime > candidate.stat().st_mtime:
                        candidate = item
        
        if candidate:
            recover_path = target_path or file_path
            recover_dir = Path(recover_path).parent
            recover_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(candidate), recover_path)
            
            return {
                'success': True,
                'operation_type': 'DELETE',
                'original_path': file_path,
                'new_path': recover_path,
                'error': None
            }
        else:
            return {
                'success': False,
                'operation_type': 'DELETE',
                'original_path': file_path,
                'new_path': None,
                'error': '未找到可恢复的文件副本（沙盒环境仅模拟）'
            }
    
    def _recover_overwritten_file(self, log_data: Dict, target_path: Optional[str]) -> Dict:
        file_id = log_data.get('file_id')
        file_path = log_data.get('file_path')
        
        if file_id:
            snapshots = db_manager.get_file_snapshots(file_id)
            if snapshots:
                latest_snapshot = snapshots[0]
                snapshot_path = latest_snapshot.get('snapshot_path')
                
                if snapshot_path and Path(snapshot_path).exists():
                    recover_path = target_path or file_path
                    recover_dir = Path(recover_path).parent
                    recover_dir.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(snapshot_path, recover_path)
                    
                    return {
                        'success': True,
                        'operation_type': 'OVERWRITE',
                        'original_path': file_path,
                        'new_path': recover_path,
                        'error': None
                    }
        
        return {
            'success': False,
            'operation_type': 'OVERWRITE',
            'original_path': file_path,
            'new_path': None,
            'error': '未找到可用的快照版本（沙盒环境仅模拟）'
        }
    
    def _recover_moved_file(self, log_data: Dict, target_path: Optional[str]) -> Dict:
        old_path = log_data.get('old_path')
        new_path = log_data.get('new_path')
        
        if not new_path:
            return {
                'success': False,
                'operation_type': 'MOVE',
                'original_path': old_path,
                'new_path': None,
                'error': '缺少移动目标路径信息'
            }
        
        source_path = Path(new_path)
        dest_path = Path(target_path or old_path)
        
        if not source_path.exists():
            return {
                'success': False,
                'operation_type': 'MOVE',
                'original_path': old_path,
                'new_path': None,
                'error': f'源文件不存在: {new_path}'
            }
        
        dest_dir = dest_path.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(source_path), str(dest_path))
        
        return {
            'success': True,
            'operation_type': 'MOVE',
            'original_path': old_path,
            'new_path': str(dest_path),
            'error': None
        }
    
    def _recover_renamed_file(self, log_data: Dict, target_path: Optional[str]) -> Dict:
        old_path = log_data.get('old_path')
        new_path = log_data.get('new_path')
        
        if not new_path or not old_path:
            return {
                'success': False,
                'operation_type': 'RENAME',
                'original_path': old_path,
                'new_path': None,
                'error': '缺少重命名路径信息'
            }
        
        source_path = Path(new_path)
        dest_path = Path(target_path or old_path)
        
        if not source_path.exists():
            return {
                'success': False,
                'operation_type': 'RENAME',
                'original_path': old_path,
                'new_path': None,
                'error': f'源文件不存在: {new_path}'
            }
        
        shutil.move(str(source_path), str(dest_path))
        
        return {
            'success': True,
            'operation_type': 'RENAME',
            'original_path': old_path,
            'new_path': str(dest_path),
            'error': None
        }
    
    def batch_recover(self, log_ids: List[int], target_directory: Optional[str] = None) -> Dict:
        results = {
            'total': len(log_ids),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for log_id in log_ids:
            result = self.recover_file(log_id, target_directory)
            results['details'].append(result)
            
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
        
        self.logger.info(f"批量恢复完成: 成功 {results['success']}, 失败 {results['failed']}")
        return results
    
    def track_deletions(self, directory: str, recursive: bool = True) -> List[Dict]:
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        deleted_files = []
        
        try:
            logs = db_manager.get_operation_logs(
                file_path=directory,
                operation_type='DELETE',
                limit=1000
            )
            
            for log in logs:
                file_path = log.get('file_path', '')
                if recursive or str(Path(file_path).parent) == directory:
                    deleted_files.append(log)
            
            self.logger.info(f"追踪到 {len(deleted_files)} 个删除操作在 {directory}")
            
        except Exception as e:
            self.logger.error(f"追踪删除操作失败: {e}")
        
        return deleted_files
    
    def get_file_versions(self, file_id: int) -> List[Dict]:
        return db_manager.get_file_snapshots(file_id)
    
    def restore_version(self, file_id: int, version: int, target_path: Optional[str] = None) -> Dict:
        snapshots = db_manager.get_file_snapshots(file_id)
        
        target_snapshot = None
        for snap in snapshots:
            if snap.get('version') == version:
                target_snapshot = snap
                break
        
        if not target_snapshot:
            return {
                'success': False,
                'error': f'未找到版本 {version}'
            }
        
        snapshot_path = target_snapshot.get('snapshot_path')
        file_path = target_snapshot.get('file_path')
        
        if not snapshot_path or not Path(snapshot_path).exists():
            return {
                'success': False,
                'error': '快照文件不存在（沙盒环境仅模拟）'
            }
        
        dest_path = Path(target_path or file_path)
        dest_dir = dest_path.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(snapshot_path, str(dest_path))
        
        return {
            'success': True,
            'original_path': snapshot_path,
            'new_path': str(dest_path),
            'version': version,
            'error': None
        }
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        stats = db_manager.get_statistics()
        
        logs = db_manager.get_operation_logs(limit=10000)
        
        pending = [l for l in logs if not l.get('is_recovered') and l.get('operation_type') in ['DELETE', 'OVERWRITE', 'MOVE']]
        
        high_risk_pending = [l for l in pending if l.get('risk_level') in ['HIGH', 'CRITICAL']]
        
        return {
            'total_operations': stats.get('total_operations', 0),
            'pending_recovery': len(pending),
            'high_risk_pending': len(high_risk_pending),
            'risk_distribution': stats.get('risk_distribution', {}),
            'operation_distribution': stats.get('operation_distribution', {})
        }

recovery_service = RecoveryService()
