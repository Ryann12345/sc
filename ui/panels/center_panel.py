from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QPushButton, QHeaderView,
    QMessageBox, QDialog, QCheckBox,
    QProgressBar, QSplitter, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QFont, QColor, QCursor
from typing import Optional, List, Dict, Any
from datetime import datetime
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.helpers import format_file_size, format_timestamp
from utils.logger import get_logger

class CenterPanel(QWidget):
    log_selected = Signal(dict)
    logs_selected = Signal(list)
    recover_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('CenterPanel')
        self.current_logs = []
        self.selected_log_ids = []
        self.filters = {
            'path': None,
            'start_time': None,
            'end_time': None,
            'risk_levels': None
        }
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("操作日志")
        title_label.setProperty("class", "title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.stats_label = QLabel("0 条记录")
        header_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(header_layout)
        
        toolbar_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.select_all_btn = QPushButton("全选")
        toolbar_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("取消全选")
        toolbar_layout.addWidget(self.deselect_all_btn)
        
        toolbar_layout.addStretch()
        
        self.recover_btn = QPushButton("恢复选中")
        self.recover_btn.setProperty("class", "primary")
        toolbar_layout.addWidget(self.recover_btn)
        
        self.batch_recover_btn = QPushButton("批量恢复")
        self.batch_recover_btn.setProperty("class", "success")
        toolbar_layout.addWidget(self.batch_recover_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(9)
        self.log_table.setHorizontalHeaderLabels([
            "选择", "操作类型", "文件名", "风险等级", "影响大小",
            "大小", "操作时间", "状态", "详情"
        ])
        
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        header.setSectionResizeMode(8, QHeaderView.Fixed)
        
        self.log_table.setColumnWidth(0, 40)
        self.log_table.setColumnWidth(1, 80)
        self.log_table.setColumnWidth(3, 80)
        self.log_table.setColumnWidth(4, 80)
        self.log_table.setColumnWidth(5, 100)
        self.log_table.setColumnWidth(6, 160)
        self.log_table.setColumnWidth(7, 80)
        self.log_table.setColumnWidth(8, 60)
        
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSortingEnabled(True)
        self.log_table.verticalHeader().setDefaultSectionSize(28)
        
        self.log_table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        main_layout.addWidget(self.log_table)
        
        self._refresh_logs()
    
    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self._refresh_logs)
        self.select_all_btn.clicked.connect(self.select_all_logs)
        self.deselect_all_btn.clicked.connect(self.deselect_all_logs)
        self.recover_btn.clicked.connect(self.recover_selected)
        self.batch_recover_btn.clicked.connect(self.show_batch_recover_dialog)
        self.log_table.itemClicked.connect(self._on_item_clicked)
        self.log_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.log_table.customContextMenuRequested.connect(self._show_context_menu)
        self.log_table.cellClicked.connect(self._on_cell_clicked)
    
    def _refresh_logs(self):
        logs = db_manager.get_operation_logs(
            file_path=self.filters.get('path'),
            start_time=self.filters.get('start_time'),
            end_time=self.filters.get('end_time'),
            limit=1000
        )
        
        self.current_logs = logs
        self._populate_table(logs)
        self.stats_label.setText(f"{len(logs)} 条记录")
        self.logger.info(f"加载了 {len(logs)} 条操作日志")
    
    def _populate_table(self, logs: List[Dict]):
        self.log_table.setRowCount(0)
        self.log_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.log_table.setCellWidget(row, 0, checkbox_widget)
            
            op_type = log.get('operation_type', 'UNKNOWN')
            op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
            op_item = QTableWidgetItem(op_info['name'])
            op_item.setData(Qt.UserRole, log['id'])
            self.log_table.setItem(row, 1, op_item)
            
            name_item = QTableWidgetItem(log.get('file_name', ''))
            name_item.setToolTip(log.get('file_path', ''))
            self.log_table.setItem(row, 2, name_item)
            
            risk_level = log.get('risk_level', 'LOW')
            risk_info = AppConfig.RISK_LEVELS.get(risk_level, {'name': risk_level, 'color': '#ffffff'})
            risk_item = QTableWidgetItem(risk_info['name'])
            risk_item.setForeground(QColor(risk_info['color']))
            risk_item.setTextAlignment(Qt.AlignCenter)
            self.log_table.setItem(row, 3, risk_item)
            
            impact_score = log.get('impact_score', 0)
            impact_item = QTableWidgetItem(str(impact_score))
            impact_item.setTextAlignment(Qt.AlignCenter)
            self.log_table.setItem(row, 4, impact_item)
            
            size = log.get('file_size', 0)
            size_item = QTableWidgetItem(format_file_size(size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.log_table.setItem(row, 5, size_item)
            
            op_time = log.get('operation_time', 0)
            time_item = QTableWidgetItem(format_timestamp(op_time))
            self.log_table.setItem(row, 6, time_item)
            
            is_recovered = log.get('is_recovered', 0)
            status_text = "已恢复" if is_recovered else "待恢复"
            status_item = QTableWidgetItem(status_text)
            if is_recovered:
                status_item.setForeground(QColor("#4ec9b0"))
            else:
                status_item.setForeground(QColor("#f14c4c"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.log_table.setItem(row, 7, status_item)
            
            detail_item = QTableWidgetItem("查看")
            detail_item.setTextAlignment(Qt.AlignCenter)
            detail_item.setForeground(QColor("#007acc"))
            self.log_table.setItem(row, 8, detail_item)
    
    def _on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        if row < len(self.current_logs):
            log_data = self.current_logs[row]
            self.log_selected.emit(log_data)
    
    def _on_cell_clicked(self, row: int, column: int):
        if column == 8 and row < len(self.current_logs):
            log_data = self.current_logs[row]
            self._show_log_details(log_data)
    
    def _on_selection_changed(self):
        selected_rows = self.log_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self.current_logs):
                log_data = self.current_logs[row]
                self.log_selected.emit(log_data)
    
    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        recover_action = QAction("恢复此项", self)
        recover_action.triggered.connect(self._context_recover)
        menu.addAction(recover_action)
        
        menu.addSeparator()
        
        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self.select_all_logs)
        menu.addAction(select_all_action)
        
        deselect_all_action = QAction("取消全选", self)
        deselect_all_action.triggered.connect(self.deselect_all_logs)
        menu.addAction(deselect_all_action)
        
        menu.addSeparator()
        
        details_action = QAction("查看详情", self)
        details_action.triggered.connect(self._context_show_details)
        menu.addAction(details_action)
        
        menu.exec(self.log_table.viewport().mapToGlobal(pos))
    
    def _context_recover(self):
        current_row = self.log_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_logs):
            log_data = self.current_logs[current_row]
            self._recover_log(log_data)
    
    def _context_show_details(self):
        current_row = self.log_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_logs):
            log_data = self.current_logs[current_row]
            self._show_log_details(log_data)
    
    def _show_log_details(self, log_data: Dict):
        dialog = QDialog(self)
        dialog.setWindowTitle("操作详情")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        details = [
            ("操作ID", str(log_data.get('id', 'N/A'))),
            ("操作类型", AppConfig.OPERATION_TYPES.get(
                log_data.get('operation_type', 'UNKNOWN'), 
                {'name': 'UNKNOWN'}
            )['name']),
            ("文件名", log_data.get('file_name', 'N/A')),
            ("文件路径", log_data.get('file_path', 'N/A')),
            ("文件大小", format_file_size(log_data.get('file_size', 0))),
            ("风险等级", AppConfig.RISK_LEVELS.get(
                log_data.get('risk_level', 'LOW'),
                {'name': 'LOW'}
            )['name']),
            ("影响分数", str(log_data.get('impact_score', 0))),
            ("是否有备份", "是" if log_data.get('has_backup') else "否"),
            ("操作时间", format_timestamp(log_data.get('operation_time', 0))),
            ("状态", "已恢复" if log_data.get('is_recovered') else "待恢复"),
            ("描述", log_data.get('description', 'N/A')),
        ]
        
        for label_text, value_text in details:
            row_layout = QHBoxLayout()
            label = QLabel(f"<b>{label_text}:</b>")
            label.setMinimumWidth(100)
            value = QLabel(str(value_text))
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row_layout.addWidget(label)
            row_layout.addWidget(value, 1)
            layout.addLayout(row_layout)
        
        if log_data.get('old_path') and log_data.get('new_path'):
            old_label = QLabel(f"<b>原路径:</b>")
            old_value = QLabel(log_data.get('old_path', ''))
            old_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(old_label)
            layout.addWidget(old_value)
            
            new_label = QLabel(f"<b>新路径:</b>")
            new_value = QLabel(log_data.get('new_path', ''))
            new_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(new_label)
            layout.addWidget(new_value)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        if not log_data.get('is_recovered'):
            recover_btn = QPushButton("恢复")
            recover_btn.setProperty("class", "primary")
            recover_btn.clicked.connect(lambda: self._recover_log_dialog(log_data, dialog))
            btn_layout.addWidget(recover_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _recover_log_dialog(self, log_data: Dict, dialog: QDialog):
        if self._recover_log(log_data):
            dialog.accept()
    
    def _recover_log(self, log_data: Dict) -> bool:
        if log_data.get('is_recovered'):
            QMessageBox.information(self, "提示", "该文件已经恢复过了")
            return False
        
        op_type = log_data.get('operation_type')
        file_name = log_data.get('file_name')
        
        reply = QMessageBox.question(
            self, "确认恢复",
            f"确定要恢复以下文件吗？\n\n文件名: {file_name}\n操作类型: {op_type}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db_manager.mark_log_recovered(log_data['id'], recovered=True)
            self._refresh_logs()
            self.logger.info(f"已恢复日志 ID: {log_data['id']}")
            QMessageBox.information(self, "恢复成功", f"文件 {file_name} 已成功恢复！")
            return True
        
        return False
    
    def filter_by_path(self, path: str):
        self.filters['path'] = path
        self._refresh_logs()
    
    def filter_by_time_range(self, start_time, end_time):
        if start_time:
            self.filters['start_time'] = start_time.timestamp()
        else:
            self.filters['start_time'] = None
        
        if end_time:
            self.filters['end_time'] = end_time.timestamp()
        else:
            self.filters['end_time'] = None
        
        self._refresh_logs()
    
    def filter_by_risk(self, risk_levels: List[str]):
        self.filters['risk_levels'] = risk_levels
        self._refresh_logs()
    
    def select_all_logs(self):
        for row in range(self.log_table.rowCount()):
            widget = self.log_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def deselect_all_logs(self):
        for row in range(self.log_table.rowCount()):
            widget = self.log_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def get_selected_logs(self) -> List[Dict]:
        selected = []
        for row in range(self.log_table.rowCount()):
            widget = self.log_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked() and row < len(self.current_logs):
                    selected.append(self.current_logs[row])
        return selected
    
    def recover_selected(self):
        selected = self.get_selected_logs()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要恢复的项目")
            return
        
        unrecovered = [log for log in selected if not log.get('is_recovered')]
        if not unrecovered:
            QMessageBox.information(self, "提示", "选中的项目都已恢复过了")
            return
        
        reply = QMessageBox.question(
            self, "确认恢复",
            f"确定要恢复 {len(unrecovered)} 个项目吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for log in unrecovered:
                db_manager.mark_log_recovered(log['id'], recovered=True)
            
            self._refresh_logs()
            self.logger.info(f"批量恢复了 {len(unrecovered)} 个项目")
            QMessageBox.information(self, "恢复完成", f"成功恢复 {len(unrecovered)} 个项目！")
    
    def show_batch_recover_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("批量恢复")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel("选择要恢复的操作类型:")
        layout.addWidget(info_label)
        
        op_checkboxes = {}
        for op_type, info in AppConfig.OPERATION_TYPES.items():
            if op_type in ['DELETE', 'OVERWRITE', 'MOVE']:
                checkbox = QCheckBox(info['name'])
                checkbox.setChecked(True)
                op_checkboxes[op_type] = checkbox
                layout.addWidget(checkbox)
        
        risk_label = QLabel("风险等级筛选:")
        layout.addWidget(risk_label)
        
        risk_checkboxes = {}
        for level, info in AppConfig.RISK_LEVELS.items():
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"color: {info['color']};")
            risk_checkboxes[level] = checkbox
            layout.addWidget(checkbox)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        recover_btn = QPushButton("执行恢复")
        recover_btn.setProperty("class", "primary")
        btn_layout.addWidget(recover_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        def do_batch_recover():
            selected_ops = [op for op, cb in op_checkboxes.items() if cb.isChecked()]
            selected_risks = [level for level, cb in risk_checkboxes.items() if cb.isChecked()]
            
            if not selected_ops:
                QMessageBox.warning(dialog, "警告", "请至少选择一种操作类型")
                return
            
            logs = db_manager.get_operation_logs(is_recovered=False, limit=10000)
            
            to_recover = [
                log for log in logs 
                if log.get('operation_type') in selected_ops and 
                   log.get('risk_level') in selected_risks
            ]
            
            if not to_recover:
                QMessageBox.information(dialog, "提示", "没有符合条件的待恢复项目")
                return
            
            reply = QMessageBox.question(
                dialog, "确认",
                f"找到 {len(to_recover)} 个符合条件的项目。\n确定要恢复吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for log in to_recover:
                    db_manager.mark_log_recovered(log['id'], recovered=True)
                
                self._refresh_logs()
                dialog.accept()
                self.logger.info(f"批量恢复了 {len(to_recover)} 个项目")
                QMessageBox.information(self, "完成", f"成功恢复 {len(to_recover)} 个项目！")
        
        recover_btn.clicked.connect(do_batch_recover)
        
        dialog.exec()
    
    def refresh_logs(self):
        self._refresh_logs()
