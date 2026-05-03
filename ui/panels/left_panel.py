from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QPushButton, QComboBox,
    QCheckBox, QFrame, QSplitter, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from typing import Optional, List
from datetime import datetime
from config.app_config import AppConfig
from database.db_manager import db_manager
from sandbox.file_simulator import file_simulator
from utils.helpers import format_file_size, get_time_range
from utils.logger import get_logger

class LeftPanel(QWidget):
    directory_selected = Signal(str)
    timeline_filter_changed = Signal(object, object)
    risk_filter_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('LeftPanel')
        self.selected_path = None
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        title_label = QLabel("监控与筛选")
        title_label.setProperty("class", "title")
        main_layout.addWidget(title_label)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        directory_group = QGroupBox("监控目录")
        directory_layout = QVBoxLayout(directory_group)
        directory_layout.setSpacing(4)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索目录...")
        search_layout.addWidget(self.search_input)
        directory_layout.addLayout(search_layout)
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels(["名称", "路径", "状态"])
        self.directory_tree.setColumnWidth(0, 150)
        self.directory_tree.setColumnWidth(1, 200)
        self.directory_tree.setColumnWidth(2, 60)
        self.directory_tree.setAlternatingRowColors(True)
        directory_layout.addWidget(self.directory_tree)
        
        btn_layout = QHBoxLayout()
        self.refresh_dirs_btn = QPushButton("刷新")
        self.refresh_dirs_btn.setMaximumWidth(80)
        btn_layout.addWidget(self.refresh_dirs_btn)
        btn_layout.addStretch()
        directory_layout.addLayout(btn_layout)
        
        splitter.addWidget(directory_group)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(10)
        
        time_label = QLabel("时间范围:")
        filter_layout.addWidget(time_label)
        
        self.time_combo = QComboBox()
        for label, seconds in AppConfig.TIMELINE_INTERVALS:
            self.time_combo.addItem(label, seconds)
        filter_layout.addWidget(self.time_combo)
        
        risk_label = QLabel("风险等级:")
        filter_layout.addWidget(risk_label)
        
        risk_layout = QVBoxLayout()
        self.risk_checkboxes = {}
        
        for level, info in AppConfig.RISK_LEVELS.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"color: {info['color']}; font-weight: bold;")
            self.risk_checkboxes[level] = checkbox
            risk_layout.addWidget(checkbox)
        
        filter_layout.addLayout(risk_layout)
        
        op_label = QLabel("操作类型:")
        filter_layout.addWidget(op_label)
        
        op_layout = QVBoxLayout()
        self.op_checkboxes = {}
        
        for op_type, info in AppConfig.OPERATION_TYPES.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            self.op_checkboxes[op_type] = checkbox
            op_layout.addWidget(checkbox)
        
        filter_layout.addLayout(op_layout)
        
        filter_layout.addStretch()
        
        apply_btn = QPushButton("应用筛选")
        apply_btn.setProperty("class", "primary")
        filter_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("重置筛选")
        filter_layout.addWidget(reset_btn)
        
        splitter.addWidget(filter_group)
        
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(6)
        
        self.stats_labels = {}
        stats_items = [
            ("total", "总操作数"),
            ("pending", "待恢复"),
            ("high_risk", "高风险"),
        ]
        
        for key, label_text in stats_items:
            row_layout = QHBoxLayout()
            label = QLabel(f"{label_text}:")
            value_label = QLabel("0")
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(value_label)
            stats_layout.addLayout(row_layout)
            self.stats_labels[key] = value_label
        
        splitter.addWidget(stats_group)
        
        splitter.setSizes([300, 300, 150])
        main_layout.addWidget(splitter)
        
        self._load_directories()
        self._update_statistics()
    
    def _connect_signals(self):
        self.directory_tree.itemClicked.connect(self._on_directory_clicked)
        self.search_input.textChanged.connect(self._filter_directories)
        self.refresh_dirs_btn.clicked.connect(self.refresh_directories)
        self.time_combo.currentIndexChanged.connect(self._on_time_filter_changed)
        
        for checkbox in self.risk_checkboxes.values():
            checkbox.stateChanged.connect(self._on_risk_filter_changed)
        
        for checkbox in self.op_checkboxes.values():
            checkbox.stateChanged.connect(self._on_op_filter_changed)
    
    def _load_directories(self):
        self.directory_tree.clear()
        
        sandbox_item = QTreeWidgetItem(self.directory_tree)
        sandbox_item.setText(0, "沙盒环境")
        sandbox_item.setText(1, str(AppConfig.SANDBOX_DIR))
        sandbox_item.setText(2, "激活")
        sandbox_item.setData(0, Qt.UserRole, str(AppConfig.SANDBOX_DIR))
        sandbox_item.setForeground(0, QColor("#4ec9b0"))
        
        monitored_paths = db_manager.get_monitored_paths(active_only=True)
        for path_info in monitored_paths:
            path = path_info['path']
            if path == str(AppConfig.SANDBOX_DIR):
                continue
            
            item = QTreeWidgetItem(self.directory_tree)
            item.setText(0, path.split('\\')[-1] or path)
            item.setText(1, path)
            item.setText(2, "激活" if path_info['is_active'] else "禁用")
            item.setData(0, Qt.UserRole, path)
        
        monitored_paths = db_manager.get_monitored_paths(active_only=True)
        for path_info in monitored_paths:
            path = path_info['path']
            if path == str(AppConfig.SANDBOX_DIR):
                continue
            
            item = QTreeWidgetItem(self.directory_tree)
            item.setText(0, path.split('\\')[-1] or path)
            item.setText(1, path)
            item.setText(2, "激活" if path_info['is_active'] else "禁用")
            item.setData(0, Qt.UserRole, path)
        
        self.directory_tree.expandAll()
    
    def _filter_directories(self, text: str):
        for i in range(self.directory_tree.topLevelItemCount()):
            item = self.directory_tree.topLevelItem(i)
            if not text or text.lower() in item.text(0).lower() or text.lower() in item.text(1).lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _on_directory_clicked(self, item: QTreeWidgetItem, column: int):
        path = item.data(0, Qt.UserRole)
        if path:
            self.selected_path = path
            self.directory_selected.emit(path)
            self.logger.info(f"选中目录: {path}")
    
    def _on_time_filter_changed(self, index: int):
        seconds = self.time_combo.itemData(index)
        start_time, end_time = get_time_range(seconds)
        self.timeline_filter_changed.emit(start_time, end_time)
    
    def _on_risk_filter_changed(self, state):
        selected_risks = [level for level, cb in self.risk_checkboxes.items() if cb.isChecked()]
        self.risk_filter_changed.emit(selected_risks)
    
    def _on_op_filter_changed(self, state):
        pass
    
    def _update_statistics(self):
        stats = db_manager.get_statistics()
        
        self.stats_labels['total'].setText(str(stats.get('total_operations', 0)))
        self.stats_labels['pending'].setText(str(stats.get('pending_recovery', 0)))
        
        risk_dist = stats.get('risk_distribution', {})
        high_risk = risk_dist.get('HIGH', 0) + risk_dist.get('CRITICAL', 0)
        self.stats_labels['high_risk'].setText(str(high_risk))
        
        QTimer.singleShot(5000, self._update_statistics)
    
    def refresh_directories(self):
        self._load_directories()
        self._update_statistics()
        self.logger.info("目录列表已刷新")
    
    def get_selected_path(self) -> Optional[str]:
        return self.selected_path
    
    def get_time_filter(self) -> tuple:
        index = self.time_combo.currentIndex()
        seconds = self.time_combo.itemData(index)
        return get_time_range(seconds)
    
    def get_risk_filter(self) -> List[str]:
        return [level for level, cb in self.risk_checkboxes.items() if cb.isChecked()]
    
    def get_operation_filter(self) -> List[str]:
        return [op for op, cb in self.op_checkboxes.items() if cb.isChecked()]
