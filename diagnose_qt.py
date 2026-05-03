import sys
import os

print("=" * 60)
print("Qt环境诊断")
print("=" * 60)

print(f"\n[1] Python版本: {sys.version}")
print(f"    Python路径: {sys.executable}")

print("\n[2] 检查PySide6安装...")
try:
    import PySide6
    print(f"    PySide6版本: {PySide6.__version__}")
    print(f"    PySide6路径: {os.path.dirname(PySide6.__file__)}")
    
    pyside6_path = os.path.dirname(PySide6.__file__)
    plugins_path = os.path.join(pyside6_path, "Qt", "plugins")
    platforms_path = os.path.join(plugins_path, "platforms")
    
    print(f"    插件路径: {plugins_path}")
    print(f"    platforms路径: {platforms_path}")
    
    if os.path.exists(platforms_path):
        print(f"    platforms目录存在: ✓")
        platform_files = os.listdir(platforms_path)
        print(f"    platforms内容: {platform_files}")
    else:
        print(f"    platforms目录不存在: ✗")
    
    current_qpa_plugin = os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH')
    print(f"    当前QT_QPA_PLATFORM_PLUGIN_PATH: {current_qpa_plugin}")
    
except ImportError as e:
    print(f"    PySide6导入失败: {e}")

print("\n[3] 系统环境变量中的Qt相关设置...")
for key in os.environ:
    if 'QT' in key.upper() or 'PYSIDE' in key.upper():
        print(f"    {key} = {os.environ[key]}")

print("\n[4] 尝试导入Qt模块...")
try:
    from PySide6.QtCore import Qt
    print("    PySide6.QtCore: ✓")
except ImportError as e:
    print(f"    PySide6.QtCore: ✗ {e}")

try:
    from PySide6.QtWidgets import QApplication
    print("    PySide6.QtWidgets: ✓")
except ImportError as e:
    print(f"    PySide6.QtWidgets: ✗ {e}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)

print("\n[建议修复方案]")
print("方案1: 在main.py开头设置Qt插件路径")
print('''
import os
import sys

# 修复Qt平台插件问题
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
''')

print("\n方案2: 重新安装PySide6")
print("    pip uninstall pyside6")
print("    pip install pyside6 --no-cache-dir")
