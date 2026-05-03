import os
from pathlib import Path

class AppConfig:
    APP_NAME = "File Recovery Pro"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "Recovery Team"
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "recovery.db"
    SANDBOX_DIR = DATA_DIR / "sandbox"
    
    DARK_THEME = True
    
    LOG_LEVEL = "INFO"
    LOG_FILE = DATA_DIR / "app.log"
    
    TIMELINE_INTERVALS = [
        ("1小时内", 3600),
        ("6小时内", 21600),
        ("24小时内", 86400),
        ("7天内", 604800),
        ("30天内", 2592000),
        ("全部", None)
    ]
    
    RISK_LEVELS = {
        "LOW": {"name": "低风险", "color": "#4CAF50", "priority": 1},
        "MEDIUM": {"name": "中风险", "color": "#FF9800", "priority": 2},
        "HIGH": {"name": "高风险", "color": "#F44336", "priority": 3},
        "CRITICAL": {"name": "严重", "color": "#9C27B0", "priority": 4}
    }
    
    OPERATION_TYPES = {
        "DELETE": {"name": "删除", "icon": "delete", "default_risk": "HIGH"},
        "OVERWRITE": {"name": "覆盖", "icon": "overwrite", "default_risk": "HIGH"},
        "MOVE": {"name": "移动", "icon": "move", "default_risk": "MEDIUM"},
        "RENAME": {"name": "重命名", "icon": "rename", "default_risk": "LOW"},
        "MODIFY": {"name": "修改", "icon": "modify", "default_risk": "LOW"},
        "CREATE": {"name": "创建", "icon": "create", "default_risk": "LOW"}
    }
    
    @classmethod
    def init_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
