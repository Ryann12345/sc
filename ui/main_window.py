from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QStatusBar, QToolBar,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence
from config.app_config import AppConfig
from ui.styles import get_style
from ui.panels.left_panel import LeftPanel
from ui.panels.center_panel import CenterPanel
from ui.panels.right_panel import RightPanel
from sandbox.file_simulator import file_simulator
from database.db_manager import db_manager
from utils.logger import get_logger

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = get_logger('MainWindow')
        self.setWindowTitle(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        self.setStyleSheet(get_style())
        
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_main_layout()
        
        self._connect_signals()
        self._check_demo_environment()
        
        self.logger.info("主窗口初始化完成")
    
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("文件(&F)")
        
        add_monitor_action = QAction("添加监控目录", self)
        add_monitor_action.setShortcut(QKeySequence("Ctrl+O"))
        add_monitor_action.triggered.connect(self._add_monitor_directory)
        file_menu.addAction(add_monitor_action)
        
        export_report_action = QAction("导出恢复报告", self)
        export_report_action.setShortcut(QKeySequence("Ctrl+E"))
        export_report_action.triggered.connect(self._export_report)
        file_menu.addAction(export_report_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menu_bar.addMenu("编辑(&E)")
        
        select_all_action = QAction("全选", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self._select_all_logs)
        edit_menu.addAction(select_all_action)
        
        deselect_all_action = QAction("取消全选", self)
        deselect_all_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        deselect_all_action.triggered.connect(self._deselect_all_logs)
        edit_menu.addAction(deselect_all_action)
        
        edit_menu.addSeparator()
        
        recovery_menu = menu_bar.addMenu("恢复(&R)")
        
        recover_selected_action = QAction("恢复选中项", self)
        recover_selected_action.setShortcut(QKeySequence("F5"))
        recover_selected_action.triggered.connect(self._recover_selected)
        recovery_menu.addAction(recover_selected_action)
        
        batch_recover_action = QAction("批量恢复", self)
        batch_recover_action.setShortcut(QKeySequence("F6"))
        batch_recover_action.triggered.connect(self._batch_recover)
        recovery_menu.addAction(batch_recover_action)
        
        view_menu = menu_bar.addMenu("视图(&V)")
        
        toggle_theme_action = QAction("切换主题", self)
        toggle_theme_action.setShortcut(QKeySequence("Ctrl+T"))
        toggle_theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_data)
        view_menu.addAction(refresh_action)
        
        demo_menu = menu_bar.addMenu("演示(&D)")
        
        setup_demo_action = QAction("初始化演示环境", self)
        setup_demo_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        setup_demo_action.triggered.connect(self._setup_demo_environment)
        demo_menu.addAction(setup_demo_action)
        
        reset_demo_action = QAction("重置演示环境", self)
        reset_demo_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reset_demo_action.triggered.connect(self._reset_demo_environment)
        demo_menu.addAction(reset_demo_action)
        
        help_menu = menu_bar.addMenu("帮助(&H)")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        self.refresh_action = QAction("刷新", self)
        self.refresh_action.triggered.connect(self._refresh_data)
        toolbar.addAction(self.refresh_action)
        
        toolbar.addSeparator()
        
        self.recover_action = QAction("恢复", self)
        self.recover_action.triggered.connect(self._recover_selected)
        toolbar.addAction(self.recover_action)
        
        self.batch_recover_action = QAction("批量恢复", self)
        self.batch_recover_action.triggered.connect(self._batch_recover)
        toolbar.addAction(self.batch_recover_action)
        
        toolbar.addSeparator()
        
        self.export_action = QAction("导出报告", self)
        self.export_action.triggered.connect(self._export_report)
        toolbar.addAction(self.export_action)
        
        toolbar.addSeparator()
        
        self.setup_demo_action = QAction("演示环境", self)
        self.setup_demo_action.triggered.connect(self._setup_demo_environment)
        toolbar.addAction(self.setup_demo_action)
    
    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _create_main_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        
        self.left_panel = LeftPanel()
        main_splitter.addWidget(self.left_panel)
        
        self.center_panel = CenterPanel()
        main_splitter.addWidget(self.center_panel)
        
        self.right_panel = RightPanel()
        main_splitter.addWidget(self.right_panel)
        
        main_splitter.setSizes([350, 500, 550])
        
        main_layout.addWidget(main_splitter)
    
    def _connect_signals(self):
        self.left_panel.directory_selected.connect(self._on_directory_selected)
        self.left_panel.timeline_filter_changed.connect(self._on_timeline_filter_changed)
        self.left_panel.risk_filter_changed.connect(self._on_risk_filter_changed)
        
        self.center_panel.log_selected.connect(self._on_log_selected)
        self.center_panel.logs_selected.connect(self._on_logs_selected)
        self.center_panel.recover_requested.connect(self._on_recover_requested)
        
        self.right_panel.version_selected.connect(self._on_version_selected)
    
    def _check_demo_environment(self):
        stats = db_manager.get_statistics()
        if stats['total_operations'] == 0:
            self.status_bar.showMessage("未检测到演示数据，建议初始化演示环境")
    
    def _add_monitor_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择要监控的目录")
        if dir_path:
            db_manager.add_monitored_path(dir_path, is_recursive=True)
            self.status_bar.showMessage(f"已添加监控目录: {dir_path}")
            self._refresh_data()
    
    def _export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出恢复报告", "", 
            "HTML报告 (*.html);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        if file_path:
            self.status_bar.showMessage(f"报告已导出到: {file_path}")
    
    def _select_all_logs(self):
        self.center_panel.select_all_logs()
    
    def _deselect_all_logs(self):
        self.center_panel.deselect_all_logs()
    
    def _recover_selected(self):
        self.center_panel.recover_selected()
    
    def _batch_recover(self):
        self.center_panel.show_batch_recover_dialog()
    
    def _toggle_theme(self):
        AppConfig.DARK_THEME = not AppConfig.DARK_THEME
        self.setStyleSheet(get_style())
    
    def _refresh_data(self):
        self.left_panel.refresh_directories()
        self.center_panel.refresh_logs()
        self.status_bar.showMessage("数据已刷新")
    
    def _setup_demo_environment(self):
        reply = QMessageBox.question(
            self, "初始化演示环境",
            "这将创建模拟文件和操作日志。是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_bar.showMessage("正在初始化演示环境...")
            try:
                result = file_simulator.setup_demo_environment()
                self._refresh_data()
                self.status_bar.showMessage(
                    f"演示环境已初始化: {len(result['files'])} 个文件, {len(result['log_ids'])} 条记录"
                )
                QMessageBox.information(
                    self, "初始化完成",
                    f"演示环境已成功创建！\n\n文件数量: {len(result['files'])}\n操作记录: {len(result['log_ids'])}\n沙盒路径: {result['sandbox_path']}"
                )
            except Exception as e:
                self.logger.error(f"初始化演示环境失败: {e}")
                QMessageBox.critical(self, "错误", f"初始化演示环境失败: {str(e)}")
    
    def _reset_demo_environment(self):
        reply = QMessageBox.question(
            self, "重置演示环境",
            "这将删除所有模拟数据。是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            file_simulator.reset_sandbox()
            self._refresh_data()
            self.status_bar.showMessage("演示环境已重置")
    
    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            f"<h3>{AppConfig.APP_NAME}</h3>"
            f"<p>版本: {AppConfig.APP_VERSION}</p>"
            f"<p>开发者: {AppConfig.APP_AUTHOR}</p>"
            f"<p>本地文件误删回溯工具</p>"
            f"<p>基于 Python + PySide6 + SQLite</p>"
        )
    
    def _on_directory_selected(self, path: str):
        self.center_panel.filter_by_path(path)
    
    def _on_timeline_filter_changed(self, start_time, end_time):
        self.center_panel.filter_by_time_range(start_time, end_time)
    
    def _on_risk_filter_changed(self, risk_levels: list):
        self.center_panel.filter_by_risk(risk_levels)
    
    def _on_log_selected(self, log_data: dict):
        self.right_panel.display_log_details(log_data)
    
    def _on_logs_selected(self, logs: list):
        pass
    
    def _on_recover_requested(self, log_id: int):
        pass
    
    def _on_version_selected(self, version_data: dict):
        pass
