"""
Professional Muted Dark Theme for Admin Panel (Designer-grade / Sophisticated)

Что улучшено:
- Фоны: ровнее и чуть “подняты” (не проваливаются в чёрный на macOS)
- Акцент: менее неоновый, но всё ещё заметный
- Семантика: цвета спокойнее и гармоничнее на navy фоне
- Границы: читаются лучше, но без “рамок как в Excel”
"""

# Professional Muted Color Palette (Designer-grade sophistication)
COLORS = {
    # Background layers — cohesive navy-slate ramp (subtle, macOS-friendly)
    'bg_deepest':   '#0A0F1C',  # dialogs/overlays/backdrop - deeper, more muted
    'bg_primary':   '#0E141F',  # app base - softer navy
    'bg_secondary': '#161D2A',  # panels/cards - balanced elevation
    'bg_tertiary':  '#1D2533',  # hovers/interactive surfaces - subtle lift
    'bg_elevated':  '#242F3D',  # highest elevation (headers/menus) - refined
    'bg_input':     '#131A25',  # inputs (slightly “inkier” than panels)

    # Text hierarchy — sophisticated contrast, less harsh
    'text_primary':     '#F1F3F5',  # slightly warmer white
    'text_secondary':   '#B8C2CC',  # muted gray-blue
    'text_tertiary':    '#8894A3',  # deeper tertiary
    'text_disabled':    '#5F6B7A',  # professional disabled state
    'text_placeholder': '#6B7888',  # balanced placeholder

    # Brand & Primary Actions — sophisticated teal (muted, professional)
    'primary':         '#4A9EFF',  # softer, more professional blue
    'primary_hover':   '#3D87E6',  # refined hover state
    'primary_pressed': '#3171CC',  # deeper pressed state
    'primary_muted':   '#1A2B3D',  # very muted background accent

    # Semantic colors — enterprise-grade, muted and professional
    'success':       '#5CB85C',  # softer green, less aggressive
    'success_muted': '#1A2A1F',  # deep muted green background
    'warning':       '#F0AD4E',  # refined amber, less yellow
    'warning_muted': '#2A2318',  # sophisticated muted background
    'danger':        '#D9534F',  # professional red, not alarmist
    'danger_muted':  '#2A1F1E',  # deep muted red background
    'info':          '#5BC0DE',  # calm blue, informational
    'info_muted':    '#1A242A',  # muted blue background

    # Status indicators — refined and professional
    'status_active':    '#5CB85C',  # consistent with success
    'status_paused':    '#F0AD4E',  # consistent with warning
    'status_draft':     '#8E99A8',  # neutral, professional gray
    'status_error':     '#D9534F',  # consistent with danger
    'status_completed': '#5BC0DE',  # consistent with info

    # Borders & Dividers — sophisticated and subtle
    'border_subtle':  '#2A3441',  # very subtle divider
    'border_default': '#374151',  # professional border
    'border_strong':  '#4B5563',  # stronger but still muted
    'border_focus':   '#4A9EFF',  # matches primary
    'border_hover':   '#556068',  # sophisticated hover

    # Data visualization — muted, professional palette
    'chart_1': '#4A9EFF',  # primary blue
    'chart_2': '#D9534F',  # professional red
    'chart_3': '#5CB85C',  # success green
    'chart_4': '#F0AD4E',  # warning amber
    'chart_5': '#5BC0DE',  # info blue
    'chart_6': '#9B59B6',  # sophisticated purple

    # Special effects — refined and subtle
    'shadow_default': 'rgba(0, 0, 0, 0.25)',  # softer shadow
    'shadow_strong':  'rgba(0, 0, 0, 0.45)',  # professional depth
    'overlay_dark':   'rgba(10, 15, 28, 0.85)',  # sophisticated overlay
    'shimmer':        'rgba(74, 158, 255, 0.04)',  # subtle shimmer
}


def get_colors() -> dict:
    return COLORS


