import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("测试模块导入...")
print("=" * 50)

try:
    from config.app_config import AppConfig
    print(f"✓ config.app_config - AppConfig loaded")
    print(f"  - APP_NAME: {AppConfig.APP_NAME}")
    print(f"  - VERSION: {AppConfig.APP_VERSION}")
    print(f"  - DB_PATH: {AppConfig.DB_PATH}")
except Exception as e:
    print(f"✗ config.app_config 导入失败: {e}")

try:
    from utils.logger import setup_logger, get_logger
    print(f"✓ utils.logger 加载成功")
except Exception as e:
    print(f"✗ utils.logger 导入失败: {e}")

try:
    from utils.helpers import (
        format_file_size, format_timestamp, calculate_risk_level,
        get_time_range, generate_unique_id
    )
    print(f"✓ utils.helpers 加载成功")
    print(f"  - format_file_size(1024*1024): {format_file_size(1024*1024)}")
    print(f"  - generate_unique_id(): {generate_unique_id()[:20]}...")
except Exception as e:
    print(f"✗ utils.helpers 导入失败: {e}")

try:
    from database.db_manager import DatabaseManager, db_manager
    print(f"✓ database.db_manager 加载成功")
    
    stats = db_manager.get_statistics()
    print(f"  - 数据库统计: {stats}")
except Exception as e:
    print(f"✗ database.db_manager 导入失败: {e}")

try:
    from sandbox.file_simulator import FileSimulator, file_simulator
    print(f"✓ sandbox.file_simulator 加载成功")
    print(f"  - 沙盒路径: {file_simulator.sandbox_root}")
except Exception as e:
    print(f"✗ sandbox.file_simulator 导入失败: {e}")

try:
    from services.recovery_service import RecoveryService, recovery_service
    from services.conflict_service import ConflictService, conflict_service
    from services.report_service import ReportService, report_service
    print(f"✓ services.* 加载成功")
    
    stats = recovery_service.get_recovery_statistics()
    print(f"  - 恢复统计: {stats}")
except Exception as e:
    print(f"✗ services 导入失败: {e}")

try:
    from ui.styles import get_style, DARK_STYLE
    print(f"✓ ui.styles 加载成功")
    print(f"  - 样式长度: {len(DARK_STYLE)} 字符")
except Exception as e:
    print(f"✗ ui.styles 导入失败: {e}")

print("")
print("=" * 50)
print("测试完成!")
print("=" * 50)
