import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试沙盒环境演示数据生成")
print("=" * 60)

from config.app_config import AppConfig
from sandbox.file_simulator import file_simulator
from database.db_manager import db_manager

print("\n[1] 检查沙盒路径...")
print(f"    沙盒根目录: {file_simulator.sandbox_root}")

print("\n[2] 生成演示环境...")
result = file_simulator.setup_demo_environment()

print(f"\n[3] 演示环境创建结果:")
print(f"    - 文件数量: {len(result.get('files', []))}")
print(f"    - 操作记录: {len(result.get('log_ids', []))}")
print(f"    - 沙盒路径: {result.get('sandbox_path')}")

print("\n[4] 数据库统计:")
stats = db_manager.get_statistics()
print(f"    - 总操作数: {stats.get('total_operations', 0)}")
print(f"    - 待恢复: {stats.get('pending_recovery', 0)}")
print(f"    - 风险分布: {stats.get('risk_distribution', {})}")
print(f"    - 操作类型分布: {stats.get('operation_distribution', {})}")

print("\n[5] 最近10条操作日志:")
logs = db_manager.get_operation_logs(limit=10)
for i, log in enumerate(logs[:10]):
    op_type = log.get('operation_type', 'UNKNOWN')
    risk = log.get('risk_level', 'LOW')
    file_name = log.get('file_name', '')
    print(f"    [{i+1}] {op_type:8} | {risk:8} | {file_name}")

print("\n[6] 监控目录列表:")
monitored = db_manager.get_monitored_paths()
for path in monitored:
    print(f"    - {path.get('path')} (递归: {bool(path.get('is_recursive'))})")

print("\n" + "=" * 60)
print("沙盒环境测试完成!")
print("=" * 60)
