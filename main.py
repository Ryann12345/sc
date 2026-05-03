import sys
import os

def _fix_qt_plugins():
    try:
        import PySide6
        pyside6_dir = os.path.dirname(PySide6.__file__)
        
        plugins_dir = os.path.join(pyside6_dir, 'plugins')
        qt_plugins_dir = os.path.join(pyside6_dir, 'Qt', 'plugins')
        
        if os.path.exists(plugins_dir):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(plugins_dir, 'platforms')
            os.environ['QT_PLUGIN_PATH'] = plugins_dir
            
            if not os.path.exists(qt_plugins_dir):
                import shutil
                try:
                    shutil.copytree(plugins_dir, qt_plugins_dir, dirs_exist_ok=True)
                except Exception:
                    pass
        
        dll_dirs = [pyside6_dir]
        if hasattr(os, 'add_dll_directory'):
            for dll_dir in dll_dirs:
                if os.path.exists(dll_dir):
                    os.add_dll_directory(dll_dir)
                    
    except Exception as e:
        print(f"Warning: Could not configure Qt plugins: {e}")

_fix_qt_plugins()

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from utils.logger import setup_logger

def main():
    setup_logger()
    
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        try:
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        except AttributeError:
            pass
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
