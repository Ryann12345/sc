from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QPushButton, QComboBox,
    QCheckBox, QSplitter, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional, List, Dict, Any
from datetime import datetime
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.helpers import get_time_range
from utils.logger import get_logger

class LeftPanel(QWidget):
    directory_selected = Signal(str)
    filters_applied = Signal(dict)
    filters_reset = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('LeftPanel')
        self.selected_path = None
        self.apply_btn = None
        self.reset_btn = None
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
        
        self.clear_dir_btn = QPushButton("取消选中")
        self.clear_dir_btn.setMaximumWidth(80)
        btn_layout.addWidget(self.clear_dir_btn)
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
        
        self.apply_btn = QPushButton("应用筛选")
        self.apply_btn.setProperty("class", "primary")
        filter_layout.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("重置筛选")
        filter_layout.addWidget(self.reset_btn)
        
        splitter.addWidget(filter_group)
        
        stats_group = QGroupBox("当前筛选统计")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(6)
        
        self.stats_labels = {}
        stats_items = [
            ("total", "当前显示"),
            ("pending", "待恢复"),
            ("high_risk", "高+严重"),
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
    
    def _connect_signals(self):
        self.directory_tree.itemClicked.connect(self._on_directory_clicked)
        self.search_input.textChanged.connect(self._filter_directories)
        self.refresh_dirs_btn.clicked.connect(self.refresh_directories)
        self.clear_dir_btn.clicked.connect(self._clear_directory_selection)
        
        if self.apply_btn:
            self.apply_btn.clicked.connect(self._apply_filters)
        
        if self.reset_btn:
            self.reset_btn.clicked.connect(self._reset_filters)
    
    def _load_directories(self):
        self.directory_tree.clear()
        
        all_item = QTreeWidgetItem(self.directory_tree)
        all_item.setText(0, "全部目录")
        all_item.setText(1, "")
        all_item.setText(2, "默认")
        all_item.setData(0, Qt.UserRole, None)
        all_item.setForeground(0, QColor("#d4d4d4"))
        all_item.setSelected(True)
        
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
        self.selected_path = path
        self.logger.info(f"选中目录: {path if path else '全部目录'}")
    
    def _clear_directory_selection(self):
        for i in range(self.directory_tree.topLevelItemCount()):
            item = self.directory_tree.topLevelItem(i)
            item.setSelected(False)
        
        for i in range(self.directory_tree.topLevelItemCount()):
            item = self.directory_tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) is None:
                item.setSelected(True)
                break
        
        self.selected_path = None
    
    def _apply_filters(self):
        filters = self.get_all_filters()
        self.logger.info(f"应用筛选条件: {filters}")
        self.filters_applied.emit(filters)
    
    def _reset_filters(self):
        self.time_combo.setCurrentIndex(len(AppConfig.TIMELINE_INTERVALS) - 1)
        
        for checkbox in self.risk_checkboxes.values():
            checkbox.setChecked(True)
        
        for checkbox in self.op_checkboxes.values():
            checkbox.setChecked(True)
        
        self._clear_directory_selection()
        
        self.logger.info("重置筛选条件")
        self.filters_reset.emit()
    
    def get_all_filters(self) -> Dict[str, Any]:
        time_index = self.time_combo.currentIndex()
        seconds = self.time_combo.itemData(time_index)
        start_time, end_time = get_time_range(seconds)
        
        return {
            'path': self.selected_path,
            'start_time': start_time.timestamp() if start_time else None,
            'end_time': end_time.timestamp() if end_time else None,
            'risk_levels': [level for level, cb in self.risk_checkboxes.items() if cb.isChecked()],
            'operation_types': [op for op, cb in self.op_checkboxes.items() if cb.isChecked()]
        }
    
    def update_statistics(self, logs: List[Dict]):
        total = len(logs)
        
        pending = sum(1 for l in logs if not l.get('is_recovered', 0))
        
        high_risk = sum(
            1 for l in logs 
            if l.get('risk_level') in ['HIGH', 'CRITICAL']
        )
        
        self.stats_labels['total'].setText(str(total))
        self.stats_labels['pending'].setText(str(pending))
        self.stats_labels['high_risk'].setText(str(high_risk))
    
    def refresh_directories(self):
        self._load_directories()
        self.logger.info("目录列表已刷新")
