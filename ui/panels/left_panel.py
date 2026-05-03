from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QPushButton, QComboBox,
    QCheckBox, QSplitter, QLineEdit,
    QFrame, QSizePolicy, QScrollArea, QGridLayout
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
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)
        
        title_label = QLabel("监控与筛选")
        title_label.setProperty("class", "title")
        title_label.setMinimumHeight(30)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        main_layout.addWidget(title_label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(2, 2, 2, 2)
        scroll_layout.setSpacing(10)
        
        search_card = self._create_search_card()
        scroll_layout.addWidget(search_card)
        
        directory_card = self._create_directory_card()
        scroll_layout.addWidget(directory_card, 1)
        
        filter_card = self._create_filter_card()
        scroll_layout.addWidget(filter_card)
        
        stats_card = self._create_stats_card()
        scroll_layout.addWidget(stats_card)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        self._load_directories()
    
    def _create_search_card(self) -> QGroupBox:
        card = QGroupBox("关键词搜索")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #252526;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                background-color: #252526;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(8)
        
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入文件名、路径或描述关键词...")
        self.keyword_input.setMinimumHeight(32)
        self.keyword_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
        search_row.addWidget(self.keyword_input)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumWidth(60)
        self.search_btn.setMinimumHeight(32)
        self.search_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        search_row.addWidget(self.search_btn)
        
        layout.addLayout(search_row)
        
        tip_label = QLabel("提示: 可在筛选后使用关键词进一步过滤")
        tip_label.setStyleSheet("color: #858585; font-size: 11px;")
        layout.addWidget(tip_label)
        
        return card
    
    def _create_directory_card(self) -> QGroupBox:
        card = QGroupBox("监控目录")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #252526;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                background-color: #252526;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card.setMinimumHeight(180)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(8)
        
        dir_search_row = QHBoxLayout()
        dir_search_row.setSpacing(8)
        
        self.dir_search_input = QLineEdit()
        self.dir_search_input.setPlaceholderText("搜索目录...")
        self.dir_search_input.setMinimumHeight(28)
        self.dir_search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 12px;
            }
        """)
        dir_search_row.addWidget(self.dir_search_input)
        
        layout.addLayout(dir_search_row)
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels(["名称", "路径", "状态"])
        self.directory_tree.setColumnWidth(0, 140)
        self.directory_tree.setColumnWidth(1, 180)
        self.directory_tree.setColumnWidth(2, 60)
        self.directory_tree.setAlternatingRowColors(True)
        self.directory_tree.setMinimumHeight(120)
        self.directory_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        font = QFont()
        font.setPointSize(12)
        self.directory_tree.setFont(font)
        self.directory_tree.setStyleSheet("""
            QTreeView {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                color: #d4d4d4;
                gridline-color: #3c3c3c;
            }
            QTreeView::item {
                padding: 10px 6px;
                min-height: 28px;
                font-size: 12px;
            }
            QTreeView::item:selected {
                background-color: #094771;
            }
            QTreeView::item:hover {
                background-color: #2a2d2e;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                border: none;
                border-bottom: 1px solid #555555;
                padding: 10px 6px;
                font-weight: bold;
                color: #d4d4d4;
                font-size: 12px;
                min-height: 32px;
            }
            QHeaderView::section:hover {
                background-color: #4a4a4a;
            }
        """)
        layout.addWidget(self.directory_tree)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.refresh_dirs_btn = QPushButton("刷新")
        self.refresh_dirs_btn.setMinimumWidth(60)
        self.refresh_dirs_btn.setMinimumHeight(28)
        self.refresh_dirs_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        btn_row.addWidget(self.refresh_dirs_btn)
        
        self.clear_dir_btn = QPushButton("取消选中")
        self.clear_dir_btn.setMinimumWidth(80)
        self.clear_dir_btn.setMinimumHeight(28)
        self.clear_dir_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        btn_row.addWidget(self.clear_dir_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        return card
    
    def _create_filter_card(self) -> QGroupBox:
        card = QGroupBox("筛选条件")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #252526;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                background-color: #252526;
            }
        """)
        card.setMinimumHeight(200)
        
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        filter_scroll.setFrameShape(QFrame.NoFrame)
        filter_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                min-height: 25px;
                border-radius: 5px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
        """)
        
        filter_content = QWidget()
        filter_content.setStyleSheet("background-color: transparent;")
        filter_layout = QVBoxLayout(filter_content)
        filter_layout.setContentsMargins(12, 18, 12, 12)
        filter_layout.setSpacing(12)
        
        time_label = QLabel("时间范围:")
        time_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #d4d4d4;")
        filter_layout.addWidget(time_label)
        
        self.time_combo = QComboBox()
        self.time_combo.setMinimumHeight(32)
        self.time_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 13px;
                min-height: 32px;
            }
            QComboBox:hover {
                border-color: #666666;
            }
            QComboBox:focus {
                border-color: #007acc;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #252526;
                border: 1px solid #555555;
                selection-background-color: #094771;
                font-size: 13px;
            }
        """)
        for label, seconds in AppConfig.TIMELINE_INTERVALS:
            self.time_combo.addItem(label, seconds)
        filter_layout.addWidget(self.time_combo)
        
        risk_section_label = QLabel("风险等级:")
        risk_section_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #d4d4d4; margin-top: 6px;")
        filter_layout.addWidget(risk_section_label)
        
        risk_container = QWidget()
        risk_container.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 8px;")
        risk_grid = QGridLayout(risk_container)
        risk_grid.setContentsMargins(10, 10, 10, 10)
        risk_grid.setSpacing(12)
        
        self.risk_checkboxes = {}
        risk_row = 0
        risk_col = 0
        
        for level, info in AppConfig.RISK_LEVELS.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            checkbox.setMinimumHeight(26)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {info['color']};
                    font-weight: bold;
                    font-size: 13px;
                    spacing: 10px;
                    padding: 4px 0;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    background-color: #3c3c3c;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {info['color']};
                    border-color: {info['color']};
                }}
                QCheckBox::indicator:hover {{
                    border-color: #666666;
                }}
            """)
            self.risk_checkboxes[level] = checkbox
            
            risk_grid.addWidget(checkbox, risk_row, risk_col)
            risk_col += 1
            if risk_col >= 2:
                risk_col = 0
                risk_row += 1
        
        filter_layout.addWidget(risk_container)
        
        op_section_label = QLabel("操作类型:")
        op_section_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #d4d4d4; margin-top: 6px;")
        filter_layout.addWidget(op_section_label)
        
        op_container = QWidget()
        op_container.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 8px;")
        op_grid = QGridLayout(op_container)
        op_grid.setContentsMargins(10, 10, 10, 10)
        op_grid.setSpacing(12)
        
        self.op_checkboxes = {}
        op_row = 0
        op_col = 0
        
        for op_type, info in AppConfig.OPERATION_TYPES.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            checkbox.setMinimumHeight(26)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #d4d4d4;
                    font-size: 13px;
                    spacing: 10px;
                    padding: 4px 0;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    background-color: #3c3c3c;
                }
                QCheckBox::indicator:checked {
                    background-color: #007acc;
                    border-color: #007acc;
                }
                QCheckBox::indicator:hover {
                    border-color: #666666;
                }
            """)
            self.op_checkboxes[op_type] = checkbox
            
            op_grid.addWidget(checkbox, op_row, op_col)
            op_col += 1
            if op_col >= 2:
                op_col = 0
                op_row += 1
        
        filter_layout.addWidget(op_container)
        
        filter_layout.addStretch()
        
        filter_scroll.setWidget(filter_content)
        main_layout.addWidget(filter_scroll)
        
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: #252526; border-top: 1px solid #3c3c3c;")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(12, 10, 12, 12)
        btn_layout.setSpacing(8)
        
        self.apply_btn = QPushButton("应用筛选")
        self.apply_btn.setProperty("class", "primary")
        self.apply_btn.setMinimumHeight(34)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #1177bb;
                border-radius: 4px;
                background-color: #0e639c;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5580;
            }
        """)
        btn_layout.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("重置筛选")
        self.reset_btn.setMinimumHeight(34)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        btn_layout.addWidget(self.reset_btn)
        
        main_layout.addWidget(btn_container)
        
        return card
    
    def _create_stats_card(self) -> QGroupBox:
        card = QGroupBox("当前筛选统计")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #252526;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                background-color: #252526;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(10)
        
        self.stats_labels = {}
        stats_items = [
            ("total", "当前显示", "#007acc"),
            ("pending", "待恢复", "#ff9800"),
            ("high_risk", "高+严重", "#f14c4c"),
        ]
        
        for key, label_text, color in stats_items:
            row_container = QWidget()
            row_container.setStyleSheet("background-color: #1e1e1e; border-radius: 4px;")
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(8)
            
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-size: 13px; color: #d4d4d4;")
            label.setMinimumWidth(70)
            
            value_label = QLabel("0")
            value_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
            value_label.setMinimumWidth(50)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(value_label)
            
            layout.addWidget(row_container)
            self.stats_labels[key] = value_label
        
        return card
    
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
