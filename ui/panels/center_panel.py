from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView,
    QMessageBox, QDialog, QCheckBox,
    QMenu, QAbstractItemView, QTabWidget,
    QFrame, QScrollArea, QGridLayout, QButtonGroup,
    QRadioButton, QSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QAction, QColor, QFont
from typing import List, Dict, Any
from datetime import datetime
from config.app_config import AppConfig
from database.db_manager import db_manager
from services.recovery_service import recovery_service
from services.conflict_service import conflict_service
from services.report_service import report_service
from utils.helpers import format_file_size, format_timestamp
from utils.logger import get_logger

class PreviewDialog(QDialog):
    def __init__(self, logs: List[Dict], parent=None):
        super().__init__(parent)
        self.logger = get_logger('PreviewDialog')
        self.logs = logs
        self.conflicts = []
        self.resolutions = {}
        self._init_ui()
        self._analyze_conflicts()
    
    def _init_ui(self):
        self.setWindowTitle("批量恢复预演")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        header = QLabel(f"准备恢复 {len(self.logs)} 个文件")
        header.setProperty("class", "title")
        layout.addWidget(header)
        
        self.tab_widget = QTabWidget()
        
        self.summary_tab = self._create_summary_tab()
        self.tab_widget.addTab(self.summary_tab, "恢复概览")
        
        self.conflict_tab = self._create_conflict_tab()
        self.tab_widget.addTab(self.conflict_tab, "冲突检测")
        
        self.detail_tab = self._create_detail_tab()
        self.tab_widget.addTab(self.detail_tab, "文件列表")
        
        layout.addWidget(self.tab_widget)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.export_btn = QPushButton("导出预演报告")
        self.export_btn.clicked.connect(self._export_preview_report)
        btn_layout.addWidget(self.export_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.execute_btn = QPushButton("执行恢复")
        self.execute_btn.setProperty("class", "primary")
        self.execute_btn.clicked.connect(self._execute_recovery)
        btn_layout.addWidget(self.execute_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_summary_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        stats_group = QLabel("恢复统计")
        stats_group.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(stats_group)
        
        stats_grid = QGridLayout()
        
        by_type = {}
        by_risk = {}
        total_size = 0
        
        for log in self.logs:
            op_type = log.get('operation_type', 'UNKNOWN')
            by_type[op_type] = by_type.get(op_type, 0) + 1
            
            risk = log.get('risk_level', 'LOW')
            by_risk[risk] = by_risk.get(risk, 0) + 1
            
            total_size += log.get('file_size', 0)
        
        row = 0
        stats_grid.addWidget(QLabel("总文件数:"), row, 0)
        stats_grid.addWidget(QLabel(str(len(self.logs))), row, 1)
        row += 1
        
        stats_grid.addWidget(QLabel("总大小:"), row, 0)
        stats_grid.addWidget(QLabel(format_file_size(total_size)), row, 1)
        row += 1
        
        for op_type, count in by_type.items():
            op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
            stats_grid.addWidget(QLabel(f"{op_info['name']}:"), row, 0)
            stats_grid.addWidget(QLabel(str(count)), row, 1)
            row += 1
        
        layout.addLayout(stats_grid)
        
        target_group = QLabel("恢复选项")
        target_group.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        layout.addWidget(target_group)
        
        self.target_group = QButtonGroup(self)
        
        self.original_radio = QRadioButton("恢复到原路径")
        self.original_radio.setChecked(True)
        self.target_group.addButton(self.original_radio)
        layout.addWidget(self.original_radio)
        
        self.custom_radio = QRadioButton("恢复到指定目录:")
        self.target_group.addButton(self.custom_radio)
        layout.addWidget(self.custom_radio)
        
        custom_layout = QHBoxLayout()
        self.custom_path_edit = QLabel("(未选择)")
        self.custom_path_edit.setStyleSheet("color: #858585;")
        custom_layout.addWidget(self.custom_path_edit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_target_dir)
        custom_layout.addWidget(self.browse_btn)
        layout.addLayout(custom_layout)
        
        conflict_group = QLabel("冲突处理")
        conflict_group.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        layout.addWidget(conflict_group)
        
        self.conflict_group = QButtonGroup(self)
        
        self.skip_radio = QRadioButton("跳过冲突文件")
        self.skip_radio.setChecked(True)
        self.conflict_group.addButton(self.skip_radio)
        layout.addWidget(self.skip_radio)
        
        self.overwrite_radio = QRadioButton("覆盖现有文件")
        self.conflict_group.addButton(self.overwrite_radio)
        layout.addWidget(self.overwrite_radio)
        
        self.rename_radio = QRadioButton("重命名源文件(保留两者)")
        self.conflict_group.addButton(self.rename_radio)
        layout.addWidget(self.rename_radio)
        
        layout.addStretch()
        
        return widget
    
    def _create_conflict_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.conflict_label = QLabel("正在分析冲突...")
        layout.addWidget(self.conflict_label)
        
        self.conflict_table = QTableWidget()
        self.conflict_table.setColumnCount(5)
        self.conflict_table.setHorizontalHeaderLabels([
            "类型", "严重程度", "文件", "描述", "处理方式"
        ])
        
        header = self.conflict_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.conflict_table.setColumnWidth(0, 100)
        self.conflict_table.setColumnWidth(1, 80)
        self.conflict_table.setColumnWidth(4, 120)
        
        self.conflict_table.setAlternatingRowColors(True)
        layout.addWidget(self.conflict_table)
        
        return widget
    
    def _create_detail_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels([
            "选择", "操作类型", "文件名", "风险等级", "大小", "原路径", "状态"
        ])
        
        header = self.detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.detail_table.setColumnWidth(0, 40)
        self.detail_table.setColumnWidth(1, 80)
        self.detail_table.setColumnWidth(3, 80)
        self.detail_table.setColumnWidth(4, 100)
        self.detail_table.setColumnWidth(6, 80)
        
        self.detail_table.setAlternatingRowColors(True)
        self._populate_detail_table()
        
        layout.addWidget(self.detail_table)
        
        return widget
    
    def _populate_detail_table(self):
        self.detail_table.setRowCount(len(self.logs))
        
        for row, log in enumerate(self.logs):
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.detail_table.setCellWidget(row, 0, checkbox_widget)
            
            op_type = log.get('operation_type', 'UNKNOWN')
            op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
            op_item = QTableWidgetItem(op_info['name'])
            self.detail_table.setItem(row, 1, op_item)
            
            name_item = QTableWidgetItem(log.get('file_name', ''))
            name_item.setToolTip(log.get('file_path', ''))
            self.detail_table.setItem(row, 2, name_item)
            
            risk_level = log.get('risk_level', 'LOW')
            risk_info = AppConfig.RISK_LEVELS.get(risk_level, {'name': risk_level, 'color': '#ffffff'})
            risk_item = QTableWidgetItem(risk_info['name'])
            risk_item.setForeground(QColor(risk_info['color']))
            risk_item.setTextAlignment(Qt.AlignCenter)
            self.detail_table.setItem(row, 3, risk_item)
            
            size = log.get('file_size', 0)
            size_item = QTableWidgetItem(format_file_size(size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.detail_table.setItem(row, 4, size_item)
            
            path_item = QTableWidgetItem(log.get('file_path', ''))
            self.detail_table.setItem(row, 5, path_item)
            
            is_recovered = log.get('is_recovered', 0)
            status_text = "已恢复" if is_recovered else "待恢复"
            status_item = QTableWidgetItem(status_text)
            if is_recovered:
                status_item.setForeground(QColor("#4ec9b0"))
            else:
                status_item.setForeground(QColor("#f14c4c"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.detail_table.setItem(row, 6, status_item)
    
    def _analyze_conflicts(self):
        log_ids = [log['id'] for log in self.logs]
        self.conflicts = conflict_service.detect_conflicts(log_ids)
        
        if not self.conflicts:
            self.conflict_label.setText("✓ 未检测到严重冲突")
            self.conflict_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        else:
            high_count = sum(1 for c in self.conflicts if c.get('severity') == 'HIGH')
            self.conflict_label.setText(f"⚠ 检测到 {len(self.conflicts)} 个潜在问题 (其中 {high_count} 个高风险)")
            self.conflict_label.setStyleSheet("color: #f14c4c; font-weight: bold;")
        
        self._populate_conflict_table()
    
    def _populate_conflict_table(self):
        self.conflict_table.setRowCount(len(self.conflicts))
        
        for row, conflict in enumerate(self.conflicts):
            type_item = QTableWidgetItem(conflict.get('type', 'unknown'))
            self.conflict_table.setItem(row, 0, type_item)
            
            severity = conflict.get('severity', 'LOW')
            severity_item = QTableWidgetItem(severity)
            if severity == 'HIGH':
                severity_item.setForeground(QColor("#f14c4c"))
            elif severity == 'MEDIUM':
                severity_item.setForeground(QColor("#FF9800"))
            severity_item.setTextAlignment(Qt.AlignCenter)
            self.conflict_table.setItem(row, 1, severity_item)
            
            file_item = QTableWidgetItem(conflict.get('file_path', ''))
            self.conflict_table.setItem(row, 2, file_item)
            
            desc_item = QTableWidgetItem(conflict.get('description', ''))
            self.conflict_table.setItem(row, 3, desc_item)
            
            resolution_combo = QLabel("自动处理")
            self.conflict_table.setCellWidget(row, 4, resolution_combo)
    
    def _browse_target_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择恢复目标目录")
        if dir_path:
            self.custom_path_edit.setText(dir_path)
            self.custom_path_edit.setStyleSheet("color: #d4d4d4;")
            self.custom_radio.setChecked(True)
    
    def _get_target_path(self) -> str:
        if self.original_radio.isChecked():
            return None
        else:
            path = self.custom_path_edit.text()
            if path and path != "(未选择)":
                return path
            return None
    
    def _get_conflict_resolution(self) -> str:
        if self.skip_radio.isChecked():
            return 'skip'
        elif self.overwrite_radio.isChecked():
            return 'overwrite'
        else:
            return 'rename'
    
    def _export_preview_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出预演报告", "", 
            "HTML报告 (*.html);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        
        if file_path:
            log_ids = [log['id'] for log in self.logs]
            report = report_service.generate_report(log_ids)
            
            if file_path.endswith('.html'):
                report_service.export_to_html(report, file_path)
            elif file_path.endswith('.csv'):
                report_service.export_to_csv(report, file_path)
            else:
                report_service.export_to_json(report, file_path)
            
            QMessageBox.information(self, "导出成功", f"报告已导出到:\n{file_path}")
    
    def _execute_recovery(self):
        selected_logs = []
        for row in range(self.detail_table.rowCount()):
            widget = self.detail_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked() and row < len(self.logs):
                    selected_logs.append(self.logs[row])
        
        if not selected_logs:
            QMessageBox.warning(self, "警告", "请至少选择一个文件进行恢复")
            return
        
        unrecovered = [log for log in selected_logs if not log.get('is_recovered')]
        if not unrecovered:
            QMessageBox.information(self, "提示", "选中的项目都已恢复过了")
            return
        
        target_path = self._get_target_path()
        conflict_resolution = self._get_conflict_resolution()
        
        reply = QMessageBox.question(
            self, "确认恢复",
            f"确定要恢复 {len(unrecovered)} 个文件吗？\n\n"
            f"目标路径: {'原路径' if not target_path else target_path}\n"
            f"冲突处理: {'跳过' if conflict_resolution == 'skip' else ('覆盖' if conflict_resolution == 'overwrite' else '重命名')}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            failed_count = 0
            errors = []
            
            for log in unrecovered:
                result = recovery_service.recover_file(log['id'], target_path)
                
                if result.get('success'):
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"{log.get('file_name')}: {result.get('error', '未知错误')}")
            
            self.accept()
            
            if errors:
                error_msg = "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... 还有 {len(errors) - 10} 个错误"
                
                QMessageBox.warning(
                    self, "恢复完成",
                    f"恢复完成!\n\n成功: {success_count}\n失败: {failed_count}\n\n错误详情:\n{error_msg}"
                )
            else:
                QMessageBox.information(
                    self, "恢复成功",
                    f"成功恢复 {success_count} 个文件！"
                )

class CenterPanel(QWidget):
    log_selected = Signal(dict)
    logs_selected = Signal(list)
    recover_requested = Signal(int)
    data_filtered = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('CenterPanel')
        self.all_logs = []
        self.filtered_logs = []
        self.current_filters = {
            'path': None,
            'start_time': None,
            'end_time': None,
            'risk_levels': None,
            'operation_types': None,
            'keyword': None
        }
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("操作视图")
        title_label.setProperty("class", "title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.stats_label = QLabel("0 条记录")
        header_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(header_layout)
        
        view_switch_layout = QHBoxLayout()
        
        self.view_group = QButtonGroup(self)
        
        self.log_view_radio = QRadioButton("日志视图")
        self.log_view_radio.setChecked(True)
        self.view_group.addButton(self.log_view_radio)
        view_switch_layout.addWidget(self.log_view_radio)
        
        self.timeline_view_radio = QRadioButton("时间轴视图")
        self.view_group.addButton(self.timeline_view_radio)
        view_switch_layout.addWidget(self.timeline_view_radio)
        
        view_switch_layout.addStretch()
        
        main_layout.addLayout(view_switch_layout)
        
        self.stacked_widget = QWidget()
        stacked_layout = QVBoxLayout(self.stacked_widget)
        stacked_layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_table_container = QWidget()
        self._init_log_table()
        stacked_layout.addWidget(self.log_table_container)
        
        self.timeline_container = self._create_timeline_view()
        self.timeline_container.hide()
        stacked_layout.addWidget(self.timeline_container)
        
        main_layout.addWidget(self.stacked_widget)
    
    def _init_log_table(self):
        layout = QVBoxLayout(self.log_table_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        toolbar_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.select_all_btn = QPushButton("全选")
        toolbar_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("取消全选")
        toolbar_layout.addWidget(self.deselect_all_btn)
        
        toolbar_layout.addStretch()
        
        self.preview_btn = QPushButton("恢复预演")
        self.preview_btn.clicked.connect(self._show_preview_dialog)
        toolbar_layout.addWidget(self.preview_btn)
        
        self.recover_btn = QPushButton("恢复选中")
        self.recover_btn.setProperty("class", "primary")
        toolbar_layout.addWidget(self.recover_btn)
        
        self.batch_recover_btn = QPushButton("批量恢复")
        self.batch_recover_btn.setProperty("class", "success")
        toolbar_layout.addWidget(self.batch_recover_btn)
        
        layout.addLayout(toolbar_layout)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(10)
        self.log_table.setHorizontalHeaderLabels([
            "选择", "操作类型", "文件名", "风险等级", "影响大小",
            "大小", "操作时间", "状态", "有备份", "详情"
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
        header.setSectionResizeMode(9, QHeaderView.Fixed)
        
        self.log_table.setColumnWidth(0, 40)
        self.log_table.setColumnWidth(1, 80)
        self.log_table.setColumnWidth(3, 80)
        self.log_table.setColumnWidth(4, 80)
        self.log_table.setColumnWidth(5, 100)
        self.log_table.setColumnWidth(6, 160)
        self.log_table.setColumnWidth(7, 80)
        self.log_table.setColumnWidth(8, 60)
        self.log_table.setColumnWidth(9, 60)
        
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSortingEnabled(True)
        self.log_table.verticalHeader().setDefaultSectionSize(28)
        
        self.log_table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        layout.addWidget(self.log_table)
    
    def _create_timeline_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar_layout = QHBoxLayout()
        
        toolbar_layout.addWidget(QLabel("时间范围:"))
        
        self.timeline_day_spin = QSpinBox()
        self.timeline_day_spin.setRange(1, 30)
        self.timeline_day_spin.setValue(7)
        self.timeline_day_spin.setSuffix(" 天")
        toolbar_layout.addWidget(self.timeline_day_spin)
        
        self.refresh_timeline_btn = QPushButton("刷新时间轴")
        toolbar_layout.addWidget(self.refresh_timeline_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.timeline_content = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_content)
        self.timeline_layout.setAlignment(Qt.AlignTop)
        self.timeline_layout.setSpacing(10)
        
        scroll.setWidget(self.timeline_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self._load_all_data)
        self.select_all_btn.clicked.connect(self.select_all_logs)
        self.deselect_all_btn.clicked.connect(self.deselect_all_logs)
        self.recover_btn.clicked.connect(self.recover_selected)
        self.batch_recover_btn.clicked.connect(self.show_batch_recover_dialog)
        self.log_table.itemClicked.connect(self._on_item_clicked)
        self.log_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.log_table.customContextMenuRequested.connect(self._show_context_menu)
        self.log_table.cellClicked.connect(self._on_cell_clicked)
        
        self.log_view_radio.toggled.connect(self._on_view_changed)
        self.refresh_timeline_btn.clicked.connect(self._refresh_timeline)
    
    def _on_view_changed(self, checked):
        if self.log_view_radio.isChecked():
            self.log_table_container.show()
            self.timeline_container.hide()
        else:
            self.log_table_container.hide()
            self.timeline_container.show()
            self._refresh_timeline()
    
    def _refresh_timeline(self):
        for i in reversed(range(self.timeline_layout.count())):
            self.timeline_layout.itemAt(i).widget().setParent(None)
        
        if not self.filtered_logs:
            empty_label = QLabel("暂无数据")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #858585; font-size: 16px; padding: 50px;")
            self.timeline_layout.addWidget(empty_label)
            return
        
        logs_by_date = {}
        for log in self.filtered_logs:
            op_time = log.get('operation_time', 0)
            op_date = datetime.fromtimestamp(op_time).strftime("%Y-%m-%d")
            if op_date not in logs_by_date:
                logs_by_date[op_date] = []
            logs_by_date[op_date].append(log)
        
        sorted_dates = sorted(logs_by_date.keys(), reverse=True)
        
        for date in sorted_dates:
            date_group = QGroupBox(date)
            date_layout = QVBoxLayout(date_group)
            
            logs = logs_by_date[date]
            logs.sort(key=lambda x: x.get('operation_time', 0), reverse=True)
            
            for log in logs[:20]:
                item_frame = QFrame()
                item_frame.setFrameStyle(QFrame.StyledPanel)
                item_frame.setLineWidth(1)
                item_frame.setStyleSheet("""
                    QFrame:hover { background-color: #2a2d2e; }
                """)
                
                item_layout = QHBoxLayout(item_frame)
                
                op_type = log.get('operation_type', 'UNKNOWN')
                op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
                
                risk_level = log.get('risk_level', 'LOW')
                risk_info = AppConfig.RISK_LEVELS.get(risk_level, {'name': risk_level, 'color': '#ffffff'})
                
                type_label = QLabel(op_info['name'])
                type_label.setStyleSheet(f"font-weight: bold; color: {risk_info['color']};")
                type_label.setMinimumWidth(60)
                item_layout.addWidget(type_label)
                
                name_label = QLabel(log.get('file_name', ''))
                name_label.setToolTip(log.get('file_path', ''))
                item_layout.addWidget(name_label, 1)
                
                size_label = QLabel(format_file_size(log.get('file_size', 0)))
                size_label.setMinimumWidth(80)
                item_layout.addWidget(size_label)
                
                time_label = QLabel(datetime.fromtimestamp(log.get('operation_time', 0)).strftime("%H:%M:%S"))
                time_label.setMinimumWidth(80)
                item_layout.addWidget(time_label)
                
                is_recovered = log.get('is_recovered', 0)
                status_label = QLabel("已恢复" if is_recovered else "待恢复")
                if is_recovered:
                    status_label.setStyleSheet("color: #4ec9b0;")
                else:
                    status_label.setStyleSheet("color: #f14c4c;")
                status_label.setMinimumWidth(60)
                item_layout.addWidget(status_label)
                
                item_frame.setCursor(Qt.PointingHandCursor)
                item_frame.mousePressEvent = lambda event, l=log: self._on_timeline_item_clicked(l)
                
                date_layout.addWidget(item_frame)
            
            if len(logs) > 20:
                more_label = QLabel(f"... 还有 {len(logs) - 20} 条记录")
                more_label.setStyleSheet("color: #858585; padding: 5px;")
                date_layout.addWidget(more_label)
            
            self.timeline_layout.addWidget(date_group)
    
    def _on_timeline_item_clicked(self, log_data: Dict):
        self.log_selected.emit(log_data)
    
    def _load_all_data(self):
        logs = db_manager.get_operation_logs(limit=10000)
        self.all_logs = logs
        self.logger.info(f"从数据库加载了 {len(logs)} 条记录")
        
        self._apply_current_filters()
    
    def _apply_current_filters(self):
        self.filtered_logs = self._filter_logs(self.all_logs, self.current_filters)
        self.logger.info(f"筛选后显示 {len(self.filtered_logs)} 条记录")
        
        self._populate_table(self.filtered_logs)
        self.stats_label.setText(f"{len(self.filtered_logs)} 条记录")
        self.data_filtered.emit(self.filtered_logs)
    
    def _filter_logs(self, logs: List[Dict], filters: Dict) -> List[Dict]:
        if not logs:
            return []
        
        filtered = list(logs)
        
        path = filters.get('path')
        if path:
            filtered = [
                l for l in filtered 
                if l.get('file_path', '').startswith(path)
            ]
        
        start_time = filters.get('start_time')
        if start_time is not None:
            filtered = [
                l for l in filtered 
                if l.get('operation_time', 0) >= start_time
            ]
        
        end_time = filters.get('end_time')
        if end_time is not None:
            filtered = [
                l for l in filtered 
                if l.get('operation_time', 0) <= end_time
            ]
        
        risk_levels = filters.get('risk_levels')
        if risk_levels is not None:
            if len(risk_levels) == 0:
                filtered = []
            else:
                filtered = [
                    l for l in filtered 
                    if l.get('risk_level', 'LOW') in risk_levels
                ]
        
        operation_types = filters.get('operation_types')
        if operation_types is not None:
            if len(operation_types) == 0:
                filtered = []
            else:
                filtered = [
                    l for l in filtered 
                    if l.get('operation_type', 'UNKNOWN') in operation_types
                ]
        
        keyword = filters.get('keyword')
        if keyword:
            keyword_lower = keyword.lower()
            filtered = [
                l for l in filtered
                if keyword_lower in l.get('file_name', '').lower() or
                   keyword_lower in l.get('file_path', '').lower() or
                   keyword_lower in l.get('description', '').lower()
            ]
        
        return filtered
    
    def apply_filters(self, filters: Dict):
        self.current_filters = filters.copy()
        self._apply_current_filters()
    
    def reset_filters(self):
        self.current_filters = {
            'path': None,
            'start_time': None,
            'end_time': None,
            'risk_levels': None,
            'operation_types': None,
            'keyword': None
        }
        self._apply_current_filters()
    
    def _populate_table(self, logs: List[Dict]):
        self.log_table.setRowCount(0)
        
        if not logs:
            return
        
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
            
            has_backup = log.get('has_backup', 0)
            backup_text = "是" if has_backup else "否"
            backup_item = QTableWidgetItem(backup_text)
            if has_backup:
                backup_item.setForeground(QColor("#4ec9b0"))
            backup_item.setTextAlignment(Qt.AlignCenter)
            self.log_table.setItem(row, 8, backup_item)
            
            detail_item = QTableWidgetItem("查看")
            detail_item.setTextAlignment(Qt.AlignCenter)
            detail_item.setForeground(QColor("#007acc"))
            self.log_table.setItem(row, 9, detail_item)
    
    def _on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        if row < len(self.filtered_logs):
            log_data = self.filtered_logs[row]
            self.log_selected.emit(log_data)
    
    def _on_cell_clicked(self, row: int, column: int):
        if column == 9 and row < len(self.filtered_logs):
            log_data = self.filtered_logs[row]
            self._show_log_details(log_data)
    
    def _on_selection_changed(self):
        selected_rows = self.log_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self.filtered_logs):
                log_data = self.filtered_logs[row]
                self.log_selected.emit(log_data)
    
    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        recover_action = QAction("恢复此项", self)
        recover_action.triggered.connect(self._context_recover)
        menu.addAction(recover_action)
        
        preview_action = QAction("恢复预演", self)
        preview_action.triggered.connect(self._show_preview_dialog)
        menu.addAction(preview_action)
        
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
        if current_row >= 0 and current_row < len(self.filtered_logs):
            log_data = self.filtered_logs[current_row]
            self._recover_log(log_data)
    
    def _context_show_details(self):
        current_row = self.log_table.currentRow()
        if current_row >= 0 and current_row < len(self.filtered_logs):
            log_data = self.filtered_logs[current_row]
            self._show_log_details(log_data)
    
    def _show_log_details(self, log_data: Dict):
        dialog = QDialog(self)
        dialog.setWindowTitle("操作详情")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        
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
            result = recovery_service.recover_file(log_data['id'])
            
            if result.get('success'):
                self._load_all_data()
                self.logger.info(f"已恢复日志 ID: {log_data['id']}")
                QMessageBox.information(self, "恢复成功", f"文件 {file_name} 已成功恢复！")
                return True
            else:
                error_msg = result.get('error', '未知错误')
                QMessageBox.warning(self, "恢复失败", f"恢复失败: {error_msg}")
                return False
        
        return False
    
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
                if checkbox and checkbox.isChecked() and row < len(self.filtered_logs):
                    selected.append(self.filtered_logs[row])
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
            success_count = 0
            failed_count = 0
            errors = []
            
            for log in unrecovered:
                result = recovery_service.recover_file(log['id'])
                
                if result.get('success'):
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"{log.get('file_name')}: {result.get('error', '未知错误')}")
            
            self._load_all_data()
            self.logger.info(f"批量恢复了 {success_count} 个项目")
            
            if errors:
                error_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... 还有 {len(errors) - 5} 个错误"
                
                QMessageBox.warning(
                    self, "恢复完成",
                    f"恢复完成!\n\n成功: {success_count}\n失败: {failed_count}\n\n错误详情:\n{error_msg}"
                )
            else:
                QMessageBox.information(self, "恢复完成", f"成功恢复 {success_count} 个项目！")
    
    def _show_preview_dialog(self):
        selected = self.get_selected_logs()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要恢复的项目")
            return
        
        dialog = PreviewDialog(selected, self)
        dialog.exec()
        
        if dialog.result() == QDialog.Accepted:
            self._load_all_data()
    
    def show_batch_recover_dialog(self):
        self._show_preview_dialog()
    
    def refresh_logs(self):
        self._load_all_data()
