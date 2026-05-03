import os
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config.app_config import AppConfig

def format_file_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_name[i]}"

def format_timestamp(timestamp: float) -> str:
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def get_file_info(file_path: str) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {}
    
    stat = path.stat()
    return {
        'name': path.name,
        'path': str(path.absolute()),
        'size': stat.st_size,
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'extension': path.suffix.lower(),
        'is_directory': path.is_dir()
    }

def is_text_file(file_path: str) -> bool:
    text_extensions = {
        '.txt', '.log', '.md', '.json', '.xml', '.html', '.css', '.js',
        '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.rb', '.php', '.go',
        '.rs', '.swift', '.kt', '.ts', '.tsx', '.jsx', '.vue', '.yml',
        '.yaml', '.toml', '.ini', '.cfg', '.conf', '.sh', '.bat', '.ps1'
    }
    
    path = Path(file_path)
    return path.suffix.lower() in text_extensions

def calculate_risk_level(operation_type: str, 
                         file_size: int = 0, 
                         is_directory: bool = False,
                         has_backup: bool = False) -> str:
    base_risk = AppConfig.OPERATION_TYPES[operation_type]['default_risk']
    risk_priority = AppConfig.RISK_LEVELS[base_risk]['priority']
    
    if is_directory:
        risk_priority = min(risk_priority + 1, 4)
    
    if file_size > 100 * 1024 * 1024:
        risk_priority = min(risk_priority + 1, 4)
    
    if has_backup:
        risk_priority = max(risk_priority - 1, 1)
    
    for level, info in AppConfig.RISK_LEVELS.items():
        if info['priority'] == risk_priority:
            return level
    
    return base_risk

def get_time_range(interval_seconds: Optional[int]) -> tuple:
    now = datetime.now()
    if interval_seconds is None:
        return (None, now)
    
    start_time = now - timedelta(seconds=interval_seconds)
    return (start_time, now)

def find_common_path(paths: List[str]) -> str:
    if not paths:
        return ""
    
    path_parts = [Path(p).parts for p in paths]
    min_length = min(len(parts) for parts in path_parts)
    
    common_parts = []
    for i in range(min_length):
        if all(parts[i] == path_parts[0][i] for parts in path_parts):
            common_parts.append(path_parts[0][i])
        else:
            break
    
    return str(Path(*common_parts)) if common_parts else ""

def generate_unique_id() -> str:
    import uuid
    return str(uuid.uuid4())

def safe_delete_file(file_path: str, move_to_trash: bool = True) -> bool:
    try:
        path = Path(file_path)
        if not path.exists():
            return True
        
        if move_to_trash:
            trash_dir = AppConfig.DATA_DIR / "trash"
            trash_dir.mkdir(parents=True, exist_ok=True)
            
            import shutil
            dest = trash_dir / f"{path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(str(path), str(dest))
        else:
            if path.is_dir():
                import shutil
                shutil.rmtree(str(path))
            else:
                path.unlink()
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(AppConfig.APP_NAME)
        logger.error(f"删除文件失败: {e}")
        return False
