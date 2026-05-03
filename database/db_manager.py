import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from config.app_config import AppConfig
from utils.logger import get_logger

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(AppConfig.DB_PATH)
        self.logger = get_logger('Database')
        self._ensure_directory()
        self._init_database()
    
    def _ensure_directory(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitored_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    is_recursive INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_hash TEXT,
                    extension TEXT,
                    is_directory INTEGER DEFAULT 0,
                    parent_path TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(file_path)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    file_id INTEGER,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    old_path TEXT,
                    new_path TEXT,
                    risk_level TEXT DEFAULT 'LOW',
                    impact_score INTEGER DEFAULT 0,
                    has_backup INTEGER DEFAULT 0,
                    description TEXT,
                    operation_time REAL NOT NULL,
                    is_recovered INTEGER DEFAULT 0,
                    recovered_at REAL,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_hash TEXT,
                    snapshot_content BLOB,
                    snapshot_path TEXT,
                    version INTEGER DEFAULT 1,
                    created_at REAL NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recovery_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_ids TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    total_files INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    started_at REAL,
                    completed_at REAL,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_time ON operation_logs(operation_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_type ON operation_logs(operation_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_risk ON operation_logs(risk_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_file ON file_snapshots(file_id)')
            
            conn.commit()
            self.logger.info("数据库初始化完成")
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def add_monitored_path(self, path: str, is_recursive: bool = True) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().timestamp()
            cursor.execute('''
                INSERT OR REPLACE INTO monitored_paths 
                (path, is_recursive, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (path, 1 if is_recursive else 0, 1, now, now))
            conn.commit()
            return cursor.lastrowid
    
    def get_monitored_paths(self, active_only: bool = True) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM monitored_paths'
            params = []
            if active_only:
                query += ' WHERE is_active = 1'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def add_file(self, file_info: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().timestamp()
            cursor.execute('''
                INSERT OR REPLACE INTO files 
                (file_path, file_name, file_size, file_hash, extension, 
                 is_directory, parent_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_info.get('path'),
                file_info.get('name'),
                file_info.get('size', 0),
                file_info.get('hash'),
                file_info.get('extension'),
                1 if file_info.get('is_directory', False) else 0,
                file_info.get('parent_path'),
                now,
                now
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_file(self, file_path: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files WHERE file_path = ?', (file_path,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_operation_log(self, log_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_logs 
                (operation_type, file_id, file_path, file_name, file_size,
                 old_path, new_path, risk_level, impact_score, has_backup,
                 description, operation_time, is_recovered)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                log_data.get('operation_type'),
                log_data.get('file_id'),
                log_data.get('file_path'),
                log_data.get('file_name'),
                log_data.get('file_size', 0),
                log_data.get('old_path'),
                log_data.get('new_path'),
                log_data.get('risk_level', 'LOW'),
                log_data.get('impact_score', 0),
                1 if log_data.get('has_backup', False) else 0,
                log_data.get('description'),
                log_data.get('operation_time', datetime.now().timestamp())
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_operation_logs(
        self,
        operation_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        file_path: Optional[str] = None,
        is_recovered: Optional[bool] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query_parts = ['SELECT * FROM operation_logs WHERE 1=1']
            params = []
            
            if operation_type:
                query_parts.append('AND operation_type = ?')
                params.append(operation_type)
            
            if risk_level:
                query_parts.append('AND risk_level = ?')
                params.append(risk_level)
            
            if start_time:
                query_parts.append('AND operation_time >= ?')
                params.append(start_time)
            
            if end_time:
                query_parts.append('AND operation_time <= ?')
                params.append(end_time)
            
            if file_path:
                query_parts.append('AND file_path LIKE ?')
                params.append(f'{file_path}%')
            
            if is_recovered is not None:
                query_parts.append('AND is_recovered = ?')
                params.append(1 if is_recovered else 0)
            
            query_parts.append('ORDER BY operation_time DESC')
            query_parts.append('LIMIT ? OFFSET ?')
            params.extend([limit, offset])
            
            cursor.execute(' '.join(query_parts), params)
            return [dict(row) for row in cursor.fetchall()]
    
    def add_file_snapshot(self, snapshot_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().timestamp()
            
            cursor.execute('''
                SELECT MAX(version) as max_version FROM file_snapshots 
                WHERE file_id = ? AND is_active = 1
            ''', (snapshot_data.get('file_id'),))
            result = cursor.fetchone()
            next_version = (result['max_version'] or 0) + 1
            
            cursor.execute('''
                INSERT INTO file_snapshots 
                (file_id, file_path, file_name, file_size, file_hash,
                 snapshot_content, snapshot_path, version, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                snapshot_data.get('file_id'),
                snapshot_data.get('file_path'),
                snapshot_data.get('file_name'),
                snapshot_data.get('file_size', 0),
                snapshot_data.get('file_hash'),
                snapshot_data.get('snapshot_content'),
                snapshot_data.get('snapshot_path'),
                next_version,
                now
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_file_snapshots(self, file_id: int, active_only: bool = True) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM file_snapshots WHERE file_id = ?'
            params = [file_id]
            
            if active_only:
                query += ' AND is_active = 1'
            
            query += ' ORDER BY version DESC'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_log_recovered(self, log_id: int, recovered: bool = True) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().timestamp()
            cursor.execute('''
                UPDATE operation_logs 
                SET is_recovered = ?, recovered_at = ?
                WHERE id = ?
            ''', (1 if recovered else 0, now if recovered else None, log_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def create_recovery_task(self, log_ids: List[int], task_type: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().timestamp()
            cursor.execute('''
                INSERT INTO recovery_tasks 
                (log_ids, task_type, total_files, status, created_at)
                VALUES (?, ?, ?, 'PENDING', ?)
            ''', (
                ','.join(map(str, log_ids)),
                task_type,
                len(log_ids),
                now
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_statistics(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute('SELECT COUNT(*) as count FROM operation_logs')
            stats['total_operations'] = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM operation_logs 
                WHERE is_recovered = 0 AND operation_type IN ('DELETE', 'OVERWRITE')
            ''')
            stats['pending_recovery'] = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT risk_level, COUNT(*) as count 
                FROM operation_logs 
                WHERE is_recovered = 0
                GROUP BY risk_level
            ''')
            stats['risk_distribution'] = {row['risk_level']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('''
                SELECT operation_type, COUNT(*) as count 
                FROM operation_logs 
                GROUP BY operation_type
            ''')
            stats['operation_distribution'] = {row['operation_type']: row['count'] for row in cursor.fetchall()}
            
            return stats

db_manager = DatabaseManager()
