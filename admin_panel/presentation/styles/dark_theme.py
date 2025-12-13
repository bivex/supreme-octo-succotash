"""
Neo-Professional Dark Theme for Admin Panel

A distinctive dark interface designed for data-driven professionals.
Combines sharp contrasts with sophisticated color choices and refined typography.

Design Philosophy:
- Deep, rich backgrounds (not flat gray)
- Vibrant but professional accents
- Excellent readability for long sessions
- Color-coded for data visualization
- Refined details in every component
"""

# Neo-Professional Color Palette
COLORS = {
    # Background layers - Deep, rich tones
    'bg_deepest': '#0a0e27',      # Deep navy-black base
    'bg_primary': '#0f1419',       # Rich dark slate
    'bg_secondary': '#1a1f2e',     # Elevated panels
    'bg_tertiary': '#242b3d',      # Interactive elements
    'bg_elevated': '#2d3548',      # Highest elevation
    'bg_input': '#1e2433',         # Input fields

    # Text hierarchy - Crisp and readable
    'text_primary': '#d1d9e6',     # Soft light gray for main content
    'text_secondary': '#a0a8b9',   # Muted for secondary info
    'text_tertiary': '#7a849c',    # Subtle for labels
    'text_disabled': '#3e4853',    # Clearly disabled
    'text_placeholder': '#4d5b6a', # Form placeholders

    # Brand & Primary Actions - Distinctive cyan-blue
    'primary': '#00d9ff',          # Vibrant cyan (distinctive!)
    'primary_hover': '#00bfea',    # Hover state
    'primary_pressed': '#00a5d1',  # Pressed state
    'primary_muted': '#1a4d5f',    # Subtle background

    # Semantic colors - Professional palette
    'success': '#00e599',          # Vibrant success green
    'success_muted': '#1a4d3d',    # Subtle background
    'warning': '#ffb800',          # Bold warning yellow
    'warning_muted': '#4d3d1a',    # Subtle background
    'danger': '#ff3366',           # Sharp danger red
    'danger_muted': '#4d1a2b',     # Subtle background
    'info': '#668cff',             # Soft info blue
    'info_muted': '#1a2d4d',       # Subtle background

    # Status indicators - Clear and distinct
    'status_active': '#00e599',    # Green - running
    'status_paused': '#ffb800',    # Yellow - paused
    'status_draft': '#8891a8',     # Gray - not started
    'status_error': '#ff3366',     # Red - failed
    'status_completed': '#668cff', # Blue - done

    # Borders & Dividers - Subtle but present
    'border_subtle': '#2d3548',    # Very subtle dividers
    'border_default': '#3d4558',   # Standard borders
    'border_strong': '#4d5668',    # Emphasized borders
    'border_focus': '#00d9ff',     # Focus state (primary)
    'border_hover': '#5d6678',     # Hover state

    # Data visualization - Professional chart colors
    'chart_1': '#00d9ff',          # Cyan
    'chart_2': '#ff3366',          # Pink-red
    'chart_3': '#00e599',          # Green
    'chart_4': '#ffb800',          # Yellow
    'chart_5': '#668cff',          # Blue
    'chart_6': '#ff6b9d',          # Rose

    # Special effects
    'shadow_default': 'rgba(0, 0, 0, 0.3)',
    'shadow_strong': 'rgba(0, 0, 0, 0.5)',
    'overlay_dark': 'rgba(10, 14, 39, 0.8)',
    'shimmer': 'rgba(0, 217, 255, 0.1)',  # Subtle glow
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
    """
    return f"""
    /* ========================================
       GLOBAL STYLES & FOUNDATION
       ======================================== */

    QMainWindow, QWidget, QDialog {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
        selection-background-color: {COLORS['primary']};
        selection-color: {COLORS['bg_deepest']};
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
       BUTTONS - Primary actions
       ======================================== */

    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['bg_deepest']};
        border: none;
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
        border: 2px solid {COLORS['border_focus']};
        padding: 9px 19px;
    }}

    /* Button variants */
    QPushButton#deleteButton {{
        background-color: {COLORS['danger']};
        color: {COLORS['text_primary']};
    }}

    QPushButton#deleteButton:hover {{
        background-color: #ff4d7a;
    }}

    QPushButton#successButton {{
        background-color: {COLORS['success']};
        color: {COLORS['bg_deepest']};
    }}

    QPushButton#successButton:hover {{
        background-color: #00ffad;
    }}

    QPushButton#warningButton {{
        background-color: {COLORS['warning']};
        color: {COLORS['bg_deepest']};
    }}

    QPushButton#warningButton:hover {{
        background-color: #ffc733;
    }}

    QPushButton#secondaryButton {{
        background-color: transparent;
        border: 1px solid {COLORS['border_default']};
        color: {COLORS['text_primary']};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {COLORS['bg_tertiary']};
        border-color: {COLORS['border_hover']};
    }}

    /* ========================================
       INPUT FIELDS - Forms & data entry
       ======================================== */

    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: 7px;
        padding: 10px 14px;
        selection-background-color: {COLORS['primary']};
        selection-color: {COLORS['bg_deepest']};
        font-size: 13px;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {COLORS['border_focus']};
        padding: 9px 13px;
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
        border: 1px solid {COLORS['border_default']};
        border-radius: 7px;
        padding: 10px 14px;
        selection-background-color: {COLORS['primary']};
        font-size: 13px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLORS['border_focus']};
        padding: 9px 13px;
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
        border: 1px solid {COLORS['border_default']};
        border-radius: 7px;
        padding: 10px 14px;
        min-width: 120px;
        font-size: 13px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['border_hover']};
        background-color: {COLORS['bg_tertiary']};
    }}

    QComboBox:focus {{
        border: 2px solid {COLORS['border_focus']};
        padding: 9px 13px;
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
        background-color: {COLORS['primary']};
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
        background-color: {COLORS['primary']};
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

# The complete stylesheet can be applied to the UI
