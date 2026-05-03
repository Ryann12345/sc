from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QTextEdit, QGroupBox,
    QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QComboBox,
    QCheckBox, QButtonGroup, QRadioButton,
    QScrollArea, QGridLayout, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QTextCursor
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.app_config import AppConfig
from database.db_manager import db_manager
from services.recovery_service import recovery_service
from services.conflict_service import conflict_service
from services.report_service import report_service
from utils.helpers import format_file_size, format_timestamp, is_text_file
from utils.logger import get_logger

class RecoveryPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('RecoveryPreview')
        self.current_log = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        preview_group = QGroupBox("恢复预演")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(10)
        
        self.preview_info = QLabel("选择一个操作记录进行恢复预演")
        self.preview_info.setStyleSheet("color: #858585; padding: 40px; font-size: 14px;")
        self.preview_info.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_info)
        
        self.preview_content = QWidget()
        self.preview_content.hide()
        preview_content_layout = QVBoxLayout(self.preview_content)
        preview_content_layout.setSpacing(12)
        
        info_group = QGroupBox("文件信息")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        
        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        
        row = 0
        
        info_grid.addWidget(QLabel("操作类型:"), row, 0)
        self.op_type_label = QLabel("-")
        self.op_type_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        info_grid.addWidget(self.op_type_label, row, 1)
        row += 1
        
        info_grid.addWidget(QLabel("文件名:"), row, 0)
        self.file_name_label = QLabel("-")
        self.file_name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #007acc;")
        info_grid.addWidget(self.file_name_label, row, 1)
        row += 1
        
        info_grid.addWidget(QLabel("文件大小:"), row, 0)
        self.size_label = QLabel("-")
        self.size_label.setStyleSheet("font-size: 13px;")
        info_grid.addWidget(self.size_label, row, 1)
        row += 1
        
        info_grid.addWidget(QLabel("风险等级:"), row, 0)
        self.risk_label = QLabel("-")
        info_grid.addWidget(self.risk_label, row, 1)
        row += 1
        
        info_grid.addWidget(QLabel("恢复状态:"), row, 0)
        self.recovery_status_label = QLabel("-")
        info_grid.addWidget(self.recovery_status_label, row, 1)
        row += 1
        
        info_grid.setColumnStretch(0, 0)
        info_grid.setColumnStretch(1, 1)
        info_layout.addLayout(info_grid)
        
        path_group = QGroupBox("路径信息")
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(8)
        
        old_path_row = QHBoxLayout()
        old_path_label = QLabel("原路径:")
        old_path_label.setMinimumWidth(60)
        old_path_row.addWidget(old_path_label)
        self.old_path_display = QLabel("-")
        self.old_path_display.setStyleSheet("font-family: Consolas; font-size: 12px; color: #d4d4d4; background-color: #1e1e1e; padding: 8px; border-radius: 4px;")
        self.old_path_display.setWordWrap(True)
        self.old_path_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        old_path_row.addWidget(self.old_path_display, 1)
        path_layout.addLayout(old_path_row)
        
        target_path_row = QHBoxLayout()
        target_path_label = QLabel("恢复目标:")
        target_path_label.setMinimumWidth(60)
        target_path_row.addWidget(target_path_label)
        self.target_path_display = QLabel("-")
        self.target_path_display.setStyleSheet("font-family: Consolas; font-size: 12px; color: #4ec9b0; background-color: #1e1e1e; padding: 8px; border-radius: 4px;")
        self.target_path_display.setWordWrap(True)
        self.target_path_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        target_path_row.addWidget(self.target_path_display, 1)
        path_layout.addLayout(target_path_row)
        
        preview_content_layout.addWidget(info_group)
        preview_content_layout.addWidget(path_group)
        
        target_group = QGroupBox("恢复选项")
        target_layout = QVBoxLayout(target_group)
        target_layout.setSpacing(10)
        
        self.target_group = QButtonGroup(self)
        
        self.original_radio = QRadioButton("恢复到原路径")
        self.original_radio.setChecked(True)
        self.original_radio.setMinimumHeight(26)
        self.original_radio.setStyleSheet("font-size: 13px;")
        self.target_group.addButton(self.original_radio)
        target_layout.addWidget(self.original_radio)
        
        self.custom_radio = QRadioButton("恢复到指定目录:")
        self.custom_radio.setMinimumHeight(26)
        self.custom_radio.setStyleSheet("font-size: 13px;")
        self.target_group.addButton(self.custom_radio)
        target_layout.addWidget(self.custom_radio)
        
        custom_path_layout = QHBoxLayout()
        custom_path_layout.setSpacing(8)
        self.custom_path_edit = QLabel("(未选择)")
        self.custom_path_edit.setStyleSheet("color: #858585; font-family: Consolas; font-size: 12px; background-color: #1e1e1e; padding: 6px; border-radius: 4px;")
        self.custom_path_edit.setMinimumWidth(200)
        custom_path_layout.addWidget(self.custom_path_edit, 1)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMinimumHeight(28)
        self.browse_btn.clicked.connect(self._browse_target_dir)
        custom_path_layout.addWidget(self.browse_btn)
        target_layout.addLayout(custom_path_layout)
        
        preview_content_layout.addWidget(target_group)
        
        conflict_group = QGroupBox("冲突处理方式")
        conflict_layout = QVBoxLayout(conflict_group)
        conflict_layout.setSpacing(10)
        
        self.conflict_group = QButtonGroup(self)
        
        self.skip_radio = QRadioButton("跳过冲突文件 - 不覆盖已存在的文件")
        self.skip_radio.setChecked(True)
        self.skip_radio.setMinimumHeight(26)
        self.skip_radio.setStyleSheet("font-size: 13px;")
        self.conflict_group.addButton(self.skip_radio)
        conflict_layout.addWidget(self.skip_radio)
        
        self.overwrite_radio = QRadioButton("覆盖现有文件 - 替换已存在的文件")
        self.overwrite_radio.setMinimumHeight(26)
        self.overwrite_radio.setStyleSheet("font-size: 13px;")
        self.conflict_group.addButton(self.overwrite_radio)
        conflict_layout.addWidget(self.overwrite_radio)
        
        self.rename_radio = QRadioButton("重命名源文件 - 保留两者，自动重命名恢复文件")
        self.rename_radio.setMinimumHeight(26)
        self.rename_radio.setStyleSheet("font-size: 13px;")
        self.conflict_group.addButton(self.rename_radio)
        conflict_layout.addWidget(self.rename_radio)
        
        preview_content_layout.addWidget(conflict_group)
        
        status_group = QGroupBox("冲突检测结果")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        
        self.conflict_status_frame = QFrame()
        self.conflict_status_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 10px;")
        status_frame_layout = QVBoxLayout(self.conflict_status_frame)
        status_frame_layout.setContentsMargins(10, 10, 10, 10)
        
        self.conflict_icon_label = QLabel("⏳")
        self.conflict_icon_label.setAlignment(Qt.AlignCenter)
        self.conflict_icon_label.setStyleSheet("font-size: 24px;")
        status_frame_layout.addWidget(self.conflict_icon_label)
        
        self.conflict_title_label = QLabel("点击'检测冲突'按钮检查恢复状态")
        self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #858585;")
        self.conflict_title_label.setAlignment(Qt.AlignCenter)
        status_frame_layout.addWidget(self.conflict_title_label)
        
        self.conflict_desc_label = QLabel("")
        self.conflict_desc_label.setStyleSheet("font-size: 12px; color: #858585;")
        self.conflict_desc_label.setWordWrap(True)
        self.conflict_desc_label.setAlignment(Qt.AlignCenter)
        status_frame_layout.addWidget(self.conflict_desc_label)
        
        self.conflict_suggestion_label = QLabel("")
        self.conflict_suggestion_label.setStyleSheet("font-size: 12px; color: #007acc;")
        self.conflict_suggestion_label.setWordWrap(True)
        self.conflict_suggestion_label.setAlignment(Qt.AlignCenter)
        status_frame_layout.addWidget(self.conflict_suggestion_label)
        
        status_layout.addWidget(self.conflict_status_frame)
        
        preview_content_layout.addWidget(status_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.check_conflict_btn = QPushButton("检测冲突")
        self.check_conflict_btn.setMinimumHeight(36)
        self.check_conflict_btn.setStyleSheet("font-size: 13px;")
        self.check_conflict_btn.clicked.connect(self._check_conflicts)
        btn_layout.addWidget(self.check_conflict_btn)
        
        btn_layout.addStretch()
        
        self.recover_btn = QPushButton("执行恢复")
        self.recover_btn.setProperty("class", "primary")
        self.recover_btn.setMinimumHeight(36)
        self.recover_btn.setMinimumWidth(120)
        self.recover_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.recover_btn.clicked.connect(self._execute_recovery)
        btn_layout.addWidget(self.recover_btn)
        
        preview_content_layout.addLayout(btn_layout)
        
        preview_content_layout.addStretch()
        
        preview_layout.addWidget(self.preview_content)
        
        layout.addWidget(preview_group)
    
    def _browse_target_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择恢复目标目录")
        if dir_path:
            self.custom_path_edit.setText(dir_path)
            self.custom_path_edit.setStyleSheet("color: #d4d4d4; font-family: Consolas; font-size: 12px; background-color: #1e1e1e; padding: 6px; border-radius: 4px;")
            self.custom_radio.setChecked(True)
            self._update_target_path_display()
    
    def _update_target_path_display(self):
        if not self.current_log:
            return
        
        old_path = self.current_log.get('old_path') or self.current_log.get('file_path', '')
        
        if self.original_radio.isChecked():
            self.target_path_display.setText(old_path)
            self.target_path_display.setStyleSheet("font-family: Consolas; font-size: 12px; color: #4ec9b0; background-color: #1e1e1e; padding: 8px; border-radius: 4px;")
        else:
            custom_path = self.custom_path_edit.text()
            if custom_path and custom_path != "(未选择)":
                file_name = self.current_log.get('file_name', '')
                import os
                full_path = os.path.join(custom_path, file_name)
                self.target_path_display.setText(full_path)
                self.target_path_display.setStyleSheet("font-family: Consolas; font-size: 12px; color: #007acc; background-color: #1e1e1e; padding: 8px; border-radius: 4px;")
            else:
                self.target_path_display.setText("(未选择目标目录)")
                self.target_path_display.setStyleSheet("font-family: Consolas; font-size: 12px; color: #f14c4c; background-color: #1e1e1e; padding: 8px; border-radius: 4px;")
    
    def _get_conflict_mode_text(self) -> str:
        if self.skip_radio.isChecked():
            return "跳过"
        elif self.overwrite_radio.isChecked():
            return "覆盖"
        else:
            return "重命名"
    
    def _get_suggestion(self, conflict_type: str, severity: str) -> str:
        suggestions = {
            'TARGET_EXISTS': {
                'HIGH': "建议选择'重命名'模式以保留两个文件，或确认是否需要覆盖。",
                'MEDIUM': "目标文件已存在，请确认是否需要覆盖或选择其他目录。",
                'LOW': "目标文件已存在，建议检查后再操作。"
            },
            'PERMISSION_DENIED': {
                'HIGH': "严重：无法访问目标目录，请以管理员身份运行或选择其他目录。",
                'MEDIUM': "权限不足，请尝试选择用户目录或修改权限。"
            },
            'PATH_NOT_EXISTS': {
                'MEDIUM': "目标路径不存在，将自动创建。"
            },
            'MULTIPLE_VERSIONS': {
                'HIGH': "同一文件有多个恢复版本，建议选择最新版本或逐个恢复。"
            }
        }
        
        type_suggestions = suggestions.get(conflict_type, {})
        return type_suggestions.get(severity, type_suggestions.get('MEDIUM', "请检查恢复设置后重试。"))
    
    def set_log_data(self, log_data: Dict):
        self.current_log = log_data
        
        if not log_data:
            self.preview_info.show()
            self.preview_content.hide()
            return
        
        self.preview_info.hide()
        self.preview_content.show()
        
        op_type = log_data.get('operation_type', 'UNKNOWN')
        op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
        self.op_type_label.setText(op_info['name'])
        
        self.file_name_label.setText(log_data.get('file_name', '-'))
        
        self.size_label.setText(format_file_size(log_data.get('file_size', 0)))
        
        risk_level = log_data.get('risk_level', 'LOW')
        risk_info = AppConfig.RISK_LEVELS.get(risk_level, {'name': risk_level, 'color': '#ffffff'})
        self.risk_label.setText(f'<span style="color: {risk_info["color"]}; font-weight: bold; font-size: 13px;">{risk_info["name"]}</span>')
        
        is_recovered = log_data.get('is_recovered', 0)
        if is_recovered:
            self.recovery_status_label.setText('<span style="color: #4ec9b0; font-weight: bold;">✓ 已恢复</span>')
        else:
            self.recovery_status_label.setText('<span style="color: #ff9800; font-weight: bold;">✗ 待恢复</span>')
        
        old_path = log_data.get('old_path') or log_data.get('file_path', '-')
        self.old_path_display.setText(old_path)
        
        self._update_target_path_display()
        
        self._reset_conflict_status()
        
        self.recover_btn.setEnabled(not is_recovered)
        self.check_conflict_btn.setEnabled(not is_recovered)
        self.original_radio.setEnabled(not is_recovered)
        self.custom_radio.setEnabled(not is_recovered)
        self.browse_btn.setEnabled(not is_recovered)
        self.skip_radio.setEnabled(not is_recovered)
        self.overwrite_radio.setEnabled(not is_recovered)
        self.rename_radio.setEnabled(not is_recovered)
        
        if is_recovered:
            self.conflict_title_label.setText("该文件已恢复")
            self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #4ec9b0;")
            self.conflict_desc_label.setText("无法对已恢复的文件再次执行恢复操作")
            self.conflict_icon_label.setText("✓")
    
    def _reset_conflict_status(self):
        self.conflict_icon_label.setText("⏳")
        self.conflict_icon_label.setStyleSheet("font-size: 24px; color: #858585;")
        self.conflict_title_label.setText("点击'检测冲突'按钮检查恢复状态")
        self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #858585;")
        self.conflict_desc_label.setText("")
        self.conflict_suggestion_label.setText("")
        self.conflict_status_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 10px;")
    
    def _check_conflicts(self):
        if not self.current_log:
            return
        
        log_id = self.current_log.get('id')
        target_path = self._get_target_path()
        
        self.conflict_icon_label.setText("🔍")
        self.conflict_title_label.setText("正在检测冲突...")
        self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #007acc;")
        self.conflict_desc_label.setText("")
        self.conflict_suggestion_label.setText("")
        
        QTimer.singleShot(300, lambda: self._show_conflict_results(log_id, target_path))
    
    def _show_conflict_results(self, log_id, target_path):
        conflicts = conflict_service.detect_conflicts([log_id])
        
        conflict_mode = self._get_conflict_mode_text()
        
        if conflicts:
            conflict = conflicts[0]
            severity = conflict.get('severity', 'LOW')
            desc = conflict.get('description', '未知冲突')
            conflict_type = conflict.get('type', 'UNKNOWN')
            
            suggestion = self._get_suggestion(conflict_type, severity)
            
            if severity == 'HIGH':
                self.conflict_icon_label.setText("⚠️")
                self.conflict_icon_label.setStyleSheet("font-size: 24px; color: #f14c4c;")
                self.conflict_title_label.setText(f"检测到高风险冲突 (处理方式: {conflict_mode})")
                self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #f14c4c;")
                self.conflict_status_frame.setStyleSheet("background-color: #2a1a1a; border: 1px solid #f14c4c; border-radius: 4px; padding: 10px;")
            elif severity == 'MEDIUM':
                self.conflict_icon_label.setText("⚠️")
                self.conflict_icon_label.setStyleSheet("font-size: 24px; color: #ff9800;")
                self.conflict_title_label.setText(f"检测到潜在问题 (处理方式: {conflict_mode})")
                self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ff9800;")
                self.conflict_status_frame.setStyleSheet("background-color: #2a251a; border: 1px solid #ff9800; border-radius: 4px; padding: 10px;")
            else:
                self.conflict_icon_label.setText("ℹ️")
                self.conflict_icon_label.setStyleSheet("font-size: 24px; color: #007acc;")
                self.conflict_title_label.setText(f"检测到次要问题 (处理方式: {conflict_mode})")
                self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #007acc;")
                self.conflict_status_frame.setStyleSheet("background-color: #1a202a; border: 1px solid #007acc; border-radius: 4px; padding: 10px;")
            
            self.conflict_desc_label.setText(f"问题描述: {desc}")
            self.conflict_suggestion_label.setText(f"💡 建议: {suggestion}")
        else:
            self.conflict_icon_label.setText("✓")
            self.conflict_icon_label.setStyleSheet("font-size: 24px; color: #4ec9b0;")
            self.conflict_title_label.setText(f"未检测到严重冲突 (处理方式: {conflict_mode})")
            self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #4ec9b0;")
            self.conflict_desc_label.setText("可以安全执行恢复操作")
            self.conflict_suggestion_label.setText("💡 建议: 点击'执行恢复'按钮完成恢复")
            self.conflict_status_frame.setStyleSheet("background-color: #1a2a1a; border: 1px solid #4ec9b0; border-radius: 4px; padding: 10px;")
    
    def _get_target_path(self) -> Optional[str]:
        if self.original_radio.isChecked():
            return None
        else:
            path = self.custom_path_edit.text()
            if path and path != "(未选择)":
                return path
            return None
    
    def _execute_recovery(self):
        if not self.current_log:
            return
        
        if self.current_log.get('is_recovered'):
            QMessageBox.information(self, "提示", "该文件已经恢复过了")
            return
        
        op_type = self.current_log.get('operation_type')
        file_name = self.current_log.get('file_name')
        target_path = self._get_target_path()
        conflict_mode = self._get_conflict_mode_text()
        
        target_display = "原路径" if not target_path else target_path
        
        reply = QMessageBox.question(
            self, "确认恢复",
            f"确定要恢复以下文件吗？\n\n"
            f"文件名: {file_name}\n"
            f"操作类型: {op_type}\n"
            f"目标路径: {target_display}\n"
            f"冲突处理: {conflict_mode}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = recovery_service.recover_file(self.current_log['id'], target_path)
            
            if result.get('success'):
                self.current_log['is_recovered'] = 1
                self.recover_btn.setEnabled(False)
                self.check_conflict_btn.setEnabled(False)
                self.original_radio.setEnabled(False)
                self.custom_radio.setEnabled(False)
                self.browse_btn.setEnabled(False)
                self.skip_radio.setEnabled(False)
                self.overwrite_radio.setEnabled(False)
                self.rename_radio.setEnabled(False)
                
                self.recovery_status_label.setText('<span style="color: #4ec9b0; font-weight: bold;">✓ 已恢复</span>')
                self.conflict_icon_label.setText("✓")
                self.conflict_title_label.setText("恢复成功！")
                self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #4ec9b0;")
                self.conflict_desc_label.setText("文件已成功恢复到目标位置")
                self.conflict_suggestion_label.setText("")
                
                QMessageBox.information(self, "恢复成功", f"文件 {file_name} 已成功恢复！")
            else:
                error_msg = result.get('error', '未知错误')
                self.conflict_icon_label.setText("✗")
                self.conflict_title_label.setText("恢复失败")
                self.conflict_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #f14c4c;")
                self.conflict_desc_label.setText(f"错误: {error_msg}")
                self.conflict_suggestion_label.setText("💡 建议: 检查目标路径权限或选择其他目录")
                QMessageBox.warning(self, "恢复失败", f"恢复失败: {error_msg}")

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
        main_layout.setSpacing(10)
        
        title_label = QLabel("详情与操作")
        title_label.setProperty("class", "title")
        title_label.setMinimumHeight(28)
        main_layout.addWidget(title_label)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                padding: 10px 18px;
                font-size: 13px;
                min-height: 30px;
            }
        """)
        
        self.preview_tab = self._create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "文件预览")
        
        self.diff_tab = self._create_diff_tab()
        self.tab_widget.addTab(self.diff_tab, "版本对比")
        
        self.history_tab = self._create_history_tab()
        self.tab_widget.addTab(self.history_tab, "历史版本")
        
        self.path_tab = self._create_path_tab()
        self.tab_widget.addTab(self.path_tab, "路径变更")
        
        self.recovery_preview_tab = self._create_recovery_preview_tab()
        self.tab_widget.addTab(self.recovery_preview_tab, "恢复预演")
        
        main_layout.addWidget(self.tab_widget)
        
        self._show_empty_state()
    
    def _create_preview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        info_group = QGroupBox("文件信息")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        
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
            row_layout.setSpacing(8)
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(80)
            label.setStyleSheet("font-size: 13px;")
            value_label = QLabel("-")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            value_label.setStyleSheet("font-size: 13px;")
            row_layout.addWidget(label)
            row_layout.addWidget(value_label, 1)
            info_layout.addLayout(row_layout)
            self.preview_info_labels[key] = value_label
        
        layout.addWidget(info_group)
        
        content_group = QGroupBox("内容预览")
        content_layout = QVBoxLayout(content_group)
        content_layout.setSpacing(8)
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["UTF-8", "GBK", "GB2312", "ISO-8859-1"])
        self.encoding_combo.setMinimumHeight(28)
        self.encoding_combo.setStyleSheet("font-size: 13px;")
        toolbar_layout.addWidget(QLabel("编码:"))
        toolbar_layout.addWidget(self.encoding_combo)
        
        self.refresh_preview_btn = QPushButton("刷新")
        self.refresh_preview_btn.setMinimumHeight(28)
        toolbar_layout.addWidget(self.refresh_preview_btn)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.setMinimumHeight(28)
        toolbar_layout.addWidget(self.export_btn)
        
        toolbar_layout.addStretch()
        content_layout.addLayout(toolbar_layout)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 11))
        self.preview_text.setLineWrapMode(QTextEdit.NoWrap)
        content_layout.addWidget(self.preview_text)
        
        layout.addWidget(content_group)
        
        return widget
    
    def _create_diff_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        
        toolbar_layout.addWidget(QLabel("版本 A:"))
        self.version_a_combo = QComboBox()
        self.version_a_combo.setMinimumHeight(28)
        self.version_a_combo.setStyleSheet("font-size: 13px;")
        toolbar_layout.addWidget(self.version_a_combo, 1)
        
        toolbar_layout.addWidget(QLabel("版本 B:"))
        self.version_b_combo = QComboBox()
        self.version_b_combo.setMinimumHeight(28)
        self.version_b_combo.setStyleSheet("font-size: 13px;")
        toolbar_layout.addWidget(self.version_b_combo, 1)
        
        self.compare_btn = QPushButton("对比")
        self.compare_btn.setMinimumHeight(28)
        self.compare_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        toolbar_layout.addWidget(self.compare_btn)
        
        layout.addLayout(toolbar_layout)
        
        diff_splitter = QSplitter(Qt.Vertical)
        
        unified_group = QGroupBox("统一对比视图")
        unified_layout = QVBoxLayout(unified_group)
        self.unified_diff_text = QTextEdit()
        self.unified_diff_text.setReadOnly(True)
        self.unified_diff_text.setFont(QFont("Consolas", 11))
        unified_layout.addWidget(self.unified_diff_text)
        diff_splitter.addWidget(unified_group)
        
        side_group = QGroupBox("并排对比视图")
        side_layout = QHBoxLayout(side_group)
        
        left_diff = QWidget()
        left_layout = QVBoxLayout(left_diff)
        left_layout.setSpacing(4)
        left_label = QLabel("旧版本:")
        left_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        left_layout.addWidget(left_label)
        self.old_diff_text = QTextEdit()
        self.old_diff_text.setReadOnly(True)
        self.old_diff_text.setFont(QFont("Consolas", 11))
        left_layout.addWidget(self.old_diff_text)
        
        right_diff = QWidget()
        right_layout = QVBoxLayout(right_diff)
        right_layout.setSpacing(4)
        right_label = QLabel("新版本:")
        right_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        right_layout.addWidget(right_label)
        self.new_diff_text = QTextEdit()
        self.new_diff_text.setReadOnly(True)
        self.new_diff_text.setFont(QFont("Consolas", 11))
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
        layout.setSpacing(10)
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        
        self.refresh_history_btn = QPushButton("刷新")
        self.refresh_history_btn.setMinimumHeight(28)
        toolbar_layout.addWidget(self.refresh_history_btn)
        
        self.restore_version_btn = QPushButton("恢复此版本")
        self.restore_version_btn.setProperty("class", "primary")
        self.restore_version_btn.setMinimumHeight(28)
        toolbar_layout.addWidget(self.restore_version_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "版本号", "大小", "Hash", "创建时间", "状态", "操作", "恢复"
        ])
        
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.history_table.setColumnWidth(0, 70)
        self.history_table.setColumnWidth(1, 100)
        self.history_table.setColumnWidth(3, 160)
        self.history_table.setColumnWidth(4, 70)
        self.history_table.setColumnWidth(5, 70)
        self.history_table.setColumnWidth(6, 100)
        
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setStyleSheet("""
            QTableView::item {
                padding: 8px;
                min-height: 26px;
            }
            QHeaderView::section {
                padding: 10px;
                min-height: 30px;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def _create_path_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        info_group = QGroupBox("路径变更记录")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        
        self.path_labels = {}
        path_fields = [
            ("original", "原始路径"),
            ("current", "当前路径"),
            ("changes", "变更次数"),
        ]
        
        for key, label_text in path_fields:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(80)
            label.setStyleSheet("font-size: 13px;")
            value_label = QLabel("-")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            value_label.setStyleSheet("font-family: Consolas; font-size: 12px;")
            row_layout.addWidget(label)
            row_layout.addWidget(value_label, 1)
            info_layout.addLayout(row_layout)
            self.path_labels[key] = value_label
        
        layout.addWidget(info_group)
        
        history_group = QGroupBox("变更历史")
        history_layout = QVBoxLayout(history_group)
        history_layout.setSpacing(8)
        
        self.path_history_table = QTableWidget()
        self.path_history_table.setColumnCount(5)
        self.path_history_table.setHorizontalHeaderLabels([
            "序号", "操作类型", "原路径", "新路径", "时间"
        ])
        
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
    
    def _create_recovery_preview_tab(self) -> QWidget:
        self.recovery_preview_widget = RecoveryPreviewWidget()
        return self.recovery_preview_widget
    
    def _show_empty_state(self):
        empty_text = """
        <div style="text-align: center; padding: 60px; color: #858585;">
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
        
        self.recovery_preview_widget.set_log_data(None)
    
    def display_log_details(self, log_data: Dict[str, Any]):
        self.current_log = log_data
        
        self._update_preview_info(log_data)
        self._update_preview_content(log_data)
        self._update_version_combos(log_data)
        self._update_history_table(log_data)
        self._update_path_info(log_data)
        
        self.recovery_preview_widget.set_log_data(log_data)
        
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
            f'<span style="color: {risk_info["color"]}; font-weight: bold; font-size: 13px;">{risk_info["name"]}</span>'
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
            
            action_item = QTableWidgetItem("预览")
            action_item.setTextAlignment(Qt.AlignCenter)
            action_item.setForeground(QColor("#007acc"))
            self.history_table.setItem(row, 5, action_item)
            
            is_recovered = self.current_log.get('is_recovered', 0) if self.current_log else False
            
            restore_btn = QPushButton("恢复版本")
            if is_recovered:
                restore_btn.setEnabled(False)
                restore_btn.setStyleSheet("color: #858585; font-size: 12px;")
            else:
                restore_btn.setProperty("class", "primary")
                restore_btn.setStyleSheet("font-size: 12px;")
                restore_btn.clicked.connect(lambda checked, s=snapshot: self._restore_snapshot(s))
            self.history_table.setCellWidget(row, 6, restore_btn)
    
    def _restore_snapshot(self, snapshot: Dict):
        if not self.current_log:
            return
        
        if self.current_log.get('is_recovered'):
            QMessageBox.information(self, "提示", "该操作已恢复，无法再恢复历史版本")
            return
        
        version = snapshot.get('version', 1)
        file_name = snapshot.get('file_name', '')
        
        reply = QMessageBox.question(
            self, "确认恢复",
            f"确定要恢复版本 {version} 吗？\n\n文件: {file_name}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = recovery_service.restore_version(
                snapshot.get('file_id'),
                version
            )
            
            if result.get('success'):
                QMessageBox.information(self, "恢复成功", f"版本 {version} 已成功恢复！")
            else:
                error_msg = result.get('error', '未知错误')
                QMessageBox.warning(self, "恢复失败", f"恢复失败: {error_msg}")
    
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
