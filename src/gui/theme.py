"""
PyRestForge - Design Tokens & Dark/Light Theme Stylesheets (PySide6)
"""

from typing import Dict


class ThemeColors:
    # Backgrounds
    BG_APP_ROOT = "#0F1117"
    BG_SIDEBAR = "#161922"
    BG_PANEL = "#1F2430"
    BG_INPUT = "#12151D"
    BG_HOVER = "#282E3E"
    BG_SELECTED = "#32394D"

    # Accents & Borders
    ACCENT_PRIMARY = "#7C3AED"      # Vibrant Purple
    ACCENT_HOVER = "#8B5CF6"
    ACCENT_SECONDARY = "#06B6D4"    # Cyan
    BORDER_SUBTLE = "#2D3342"
    BORDER_FOCUS = "#7C3AED"

    # Text Colors
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"

    # HTTP Method Badges
    BADGE_GET = "#10B981"           # Emerald Green
    BADGE_POST = "#6366F1"          # Indigo Blue
    BADGE_PUT = "#F59E0B"           # Amber Orange
    BADGE_PATCH = "#8B5CF6"         # Purple
    BADGE_DELETE = "#EF4444"        # Crimson Red
    BADGE_OPTIONS = "#64748B"       # Slate
    BADGE_HEAD = "#64748B"

    # Status Code Colors
    STATUS_2XX = "#10B981"
    STATUS_3XX = "#3B82F6"
    STATUS_4XX = "#F59E0B"
    STATUS_5XX = "#EF4444"


def get_method_color(method: str) -> str:
    """Returns color code for HTTP method badge."""
    m = method.upper().strip()
    mapping = {
        "GET": ThemeColors.BADGE_GET,
        "POST": ThemeColors.BADGE_POST,
        "PUT": ThemeColors.BADGE_PUT,
        "PATCH": ThemeColors.BADGE_PATCH,
        "DELETE": ThemeColors.BADGE_DELETE,
        "OPTIONS": ThemeColors.BADGE_OPTIONS,
        "HEAD": ThemeColors.BADGE_HEAD,
    }
    return mapping.get(m, ThemeColors.BADGE_OPTIONS)


def get_status_color(status_code: int) -> str:
    """Returns status badge color."""
    if 200 <= status_code < 300:
        return ThemeColors.STATUS_2XX
    elif 300 <= status_code < 400:
        return ThemeColors.STATUS_3XX
    elif 400 <= status_code < 500:
        return ThemeColors.STATUS_4XX
    elif status_code >= 500:
        return ThemeColors.STATUS_5XX
    return ThemeColors.TEXT_MUTED


