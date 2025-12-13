"""
Modern Dark Theme for Admin Panel

Professional dark color scheme optimized for long viewing sessions.
"""

# Color Palette
COLORS = {
    # Background colors
    'bg_primary': '#1e1e2e',      # Main background
    'bg_secondary': '#2a2a3e',    # Secondary panels
    'bg_tertiary': '#363650',     # Elevated elements
    'bg_input': '#2d2d44',        # Input fields

    # Text colors
    'text_primary': '#e0e0e0',    # Primary text
    'text_secondary': '#a0a0b0',  # Secondary text
    'text_disabled': '#606070',   # Disabled text

    # Accent colors
    'accent_blue': '#61afef',     # Primary actions
    'accent_green': '#98c379',    # Success states
    'accent_red': '#e06c75',      # Danger/delete
    'accent_yellow': '#e5c07b',   # Warnings
    'accent_purple': '#c678dd',   # Special highlights

    # Border colors
    'border_default': '#3e3e54',
    'border_focus': '#61afef',
    'border_hover': '#5a5a70',

    # Status colors
    'status_active': '#98c379',
    'status_paused': '#e5c07b',
    'status_draft': '#a0a0b0',
    'status_error': '#e06c75',
}


def get_stylesheet() -> str:
    """
    Get the complete dark theme stylesheet.

    Returns CSS-like stylesheet for PyQt6 application.
    """
    return f"""
    /* ===== GLOBAL STYLES ===== */
    QMainWindow, QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
    }}

    /* ===== GROUP BOXES ===== */
    QGroupBox {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 8px;
        margin-top: 16px;
        padding: 16px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        color: {COLORS['text_primary']};
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        background-color: {COLORS['bg_secondary']};
    }}

    /* ===== BUTTONS ===== */
    QPushButton {{
        background-color: {COLORS['accent_blue']};
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        min-width: 90px;
    }}

    QPushButton:hover {{
        background-color: #5199d8;
    }}

    QPushButton:pressed {{
        background-color: #4088c7;
        padding-top: 11px;
        padding-bottom: 9px;
    }}

    QPushButton:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_disabled']};
    }}

    QPushButton#deleteButton {{
        background-color: {COLORS['accent_red']};
    }}

    QPushButton#deleteButton:hover {{
        background-color: #d35c6b;
    }}

    QPushButton#successButton {{
        background-color: {COLORS['accent_green']};
    }}

    QPushButton#successButton:hover {{
        background-color: #88b369;
    }}

    QPushButton#warningButton {{
        background-color: {COLORS['accent_yellow']};
        color: {COLORS['bg_primary']};
    }}

    /* ===== INPUT FIELDS ===== */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 6px;
        padding: 8px 12px;
        selection-background-color: {COLORS['accent_blue']};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLORS['border_focus']};
        padding: 7px 11px;
    }}

    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled,
    QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_disabled']};
    }}

    /* ===== COMBO BOX ===== */
    QComboBox {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 100px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['border_hover']};
    }}

    QComboBox:focus {{
        border: 2px solid {COLORS['border_focus']};
        padding: 7px 11px;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS['text_secondary']};
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        selection-background-color: {COLORS['accent_blue']};
        outline: none;
    }}

    /* ===== TABLES ===== */
    QTableWidget {{
        background-color: {COLORS['bg_secondary']};
        alternate-background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 8px;
        gridline-color: {COLORS['border_default']};
        selection-background-color: {COLORS['accent_blue']};
    }}

    QTableWidget::item {{
        padding: 10px;
        border: none;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['accent_blue']};
        color: #ffffff;
    }}

    QTableWidget::item:hover {{
        background-color: {COLORS['bg_tertiary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        padding: 12px;
        border: none;
        border-right: 1px solid {COLORS['border_default']};
        border-bottom: 2px solid {COLORS['accent_blue']};
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }}

    QHeaderView::section:first {{
        border-top-left-radius: 8px;
    }}

    QHeaderView::section:last {{
        border-right: none;
        border-top-right-radius: 8px;
    }}

    /* ===== TAB WIDGET ===== */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border_default']};
        background-color: {COLORS['bg_secondary']};
        border-radius: 8px;
        top: -1px;
    }}

    QTabBar::tab {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_secondary']};
        padding: 12px 24px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['accent_blue']};
        font-weight: 600;
        border-bottom: 2px solid {COLORS['accent_blue']};
    }}

    QTabBar::tab:hover {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}

    /* ===== STATUS BAR ===== */
    QStatusBar {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border-top: 1px solid {COLORS['border_default']};
        font-size: 12px;
    }}

    /* ===== SCROLL BAR ===== */
    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 12px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['bg_tertiary']};
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['border_hover']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* Horizontal */
    QScrollBar:horizontal {{
        background-color: {COLORS['bg_secondary']};
        height: 12px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {COLORS['bg_tertiary']};
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['border_hover']};
    }}

    /* ===== LABELS ===== */
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}

    QLabel#statLabel {{
        background-color: {COLORS['bg_tertiary']};
        border-left: 4px solid {COLORS['accent_blue']};
        border-radius: 6px;
        padding: 12px 16px;
        font-weight: 600;
        font-size: 14px;
    }}

    QLabel#metricValue {{
        font-size: 28px;
        font-weight: 700;
        color: {COLORS['accent_blue']};
    }}

    QLabel#successLabel {{
        color: {COLORS['status_active']};
    }}

    QLabel#errorLabel {{
        color: {COLORS['status_error']};
    }}

    /* ===== PROGRESS BAR ===== */
    QProgressBar {{
        background-color: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 6px;
        text-align: center;
        color: {COLORS['text_primary']};
        font-weight: 600;
    }}

    QProgressBar::chunk {{
        background-color: {COLORS['accent_blue']};
        border-radius: 5px;
    }}

    /* ===== MENU BAR ===== */
    QMenuBar {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border-bottom: 1px solid {COLORS['border_default']};
        padding: 4px;
    }}

    QMenuBar::item {{
        padding: 8px 12px;
        background-color: transparent;
        border-radius: 4px;
    }}

    QMenuBar::item:selected {{
        background-color: {COLORS['accent_blue']};
    }}

    QMenu {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 6px;
        padding: 8px;
    }}

    QMenu::item {{
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['accent_blue']};
    }}

    /* ===== CHECKBOX ===== */
    QCheckBox {{
        color: {COLORS['text_primary']};
        spacing: 8px;
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {COLORS['border_default']};
        border-radius: 4px;
        background-color: {COLORS['bg_input']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_blue']};
        border-color: {COLORS['accent_blue']};
        image: url(none);  /* Add checkmark icon if available */
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLORS['border_hover']};
    }}

    /* ===== DIALOG ===== */
    QDialog {{
        background-color: {COLORS['bg_primary']};
    }}

    /* ===== DATE EDIT ===== */
    QDateEdit {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 6px;
        padding: 8px 12px;
    }}

    QDateEdit:focus {{
        border: 2px solid {COLORS['border_focus']};
    }}

    QDateEdit::drop-down {{
        border: none;
        width: 20px;
    }}

    /* ===== TOOLTIPS ===== */
    QToolTip {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 4px;
        padding: 6px;
    }}
    """


def get_colors() -> dict:
    """Get the color palette."""
    return COLORS.copy()
