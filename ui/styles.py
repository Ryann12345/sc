from config.app_config import AppConfig

DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #252526;
    color: #d4d4d4;
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QFrame {
    border: none;
}

QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 24px;
    color: #d4d4d4;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #2d2d2d;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QPushButton[class="primary"] {
    background-color: #0e639c;
    border-color: #1177bb;
}

QPushButton[class="primary"]:hover {
    background-color: #1177bb;
}

QPushButton[class="danger"] {
    background-color: #c50f1f;
    border-color: #e81123;
}

QPushButton[class="danger"]:hover {
    background-color: #e81123;
}

QPushButton[class="success"] {
    background-color: #107c10;
    border-color: #139c13;
}

QPushButton[class="success"]:hover {
    background-color: #139c13;
}

QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 10px;
    color: #d4d4d4;
}

QLineEdit:focus {
    border-color: #007acc;
}

QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 10px;
    color: #d4d4d4;
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
}

QTreeView {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #d4d4d4;
}

QTreeView::item {
    padding: 4px;
}

QTreeView::item:selected {
    background-color: #094771;
}

QTreeView::item:hover {
    background-color: #2a2d2e;
}

QTreeView::branch {
    background-color: #1e1e1e;
}

QTableView {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #d4d4d4;
    gridline-color: #3c3c3c;
    selection-background-color: #094771;
    selection-color: #ffffff;
}

QTableView::item {
    padding: 6px;
}

QTableView::item:selected {
    background-color: #094771;
}

QTableView::item:hover {
    background-color: #2a2d2e;
}

QHeaderView::section {
    background-color: #3c3c3c;
    border: none;
    border-bottom: 1px solid #555555;
    padding: 8px;
    font-weight: bold;
    color: #d4d4d4;
}

QHeaderView::section:hover {
    background-color: #4a4a4a;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #969696;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    border-bottom: 1px solid #1e1e1e;
    color: #d4d4d4;
}

QTabBar::tab:hover {
    background-color: #3c3c3c;
}

QSplitter::handle {
    background-color: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QSplitter::handle:hover {
    background-color: #007acc;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 14px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 14px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #424242;
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 16px;
    padding: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}

QCheckBox::indicator:hover {
    border-color: #666666;
}

QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 8px;
    background-color: #3c3c3c;
}

QRadioButton::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}

QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #d4d4d4;
    font-family: 'Consolas', 'Courier New', monospace;
}

QPlainTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #d4d4d4;
    font-family: 'Consolas', 'Courier New', monospace;
}

