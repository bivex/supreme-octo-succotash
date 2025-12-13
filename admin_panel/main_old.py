#!/usr/bin/env python3
"""
Advertising Platform Admin Panel

PyQt6-based admin interface for managing Advertising Platform business tasks.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QComboBox, QSpinBox, QGroupBox, QFormLayout, QMessageBox, QStatusBar,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QCheckBox, QDateEdit, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import QThread, pyqtSignal, QDateTime, Qt, QTimer, QDate
from PyQt6.QtGui import QAction, QPalette, QColor, QFont

from advertising_platform_sdk import AdvertisingPlatformClient
from advertising_platform_sdk.exceptions import *

# Import dark theme
try:
    from presentation.styles import get_stylesheet
    DARK_THEME_AVAILABLE = True
except ImportError:
    DARK_THEME_AVAILABLE = False


class APIWorker(QThread):
    """Worker thread for API operations."""
    finished = pyqtSignal(object)  # Result data
    error = pyqtSignal(str)       # Error message

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class CampaignDialog(QDialog):
    """Dialog for creating/editing campaigns."""

    def __init__(self, parent=None, campaign=None):
        super().__init__(parent)
        self.campaign = campaign
        self.is_edit = campaign is not None
        self.init_ui()

        if self.campaign:
            self.populate_fields()

    def init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Edit Campaign" if self.is_edit else "Create Campaign")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Form
        form_group = QGroupBox("Campaign Details")
        form_layout = QFormLayout(form_group)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter campaign name...")
        form_layout.addRow("Name *:", self.name_edit)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "paused", "draft"])
        form_layout.addRow("Status:", self.status_combo)

        # Budget
        budget_layout = QHBoxLayout()
        self.budget_amount = QDoubleSpinBox()
        self.budget_amount.setRange(0, 1000000)
        self.budget_amount.setDecimals(2)
        self.budget_amount.setValue(1000.00)
        budget_layout.addWidget(self.budget_amount)

        self.budget_currency = QComboBox()
        self.budget_currency.addItems(["USD", "EUR", "GBP", "RUB"])
        budget_layout.addWidget(self.budget_currency)
        form_layout.addRow("Budget *:", budget_layout)

        # Budget Type
        self.budget_type = QComboBox()
        self.budget_type.addItems(["daily", "total"])
        form_layout.addRow("Budget Type:", self.budget_type)

        # Target URL
        self.target_url = QLineEdit()
        self.target_url.setPlaceholderText("https://example.com/landing-page")
        form_layout.addRow("Target URL *:", self.target_url)

        # Start/End dates
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addMonths(1))
        self.end_date.setCalendarPopup(True)
        form_layout.addRow("End Date:", self.end_date)

        layout.addWidget(form_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def populate_fields(self):
        """Populate fields with existing campaign data."""
        if not self.campaign:
            return

        self.name_edit.setText(self.campaign.get('name', ''))

        status = self.campaign.get('status', 'draft')
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        budget = self.campaign.get('budget', {})
        self.budget_amount.setValue(float(budget.get('amount', 0)))

        currency = budget.get('currency', 'USD')
        index = self.budget_currency.findText(currency)
        if index >= 0:
            self.budget_currency.setCurrentIndex(index)

        budget_type = budget.get('type', 'daily')
        index = self.budget_type.findText(budget_type)
        if index >= 0:
            self.budget_type.setCurrentIndex(index)

        self.target_url.setText(self.campaign.get('target_url', ''))

    def validate_and_accept(self):
        """Validate input and accept dialog."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Campaign name is required")
            return

        if not self.target_url.text().strip():
            QMessageBox.warning(self, "Validation Error", "Target URL is required")
            return

        if self.budget_amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Budget must be greater than 0")
            return

        self.accept()

    def get_campaign_data(self):
        """Get campaign data from form."""
        return {
            "name": self.name_edit.text().strip(),
            "status": self.status_combo.currentText(),
            "budget": {
                "amount": self.budget_amount.value(),
                "currency": self.budget_currency.currentText(),
                "type": self.budget_type.currentText()
            },
            "target_url": self.target_url.text().strip(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd")
        }


class GoalDialog(QDialog):
    """Dialog for creating/editing goals."""

    def __init__(self, parent=None, goal=None, campaigns=None, templates=None):
        super().__init__(parent)
        self.goal = goal
        self.campaigns = campaigns or []
        self.templates = templates or []
        self.is_edit = goal is not None
        self.init_ui()

        if self.goal:
            self.populate_fields()

    def init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Edit Goal" if self.is_edit else "Create Goal")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Template selection (only for new goals)
        if not self.is_edit and self.templates:
            template_group = QGroupBox("Quick Start")
            template_layout = QVBoxLayout(template_group)

            template_layout.addWidget(QLabel("Choose a template:"))
            self.template_combo = QComboBox()
            self.template_combo.addItem("-- Custom Goal --", None)
            for template in self.templates:
                self.template_combo.addItem(template.get('name', ''), template)
            self.template_combo.currentIndexChanged.connect(self.on_template_selected)
            template_layout.addWidget(self.template_combo)

            layout.addWidget(template_group)

        # Form
        form_group = QGroupBox("Goal Details")
        form_layout = QFormLayout(form_group)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter goal name...")
        form_layout.addRow("Name *:", self.name_edit)

        # Campaign
        self.campaign_combo = QComboBox()
        for campaign in self.campaigns:
            self.campaign_combo.addItem(campaign.get('name', ''), campaign.get('id', ''))
        form_layout.addRow("Campaign *:", self.campaign_combo)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["conversion", "click", "impression", "lead", "sale"])
        form_layout.addRow("Type *:", self.type_combo)

        # Value
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(0, 1000000)
        self.value_spin.setDecimals(2)
        self.value_spin.setPrefix("$ ")
        form_layout.addRow("Goal Value:", self.value_spin)

        # URL Match (for conversion tracking)
        self.url_match = QLineEdit()
        self.url_match.setPlaceholderText("https://example.com/thank-you")
        form_layout.addRow("Success URL:", self.url_match)

        layout.addWidget(form_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_template_selected(self, index):
        """Handle template selection."""
        template = self.template_combo.currentData()
        if template:
            self.name_edit.setText(template.get('name', ''))

            goal_type = template.get('type', 'conversion')
            idx = self.type_combo.findText(goal_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

            self.value_spin.setValue(float(template.get('value', 0)))

    def populate_fields(self):
        """Populate fields with existing goal data."""
        if not self.goal:
            return

        self.name_edit.setText(self.goal.get('name', ''))

        campaign_id = self.goal.get('campaign_id', '')
        for i in range(self.campaign_combo.count()):
            if self.campaign_combo.itemData(i) == campaign_id:
                self.campaign_combo.setCurrentIndex(i)
                break

        goal_type = self.goal.get('type', 'conversion')
        index = self.type_combo.findText(goal_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.value_spin.setValue(float(self.goal.get('value', 0)))
        self.url_match.setText(self.goal.get('url_match', ''))

    def validate_and_accept(self):
        """Validate input and accept dialog."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Goal name is required")
            return

        if self.campaign_combo.count() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a campaign")
            return

        self.accept()

    def get_goal_data(self):
        """Get goal data from form."""
        return {
            "name": self.name_edit.text().strip(),
            "campaign_id": self.campaign_combo.currentData(),
            "type": self.type_combo.currentText(),
            "value": self.value_spin.value(),
            "url_match": self.url_match.text().strip()
        }


class GenerateClickDialog(QDialog):
    """Dialog for generating click URLs."""

    def __init__(self, parent=None, campaigns=None):
        super().__init__(parent)
        self.campaigns = campaigns or []
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Generate Click URL")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Form
        form_group = QGroupBox("Click Configuration")
        form_layout = QFormLayout(form_group)

        # Campaign
        self.campaign_combo = QComboBox()
        for campaign in self.campaigns:
            self.campaign_combo.addItem(campaign.get('name', ''), campaign.get('id', ''))
        form_layout.addRow("Campaign *:", self.campaign_combo)

        # Source
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("e.g., google, facebook, email")
        form_layout.addRow("Source:", self.source_edit)

        # Medium
        self.medium_edit = QLineEdit()
        self.medium_edit.setPlaceholderText("e.g., cpc, social, newsletter")
        form_layout.addRow("Medium:", self.medium_edit)

        # Campaign Name (UTM)
        self.utm_campaign = QLineEdit()
        self.utm_campaign.setPlaceholderText("e.g., summer_sale")
        form_layout.addRow("UTM Campaign:", self.utm_campaign)

        layout.addWidget(form_group)

        # Generated URL display
        self.url_display = QTextEdit()
        self.url_display.setMaximumHeight(100)
        self.url_display.setReadOnly(True)
        self.url_display.setPlaceholderText("Generated URL will appear here...")
        layout.addWidget(QLabel("Generated URL:"))
        layout.addWidget(self.url_display)

        # Buttons
        button_layout = QHBoxLayout()

        generate_btn = QPushButton("Generate URL")
        generate_btn.clicked.connect(self.accept)
        button_layout.addWidget(generate_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_click_data(self):
        """Get click generation data from form."""
        return {
            "campaign_id": self.campaign_combo.currentData(),
            "source": self.source_edit.text().strip(),
            "medium": self.medium_edit.text().strip(),
            "utm_campaign": self.utm_campaign.text().strip()
        }

    def set_generated_url(self, url):
        """Set the generated URL in the display."""
        self.url_display.setText(url)


class AdminPanel(QMainWindow):
    """Main admin panel window."""

    def __init__(self):
        super().__init__()
        self.client = None
        self.current_campaigns = []
        self.current_goals = []
        self.current_clicks = []
        self.current_conversions = []
        self.goal_templates = []

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_data)

        self.init_ui()
        # Modern stylesheet now applied globally via dark theme
        # self.apply_modern_stylesheet()  # Commented out - using global dark theme
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Advertising Platform Admin Panel")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create menu bar
        self.create_menu_bar()

        # Create connection panel
        self.create_connection_panel(layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_dashboard_tab()
        self.create_campaigns_tab()
        self.create_goals_tab()
        self.create_conversions_tab()
        self.create_analytics_tab()
        self.create_clicks_tab()
        self.create_settings_tab()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Connect signals
        self.connect_button.clicked.connect(self.connect_to_api)

    def apply_modern_stylesheet(self):
        """
        Legacy stylesheet method - now using global dark theme.
        Kept for backward compatibility but does nothing.
        """
        pass  # Dark theme applied globally in main()

    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        connect_action = QAction('Connect to API', self)
        connect_action.triggered.connect(self.connect_to_api)
        file_menu.addAction(connect_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')

        refresh_action = QAction('Refresh All', self)
        refresh_action.triggered.connect(self.refresh_all_data)
        tools_menu.addAction(refresh_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_connection_panel(self, parent_layout):
        """Create the API connection panel."""
        connection_group = QGroupBox("API Connection")
        layout = QHBoxLayout(connection_group)

        # Base URL
        layout.addWidget(QLabel("Base URL:"))
        self.base_url_edit = QLineEdit("http://127.0.0.1:5000/v1")
        layout.addWidget(self.base_url_edit)

        # Authentication
        layout.addWidget(QLabel("Auth Token:"))
        self.auth_token_edit = QLineEdit()
        self.auth_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.auth_token_edit)

        # Connect button
        self.connect_button = QPushButton("Connect")
        layout.addWidget(self.connect_button)

        # Connection status
        self.connection_status = QLabel("✗ Not connected")
        self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(self.connection_status)

        parent_layout.addWidget(connection_group)

    def create_dashboard_tab(self):
        """Create the dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)

        # Overview section
        overview_group = QGroupBox("System Overview")
        overview_layout = QHBoxLayout(overview_group)

        # Health status
        health_layout = QVBoxLayout()
        health_layout.addWidget(QLabel("API Health:"))
        self.health_status = QLabel("Unknown")
        self.health_status.setStyleSheet("font-size: 14px; font-weight: bold;")
        health_layout.addWidget(self.health_status)
        overview_layout.addLayout(health_layout)

        # Quick stats
        stats_layout = QVBoxLayout()
        stats_heading = QLabel("📈 Quick Statistics")
        stats_heading.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        stats_layout.addWidget(stats_heading)

        self.stats_labels = {}
        stats = ["Total Campaigns", "Active Campaigns", "Total Goals", "Today's Clicks", "Today's Conversions"]
        for stat in stats:
            label = QLabel(f"{stat}: --")
            label.setStyleSheet("""
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border-left: 4px solid #3498db;
                font-size: 13px;
                margin: 2px;
            """)
            self.stats_labels[stat] = label
            stats_layout.addWidget(label)

        overview_layout.addLayout(stats_layout)

        layout.addWidget(overview_group)

        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)

        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setReadOnly(True)
        self.activity_log.setStyleSheet("""
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        """)
        activity_layout.addWidget(self.activity_log)

        layout.addWidget(activity_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh Dashboard")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        layout.addWidget(refresh_btn)

        self.tab_widget.addTab(dashboard_widget, "Dashboard")

    def create_campaigns_tab(self):
        """Create the campaigns management tab."""
        campaigns_widget = QWidget()
        layout = QVBoxLayout(campaigns_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.campaign_search = QLineEdit()
        self.campaign_search.setPlaceholderText("Search campaigns...")
        controls_layout.addWidget(self.campaign_search)

        self.campaign_status_filter = QComboBox()
        self.campaign_status_filter.addItems(["All", "active", "paused", "draft"])
        controls_layout.addWidget(self.campaign_status_filter)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_campaigns)
        controls_layout.addWidget(refresh_btn)

        create_btn = QPushButton("Create Campaign")
        create_btn.clicked.connect(self.show_create_campaign_dialog)
        controls_layout.addWidget(create_btn)

        layout.addLayout(controls_layout)

        # Campaigns table
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels([
            "ID", "Name", "Status", "Budget", "Created", "Actions"
        ])
        self.campaigns_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.campaigns_table)

        # Connect signals
        self.campaign_search.textChanged.connect(self.filter_campaigns)
        self.campaign_status_filter.currentTextChanged.connect(self.filter_campaigns)

        self.tab_widget.addTab(campaigns_widget, "Campaigns")

    def create_goals_tab(self):
        """Create the goals management tab."""
        goals_widget = QWidget()
        layout = QVBoxLayout(goals_widget)

        # Controls
        controls_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_goals)
        controls_layout.addWidget(refresh_btn)

        create_btn = QPushButton("Create Goal")
        create_btn.clicked.connect(self.show_create_goal_dialog)
        controls_layout.addWidget(create_btn)

        layout.addLayout(controls_layout)

        # Goals table
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(5)
        self.goals_table.setHorizontalHeaderLabels([
            "ID", "Name", "Campaign", "Type", "Actions"
        ])
        self.goals_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.goals_table)

        self.tab_widget.addTab(goals_widget, "Goals")

    def create_conversions_tab(self):
        """Create the conversions tracking tab."""
        conversions_widget = QWidget()
        layout = QVBoxLayout(conversions_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.conversions_campaign_select = QComboBox()
        self.conversions_campaign_select.addItem("All Campaigns", None)
        controls_layout.addWidget(self.conversions_campaign_select)

        refresh_btn = QPushButton("Refresh Conversions")
        refresh_btn.clicked.connect(self.refresh_conversions)
        controls_layout.addWidget(refresh_btn)

        track_btn = QPushButton("Track Conversion")
        track_btn.setObjectName("successButton")
        track_btn.clicked.connect(self.show_track_conversion_dialog)
        controls_layout.addWidget(track_btn)

        layout.addLayout(controls_layout)

        # Conversions stats
        stats_group = QGroupBox("Conversion Statistics")
        stats_layout = QHBoxLayout(stats_group)

        self.conv_total_label = QLabel("Total: 0")
        self.conv_total_label.setObjectName("statLabel")
        stats_layout.addWidget(self.conv_total_label)

        self.conv_today_label = QLabel("Today: 0")
        self.conv_today_label.setObjectName("statLabel")
        stats_layout.addWidget(self.conv_today_label)

        self.conv_revenue_label = QLabel("Revenue: $0.00")
        self.conv_revenue_label.setObjectName("statLabel")
        stats_layout.addWidget(self.conv_revenue_label)

        layout.addWidget(stats_group)

        # Conversions table
        self.conversions_table = QTableWidget()
        self.conversions_table.setColumnCount(6)
        self.conversions_table.setHorizontalHeaderLabels([
            "ID", "Campaign", "Goal", "Value", "Created", "Details"
        ])
        self.conversions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.conversions_table)

        self.tab_widget.addTab(conversions_widget, "Conversions")

    def create_analytics_tab(self):
        """Create the analytics tab."""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.analytics_campaign_select = QComboBox()
        self.analytics_campaign_select.addItem("All Campaigns", None)
        controls_layout.addWidget(self.analytics_campaign_select)

        self.analytics_period_select = QComboBox()
        self.analytics_period_select.addItems(["Today", "Yesterday", "Last 7 days", "Last 30 days"])
        controls_layout.addWidget(self.analytics_period_select)

        refresh_btn = QPushButton("Load Analytics")
        refresh_btn.clicked.connect(self.load_analytics)
        controls_layout.addWidget(refresh_btn)

        layout.addLayout(controls_layout)

        # Analytics display
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        layout.addWidget(self.analytics_text)

        self.tab_widget.addTab(analytics_widget, "Analytics")

    def create_clicks_tab(self):
        """Create the clicks management tab."""
        clicks_widget = QWidget()
        layout = QVBoxLayout(clicks_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.clicks_campaign_select = QComboBox()
        self.clicks_campaign_select.addItem("All Campaigns", None)
        controls_layout.addWidget(self.clicks_campaign_select)

        refresh_btn = QPushButton("Refresh Clicks")
        refresh_btn.clicked.connect(self.refresh_clicks)
        controls_layout.addWidget(refresh_btn)

        generate_btn = QPushButton("Generate Click URL")
        generate_btn.clicked.connect(self.show_generate_click_dialog)
        controls_layout.addWidget(generate_btn)

        layout.addLayout(controls_layout)

        # Clicks table
        self.clicks_table = QTableWidget()
        self.clicks_table.setColumnCount(5)
        self.clicks_table.setHorizontalHeaderLabels([
            "ID", "Campaign", "IP", "User Agent", "Created"
        ])
        self.clicks_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.clicks_table)

        self.tab_widget.addTab(clicks_widget, "Clicks")

    def create_settings_tab(self):
        """Create the settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)

        # API Settings
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(api_group)

        self.settings_base_url = QLineEdit("http://127.0.0.1:5000/v1")
        api_layout.addRow("Base URL:", self.settings_base_url)

        self.settings_timeout = QSpinBox()
        self.settings_timeout.setRange(5, 300)
        self.settings_timeout.setValue(30)
        api_layout.addRow("Timeout (seconds):", self.settings_timeout)

        layout.addWidget(api_group)

        # Authentication Settings
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout(auth_group)

        self.settings_bearer_token = QLineEdit()
        self.settings_bearer_token.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addRow("Bearer Token:", self.settings_bearer_token)

        self.settings_api_key = QLineEdit()
        self.settings_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addRow("API Key:", self.settings_api_key)

        layout.addWidget(auth_group)

        # UI Settings
        ui_group = QGroupBox("UI Settings")
        ui_layout = QFormLayout(ui_group)

        self.auto_refresh_checkbox = QCheckBox("Enable auto-refresh (30 seconds)")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.toggled.connect(self.toggle_auto_refresh)
        ui_layout.addRow("Auto Refresh:", self.auto_refresh_checkbox)

        layout.addWidget(ui_group)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        self.tab_widget.addTab(settings_widget, "Settings")

    def connect_to_api(self):
        """Connect to the API."""
        base_url = self.base_url_edit.text().strip()
        auth_token = self.auth_token_edit.text().strip()

        if not base_url:
            QMessageBox.warning(self, "Error", "Please enter a base URL")
            return

        # Validate base URL format
        if not self._validate_url(base_url):
            QMessageBox.warning(self, "Invalid URL",
                "The base URL format is incorrect.\n\n"
                "URL should start with 'http://' or 'https://' and be a valid web address.\n"
                "Example: http://127.0.0.1:5000/v1")
            return

        # Validate auth token format
        if auth_token and not self._validate_token(auth_token):
            QMessageBox.warning(self, "Invalid Token",
                "The authentication token format is incorrect.\n\n"
                "Token should be a valid Bearer token (usually starts with 'Bearer ' or is a JWT-like string).\n"
                "Please check your token and try again.")
            return

        try:
            self.client = AdvertisingPlatformClient(
                base_url=base_url,
                bearer_token=auth_token if auth_token else None
            )

            # Test connection with health check
            self.test_connection()

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {e}")
            self.connection_status.setText("Connection failed")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")

    def test_connection(self):
        """Test API connection."""
        if not self.client:
            return

        self.status_bar.showMessage("Testing connection...")

        def on_success(result):
            self.connection_status.setText("✓ Connected")
            self.connection_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.status_bar.showMessage("Connected successfully")
            self.refresh_dashboard()

            # Start auto-refresh timer (every 30 seconds)
            self.refresh_timer.start(30000)

        def on_error(error_msg):
            self.connection_status.setText("Connection failed")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
            self.status_bar.showMessage(f"Connection failed: {error_msg}")

            # Provide more specific error messages for common issues
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                QMessageBox.warning(self, "Authentication Error",
                    "Failed to connect to API: Invalid or expired authentication token.\n\n"
                    "Please check your authentication token and try again.")
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                QMessageBox.warning(self, "Access Denied",
                    "Failed to connect to API: Access denied.\n\n"
                    "Your token may not have the required permissions.")
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                QMessageBox.warning(self, "Connection Error",
                    "Failed to connect to API: Network connection issue.\n\n"
                    "Please check your internet connection and API URL.")
            else:
                QMessageBox.warning(self, "Connection Error", f"Failed to connect to API: {error_msg}")

        worker = APIWorker(self.client.get_health)
        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        worker.start()

    def refresh_dashboard(self):
        """Refresh dashboard data."""
        if not self.client:
            return

        self.status_bar.showMessage("Refreshing dashboard...")

        # Test health
        def on_health_success(result):
            status = result.get('status', 'unknown')
            self.health_status.setText(status.upper())
            if status == 'healthy':
                self.health_status.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
            else:
                self.health_status.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")

            self.log_activity(f"✓ Health check: {status}")

        def on_health_error(error):
            self.health_status.setText("ERROR")
            self.health_status.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
            self.log_activity(f"✗ Health check failed: {error}")

        health_worker = APIWorker(self.client.get_health)
        health_worker.finished.connect(on_health_success)
        health_worker.error.connect(on_health_error)
        health_worker.start()

        # Load campaigns count
        def on_campaigns_success(result):
            campaigns = result.get('data', [])
            active_count = len([c for c in campaigns if c.get('status') == 'active'])
            paused_count = len([c for c in campaigns if c.get('status') == 'paused'])
            draft_count = len([c for c in campaigns if c.get('status') == 'draft'])

            self.stats_labels["Total Campaigns"].setText(f"📊 Total Campaigns: {len(campaigns)}")
            self.stats_labels["Active Campaigns"].setText(f"✅ Active: {active_count} | ⏸️ Paused: {paused_count} | 📝 Draft: {draft_count}")

        campaigns_worker = APIWorker(self.client.get_campaigns)
        campaigns_worker.finished.connect(on_campaigns_success)
        campaigns_worker.error.connect(lambda e: None)  # Ignore errors for stats
        campaigns_worker.start()

        # Load goals count
        def on_goals_success(result):
            goals = result.get('data', [])
            self.stats_labels["Total Goals"].setText(f"🎯 Total Goals: {len(goals)}")

        goals_worker = APIWorker(self.client.get_goals)
        goals_worker.finished.connect(on_goals_success)
        goals_worker.error.connect(lambda e: None)
        goals_worker.start()

        # Load real-time analytics
        def on_analytics_success(result):
            clicks = result.get('clicks', 0)
            conversions = result.get('conversions', 0)
            revenue = result.get('revenue', 0.0)

            self.stats_labels["Today's Clicks"].setText(f"👆 Today's Clicks: {clicks}")
            self.stats_labels["Today's Conversions"].setText(f"💰 Today's Conversions: {conversions} (${revenue:.2f})")

        analytics_worker = APIWorker(self.client.get_real_time_analytics)
        analytics_worker.finished.connect(on_analytics_success)
        analytics_worker.error.connect(lambda e: None)
        analytics_worker.start()

        self.status_bar.showMessage("Dashboard refreshed")

    def refresh_campaigns(self):
        """Refresh campaigns list."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        self.status_bar.showMessage("Loading campaigns...")

        def on_success(result):
            self.current_campaigns = result.get('data', [])
            self.populate_campaigns_table()
            self.update_campaign_selectors()
            self.status_bar.showMessage("Campaigns loaded successfully")

        def on_error(error_msg):
            self.status_bar.showMessage(f"Failed to load campaigns: {error_msg}")

            # Provide specific error messages for auth issues
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                QMessageBox.warning(self, "Authentication Error",
                    "Failed to load campaigns: Your authentication token is invalid or expired.\n\n"
                    "Please reconnect to the API with a valid token.")
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                QMessageBox.warning(self, "Access Denied",
                    "Failed to load campaigns: Access denied.\n\n"
                    "Your token may not have permission to view campaigns.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load campaigns: {error_msg}")

        worker = APIWorker(self.client.get_campaigns)
        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        worker.start()

    def populate_campaigns_table(self):
        """Populate the campaigns table."""
        self.campaigns_table.setRowCount(len(self.current_campaigns))

        for row, campaign in enumerate(self.current_campaigns):
            self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign.get('id', '')))
            self.campaigns_table.setItem(row, 1, QTableWidgetItem(campaign.get('name', '')))
            self.campaigns_table.setItem(row, 2, QTableWidgetItem(campaign.get('status', '')))

            # Budget
            budget = campaign.get('budget', {})
            budget_text = f"{budget.get('amount', 0)} {budget.get('currency', '')}"
            self.campaigns_table.setItem(row, 3, QTableWidgetItem(budget_text))

            # Created date
            created = campaign.get('created_at', '')
            self.campaigns_table.setItem(row, 4, QTableWidgetItem(created))

            # Actions button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setMaximumWidth(80)
            edit_btn.clicked.connect(lambda checked, c=campaign: self.edit_campaign(c))
            actions_layout.addWidget(edit_btn)

            pause_btn = QPushButton("⏸️ Pause" if campaign.get('status') == 'active' else "▶️ Resume")
            pause_btn.setMaximumWidth(90)
            if campaign.get('status') != 'active':
                pause_btn.setObjectName("successButton")
            pause_btn.clicked.connect(lambda checked, c=campaign: self.toggle_campaign_status(c))
            actions_layout.addWidget(pause_btn)

            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.setObjectName("deleteButton")
            delete_btn.setMaximumWidth(90)
            delete_btn.clicked.connect(lambda checked, c=campaign: self.delete_campaign(c))
            actions_layout.addWidget(delete_btn)

            actions_layout.setContentsMargins(0, 0, 0, 0)
            self.campaigns_table.setCellWidget(row, 5, actions_widget)

        self.campaigns_table.resizeColumnsToContents()

    def filter_campaigns(self):
        """Filter campaigns based on search and status."""
        search_text = self.campaign_search.text().lower()
        status_filter = self.campaign_status_filter.currentText()

        for row in range(self.campaigns_table.rowCount()):
            campaign_id = self.campaigns_table.item(row, 0).text().lower()
            campaign_name = self.campaigns_table.item(row, 1).text().lower()
            campaign_status = self.campaigns_table.item(row, 2).text()

            # Search filter
            search_match = search_text in campaign_id or search_text in campaign_name

            # Status filter
            status_match = status_filter == "All" or status_filter == campaign_status

            # Show/hide row
            self.campaigns_table.setRowHidden(row, not (search_match and status_match))

    def refresh_goals(self):
        """Refresh goals list."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        self.status_bar.showMessage("Loading goals...")

        def on_success(result):
            self.current_goals = result.get('data', [])
            self.populate_goals_table()
            self.status_bar.showMessage("Goals loaded successfully")

        def on_error(error_msg):
            self.status_bar.showMessage(f"Failed to load goals: {error_msg}")

            # Provide specific error messages for auth issues
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                QMessageBox.warning(self, "Authentication Error",
                    "Failed to load goals: Your authentication token is invalid or expired.\n\n"
                    "Please reconnect to the API with a valid token.")
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                QMessageBox.warning(self, "Access Denied",
                    "Failed to load goals: Access denied.\n\n"
                    "Your token may not have permission to view goals.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load goals: {error_msg}")

        worker = APIWorker(self.client.get_goals)
        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        worker.start()

    def populate_goals_table(self):
        """Populate the goals table."""
        self.goals_table.setRowCount(len(self.current_goals))

        for row, goal in enumerate(self.current_goals):
            self.goals_table.setItem(row, 0, QTableWidgetItem(goal.get('id', '')))
            self.goals_table.setItem(row, 1, QTableWidgetItem(goal.get('name', '')))
            self.goals_table.setItem(row, 2, QTableWidgetItem(goal.get('campaign_id', '')))
            self.goals_table.setItem(row, 3, QTableWidgetItem(goal.get('type', '')))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setMaximumWidth(80)
            edit_btn.clicked.connect(lambda checked, g=goal: self.edit_goal(g))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.setObjectName("deleteButton")
            delete_btn.setMaximumWidth(90)
            delete_btn.clicked.connect(lambda checked, g=goal: self.delete_goal(g))
            actions_layout.addWidget(delete_btn)

            actions_layout.setContentsMargins(0, 0, 0, 0)
            self.goals_table.setCellWidget(row, 4, actions_widget)

        self.goals_table.resizeColumnsToContents()

    def load_analytics(self):
        """Load analytics data."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        campaign_id = self.analytics_campaign_select.currentData()
        period = self.analytics_period_select.currentText()

        self.status_bar.showMessage("Loading analytics...")

        # For now, just load basic campaign analytics
        if campaign_id:
            def on_success(result):
                self.display_analytics(result)
                self.status_bar.showMessage("Analytics loaded successfully")

            def on_error(error_msg):
                self.status_bar.showMessage(f"Failed to load analytics: {error_msg}")

                # Provide specific error messages for auth issues
                if "401" in error_msg or "unauthorized" in error_msg.lower():
                    QMessageBox.warning(self, "Authentication Error",
                        "Failed to load analytics: Your authentication token is invalid or expired.\n\n"
                        "Please reconnect to the API with a valid token.")
                elif "403" in error_msg or "forbidden" in error_msg.lower():
                    QMessageBox.warning(self, "Access Denied",
                        "Failed to load analytics: Access denied.\n\n"
                        "Your token may not have permission to view analytics.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to load analytics: {error_msg}")

            worker = APIWorker(self.client.get_campaign_analytics, campaign_id)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()
        else:
            # Load real-time analytics for all campaigns
            def on_success(result):
                self.display_analytics(result)
                self.status_bar.showMessage("Analytics loaded successfully")

            worker = APIWorker(self.client.get_real_time_analytics)
            worker.finished.connect(on_success)
            worker.error.connect(lambda e: QMessageBox.warning(self, "Error", f"Failed to load analytics: {e}"))
            worker.start()

    def display_analytics(self, data):
        """Display analytics data."""
        self.analytics_text.clear()

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    self.analytics_text.append(f"{key}:")
                    for sub_key, sub_value in value.items():
                        self.analytics_text.append(f"  {sub_key}: {sub_value}")
                else:
                    self.analytics_text.append(f"{key}: {value}")
                self.analytics_text.append("")
        else:
            self.analytics_text.setText(str(data))

    def refresh_clicks(self):
        """Refresh clicks list."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        campaign_id = self.clicks_campaign_select.currentData()

        self.status_bar.showMessage("Loading clicks...")

        def on_success(result):
            self.current_clicks = result.get('data', [])
            self.populate_clicks_table()
            self.status_bar.showMessage("Clicks loaded successfully")

        def on_error(error_msg):
            self.status_bar.showMessage(f"Failed to load clicks: {error_msg}")

            # Provide specific error messages for auth issues
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                QMessageBox.warning(self, "Authentication Error",
                    "Failed to load clicks: Your authentication token is invalid or expired.\n\n"
                    "Please reconnect to the API with a valid token.")
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                QMessageBox.warning(self, "Access Denied",
                    "Failed to load clicks: Access denied.\n\n"
                    "Your token may not have permission to view clicks.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load clicks: {error_msg}")

        worker = APIWorker(self.client.get_clicks, campaign_id=campaign_id)
        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        worker.start()

    def populate_clicks_table(self):
        """Populate the clicks table."""
        self.clicks_table.setRowCount(len(self.current_clicks))

        for row, click in enumerate(self.current_clicks):
            self.clicks_table.setItem(row, 0, QTableWidgetItem(click.get('id', '')))
            self.clicks_table.setItem(row, 1, QTableWidgetItem(click.get('campaign_id', '')))
            self.clicks_table.setItem(row, 2, QTableWidgetItem(click.get('ip_address', '')))
            self.clicks_table.setItem(row, 3, QTableWidgetItem(click.get('user_agent', '')[:50] + "..." if click.get('user_agent') and len(click.get('user_agent', '')) > 50 else click.get('user_agent', '')))
            self.clicks_table.setItem(row, 4, QTableWidgetItem(click.get('created_at', '')))

        self.clicks_table.resizeColumnsToContents()

    def refresh_all_data(self):
        """Refresh all data in all tabs."""
        self.refresh_dashboard()
        self.refresh_campaigns()
        self.refresh_goals()
        self.refresh_clicks()

    def show_create_campaign_dialog(self):
        """Show dialog to create a new campaign."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        dialog = CampaignDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            campaign_data = dialog.get_campaign_data()

            self.status_bar.showMessage("Creating campaign...")

            def on_success(result):
                self.status_bar.showMessage("Campaign created successfully")
                self.log_activity(f"Created campaign: {campaign_data['name']}")
                self.refresh_campaigns()
                QMessageBox.information(self, "Success", "Campaign created successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to create campaign")
                QMessageBox.warning(self, "Error", f"Failed to create campaign: {error_msg}")

            worker = APIWorker(self.client.create_campaign, campaign_data)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def show_create_goal_dialog(self):
        """Show dialog to create a new goal."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        if not self.current_campaigns:
            QMessageBox.warning(self, "Error", "Please load campaigns first")
            return

        # Load goal templates if not already loaded
        if not self.goal_templates:
            try:
                worker = APIWorker(self.client.get_goal_templates)
                worker.finished.connect(lambda templates: setattr(self, 'goal_templates', templates))
                worker.start()
            except:
                pass  # Templates are optional

        dialog = GoalDialog(self, None, self.current_campaigns, self.goal_templates)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()

            self.status_bar.showMessage("Creating goal...")

            def on_success(result):
                self.status_bar.showMessage("Goal created successfully")
                self.log_activity(f"Created goal: {goal_data['name']}")
                self.refresh_goals()
                QMessageBox.information(self, "Success", "Goal created successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to create goal")
                QMessageBox.warning(self, "Error", f"Failed to create goal: {error_msg}")

            worker = APIWorker(self.client.create_goal, goal_data)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def show_generate_click_dialog(self):
        """Show dialog to generate a click URL."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        if not self.current_campaigns:
            QMessageBox.warning(self, "Error", "Please load campaigns first")
            return

        dialog = GenerateClickDialog(self, self.current_campaigns)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            click_data = dialog.get_click_data()

            self.status_bar.showMessage("Generating click URL...")

            def on_success(result):
                click_url = result.get('url', result.get('click_url', 'No URL returned'))
                dialog.set_generated_url(click_url)
                self.status_bar.showMessage("Click URL generated successfully")
                self.log_activity(f"Generated click URL for campaign {click_data['campaign_id']}")

                # Show the URL in a message box with copy option
                msg = QMessageBox(self)
                msg.setWindowTitle("Click URL Generated")
                msg.setText("Click URL generated successfully!")
                msg.setDetailedText(click_url)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to generate click URL")
                QMessageBox.warning(self, "Error", f"Failed to generate click URL: {error_msg}")

            worker = APIWorker(self.client.generate_click, click_data)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def edit_campaign(self, campaign):
        """Edit a campaign."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        dialog = CampaignDialog(self, campaign)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            campaign_data = dialog.get_campaign_data()
            campaign_id = campaign.get('id')

            self.status_bar.showMessage("Updating campaign...")

            def on_success(result):
                self.status_bar.showMessage("Campaign updated successfully")
                self.log_activity(f"Updated campaign: {campaign_data['name']}")
                self.refresh_campaigns()
                QMessageBox.information(self, "Success", "Campaign updated successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to update campaign")
                QMessageBox.warning(self, "Error", f"Failed to update campaign: {error_msg}")

            worker = APIWorker(self.client.update_campaign, campaign_id, campaign_data)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def toggle_campaign_status(self, campaign):
        """Toggle campaign status (pause/resume)."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        campaign_id = campaign.get('id')
        current_status = campaign.get('status')
        is_active = current_status == 'active'

        action = "pause" if is_active else "resume"
        self.status_bar.showMessage(f"{action.capitalize()}ing campaign...")

        def on_success(result):
            self.status_bar.showMessage(f"Campaign {action}d successfully")
            self.log_activity(f"{action.capitalize()}d campaign: {campaign.get('name')}")
            self.refresh_campaigns()

        def on_error(error_msg):
            self.status_bar.showMessage(f"Failed to {action} campaign")
            QMessageBox.warning(self, "Error", f"Failed to {action} campaign: {error_msg}")

        if is_active:
            worker = APIWorker(self.client.pause_campaign, campaign_id)
        else:
            worker = APIWorker(self.client.resume_campaign, campaign_id)

        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        worker.start()

    def delete_campaign(self, campaign):
        """Delete a campaign."""
        reply = QMessageBox.question(
            self, "Delete Campaign",
            f"Are you sure you want to delete campaign '{campaign.get('name')}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if not self.client:
                QMessageBox.warning(self, "Error", "Not connected to API")
                return

            campaign_id = campaign.get('id')
            self.status_bar.showMessage("Deleting campaign...")

            def on_success(result):
                self.status_bar.showMessage("Campaign deleted successfully")
                self.log_activity(f"Deleted campaign: {campaign.get('name')}")
                self.refresh_campaigns()
                QMessageBox.information(self, "Success", "Campaign deleted successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to delete campaign")
                QMessageBox.warning(self, "Error", f"Failed to delete campaign: {error_msg}")

            worker = APIWorker(self.client.delete_campaign, campaign_id)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def edit_goal(self, goal):
        """Edit a goal."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        if not self.current_campaigns:
            QMessageBox.warning(self, "Error", "Please load campaigns first")
            return

        dialog = GoalDialog(self, goal, self.current_campaigns)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            goal_id = goal.get('id')

            self.status_bar.showMessage("Updating goal...")

            def on_success(result):
                self.status_bar.showMessage("Goal updated successfully")
                self.log_activity(f"Updated goal: {goal_data['name']}")
                self.refresh_goals()
                QMessageBox.information(self, "Success", "Goal updated successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to update goal")
                QMessageBox.warning(self, "Error", f"Failed to update goal: {error_msg}")

            worker = APIWorker(self.client.update_goal, goal_id, goal_data)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def delete_goal(self, goal):
        """Delete a goal."""
        reply = QMessageBox.question(
            self, "Delete Goal",
            f"Are you sure you want to delete goal '{goal.get('name')}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if not self.client:
                QMessageBox.warning(self, "Error", "Not connected to API")
                return

            goal_id = goal.get('id')
            self.status_bar.showMessage("Deleting goal...")

            def on_success(result):
                self.status_bar.showMessage("Goal deleted successfully")
                self.log_activity(f"Deleted goal: {goal.get('name')}")
                self.refresh_goals()
                QMessageBox.information(self, "Success", "Goal deleted successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to delete goal")
                QMessageBox.warning(self, "Error", f"Failed to delete goal: {error_msg}")

            worker = APIWorker(self.client.delete_goal, goal_id)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def show_track_conversion_dialog(self):
        """Show dialog to track a conversion."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        # Simple input dialog for conversion tracking
        from PyQt6.QtWidgets import QInputDialog

        campaign_names = [c.get('name', '') for c in self.current_campaigns]
        if not campaign_names:
            QMessageBox.warning(self, "Error", "Please load campaigns first")
            return

        campaign_name, ok = QInputDialog.getItem(
            self, "Track Conversion", "Select Campaign:", campaign_names, 0, False
        )

        if ok and campaign_name:
            # Find campaign ID
            campaign_id = None
            for c in self.current_campaigns:
                if c.get('name') == campaign_name:
                    campaign_id = c.get('id')
                    break

            if not campaign_id:
                return

            conversion_data = {
                "campaign_id": campaign_id,
                "value": 0.0,  # Can be extended with more fields
            }

            self.status_bar.showMessage("Tracking conversion...")

            def on_success(result):
                self.status_bar.showMessage("Conversion tracked successfully")
                self.log_activity(f"Tracked conversion for campaign {campaign_name}")
                QMessageBox.information(self, "Success", "Conversion tracked successfully!")

            def on_error(error_msg):
                self.status_bar.showMessage("Failed to track conversion")
                QMessageBox.warning(self, "Error", f"Failed to track conversion: {error_msg}")

            worker = APIWorker(self.client.track_conversion, conversion_data)
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()

    def refresh_conversions(self):
        """Refresh conversions list."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to API")
            return

        # Note: The API doesn't have a get_conversions endpoint yet
        # This is a placeholder for when it's implemented
        self.status_bar.showMessage("Conversion tracking endpoint not yet available in API")
        self.log_activity("Note: Conversion viewing requires additional API endpoint")

    def auto_refresh_data(self):
        """Auto-refresh data periodically."""
        if self.client and self.tab_widget.currentIndex() == 0:  # Dashboard tab
            self.refresh_dashboard()

    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh functionality."""
        if enabled and self.client:
            self.refresh_timer.start(30000)
            self.log_activity("Auto-refresh enabled")
        else:
            self.refresh_timer.stop()
            self.log_activity("Auto-refresh disabled")

    def update_campaign_selectors(self):
        """Update campaign selectors in other tabs."""
        # Analytics tab
        self.analytics_campaign_select.clear()
        self.analytics_campaign_select.addItem("All Campaigns", None)
        for campaign in self.current_campaigns:
            self.analytics_campaign_select.addItem(campaign.get('name', ''), campaign.get('id', ''))

        # Clicks tab
        self.clicks_campaign_select.clear()
        self.clicks_campaign_select.addItem("All Campaigns", None)
        for campaign in self.current_campaigns:
            self.clicks_campaign_select.addItem(campaign.get('name', ''), campaign.get('id', ''))

        # Conversions tab
        self.conversions_campaign_select.clear()
        self.conversions_campaign_select.addItem("All Campaigns", None)
        for campaign in self.current_campaigns:
            self.conversions_campaign_select.addItem(campaign.get('name', ''), campaign.get('id', ''))

    def save_settings(self):
        """Save settings."""
        base_url = self.settings_base_url.text().strip()
        bearer_token = self.settings_bearer_token.text().strip()
        api_key = self.settings_api_key.text().strip()

        # Validate base URL if provided
        if base_url and not self._validate_url(base_url):
            QMessageBox.warning(self, "Invalid Base URL",
                "The base URL format is incorrect.\n\n"
                "URL should start with 'http://' or 'https://' and be a valid web address.\n"
                "Example: http://127.0.0.1:5000/v1")
            return

        # Validate tokens if provided
        if bearer_token and not self._validate_token(bearer_token):
            QMessageBox.warning(self, "Invalid Bearer Token",
                "The Bearer token format is incorrect.\n\n"
                "Token should be a valid Bearer token (usually starts with 'Bearer ' or is a JWT-like string).\n"
                "Please check your token and try again.")
            return

        if api_key and not self._validate_api_key(api_key):
            QMessageBox.warning(self, "Invalid API Key",
                "The API key format is incorrect.\n\n"
                "API key should be alphanumeric with allowed special characters (-, _, .).\n"
                "Please check your API key and try again.")
            return

        QMessageBox.information(self, "Settings", "Settings saved successfully")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About",
            "Advertising Platform Admin Panel\n\n"
            "A PyQt6-based admin interface for managing\n"
            "Advertising Platform business tasks.\n\n"
            "Version 1.0.0"
        )

    def log_activity(self, message):
        """Log activity to the dashboard."""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.activity_log.append(f"<span style='color: #7f8c8d;'>[{timestamp}]</span> {message}")

    def load_config(self):
        """Load configuration from environment or config file."""
        # This would load saved settings
        self.log_activity("🚀 <b>Welcome to Advertising Platform Admin Panel!</b>")
        self.log_activity("ℹ️  Connect to the API to get started.")

    def _validate_token(self, token):
        """Validate authentication token format."""
        import re

        if not token or len(token.strip()) == 0:
            return False

        # Basic validation: should be reasonably long and contain valid characters
        # Allow Bearer tokens, JWT tokens, or API keys
        if len(token) < 10:
            return False

        # Check for invalid characters (basic check)
        if re.search(r'[<>]', token):
            return False

        # Allow alphanumeric, dots, hyphens, underscores, plus signs (common in tokens)
        if not re.match(r'^[A-Za-z0-9._\-+/=]+$', token):
            return False

        return True

    def _validate_api_key(self, api_key):
        """Validate API key format."""
        import re

        if not api_key or len(api_key.strip()) == 0:
            return False

        # API keys are typically shorter than auth tokens
        if len(api_key) < 8:
            return False

        # Allow alphanumeric with common separators
        if not re.match(r'^[A-Za-z0-9._\-]+$', api_key):
            return False

        return True

    def _validate_url(self, url):
        """Validate URL format."""
        import re

        if not url or len(url.strip()) == 0:
            return False

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

        return url_pattern.match(url) is not None

    def closeEvent(self, event):
        """Handle application close event."""
        if self.client:
            self.client.close()
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Advertising Platform Admin Panel")
    app.setApplicationVersion("2.0.0")  # Updated with dark theme

    # Apply dark theme
    if DARK_THEME_AVAILABLE:
        app.setStyleSheet(get_stylesheet())
        print("🌙 Dark theme applied successfully!")
    else:
        # Fallback to Fusion style
        app.setStyle('Fusion')
        print("⚠️  Dark theme not available, using Fusion style")

    # Create and show main window
    window = AdminPanel()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()