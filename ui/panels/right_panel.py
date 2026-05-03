from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QTextEdit, QGroupBox,
    QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QTextCursor
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.helpers import format_file_size, format_timestamp, is_text_file
from utils.logger import get_logger

class RightPanel(QWidget):
    version_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('RightPanel')
        self.current_log = None
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        title_label = QLabel("详情与预览")
        title_label.setProperty("class", "title")
        main_layout.addWidget(title_label)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        self.preview_tab = self._create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "文件预览")
        
        self.diff_tab = self._create_diff_tab()
        self.tab_widget.addTab(self.diff_tab, "版本对比")
        
        self.history_tab = self._create_history_tab()
        self.tab_widget.addTab(self.history_tab, "历史版本")
        
        self.path_tab = self._create_path_tab()
        self.tab_widget.addTab(self.path_tab, "路径变更")
        
        main_layout.addWidget(self.tab_widget)
        
        self._show_empty_state()
    
    def _create_preview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        info_group = QGroupBox("文件信息")
        info_layout = QVBoxLayout(info_group)
        
        self.preview_info_labels = {}
        info_fields = [
            ("name", "文件名"),
            ("path", "文件路径"),
            ("size", "大小"),
            ("type", "操作类型"),
            ("risk", "风险等级"),
            ("time", "操作时间"),
        ]
        
        for key, label_text in info_fields:
            row_layout = QHBoxLayout()
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(80)
            value_label = QLabel("-")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            row_layout.addWidget(label)
            row_layout.addWidget(value_label, 1)
            info_layout.addLayout(row_layout)
            self.preview_info_labels[key] = value_label
        
        layout.addWidget(info_group)
        
        content_group = QGroupBox("内容预览")
        content_layout = QVBoxLayout(content_group)
        
        toolbar_layout = QHBoxLayout()
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["UTF-8", "GBK", "GB2312", "ISO-8859-1"])
        toolbar_layout.addWidget(QLabel("编码:"))
        toolbar_layout.addWidget(self.encoding_combo)
        
        self.refresh_preview_btn = QPushButton("刷新")
        toolbar_layout.addWidget(self.refresh_preview_btn)
        
        self.export_btn = QPushButton("导出")
        toolbar_layout.addWidget(self.export_btn)
        
        toolbar_layout.addStretch()
        content_layout.addLayout(toolbar_layout)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        self.preview_text.setLineWrapMode(QTextEdit.NoWrap)
        content_layout.addWidget(self.preview_text)
        
        layout.addWidget(content_group)
        
        return widget
    
    def _create_diff_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar_layout = QHBoxLayout()
        
        toolbar_layout.addWidget(QLabel("版本 A:"))
        self.version_a_combo = QComboBox()
        toolbar_layout.addWidget(self.version_a_combo, 1)
        
        toolbar_layout.addWidget(QLabel("版本 B:"))
        self.version_b_combo = QComboBox()
        toolbar_layout.addWidget(self.version_b_combo, 1)
        
        self.compare_btn = QPushButton("对比")
        toolbar_layout.addWidget(self.compare_btn)
        
        layout.addLayout(toolbar_layout)
        
        diff_splitter = QSplitter(Qt.Vertical)
        
        unified_group = QGroupBox("统一对比视图")
        unified_layout = QVBoxLayout(unified_group)
        self.unified_diff_text = QTextEdit()
        self.unified_diff_text.setReadOnly(True)
        self.unified_diff_text.setFont(QFont("Consolas", 10))
        unified_layout.addWidget(self.unified_diff_text)
        diff_splitter.addWidget(unified_group)
        
        side_group = QGroupBox("并排对比视图")
        side_layout = QHBoxLayout(side_group)
        
        left_diff = QWidget()
        left_layout = QVBoxLayout(left_diff)
        left_layout.addWidget(QLabel("旧版本:"))
        self.old_diff_text = QTextEdit()
        self.old_diff_text.setReadOnly(True)
        self.old_diff_text.setFont(QFont("Consolas", 10))
        left_layout.addWidget(self.old_diff_text)
        
        right_diff = QWidget()
        right_layout = QVBoxLayout(right_diff)
        right_layout.addWidget(QLabel("新版本:"))
        self.new_diff_text = QTextEdit()
        self.new_diff_text.setReadOnly(True)
        self.new_diff_text.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.new_diff_text)
        
        side_layout.addWidget(left_diff)
        side_layout.addWidget(right_diff)
        
        diff_splitter.addWidget(side_group)
        
        diff_splitter.setSizes([300, 300])
        layout.addWidget(diff_splitter)
        
        return widget
    
    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar_layout = QHBoxLayout()
        
        self.refresh_history_btn = QPushButton("刷新")
        toolbar_layout.addWidget(self.refresh_history_btn)
        
        self.restore_version_btn = QPushButton("恢复此版本")
        self.restore_version_btn.setProperty("class", "primary")
        toolbar_layout.addWidget(self.restore_version_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "版本号", "大小", "Hash", "创建时间", "状态", "操作"
        ])
        
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        
        self.history_table.setColumnWidth(0, 80)
        self.history_table.setColumnWidth(1, 100)
        self.history_table.setColumnWidth(3, 160)
        self.history_table.setColumnWidth(4, 80)
        self.history_table.setColumnWidth(5, 80)
        
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def _create_path_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        info_group = QGroupBox("路径变更记录")
        info_layout = QVBoxLayout(info_group)
        
        self.path_labels = {}
        path_fields = [
            ("original", "原始路径"),
            ("current", "当前路径"),
            ("changes", "变更次数"),
        ]
        
        for key, label_text in path_fields:
            row_layout = QHBoxLayout()
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(80)
            value_label = QLabel("-")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            value_label.setStyleSheet("font-family: Consolas;")
            row_layout.addWidget(label)
            row_layout.addWidget(value_label, 1)
            info_layout.addLayout(row_layout)
            self.path_labels[key] = value_label
        
        layout.addWidget(info_group)
        
        history_group = QGroupBox("变更历史")
        history_layout = QVBoxLayout(history_group)
        
        self.path_history_table = QTableWidget()
        self.path_history_table.setColumnCount(4)
        self.path_history_table.setHorizontalHeaderLabels([
            "序号", "操作类型", "原路径", "新路径", "时间"
        ])
        self.path_history_table.setColumnCount(5)
        
        header = self.path_history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.path_history_table.setColumnWidth(0, 50)
        self.path_history_table.setColumnWidth(1, 80)
        self.path_history_table.setColumnWidth(4, 160)
        
        self.path_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.path_history_table.setAlternatingRowColors(True)
        
        history_layout.addWidget(self.path_history_table)
        
        layout.addWidget(history_group)
        
        return widget
    
    def _show_empty_state(self):
        empty_text = """
        <div style="text-align: center; padding: 50px; color: #858585;">
            <h3>暂无选择</h3>
            <p>请从左侧选择一个监控目录<br>或从中间列表选择一条操作记录</p>
        </div>
        """
        self.preview_text.setHtml(empty_text)
        self.unified_diff_text.setHtml(empty_text)
        self.old_diff_text.setHtml(empty_text)
        self.new_diff_text.setHtml(empty_text)
        
        for key in self.preview_info_labels:
            self.preview_info_labels[key].setText("-")
        
        for key in self.path_labels:
            self.path_labels[key].setText("-")
        
        self.history_table.setRowCount(0)
        self.path_history_table.setRowCount(0)
    
    def display_log_details(self, log_data: Dict[str, Any]):
        self.current_log = log_data
        
        self._update_preview_info(log_data)
        self._update_preview_content(log_data)
        self._update_version_combos(log_data)
        self._update_history_table(log_data)
        self._update_path_info(log_data)
        
        self.logger.info(f"显示日志详情: ID={log_data.get('id')}")
    
    def _update_preview_info(self, log_data: Dict):
        self.preview_info_labels['name'].setText(log_data.get('file_name', '-'))
        self.preview_info_labels['path'].setText(log_data.get('file_path', '-'))
        self.preview_info_labels['size'].setText(format_file_size(log_data.get('file_size', 0)))
        
        op_type = log_data.get('operation_type', 'UNKNOWN')
        op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
        self.preview_info_labels['type'].setText(op_info['name'])
        
        risk_level = log_data.get('risk_level', 'LOW')
        risk_info = AppConfig.RISK_LEVELS.get(risk_level, {'name': risk_level, 'color': '#ffffff'})
        self.preview_info_labels['risk'].setText(
            f'<span style="color: {risk_info["color"]}; font-weight: bold;">{risk_info["name"]}</span>'
        )
        
        op_time = log_data.get('operation_time', 0)
        self.preview_info_labels['time'].setText(format_timestamp(op_time))
    
    def _update_preview_content(self, log_data: Dict):
        file_path = log_data.get('file_path', '')
        
        if not file_path:
            self.preview_text.setPlainText("(无文件内容可预览)")
            return
        
        import os
        if not os.path.exists(file_path):
            self.preview_text.setPlainText(f"(文件不存在: {file_path})")
            return
        
        if os.path.isdir(file_path):
            self.preview_text.setPlainText(f"(这是一个目录: {file_path})")
            return
        
        if not is_text_file(file_path):
            self.preview_text.setPlainText(f"(二进制文件，无法预览: {file_path})")
            return
        
        try:
            encoding = self.encoding_combo.currentText()
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read(50000)
            
            if len(content) >= 50000:
                content += "\n\n... (内容已截断，只显示前50000字符)"
            
            self.preview_text.setPlainText(content)
        except Exception as e:
            self.preview_text.setPlainText(f"读取文件失败: {str(e)}")
    
    def _update_version_combos(self, log_data: Dict):
        self.version_a_combo.clear()
        self.version_b_combo.clear()
        
        file_id = log_data.get('file_id')
        if file_id:
            snapshots = db_manager.get_file_snapshots(file_id)
            for snapshot in snapshots:
                version_text = f"版本 {snapshot.get('version', 1)} ({format_timestamp(snapshot.get('created_at', 0))})"
                self.version_a_combo.addItem(version_text, snapshot)
                self.version_b_combo.addItem(version_text, snapshot)
        
        if self.version_a_combo.count() > 1:
            self.version_b_combo.setCurrentIndex(1)
    
    def _update_history_table(self, log_data: Dict):
        self.history_table.setRowCount(0)
        
        file_id = log_data.get('file_id')
        if not file_id:
            return
        
        snapshots = db_manager.get_file_snapshots(file_id)
        
        self.history_table.setRowCount(len(snapshots))
        
        for row, snapshot in enumerate(snapshots):
            version_item = QTableWidgetItem(str(snapshot.get('version', 1)))
            version_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(row, 0, version_item)
            
            size_item = QTableWidgetItem(format_file_size(snapshot.get('file_size', 0)))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.history_table.setItem(row, 1, size_item)
            
            file_hash = snapshot.get('file_hash', '-')
            if file_hash and len(file_hash) > 20:
                file_hash = file_hash[:20] + "..."
            hash_item = QTableWidgetItem(file_hash)
            self.history_table.setItem(row, 2, hash_item)
            
            created_item = QTableWidgetItem(format_timestamp(snapshot.get('created_at', 0)))
            self.history_table.setItem(row, 3, created_item)
            
            is_active = snapshot.get('is_active', 1)
            status_text = "有效" if is_active else "已失效"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            if is_active:
                status_item.setForeground(QColor("#4ec9b0"))
            else:
                status_item.setForeground(QColor("#f14c4c"))
            self.history_table.setItem(row, 4, status_item)
            
            action_item = QTableWidgetItem("恢复")
            action_item.setTextAlignment(Qt.AlignCenter)
            action_item.setForeground(QColor("#007acc"))
            self.history_table.setItem(row, 5, action_item)
    
    def _update_path_info(self, log_data: Dict):
        old_path = log_data.get('old_path', '-')
        new_path = log_data.get('new_path', '-')
        
        self.path_labels['original'].setText(old_path)
        self.path_labels['current'].setText(new_path if new_path != '-' else log_data.get('file_path', '-'))
        
        file_path = log_data.get('file_path', '')
        if file_path:
            related_logs = db_manager.get_operation_logs(
                file_path=file_path,
                limit=100
            )
            
            move_rename_logs = [
                log for log in related_logs 
                if log.get('operation_type') in ['MOVE', 'RENAME']
            ]
            
            self.path_labels['changes'].setText(str(len(move_rename_logs)))
            
            self.path_history_table.setRowCount(len(move_rename_logs))
            
            for row, log in enumerate(move_rename_logs):
                seq_item = QTableWidgetItem(str(row + 1))
                seq_item.setTextAlignment(Qt.AlignCenter)
                self.path_history_table.setItem(row, 0, seq_item)
                
                op_type = log.get('operation_type', 'UNKNOWN')
                op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
                op_item = QTableWidgetItem(op_info['name'])
                op_item.setTextAlignment(Qt.AlignCenter)
                self.path_history_table.setItem(row, 1, op_item)
                
                old_p = log.get('old_path', '-')
                old_item = QTableWidgetItem(old_p)
                old_item.setForeground(QColor("#f14c4c"))
                self.path_history_table.setItem(row, 2, old_item)
                
                new_p = log.get('new_path', '-')
                new_item = QTableWidgetItem(new_p)
                new_item.setForeground(QColor("#4ec9b0"))
                self.path_history_table.setItem(row, 3, new_item)
                
                time_item = QTableWidgetItem(format_timestamp(log.get('operation_time', 0)))
                self.path_history_table.setItem(row, 4, time_item)
        else:
            self.path_labels['changes'].setText("0")