QLabel[class="title"] {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

QLabel[class="subtitle"] {
    font-size: 12px;
    color: #858585;
}

QLabel[class="risk-high"] {
    color: #f14c4c;
    font-weight: bold;
}

QLabel[class="risk-medium"] {
    color: #cca700;
    font-weight: bold;
}

QLabel[class="risk-low"] {
    color: #4ec9b0;
    font-weight: bold;
}

QLabel[class="empty-state"] {
    font-size: 14px;
    color: #858585;
}

QStatusBar {
    background-color: #007acc;
    color: #ffffff;
}

QMenuBar {
    background-color: #3c3c3c;
    border-bottom: 1px solid #555555;
}

QMenuBar::item {
    padding: 8px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #094771;
}

QMenu {
    background-color: #252526;
    border: 1px solid #454545;
}

QMenu::item {
    padding: 8px 24px;
}

QMenu::item:selected {
    background-color: #094771;
}

QToolBar {
    background-color: #3c3c3c;
    border: none;
    padding: 4px;
    spacing: 4px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px;
}

QToolButton:hover {
    background-color: #4a4a4a;
    border-color: #555555;
}

QToolButton:pressed {
    background-color: #2d2d2d;
}

QProgressBar {
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    background-color: #3c3c3c;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 3px;
}

QSplitter {
    background-color: #1e1e1e;
}
"""

LIGHT_STYLE = """
QMainWindow {
    background-color: #f3f3f3;
}

QWidget {
    background-color: #ffffff;
    color: #333333;
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QFrame {
    border: none;
}

QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 24px;
    color: #333333;
}

QPushButton:hover {
    background-color: #e5e5e5;
    border-color: #bbbbbb;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #999999;
}

QPushButton[class="primary"] {
    background-color: #0078d4;
    border-color: #0078d4;
    color: #ffffff;
}

QPushButton[class="primary"]:hover {
    background-color: #106ebe;
}

QPushButton[class="danger"] {
    background-color: #dc3545;
    border-color: #dc3545;
    color: #ffffff;
}

QPushButton[class="danger"]:hover {
    background-color: #c82333;
}

QPushButton[class="success"] {
    background-color: #28a745;
    border-color: #28a745;
    color: #ffffff;
}

QPushButton[class="success"]:hover {
    background-color: #218838;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 10px;
    color: #333333;
}

QLineEdit:focus {
    border-color: #0078d4;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 10px;
    color: #333333;
}

QComboBox:hover {
    border-color: #bbbbbb;
}

QComboBox:focus {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    selection-background-color: #cce5ff;
}

QTreeView {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    border-radius: 4px;
    color: #333333;
}

QTreeView::item {
    padding: 4px;
}

QTreeView::item:selected {
    background-color: #cce5ff;
}

QTreeView::item:hover {
    background-color: #f5f5f5;
}

QTableView {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    border-radius: 4px;
    color: #333333;
    gridline-color: #eeeeee;
    selection-background-color: #cce5ff;
}

QTableView::item {
    padding: 6px;
}

QTableView::item:selected {
    background-color: #cce5ff;
}

QTableView::item:hover {
    background-color: #f5f5f5;
}

QHeaderView::section {
    background-color: #f0f0f0;
    border: none;
    border-bottom: 1px solid #dddddd;
    padding: 8px;
    font-weight: bold;
    color: #333333;
}

QTabWidget::pane {
    border: 1px solid #dddddd;
    border-radius: 4px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f5f5f5;
    border: 1px solid #dddddd;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #666666;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: 1px solid #ffffff;
    color: #333333;
}

QTabBar::tab:hover {
    background-color: #e5e5e5;
}

QSplitter::handle {
    background-color: #dddddd;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QSplitter::handle:hover {
    background-color: #0078d4;
}

QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 14px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 14px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #c0c0c0;
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QGroupBox {
    border: 1px solid #dddddd;
    border-radius: 4px;
    margin-top: 16px;
    padding: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #cccccc;
    border-radius: 3px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #cccccc;
    border-radius: 8px;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    border-radius: 4px;
    color: #333333;
    font-family: 'Consolas', 'Courier New', monospace;
}

QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    border-radius: 4px;
    color: #333333;
    font-family: 'Consolas', 'Courier New', monospace;
}

QLabel[class="title"] {
    font-size: 16px;
    font-weight: bold;
    color: #333333;
}

QLabel[class="subtitle"] {
    font-size: 12px;
    color: #888888;
}

QLabel[class="risk-high"] {
    color: #dc3545;
    font-weight: bold;
}

QLabel[class="risk-medium"] {
    color: #ffc107;
    font-weight: bold;
}

QLabel[class="risk-low"] {
    color: #28a745;
    font-weight: bold;
}

QLabel[class="empty-state"] {
    font-size: 14px;
    color: #888888;
}

QStatusBar {
    background-color: #0078d4;
    color: #ffffff;
}

QMenuBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #dddddd;
}

QMenuBar::item {
    padding: 8px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #cce5ff;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #dddddd;
}

QMenu::item {
    padding: 8px 24px;
}

QMenu::item:selected {
    background-color: #cce5ff;
}

QToolBar {
    background-color: #f0f0f0;
    border: none;
    padding: 4px;
    spacing: 4px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px;
}

QToolButton:hover {
    background-color: #e5e5e5;
    border-color: #dddddd;
}

QToolButton:pressed {
    background-color: #d0d0d0;
}

QProgressBar {
    border: 1px solid #dddddd;
    border-radius: 4px;
    text-align: center;
    background-color: #f5f5f5;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}

QSplitter {
    background-color: #f3f3f3;
}
"""

def get_style():
    return DARK_STYLE if AppConfig.DARK_THEME else LIGHT_STYLE
