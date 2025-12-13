"""
Neo-Professional Dark Theme for Admin Panel (Refined Tones)

A distinctive dark interface designed for data-driven professionals.
Refined to keep background layers in one cohesive navy-slate ramp,
with smoother midtones and less “jump” between elevations.

Design Philosophy:
- Deep, rich backgrounds (not flat gray)
- Vibrant but professional accents
- Excellent readability for long sessions
- Color-coded for data visualization
- Refined details in every component
"""

# Neo-Professional Color Palette (refined tones)
COLORS = {
    # Background layers — cohesive navy-slate ramp
    'bg_deepest':   '#070B18',  # deepest base (dialogs/overlays/backdrop)
    'bg_primary':   '#0C111E',  # app base
    'bg_secondary': '#121A2B',  # panels/cards
    'bg_tertiary':  '#19233A',  # hovers/interactive surfaces
    'bg_elevated':  '#1F2B45',  # highest elevation (headers/menus)
    'bg_input':     '#0F1727',  # inputs (slightly “inkier” than panels)

    # Text hierarchy — clean contrast
    'text_primary':     '#D7DEE9',
    'text_secondary':   '#A8B3C6',
    'text_tertiary':    '#7F8AA3',
    'text_disabled':    '#485263',
    'text_placeholder': '#5D6A7F',

    # Brand & Primary Actions — distinctive but less neon
    'primary':         '#00D1F2',
    'primary_hover':   '#00BBDD',
    'primary_pressed': '#00A5C6',
    'primary_muted':   '#103A46',

    # Semantic colors — tuned for navy background
    'success':       '#22E3A1',
    'success_muted': '#123A31',
    'warning':       '#FFB020',
    'warning_muted': '#3A2F16',
    'danger':        '#FF3B6E',
    'danger_muted':  '#3A1624',
    'info':          '#6D8CFF',
    'info_muted':    '#17254A',

    # Status indicators
    'status_active':    '#22E3A1',
    'status_paused':    '#FFB020',
    'status_draft':     '#8D97AC',
    'status_error':     '#FF3B6E',
    'status_completed': '#6D8CFF',

    # Borders & Dividers — smoother progression
    'border_subtle':  '#24314B',
    'border_default': '#2B3A57',
    'border_strong':  '#334565',
    'border_focus':   '#00D1F2',
    'border_hover':   '#3C5175',

    # Data visualization
    'chart_1': '#00D1F2',
    'chart_2': '#FF3B6E',
    'chart_3': '#22E3A1',
    'chart_4': '#FFB020',
    'chart_5': '#6D8CFF',
    'chart_6': '#FF6FA3',

    # Special effects
    'shadow_default': 'rgba(0, 0, 0, 0.32)',
    'shadow_strong':  'rgba(0, 0, 0, 0.55)',
    'overlay_dark':   'rgba(7, 11, 24, 0.82)',
    'shimmer':        'rgba(0, 209, 242, 0.08)',
}


def get_colors() -> dict:
    """
    Get the complete color palette dictionary.

    Returns the full COLORS dictionary for programmatic access
    to theme colors.
    """
    return COLORS


def get_stylesheet() -> str:
    """
    Get the complete Neo-Professional dark theme stylesheet.

    Returns CSS-like stylesheet for PyQt6 application with distinctive,
    professional aesthetics designed for data-driven work.

    Notes:
    - Focus styles are implemented with constant 2px borders to avoid
      layout “jumping” (no padding compensation needed).
    """
    return f"""
    /* ========================================
       GLOBAL STYLES & FOUNDATION
       ======================================== */

    QMainWindow, QWidget, QDialog {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'Helvetica Neue', Arial;
        font-size: 13px;
        selection-background-color: {COLORS['primary']};
        selection-color: {COLORS['bg_deepest']};
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
        background-color: #ff527f;
    }}

    QPushButton#successButton {{
        background-color: {COLORS['success']};
        color: {COLORS['bg_deepest']};
    }}

    QPushButton#successButton:hover {{
        background-color: #3af0b3;
    }}

    QPushButton#warningButton {{
        background-color: {COLORS['warning']};
        color: {COLORS['bg_deepest']};
    }}

    QPushButton#warningButton:hover {{
        background-color: #ffc24d;
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
        selection-background-color: {COLORS['primary']};
        selection-color: {COLORS['bg_deepest']};
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
        selection-background-color: {COLORS['primary']};
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


# Example usage:
# app.setStyleSheet(get_stylesheet())
