import os
import shutil
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.logger import get_logger
from utils.helpers import calculate_risk_level, format_file_size

class FileSimulator:
    def __init__(self):
        self.logger = get_logger('FileSimulator')
        self.sandbox_root = AppConfig.SANDBOX_DIR
        self.sample_content = {
            'txt': [
                "这是一个重要的文档文件，包含项目的关键信息。\n\n第一章：项目概述\n本项目旨在开发一个文件恢复工具。\n\n第二章：技术栈\n使用Python和PySide6进行开发。",
                "会议记录\n日期：2024年1月15日\n参会人员：张三、李四\n议题：\n1. 项目进度汇报\n2. 下一阶段计划\n3. 风险评估",
                "README.md\n# 项目名称\n\n## 简介\n这是一个示例项目。\n\n## 安装\npip install -r requirements.txt\n\n## 使用\npython main.py",
                "日志文件\n[INFO] 系统启动\n[INFO] 加载配置文件\n[INFO] 初始化数据库连接\n[INFO] 准备就绪，等待操作"
            ],
            'json': [
                '{\n  "name": "项目配置",\n  "version": "1.0.0",\n  "enabled": true,\n  "settings": {\n    "timeout": 30,\n    "retries": 3\n  }\n}',
                '{\n  "users": [\n    {"id": 1, "name": "张三", "active": true},\n    {"id": 2, "name": "李四", "active": false}\n  ]\n}'
            ],
            'log': [
                "2024-01-15 09:00:00 [INFO] Application started\n2024-01-15 09:00:01 [INFO] Loading configuration\n2024-01-15 09:00:02 [INFO] Connecting to database\n2024-01-15 09:00:03 [INFO] Ready"
            ]
        }
    
    def _generate_random_filename(self, extension: str = 'txt') -> str:
        name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{name}.{extension}"
    
    def _create_sample_file(self, file_path: str, content_type: str = 'txt') -> None:
        content = random.choice(self.sample_content.get(content_type, self.sample_content['txt']))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def generate_sample_files(self, count: int = 20) -> List[Dict[str, Any]]:
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        
        directories = [
            self.sandbox_root / "documents",
            self.sandbox_root / "projects" / "web_app",
            self.sandbox_root / "projects" / "mobile_app",
            self.sandbox_root / "logs",
            self.sandbox_root / "backups"
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        file_templates = [
            ("documents", "重要报告", "txt"),
            ("documents", "会议纪要", "txt"),
            ("documents", "财务数据", "json"),
            ("projects/web_app", "index", "html"),
            ("projects/web_app", "style", "css"),
            ("projects/web_app", "app", "js"),
            ("projects/web_app", "config", "json"),
            ("projects/mobile_app", "MainActivity", "java"),
            ("projects/mobile_app", "build", "gradle"),
            ("logs", "system", "log"),
            ("logs", "error", "log"),
            ("backups", "backup_2024", "zip"),
        ]
        
        created_files = []
        
        for i in range(count):
            if i < len(file_templates):
                dir_name, base_name, ext = file_templates[i]
                filename = f"{base_name}_{i+1}.{ext}"
            else:
                dir_name = random.choice(["documents", "projects/web_app", "logs"])
                filename = self._generate_random_filename(random.choice(['txt', 'json', 'log', 'html']))
            
            file_path = self.sandbox_root / dir_name / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            ext = filename.split('.')[-1].lower()
            self._create_sample_file(str(file_path), ext)
            
            file_info = {
                'path': str(file_path.absolute()),
                'name': filename,
                'size': file_path.stat().st_size,
                'extension': f'.{ext}',
                'is_directory': False,
                'parent_path': str(file_path.parent.absolute())
            }
            
            file_id = db_manager.add_file(file_info)
            file_info['file_id'] = file_id
            
            created_files.append(file_info)
            self.logger.info(f"创建模拟文件: {filename}")
        
        return created_files
    
    def generate_operation_history(self, files: List[Dict], days_back: int = 7) -> List[int]:
        log_ids = []
        now = datetime.now()
        
        operation_types = ['DELETE', 'OVERWRITE', 'MOVE', 'RENAME', 'MODIFY', 'CREATE']
        weights = [0.25, 0.15, 0.15, 0.1, 0.25, 0.1]
        
        for i, file_info in enumerate(files):
            hours_ago = random.randint(0, days_back * 24)
            minutes_ago = random.randint(0, 59)
            op_time = (now - timedelta(hours=hours_ago, minutes=minutes_ago)).timestamp()
            
            op_type = random.choices(operation_types, weights=weights, k=1)[0]
            
            is_directory = file_info.get('is_directory', False)
            file_size = file_info.get('size', 0)
            has_backup = random.random() < 0.3
            
            risk_level = calculate_risk_level(op_type, file_size, is_directory, has_backup)
            
            impact_score = random.randint(1, 100)
            
            old_path = file_info['path']
            new_path = None
            description = ""
            
            if op_type == 'MOVE':
                new_dir = self.sandbox_root / "moved_files"
                new_dir.mkdir(exist_ok=True)
                new_path = str(new_dir / file_info['name'])
                description = f"文件从 {old_path} 移动到 {new_path}"
            elif op_type == 'RENAME':
                new_name = f"renamed_{file_info['name']}"
                new_path = str(Path(old_path).parent / new_name)
                description = f"文件重命名为 {new_name}"
            elif op_type == 'DELETE':
                description = f"文件已删除"
            elif op_type == 'OVERWRITE':
                description = f"文件内容被覆盖"
            elif op_type == 'MODIFY':
                description = f"文件内容被修改"
            elif op_type == 'CREATE':
                description = f"新文件创建"
            
            log_data = {
                'operation_type': op_type,
                'file_id': file_info.get('file_id'),
                'file_path': old_path,
                'file_name': file_info['name'],
                'file_size': file_size,
                'old_path': old_path,
                'new_path': new_path,
                'risk_level': risk_level,
                'impact_score': impact_score,
                'has_backup': has_backup,
                'description': description,
                'operation_time': op_time
            }
            
            log_id = db_manager.add_operation_log(log_data)
            log_ids.append(log_id)
            
            if op_type in ['MODIFY', 'OVERWRITE']:
                snapshot_data = {
                    'file_id': file_info.get('file_id'),
                    'file_path': old_path,
                    'file_name': file_info['name'],
                    'file_size': file_size,
                    'file_hash': None,
                    'snapshot_content': None,
                    'snapshot_path': None
                }
                db_manager.add_file_snapshot(snapshot_data)
            
            self.logger.info(f"生成操作日志: {op_type} - {file_info['name']}")
        
        return log_ids
    
    def setup_demo_environment(self) -> Dict[str, Any]:
        self.logger.info("开始设置演示环境...")
        
        if self.sandbox_root.exists():
            shutil.rmtree(self.sandbox_root)
        
        files = self.generate_sample_files(25)
        
        log_ids = self.generate_operation_history(files, days_back=7)
        
        db_manager.add_monitored_path(str(self.sandbox_root.absolute()), is_recursive=True)
        
        self.logger.info(f"演示环境设置完成: {len(files)} 个文件, {len(log_ids)} 条操作记录")
        
        return {
            'files': files,
            'log_ids': log_ids,
            'sandbox_path': str(self.sandbox_root.absolute())
        }
    
    def get_sandbox_structure(self) -> Dict[str, Any]:
        def build_tree(path: Path) -> Dict:
            result = {
                'name': path.name,
                'path': str(path.absolute()),
                'is_directory': path.is_dir(),
                'children': []
            }
            
            if path.is_dir():
                for child in path.iterdir():
                    result['children'].append(build_tree(child))
                result['children'].sort(key=lambda x: (not x['is_directory'], x['name']))
            
            return result
        
        if not self.sandbox_root.exists():
            return {'name': 'sandbox', 'path': str(self.sandbox_root), 'is_directory': True, 'children': []}
        
        return build_tree(self.sandbox_root)
    
    def reset_sandbox(self) -> None:
        if self.sandbox_root.exists():
            shutil.rmtree(self.sandbox_root)
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.logger.info("沙盒环境已重置")

file_simulator = FileSimulator()
