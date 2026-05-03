import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

print("=" * 60)
print("测试筛选逻辑")
print("=" * 60)

logs = db_manager.get_operation_logs(limit=10000)
print(f"\n总记录数: {len(logs)}")

if len(logs) == 0:
    print("\n警告：数据库为空，建议先运行test_sandbox.py初始化演示数据")
    sys.exit(0)

print("\n[1] 按风险等级筛选测试:")
risk_counts = {}
for log in logs:
    risk = log.get('risk_level', 'LOW')
    risk_counts[risk] = risk_counts.get(risk, 0) + 1
print(f"    风险分布: {risk_counts}")

high_risk_logs = [l for l in logs if l.get('risk_level') in ['HIGH', 'CRITICAL']]
print(f"    高风险+严重: {len(high_risk_logs)} 条")

print("\n[2] 按操作类型筛选测试:")
op_counts = {}
for log in logs:
    op = log.get('operation_type', 'UNKNOWN')
    op_counts[op] = op_counts.get(op, 0) + 1
print(f"    操作分布: {op_counts}")

delete_logs = [l for l in logs if l.get('operation_type') == 'DELETE']
print(f"    删除操作: {len(delete_logs)} 条")

print("\n[3] 按恢复状态筛选测试:")
pending = [l for l in logs if not l.get('is_recovered', 0)]
recovered = [l for l in logs if l.get('is_recovered', 0)]
print(f"    待恢复: {len(pending)} 条")
print(f"    已恢复: {len(recovered)} 条")

print("\n[4] 组合筛选测试 (高风险+待恢复+删除操作):")
filtered = [
    l for l in logs 
    if l.get('risk_level') in ['HIGH', 'CRITICAL']
    and not l.get('is_recovered', 0)
    and l.get('operation_type') in ['DELETE', 'OVERWRITE']
]
print(f"    符合条件: {len(filtered)} 条")

if filtered:
    print("\n[5] 筛选结果示例:")
    for i, log in enumerate(filtered[:3]):
        print(f"    [{i+1}] ID={log.get('id')}, "
              f"操作={log.get('operation_type')}, "
              f"风险={log.get('risk_level')}, "
              f"文件={log.get('file_name')}")

print("\n" + "=" * 60)
print("筛选逻辑测试完成！")
print("=" * 60)