def get_stylesheet() -> str:
    """
    Complete Neo-Professional dark theme stylesheet (PyQt6), macOS refined.
    Focus styles: constant 2px borders to avoid layout jumping.
    """
    return f"""
    /* ========================================
       GLOBAL STYLES & FOUNDATION
       ======================================== */

    QMainWindow, QWidget, QDialog {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: -apple-system, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
        selection-background-color: {COLORS['primary_muted']};
        selection-color: {COLORS['text_primary']};
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_strong']};
        padding: 6px 10px;
        border-radius: 6px;
    }}

    /* ========================================
       GROUP BOXES - Elevated panels
       ======================================== */

    QGroupBox {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 10px;
        margin-top: 18px;
        padding: 20px 16px 16px 16px;
        font-weight: 600;
        font-size: 12px;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }}

    QGroupBox::title {{
        color: {COLORS['text_secondary']};
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        padding: 0 8px;
        background-color: {COLORS['bg_secondary']};
    }}

    /* ========================================
       BUTTONS - Primary actions (no focus jump)
       ======================================== */

    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['bg_deepest']};
        border: 2px solid transparent;
        border-radius: 7px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
        min-width: 90px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['primary_pressed']};
    }}

    QPushButton:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_disabled']};
    }}

    QPushButton:focus {{
        border-color: {COLORS['border_focus']};
    }}

    /* Button variants */
    QPushButton#deleteButton {{
        background-color: {COLORS['danger']};
        color: {COLORS['text_primary']};
    }}

    QPushButton#deleteButton:hover {{
        background-color: #ff6a93;
    }}

    QPushButton#successButton {{
        background-color: {COLORS['success']};
        color: {COLORS['bg_deepest']};
    }}

    QPushButton#successButton:hover {{
        background-color: #55e1b6;
    }}

    QPushButton#warningButton {{
        background-color: {COLORS['warning']};
        color: {COLORS['bg_deepest']};
    }}

    QPushButton#warningButton:hover {{
        background-color: #f7c36b;
    }}

    QPushButton#secondaryButton {{
        background-color: transparent;
        border: 2px solid {COLORS['border_default']};
        color: {COLORS['text_primary']};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {COLORS['bg_tertiary']};
        border-color: {COLORS['border_hover']};
    }}

    /* ========================================
       INPUT FIELDS - Forms & data entry
       (constant 2px border => no layout jump)
       ======================================== */

    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_secondary']};
        border: 2px solid {COLORS['border_default']};
        border-radius: 7px;
        padding: 9px 13px;
        selection-background-color: {COLORS['primary_muted']};
        selection-color: {COLORS['text_primary']};
        font-size: 13px;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {COLORS['border_focus']};
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}

    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_disabled']};
        border-color: {COLORS['border_subtle']};
    }}

    QLineEdit::placeholder {{
        color: {COLORS['text_placeholder']};
    }}

    /* ========================================
       SPINBOXES - Numeric inputs
       ======================================== */

    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_secondary']};
        border: 2px solid {COLORS['border_default']};
        border-radius: 7px;
        padding: 9px 13px;
        selection-background-color: {COLORS['primary_muted']};
        font-size: 13px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {COLORS['border_focus']};
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}

    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        background-color: transparent;
        border: none;
        width: 20px;
        margin-right: 4px;
    }}

    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: transparent;
        border: none;
        width: 20px;
        margin-right: 4px;
    }}

    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {COLORS['bg_tertiary']};
        border-radius: 4px;
    }}

    /* ========================================
       COMBO BOXES - Dropdowns
       ======================================== */

    QComboBox {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_secondary']};
        border: 2px solid {COLORS['border_default']};
        border-radius: 7px;
        padding: 9px 13px;
        min-width: 120px;
        font-size: 13px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['border_hover']};
        background-color: {COLORS['bg_tertiary']};
    }}

    QComboBox:focus {{
        border-color: {COLORS['border_focus']};
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 32px;
        margin-right: 4px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS['text_secondary']};
        margin-right: 8px;
    }}

    QComboBox::down-arrow:hover {{
        border-top-color: {COLORS['primary']};
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_strong']};
        border-radius: 7px;
        selection-background-color: {COLORS['primary']};
        selection-color: {COLORS['bg_deepest']};
        outline: none;
        padding: 4px;
    }}

    QComboBox QAbstractItemView::item {{
        padding: 8px 12px;
        border-radius: 4px;
        margin: 2px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS['bg_tertiary']};
    }}

    /* ========================================
       TABLES - Data grids
       ======================================== */

    QTableWidget {{
        background-color: {COLORS['bg_secondary']};
        alternate-background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 10px;
        gridline-color: {COLORS['border_subtle']};
        selection-background-color: {COLORS['primary_muted']};
        selection-color: {COLORS['primary']};
    }}

    QTableWidget::item {{
        padding: 12px 16px;
        border: none;
        font-size: 13px;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['primary_muted']};
        color: {COLORS['primary']};
    }}

    QTableWidget::item:hover {{
        background-color: {COLORS['bg_tertiary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_secondary']};
        padding: 14px 16px;
        border: none;
        border-right: 1px solid {COLORS['border_subtle']};
        border-bottom: 2px solid {COLORS['primary']};
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }}

    QHeaderView::section:first {{
        border-top-left-radius: 10px;
    }}

    QHeaderView::section:last {{
        border-right: none;
        border-top-right-radius: 10px;
    }}

    QHeaderView::section:hover {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['primary']};
    }}

    /* ========================================
       TAB WIDGET - Navigation tabs
       ======================================== */

    QTabWidget::pane {{
        border: 1px solid {COLORS['border_default']};
        background-color: {COLORS['bg_secondary']};
        border-radius: 10px;
        top: -1px;
    }}

    QTabBar::tab {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
        padding: 12px 24px;
        margin-right: 4px;
        margin-bottom: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
        font-size: 13px;
        min-width: 100px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['primary']};
        font-weight: 600;
        border-bottom: 3px solid {COLORS['primary']};
        margin-bottom: 0px;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
    }}

    /* ========================================
       STATUS BAR - Bottom status
       ======================================== */

    QStatusBar {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['border_default']};
        font-size: 12px;
        padding: 6px 16px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* ========================================
       SCROLL BARS - Custom scrolling
       ======================================== */

    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 14px;
        margin: 0;
        border-radius: 7px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['bg_elevated']};
        min-height: 30px;
        border-radius: 7px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['border_hover']};
    }}

    QScrollBar::handle:vertical:pressed {{
        background-color: {COLORS['primary_pressed']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background-color: {COLORS['bg_secondary']};
        height: 14px;
        margin: 0;
        border-radius: 7px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {COLORS['bg_elevated']};
        min-width: 30px;
        border-radius: 7px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['border_hover']};
    }}

    QScrollBar::handle:horizontal:pressed {{
        background-color: {COLORS['primary_pressed']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ========================================
       LABELS - Text display
       ======================================== */

    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
        border: none;
    }}

    QLabel#statLabel {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 {COLORS['primary_muted']},
                                    stop:1 {COLORS['bg_elevated']});
        border-left: 4px solid {COLORS['primary']};
        border-radius: 8px;
        padding: 14px 18px;
        font-weight: 600;
        font-size: 14px;
        color: {COLORS['text_primary']};
    }}

    QLabel#metricValue {{
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['primary']};
        letter-spacing: -0.5px;
    }}

    QLabel#successLabel {{
        color: {COLORS['status_active']};
        font-weight: 600;
        font-size: 13px;
    }}

    QLabel#warningLabel {{
        color: {COLORS['warning']};
        font-weight: 600;
        font-size: 13px;
    }}

    QLabel#dangerLabel {{
        color: {COLORS['danger']};
        font-weight: 600;
        font-size: 13px;
    }}

    QLabel#infoLabel {{
        color: {COLORS['info']};
        font-weight: 600;
        font-size: 13px;
    }}
    """
