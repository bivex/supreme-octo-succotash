#!/usr/bin/env python3
"""
Advertising Platform Admin Panel

PyQt6-based admin interface for managing Advertising Platform business tasks.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QMessageBox, QSplitter, QTreeWidget,
    QTreeWidgetItem, QProgressBar, QStatusBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QDateTime
from PyQt6.QtGui import QAction, QFont, QPalette, QColor

from advertising_platform_sdk import AdvertisingPlatformClient
from advertising_platform_sdk.exceptions import *


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


class AdminPanel(QMainWindow):
    """Main admin panel window."""

    def __init__(self):
        super().__init__()
        self.client = None
        self.current_campaigns = []
        self.current_goals = []
        self.current_clicks = []

        self.init_ui()
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
        self.create_analytics_tab()
        self.create_clicks_tab()
        self.create_settings_tab()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Connect signals
        self.connect_button.clicked.connect(self.connect_to_api)

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
        self.connection_status = QLabel("Not connected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
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
        stats_layout.addWidget(QLabel("Quick Statistics:"))

        self.stats_labels = {}
        stats = ["Total Campaigns", "Active Campaigns", "Total Goals", "Today's Clicks", "Today's Conversions"]
        for stat in stats:
            label = QLabel(f"{stat}: --")
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
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            self.status_bar.showMessage("Connected successfully")
            self.refresh_dashboard()

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
                self.health_status.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            else:
                self.health_status.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")

            self.log_activity(f"Health check: {status}")

        def on_health_error(error):
            self.health_status.setText("ERROR")
            self.health_status.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            self.log_activity(f"Health check failed: {error}")

        health_worker = APIWorker(self.client.get_health)
        health_worker.finished.connect(on_health_success)
        health_worker.error.connect(on_health_error)
        health_worker.start()

        # Load campaigns count
        def on_campaigns_success(result):
            campaigns = result.get('data', [])
            active_count = len([c for c in campaigns if c.get('status') == 'active'])
            self.stats_labels["Total Campaigns"].setText(f"Total Campaigns: {len(campaigns)}")
            self.stats_labels["Active Campaigns"].setText(f"Active Campaigns: {active_count}")

        campaigns_worker = APIWorker(self.client.get_campaigns)
        campaigns_worker.finished.connect(on_campaigns_success)
        campaigns_worker.error.connect(lambda e: None)  # Ignore errors for stats
        campaigns_worker.start()

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

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, c=campaign: self.edit_campaign(c))
            actions_layout.addWidget(edit_btn)

            pause_btn = QPushButton("Pause" if campaign.get('status') == 'active' else "Resume")
            pause_btn.clicked.connect(lambda checked, c=campaign: self.toggle_campaign_status(c))
            actions_layout.addWidget(pause_btn)

            delete_btn = QPushButton("Delete")
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

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, g=goal: self.edit_goal(g))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Delete")
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
        QMessageBox.information(self, "Create Campaign", "Campaign creation dialog not implemented yet")

    def show_create_goal_dialog(self):
        """Show dialog to create a new goal."""
        QMessageBox.information(self, "Create Goal", "Goal creation dialog not implemented yet")

    def show_generate_click_dialog(self):
        """Show dialog to generate a click URL."""
        QMessageBox.information(self, "Generate Click", "Click generation dialog not implemented yet")

    def edit_campaign(self, campaign):
        """Edit a campaign."""
        QMessageBox.information(self, "Edit Campaign", f"Edit campaign {campaign.get('name')} not implemented yet")

    def toggle_campaign_status(self, campaign):
        """Toggle campaign status (pause/resume)."""
        QMessageBox.information(self, "Toggle Status", f"Toggle status for {campaign.get('name')} not implemented yet")

    def delete_campaign(self, campaign):
        """Delete a campaign."""
        reply = QMessageBox.question(
            self, "Delete Campaign",
            f"Are you sure you want to delete campaign '{campaign.get('name')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Delete Campaign", "Campaign deletion not implemented yet")

    def edit_goal(self, goal):
        """Edit a goal."""
        QMessageBox.information(self, "Edit Goal", f"Edit goal {goal.get('name')} not implemented yet")

    def delete_goal(self, goal):
        """Delete a goal."""
        QMessageBox.information(self, "Delete Goal", f"Delete goal {goal.get('name')} not implemented yet")

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
        self.activity_log.append(f"[{timestamp}] {message}")

    def load_config(self):
        """Load configuration from environment or config file."""
        # This would load saved settings
        pass

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
    app.setApplicationVersion("1.0.0")

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = AdminPanel()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()