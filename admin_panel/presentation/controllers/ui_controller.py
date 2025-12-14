"""
UI Controller - Handles UI initialization and setup.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QComboBox,
    QSpinBox, QGroupBox, QFormLayout, QStatusBar, QDoubleSpinBox,
    QCheckBox, QDateEdit, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QPalette, QColor, QFont

from .base_controller import BaseController


class UIController(BaseController):
    """Handles UI initialization and setup."""

    def initialize(self) -> None:
        """Initialize the UI controller."""
        self.main_window.setWindowTitle("Advertising Platform Admin Panel")
        self.main_window.setGeometry(100, 100, 1400, 900)
        self.main_window.setStatusBar(QStatusBar())

        # Initialize central widget and layout
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Initialize UI components
        self.init_ui()
        self.create_menu_bar()
        self.apply_modern_stylesheet()

    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Create all tabs
        self.create_connection_panel(self.main_window.centralWidget().layout())
        self.create_dashboard_tab()
        self.create_campaigns_tab()
        self.create_offers_tab()
        self.create_landing_pages_tab()
        self.create_goals_tab()
        self.create_conversions_tab()
        self.create_analytics_tab()
        self.create_clicks_tab()
        self.create_settings_tab()

    def apply_modern_stylesheet(self) -> None:
        """Apply modern stylesheet to the application."""
        from ..styles import get_stylesheet
        self.main_window.setStyleSheet(get_stylesheet())

    def create_menu_bar(self) -> None:
        """Create the menu bar."""
        menubar = self.main_window.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        refresh_action = QAction('&Refresh All', self.main_window)
        refresh_action.triggered.connect(self.main_window.refresh_all_data)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction('&Exit', self.main_window)
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('&View')

        toggle_refresh_action = QAction('&Auto Refresh', self.main_window)
        toggle_refresh_action.setCheckable(True)
        toggle_refresh_action.setChecked(True)
        toggle_refresh_action.triggered.connect(self.main_window.toggle_auto_refresh)
        view_menu.addAction(toggle_refresh_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self.main_window)
        about_action.triggered.connect(self.main_window.show_about)
        help_menu.addAction(about_action)

    def create_connection_panel(self, parent_layout) -> None:
        """Create connection panel."""
        connection_group = QGroupBox("API Connection")
        connection_layout = QFormLayout()

        # API URL input
        self.main_window.api_url_edit = QLineEdit()
        self.main_window.api_url_edit.setText("http://127.0.0.1:5000/v1")
        connection_layout.addRow("API URL:", self.main_window.api_url_edit)

        # Bearer Token input
        self.main_window.bearer_token_edit = QLineEdit()
        self.main_window.bearer_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        connection_layout.addRow("Bearer Token:", self.main_window.bearer_token_edit)

        # API Key input
        self.main_window.api_key_edit = QLineEdit()
        self.main_window.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        connection_layout.addRow("API Key:", self.main_window.api_key_edit)

        # Connect button
        self.main_window.connect_btn = QPushButton("Connect")
        self.main_window.connect_btn.clicked.connect(self.main_window.connect_to_api)
        connection_layout.addRow(self.main_window.connect_btn)

        # Test connection button
        self.main_window.test_btn = QPushButton("Test Connection")
        self.main_window.test_btn.clicked.connect(self.main_window.test_connection)
        self.main_window.test_btn.setEnabled(False)
        connection_layout.addRow(self.main_window.test_btn)

        connection_group.setLayout(connection_layout)
        parent_layout.addWidget(connection_group)

    def create_dashboard_tab(self) -> None:
        """Create dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)

        # Health status section
        health_group = QGroupBox("System Health")
        health_layout = QVBoxLayout()

        self.main_window.health_status_label = QLabel("Status: Not Connected")
        health_layout.addWidget(self.main_window.health_status_label)

        self.main_window.health_progress = QProgressBar()
        self.main_window.health_progress.setRange(0, 0)  # Indeterminate progress
        self.main_window.health_progress.setVisible(False)
        health_layout.addWidget(self.main_window.health_progress)

        health_group.setLayout(health_layout)
        layout.addWidget(health_group)

        # Statistics section
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()

        self.main_window.stats_label = QLabel("No data available")
        stats_layout.addWidget(self.main_window.stats_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()
        self.tab_widget.addTab(dashboard_widget, "Dashboard")

    def create_campaigns_tab(self) -> None:
        """Create campaigns tab."""
        campaigns_widget = QWidget()
        layout = QVBoxLayout(campaigns_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.main_window.campaign_filter_combo = QComboBox()
        self.main_window.campaign_filter_combo.addItem("All", None)
        self.main_window.campaign_filter_combo.addItem("Active", "active")
        self.main_window.campaign_filter_combo.addItem("Paused", "paused")
        self.main_window.campaign_filter_combo.currentTextChanged.connect(
            self.main_window.filter_campaigns
        )
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(self.main_window.campaign_filter_combo)

        controls_layout.addStretch()

        create_btn = QPushButton("Create Campaign")
        create_btn.clicked.connect(self.main_window.show_create_campaign_dialog)
        controls_layout.addWidget(create_btn)

        layout.addLayout(controls_layout)

        # Table
        self.main_window.campaigns_table = QTableWidget()
        self.main_window.campaigns_table.setColumnCount(6)
        self.main_window.campaigns_table.setHorizontalHeaderLabels([
            "ID", "Name", "Status", "Budget", "Date Range", "Actions"
        ])
        layout.addWidget(self.main_window.campaigns_table)

        self.tab_widget.addTab(campaigns_widget, "Campaigns")

    def create_offers_tab(self) -> None:
        """Create offers tab."""
        offers_widget = QWidget()
        layout = QVBoxLayout(offers_widget)

        # Controls
        controls_layout = QHBoxLayout()

        controls_layout.addStretch()

        create_btn = QPushButton("Create Offer")
        create_btn.clicked.connect(self.main_window.show_create_offer_dialog)
        controls_layout.addWidget(create_btn)

        layout.addLayout(controls_layout)

        # Table
        self.main_window.offers_table = QTableWidget()
        self.main_window.offers_table.setColumnCount(7)
        self.main_window.offers_table.setHorizontalHeaderLabels([
            "ID", "Name", "URL", "Weight", "Status", "Campaign", "Actions"
        ])
        layout.addWidget(self.main_window.offers_table)

        self.tab_widget.addTab(offers_widget, "Offers")

    def create_landing_pages_tab(self) -> None:
        """Create landing pages tab."""
        landing_pages_widget = QWidget()
        layout = QVBoxLayout(landing_pages_widget)

        # Controls
        controls_layout = QHBoxLayout()

        controls_layout.addStretch()

        create_btn = QPushButton("Create Landing Page")
        create_btn.clicked.connect(self.main_window.show_create_landing_page_dialog)
        controls_layout.addWidget(create_btn)

        layout.addLayout(controls_layout)

        # Table
        self.main_window.landing_pages_table = QTableWidget()
        self.main_window.landing_pages_table.setColumnCount(6)
        self.main_window.landing_pages_table.setHorizontalHeaderLabels([
            "ID", "Name", "URL", "Weight", "Status", "Actions"
        ])
        layout.addWidget(self.main_window.landing_pages_table)

        self.tab_widget.addTab(landing_pages_widget, "Landing Pages")

    def create_goals_tab(self) -> None:
        """Create goals tab."""
        goals_widget = QWidget()
        layout = QVBoxLayout(goals_widget)

        # Controls
        controls_layout = QHBoxLayout()

        controls_layout.addStretch()

        create_btn = QPushButton("Create Goal")
        create_btn.clicked.connect(self.main_window.show_create_goal_dialog)
        controls_layout.addWidget(create_btn)

        layout.addLayout(controls_layout)

        # Table
        self.main_window.goals_table = QTableWidget()
        self.main_window.goals_table.setColumnCount(5)
        self.main_window.goals_table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Value", "Actions"
        ])
        layout.addWidget(self.main_window.goals_table)

        self.tab_widget.addTab(goals_widget, "Goals")

    def create_conversions_tab(self) -> None:
        """Create conversions tab."""
        conversions_widget = QWidget()
        layout = QVBoxLayout(conversions_widget)

        # Controls
        controls_layout = QHBoxLayout()

        track_btn = QPushButton("Track Conversion")
        track_btn.clicked.connect(self.main_window.show_track_conversion_dialog)
        controls_layout.addWidget(track_btn)

        controls_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.main_window.refresh_conversions)
        controls_layout.addWidget(refresh_btn)

        layout.addLayout(controls_layout)

        # Table
        self.main_window.conversions_table = QTableWidget()
        self.main_window.conversions_table.setColumnCount(5)
        self.main_window.conversions_table.setHorizontalHeaderLabels([
            "ID", "Click ID", "Goal", "Value", "Timestamp"
        ])
        layout.addWidget(self.main_window.conversions_table)

        self.tab_widget.addTab(conversions_widget, "Conversions")

    def create_analytics_tab(self) -> None:
        """Create analytics tab."""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.main_window.analytics_campaign_combo = QComboBox()
        self.main_window.analytics_campaign_combo.addItem("All Campaigns", None)
        controls_layout.addWidget(QLabel("Campaign:"))
        controls_layout.addWidget(self.main_window.analytics_campaign_combo)

        load_btn = QPushButton("Load Analytics")
        load_btn.clicked.connect(self.main_window.load_analytics)
        controls_layout.addWidget(load_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Results display
        self.main_window.analytics_text = QTextEdit()
        self.main_window.analytics_text.setReadOnly(True)
        layout.addWidget(self.main_window.analytics_text)

        self.tab_widget.addTab(analytics_widget, "Analytics")

    def create_clicks_tab(self) -> None:
        """Create clicks tab."""
        clicks_widget = QWidget()
        layout = QVBoxLayout(clicks_widget)

        # Controls
        controls_layout = QHBoxLayout()

        generate_btn = QPushButton("Generate Click")
        generate_btn.clicked.connect(self.main_window.show_generate_click_dialog)
        controls_layout.addWidget(generate_btn)

        controls_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.main_window.refresh_clicks)
        controls_layout.addWidget(refresh_btn)

        layout.addLayout(controls_layout)

        # Table
        self.main_window.clicks_table = QTableWidget()
        self.main_window.clicks_table.setColumnCount(7)
        self.main_window.clicks_table.setHorizontalHeaderLabels([
            "ID", "Campaign", "Offer", "Landing Page", "IP", "User Agent", "Timestamp"
        ])
        layout.addWidget(self.main_window.clicks_table)

        self.tab_widget.addTab(clicks_widget, "Clicks")

    def create_settings_tab(self) -> None:
        """Create settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)

        # API Settings
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout()

        self.main_window.settings_api_url = QLineEdit()
        api_layout.addRow("API Base URL:", self.main_window.settings_api_url)

        self.main_window.settings_bearer_token = QLineEdit()
        self.main_window.settings_bearer_token.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Bearer Token:", self.main_window.settings_bearer_token)

        self.main_window.settings_api_key = QLineEdit()
        self.main_window.settings_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("API Key:", self.main_window.settings_api_key)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # UI Settings
        ui_group = QGroupBox("UI Settings")
        ui_layout = QFormLayout()

        self.main_window.settings_auto_refresh = QCheckBox("Enable Auto Refresh")
        self.main_window.settings_auto_refresh.setChecked(True)
        ui_layout.addRow(self.main_window.settings_auto_refresh)

        self.main_window.settings_refresh_interval = QSpinBox()
        self.main_window.settings_refresh_interval.setRange(30, 3600)
        self.main_window.settings_refresh_interval.setValue(300)
        self.main_window.settings_refresh_interval.setSuffix(" seconds")
        ui_layout.addRow("Refresh Interval:", self.main_window.settings_refresh_interval)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        # Logging Settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout()

        self.main_window.settings_log_level = QComboBox()
        self.main_window.settings_log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.main_window.settings_log_level.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.main_window.settings_log_level)

        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.main_window.save_settings)
        buttons_layout.addWidget(save_btn)

        load_btn = QPushButton("Load from Config")
        load_btn.clicked.connect(self.main_window.load_config)
        buttons_layout.addWidget(load_btn)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        layout.addStretch()
        self.tab_widget.addTab(settings_widget, "Settings")