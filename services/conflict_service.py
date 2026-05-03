import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.logger import get_logger
from utils.helpers import calculate_file_hash

class ConflictService:
    def __init__(self):
        self.logger = get_logger('ConflictService')
    
    def detect_conflicts(self, log_ids: List[int]) -> List[Dict[str, Any]]:
        conflicts = []
        logs = db_manager.get_operation_logs(limit=10000)
        
        target_logs = [l for l in logs if l.get('id') in log_ids]
        
        file_operations = {}
        for log in target_logs:
            file_path = log.get('file_path')
            if file_path not in file_operations:
                file_operations[file_path] = []
            file_operations[file_path].append(log)
        
        for file_path, ops in file_operations.items():
            if len(ops) > 1:
                conflict = self._analyze_file_conflicts(file_path, ops)
                if conflict:
                    conflicts.append(conflict)
        
        for log in target_logs:
            overlap = self._check_time_overlap(log, target_logs)
            if overlap:
                exists = any(
                    c.get('type') == 'time_overlap' and 
                    c.get('log_id') == log.get('id')
                    for c in conflicts
                )
                if not exists:
                    conflicts.append({
                        'type': 'time_overlap',
                        'severity': 'MEDIUM',
                        'log_id': log.get('id'),
                        'file_path': log.get('file_path'),
                        'description': f"操作时间与其他操作重叠",
                        'overlapping_ids': overlap
                    })
        
        self.logger.info(f"检测到 {len(conflicts)} 个冲突")
        return conflicts
    
    def _analyze_file_conflicts(self, file_path: str, operations: List[Dict]) -> Optional[Dict]:
        if len(operations) <= 1:
            return None
        
        op_types = [op.get('operation_type') for op in operations]
        times = [op.get('operation_time') for op in operations]
        
        sorted_ops = sorted(operations, key=lambda x: x.get('operation_time', 0))
        
        conflict_type = None
        severity = 'LOW'
        description = ""
        
        if 'DELETE' in op_types:
            delete_ops = [o for o in sorted_ops if o.get('operation_type') == 'DELETE']
            other_ops = [o for o in sorted_ops if o.get('operation_type') != 'DELETE']
            
            if other_ops:
                last_delete = max(delete_ops, key=lambda x: x.get('operation_time', 0))
                first_other = min(other_ops, key=lambda x: x.get('operation_time', 0))
                
                if last_delete.get('operation_time', 0) > first_other.get('operation_time', 0):
                    conflict_type = 'delete_then_modify'
                    severity = 'HIGH'
                    description = f"文件被删除后又被修改/移动，恢复顺序可能有问题"
        
        if 'OVERWRITE' in op_types and len([o for o in op_types if o == 'OVERWRITE']) > 1:
            conflict_type = 'multiple_overwrites'
            severity = 'MEDIUM'
            description = f"文件被多次覆盖，需要确定恢复哪个版本"
        
        if 'MOVE' in op_types and len([o for o in op_types if o == 'MOVE']) > 1:
            conflict_type = 'multiple_moves'
            severity = 'MEDIUM'
            description = f"文件被多次移动，路径追踪可能混乱"
        
        if conflict_type:
            return {
                'type': conflict_type,
                'severity': severity,
                'file_path': file_path,
                'operations': sorted_ops,
                'description': description,
                'recommendation': self._get_recommendation(conflict_type)
            }
        
        return None
    
    def _check_time_overlap(self, log: Dict, all_logs: List[Dict]) -> List[int]:
        log_time = log.get('operation_time', 0)
        window_seconds = 5
        
        overlapping = []
        for other in all_logs:
            if other.get('id') == log.get('id'):
                continue
            
            other_time = other.get('operation_time', 0)
            if abs(log_time - other_time) < window_seconds:
                overlapping.append(other.get('id'))
        
        return overlapping
    
    def _get_recommendation(self, conflict_type: str) -> str:
        recommendations = {
            'delete_then_modify': "建议先恢复删除后的修改操作，再处理删除。或者检查是否需要完全恢复到删除前的状态。",
            'multiple_overwrites': "查看所有版本快照，选择需要恢复的具体版本。建议使用版本对比功能。",
            'multiple_moves': "追踪完整的移动历史，确定最终目标位置。建议查看路径变更视图。",
            'time_overlap': "检查同一时间内的多个操作，确认它们的执行顺序和相互影响。"
        }
        return recommendations.get(conflict_type, "请仔细检查操作记录，确认恢复顺序。")
    
    def check_destination_conflict(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        dest = Path(dest_path)
        
        result = {
            'has_conflict': False,
            'conflict_type': None,
            'description': '',
            'resolution_options': []
        }
        
        if dest.exists():
            result['has_conflict'] = True
            
            source = Path(source_path)
            if source.exists():
                source_stat = source.stat()
                dest_stat = dest.stat()
                
                if calculate_file_hash(str(source)) == calculate_file_hash(str(dest)):
                    result['conflict_type'] = 'identical_files'
                    result['description'] = "目标位置已存在相同文件"
                    result['resolution_options'] = ['skip', 'overwrite']
                elif source_stat.st_mtime > dest_stat.st_mtime:
                    result['conflict_type'] = 'newer_source'
                    result['description'] = "源文件比目标文件更新"
                    result['resolution_options'] = ['overwrite', 'rename_source', 'skip']
                else:
                    result['conflict_type'] = 'newer_destination'
                    result['description'] = "目标文件比源文件更新"
                    result['resolution_options'] = ['overwrite', 'rename_source', 'keep_both', 'skip']
            else:
                result['conflict_type'] = 'destination_exists'
                result['description'] = "目标位置已存在文件"
                result['resolution_options'] = ['overwrite', 'rename_source', 'keep_both', 'skip']
        
        return result
    
    def check_batch_conflicts(self, log_ids: List[int]) -> Dict[str, Any]:
        result = {
            'total': len(log_ids),
            'conflicts': [],
            'warnings': [],
            'can_proceed': True
        }
        
        conflicts = self.detect_conflicts(log_ids)
        
        for conflict in conflicts:
            if conflict.get('severity') == 'HIGH':
                result['conflicts'].append(conflict)
                result['can_proceed'] = False
            else:
                result['warnings'].append(conflict)
        
        file_paths = set()
        logs = db_manager.get_operation_logs(limit=10000)
        for log in logs:
            if log.get('id') in log_ids:
                file_paths.add(log.get('file_path'))
        
        if len(file_paths) < len(log_ids):
            result['warnings'].append({
                'type': 'duplicate_files',
                'severity': 'LOW',
                'description': f"多个操作涉及相同文件 ({len(log_ids) - len(file_paths)} 个重复)",
                'recommendation': "检查这些文件的操作顺序"
            })
        
        self.logger.info(f"批量冲突检测完成: {len(result['conflicts'])} 冲突, {len(result['warnings'])} 警告")
        
        return result
    
    def resolve_conflict(self, conflict: Dict, resolution: str) -> Dict:
        result = {
            'success': False,
            'action': None,
            'description': ''
        }
        
        conflict_type = conflict.get('type')
        options = conflict.get('resolution_options', [])
        
        if resolution not in options:
            result['description'] = f"无效的解决方案: {resolution}。可用选项: {options}"
            return result
        
        if resolution == 'skip':
            result['success'] = True
            result['action'] = 'skip'
            result['description'] = "跳过此文件，不进行恢复"
        elif resolution == 'overwrite':
            result['success'] = True
            result['action'] = 'overwrite'
            result['description'] = "覆盖目标文件"
        elif resolution == 'rename_source':
            result['success'] = True
            result['action'] = 'rename_source'
            result['description'] = "重命名源文件后恢复"
        elif resolution == 'keep_both':
            result['success'] = True
            result['action'] = 'keep_both'
            result['description'] = "保留两个文件（自动重命名）"
        else:
            result['description'] = f"未实现的解决方案: {resolution}"
        
        return result

conflict_service = ConflictService()
