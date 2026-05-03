from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QPushButton, QComboBox,
    QCheckBox, QSplitter, QLineEdit,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
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
        main_layout.setSpacing(10)
        
        title_label = QLabel("监控与筛选")
        title_label.setProperty("class", "title")
        title_label.setMinimumHeight(28)
        main_layout.addWidget(title_label)
        
        search_group = QGroupBox("关键词搜索")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(6)
        
        keyword_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入文件名、路径或描述关键词...")
        self.keyword_input.setMinimumHeight(28)
        keyword_layout.addWidget(self.keyword_input)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMaximumWidth(60)
        self.search_btn.setMinimumHeight(28)
        keyword_layout.addWidget(self.search_btn)
        
        search_layout.addLayout(keyword_layout)
        
        search_tip = QLabel("提示: 可在筛选后使用关键词进一步过滤")
        search_tip.setStyleSheet("color: #858585; font-size: 12px;")
        search_layout.addWidget(search_tip)
        
        main_layout.addWidget(search_group)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        directory_group = QGroupBox("监控目录")
        directory_layout = QVBoxLayout(directory_group)
        directory_layout.setSpacing(6)
        
        dir_search_layout = QHBoxLayout()
        self.dir_search_input = QLineEdit()
        self.dir_search_input.setPlaceholderText("搜索目录...")
        self.dir_search_input.setMinimumHeight(26)
        dir_search_layout.addWidget(self.dir_search_input)
        directory_layout.addLayout(dir_search_layout)
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels(["名称", "路径", "状态"])
        self.directory_tree.setColumnWidth(0, 130)
        self.directory_tree.setColumnWidth(1, 200)
        self.directory_tree.setColumnWidth(2, 60)
        self.directory_tree.setAlternatingRowColors(True)
        self.directory_tree.setMinimumHeight(180)
        self.directory_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        font = QFont()
        font.setPointSize(12)
        self.directory_tree.setFont(font)
        self.directory_tree.setStyleSheet("""
            QTreeView::item {
                padding: 8px;
                min-height: 26px;
            }
            QTreeView::item:selected {
                background-color: #094771;
            }
            QTreeView::item:hover {
                background-color: #2a2d2e;
            }
            QHeaderView::section {
                padding: 10px;
                min-height: 30px;
                font-size: 12px;
            }
        """)
        directory_layout.addWidget(self.directory_tree)
        
        btn_layout = QHBoxLayout()
        self.refresh_dirs_btn = QPushButton("刷新")
        self.refresh_dirs_btn.setMaximumWidth(60)
        self.refresh_dirs_btn.setMinimumHeight(28)
        btn_layout.addWidget(self.refresh_dirs_btn)
        
        self.clear_dir_btn = QPushButton("取消选中")
        self.clear_dir_btn.setMaximumWidth(80)
        self.clear_dir_btn.setMinimumHeight(28)
        btn_layout.addWidget(self.clear_dir_btn)
        btn_layout.addStretch()
        directory_layout.addLayout(btn_layout)
        
        splitter.addWidget(directory_group)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        
        time_label = QLabel("时间范围:")
        time_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        filter_layout.addWidget(time_label)
        
        self.time_combo = QComboBox()
        self.time_combo.setMinimumHeight(30)
        self.time_combo.setStyleSheet("font-size: 13px; padding: 6px 10px;")
        for label, seconds in AppConfig.TIMELINE_INTERVALS:
            self.time_combo.addItem(label, seconds)
        filter_layout.addWidget(self.time_combo)
        
        risk_label = QLabel("风险等级:")
        risk_label.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 8px;")
        filter_layout.addWidget(risk_label)
        
        risk_layout = QVBoxLayout()
        risk_layout.setSpacing(8)
        self.risk_checkboxes = {}
        
        for level, info in AppConfig.RISK_LEVELS.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            checkbox.setMinimumHeight(24)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {info['color']};
                    font-weight: bold;
                    font-size: 13px;
                    spacing: 10px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                }}
            """)
            self.risk_checkboxes[level] = checkbox
            risk_layout.addWidget(checkbox)
        
        filter_layout.addLayout(risk_layout)
        
        op_label = QLabel("操作类型:")
        op_label.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 8px;")
        filter_layout.addWidget(op_label)
        
        op_layout = QVBoxLayout()
        op_layout.setSpacing(8)
        self.op_checkboxes = {}
        
        for op_type, info in AppConfig.OPERATION_TYPES.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            checkbox.setMinimumHeight(24)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #d4d4d4;
                    font-size: 13px;
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                }
            """)
            self.op_checkboxes[op_type] = checkbox
            op_layout.addWidget(checkbox)
        
        filter_layout.addLayout(op_layout)
        
        filter_layout.addStretch()
        
        btn_container = QVBoxLayout()
        btn_container.setSpacing(8)
        
        self.apply_btn = QPushButton("应用筛选")
        self.apply_btn.setProperty("class", "primary")
        self.apply_btn.setMinimumHeight(32)
        self.apply_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        btn_container.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("重置筛选")
        self.reset_btn.setMinimumHeight(32)
        self.reset_btn.setStyleSheet("font-size: 13px;")
        btn_container.addWidget(self.reset_btn)
        
        filter_layout.addLayout(btn_container)
        
        splitter.addWidget(filter_group)
        
        stats_group = QGroupBox("当前筛选统计")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(8)
        
        self.stats_labels = {}
        stats_items = [
            ("total", "当前显示"),
            ("pending", "待恢复"),
            ("high_risk", "高+严重"),
        ]
        
        for key, label_text in stats_items:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-size: 13px;")
            label.setMinimumWidth(70)
            value_label = QLabel("0")
            value_label.setStyleSheet("font-size: 13px; font-weight: bold;")
            value_label.setMinimumWidth(50)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(value_label)
            stats_layout.addLayout(row_layout)
            self.stats_labels[key] = value_label
        
        splitter.addWidget(stats_group)
        
        splitter.setSizes([280, 350, 120])
        main_layout.addWidget(splitter)
        
        self._load_directories()
    
    def _connect_signals(self):
        self.directory_tree.itemClicked.connect(self._on_directory_clicked)
        self.directory_tree.itemSelectionChanged.connect(self._on_directory_selection_changed)
        self.dir_search_input.textChanged.connect(self._filter_directories)
        self.refresh_dirs_btn.clicked.connect(self.refresh_directories)
        self.clear_dir_btn.clicked.connect(self._clear_directory_selection)
        
        self.search_btn.clicked.connect(self._on_keyword_search)
        self.keyword_input.returnPressed.connect(self._on_keyword_search)
        
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
    
    def _on_directory_selection_changed(self):
        selected_items = self.directory_tree.selectedItems()
        if selected_items:
            path = selected_items[0].data(0, Qt.UserRole)
            self.selected_path = path
    
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
    
    def _on_keyword_search(self):
        self._apply_filters()
    
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
        
        self.keyword_input.clear()
        
        self._clear_directory_selection()
        
        self.logger.info("重置筛选条件")
        self.filters_reset.emit()
    
    def get_all_filters(self) -> Dict[str, Any]:
        time_index = self.time_combo.currentIndex()
        seconds = self.time_combo.itemData(time_index)
        start_time, end_time = get_time_range(seconds)
        
        risk_levels = [level for level, cb in self.risk_checkboxes.items() if cb.isChecked()]
        operation_types = [op for op, cb in self.op_checkboxes.items() if cb.isChecked()]
        
        keyword = self.keyword_input.text().strip()
        
        return {
            'path': self.selected_path,
            'start_time': start_time.timestamp() if start_time else None,
            'end_time': end_time.timestamp() if end_time else None,
            'risk_levels': risk_levels,
            'operation_types': operation_types,
            'keyword': keyword if keyword else None
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