DARK_STYLESHEET = f"""
/* Global Reset & Base Canvas */
QWidget {{
    background-color: {ThemeColors.BG_APP_ROOT};
    color: {ThemeColors.TEXT_PRIMARY};
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: {ThemeColors.ACCENT_PRIMARY};
    selection-color: #FFFFFF;
    outline: none;
}}

/* Main Window & Splitters */
QMainWindow {{
    background-color: {ThemeColors.BG_APP_ROOT};
}}

QSplitter::handle {{
    background-color: {ThemeColors.BORDER_SUBTLE};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {ThemeColors.BORDER_SUBTLE};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ThemeColors.ACCENT_PRIMARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {ThemeColors.BORDER_SUBTLE};
    min-width: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {ThemeColors.ACCENT_PRIMARY};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    width: 0px;
}}

/* Tree View (Sidebar Collections) */
QTreeView {{
    background-color: {ThemeColors.BG_SIDEBAR};
    border: none;
    border-right: 1px solid {ThemeColors.BORDER_SUBTLE};
    padding: 6px;
    font-size: 13px;
}}

QTreeView::item {{
    height: 32px;
    border-radius: 6px;
    padding-left: 6px;
    color: {ThemeColors.TEXT_PRIMARY};
}}

QTreeView::item:hover {{
    background-color: {ThemeColors.BG_HOVER};
}}

QTreeView::item:selected {{
    background-color: {ThemeColors.BG_SELECTED};
    color: #FFFFFF;
}}

/* Line Edits & Text Editors */
QLineEdit {{
    background-color: {ThemeColors.BG_INPUT};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 6px 10px;
    color: {ThemeColors.TEXT_PRIMARY};
    font-size: 13px;
}}

QLineEdit:focus {{
    border: 1px solid {ThemeColors.BORDER_FOCUS};
}}

QPlainTextEdit, QTextEdit {{
    background-color: {ThemeColors.BG_INPUT};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    color: {ThemeColors.TEXT_PRIMARY};
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    padding: 8px;
}}

QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {ThemeColors.BORDER_FOCUS};
}}

/* Push Buttons */
QPushButton {{
    background-color: {ThemeColors.BG_PANEL};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 7px 14px;
    color: {ThemeColors.TEXT_PRIMARY};
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {ThemeColors.BG_HOVER};
    border-color: {ThemeColors.ACCENT_PRIMARY};
}}

QPushButton:pressed {{
    background-color: {ThemeColors.BG_SELECTED};
}}

QPushButton#primaryButton, QPushButton#sendButton {{
    background-color: {ThemeColors.ACCENT_PRIMARY};
    border: 1px solid {ThemeColors.ACCENT_PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
}}

QPushButton#primaryButton:hover, QPushButton#sendButton:hover {{
    background-color: {ThemeColors.ACCENT_HOVER};
    border-color: {ThemeColors.ACCENT_HOVER};
}}

QPushButton#cancelButton {{
    background-color: {ThemeColors.BADGE_DELETE};
    border: 1px solid {ThemeColors.BADGE_DELETE};
    color: #FFFFFF;
    font-weight: 600;
}}

/* Combo Boxes */
QComboBox {{
    background-color: {ThemeColors.BG_PANEL};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 6px 12px;
    color: {ThemeColors.TEXT_PRIMARY};
    font-weight: 500;
}}

QComboBox:hover {{
    border-color: {ThemeColors.ACCENT_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {ThemeColors.BG_PANEL};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    selection-background-color: {ThemeColors.ACCENT_PRIMARY};
    selection-color: #FFFFFF;
    padding: 4px;
}}

/* Tabs */
QTabWidget::pane {{
    border: none;
    background-color: {ThemeColors.BG_APP_ROOT};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {ThemeColors.TEXT_SECONDARY};
    padding: 8px 16px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}}

QTabBar::tab:hover {{
    color: {ThemeColors.TEXT_PRIMARY};
}}

QTabBar::tab:selected {{
    color: {ThemeColors.ACCENT_PRIMARY};
    border-bottom: 2px solid {ThemeColors.ACCENT_PRIMARY};
}}

/* Tables */
QTableWidget {{
    background-color: {ThemeColors.BG_APP_ROOT};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    gridline-color: {ThemeColors.BORDER_SUBTLE};
}}

QTableWidget::item {{
    padding: 6px;
}}

QTableWidget::item:selected {{
    background-color: {ThemeColors.BG_SELECTED};
    color: #FFFFFF;
}}

QHeaderView::section {{
    background-color: {ThemeColors.BG_PANEL};
    color: {ThemeColors.TEXT_SECONDARY};
    padding: 6px;
    border: none;
    border-right: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE};
    font-weight: 600;
    font-size: 12px;
}}

/* Checkboxes */
QCheckBox {{
    color: {ThemeColors.TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    background-color: {ThemeColors.BG_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {ThemeColors.ACCENT_PRIMARY};
    border-color: {ThemeColors.ACCENT_PRIMARY};
}}

/* Status Bar */
QStatusBar {{
    background-color: {ThemeColors.BG_SIDEBAR};
    color: {ThemeColors.TEXT_SECONDARY};
    border-top: 1px solid {ThemeColors.BORDER_SUBTLE};
    font-size: 12px;
}}
"""
