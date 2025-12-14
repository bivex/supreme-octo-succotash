"""Main window for the admin panel."""

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QComboBox, QSpinBox, QGroupBox,
    QFormLayout, QMessageBox, QStatusBar, QDoubleSpinBox,
    QCheckBox, QDateEdit, QProgressBar, QFrame, QScrollArea, QDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, QDateTime, Qt, QTimer, QDate
from PyQt6.QtGui import QAction, QPalette, QColor, QFont

# Import SDK
from advertising_platform_sdk import AdvertisingPlatformClient
from advertising_platform_sdk.exceptions import *

# Import presentation components
from ..workers import APIWorker
from ..dialogs import CampaignDialog, GoalDialog, GenerateClickDialog, OfferDialog, LandingPageDialog

# Import controllers
from ..controllers import (
    UIController, DataController, TableController, CRUDController,
    SettingsController, ConnectionController
)


class MainWindow(QMainWindow):
    """Main admin panel window with separated concerns via controllers."""

    def __init__(self):
        super().__init__()

        # Data storage
        self.client = None
        self.current_campaigns = []
        self.current_offers = []
        self.current_landing_pages = []
        self.current_goals = []
        self.current_clicks = []
        self.current_conversions = []
        self.goal_templates = []

        # Thread management (now handled by WorkerManager)
        self.active_workers = []

        # Dependency injection (set by Application)
        self.container = None
        self.app_settings = None

        # Dialogs
        self.campaign_dialog = CampaignDialog(self)
        self.goal_dialog = GoalDialog(self)
        self.click_dialog = GenerateClickDialog(self)
        self.offer_dialog = OfferDialog(self)
        self.landing_page_dialog = LandingPageDialog(self)

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_data)

        # Initialize controllers
        self._init_controllers()

        # Initialize UI after controller setup
        self.init_ui()
        # Modern stylesheet now applied globally via dark theme
        # self.apply_modern_stylesheet()  # Commented out - using global dark theme

    def _init_controllers(self) -> None:
        """Initialize all controllers."""
        self.ui_controller = UIController(self)
        self.data_controller = DataController(self)
        self.table_controller = TableController(self)
        self.crud_controller = CRUDController(self)
        self.settings_controller = SettingsController(self)
        self.connection_controller = ConnectionController(self)

    # UI Methods - Delegated to UI Controller
    def init_ui(self) -> None:
        """Initialize the user interface using UI controller."""
        self.ui_controller.initialize()

    def apply_modern_stylesheet(self) -> None:
        """Apply modern stylesheet."""
        self.ui_controller.apply_modern_stylesheet()

    def create_menu_bar(self) -> None:
        """Create menu bar."""
        self.ui_controller.create_menu_bar()

    # Data Methods - Delegated to Data Controller
    def refresh_dashboard(self) -> None:
        """Refresh dashboard data."""
        self.data_controller.refresh_dashboard()

    def refresh_campaigns(self) -> None:
        """Refresh campaigns data."""
        self.data_controller.refresh_campaigns()

    def refresh_offers(self) -> None:
        """Refresh offers data."""
        self.data_controller.refresh_offers()

    def refresh_landing_pages(self) -> None:
        """Refresh landing pages data."""
        self.data_controller.refresh_landing_pages()

    def refresh_goals(self) -> None:
        """Refresh goals data."""
        self.data_controller.refresh_goals()

    def refresh_clicks(self) -> None:
        """Refresh clicks data."""
        self.data_controller.refresh_clicks()

    def load_analytics(self) -> None:
        """Load analytics data."""
        self.data_controller.load_analytics()

    def refresh_conversions(self) -> None:
        """Refresh conversions data."""
        self.data_controller.refresh_conversions()

    def refresh_all_data(self) -> None:
        """Refresh all data."""
        self.data_controller.refresh_all_data()

    def auto_refresh_data(self) -> None:
        """Auto refresh data."""
        self.data_controller.auto_refresh_data()

    # Table Methods - Delegated to Table Controller
    def populate_campaigns_table(self) -> None:
        """Populate campaigns table."""
        self.table_controller.populate_campaigns_table()

    def populate_offers_table(self) -> None:
        """Populate offers table."""
        self.table_controller.populate_offers_table()

    def populate_landing_pages_table(self) -> None:
        """Populate landing pages table."""
        self.table_controller.populate_landing_pages_table()

    def populate_goals_table(self) -> None:
        """Populate goals table."""
        self.table_controller.populate_goals_table()

    def populate_clicks_table(self) -> None:
        """Populate clicks table."""
        self.table_controller.populate_clicks_table()

    def filter_campaigns(self) -> None:
        """Filter campaigns."""
        self.table_controller.filter_campaigns()

    def display_analytics(self, data) -> None:
        """Display analytics data."""
        self.table_controller.display_analytics(data)

    # CRUD Methods - Delegated to CRUD Controller
    def show_create_campaign_dialog(self) -> None:
        """Show create campaign dialog."""
        self.crud_controller.show_create_campaign_dialog()

    def show_create_offer_dialog(self) -> None:
        """Show create offer dialog."""
        self.crud_controller.show_create_offer_dialog()

    def show_new_landing_page_dialog(self) -> None:
        """Show create landing page dialog."""
        self.crud_controller.show_new_landing_page_dialog()

    def show_create_goal_dialog(self) -> None:
        """Show create goal dialog."""
        self.crud_controller.show_create_goal_dialog()

    def show_edit_offer_dialog(self, offer) -> None:
        """Show edit offer dialog."""
        self.crud_controller.show_edit_offer_dialog(offer)

    def show_edit_landing_page_dialog(self, landing_page) -> None:
        """Show edit landing page dialog."""
        self.crud_controller.show_edit_landing_page_dialog(landing_page)

    def show_generate_click_dialog(self) -> None:
        """Show generate click dialog."""
        self.crud_controller.show_generate_click_dialog()

    def edit_campaign(self, campaign) -> None:
        """Edit campaign."""
        self.crud_controller.edit_campaign(campaign)

    def toggle_campaign_status(self, campaign) -> None:
        """Toggle campaign status."""
        self.crud_controller.toggle_campaign_status(campaign)

    def delete_campaign(self, campaign) -> None:
        """Delete campaign."""
        self.crud_controller.delete_campaign(campaign)

    def edit_goal(self, goal) -> None:
        """Edit goal."""
        self.crud_controller.edit_goal(goal)

    def delete_goal(self, goal) -> None:
        """Delete goal."""
        self.crud_controller.delete_goal(goal)

    def delete_offer(self, offer) -> None:
        """Delete offer."""
        self.crud_controller.delete_offer(offer)

    def delete_landing_page(self, landing_page) -> None:
        """Delete landing page."""
        self.crud_controller.delete_landing_page(landing_page)

    def show_track_conversion_dialog(self) -> None:
        """Show track conversion dialog."""
        self.crud_controller.show_track_conversion_dialog()

    # Settings Methods - Delegated to Settings Controller
    def save_settings(self) -> None:
        """Save settings."""
        self.settings_controller.save_settings()

    def load_config(self) -> None:
        """Load configuration."""
        self.settings_controller.load_config()

    def toggle_auto_refresh(self, enabled: bool) -> None:
        """Toggle auto refresh."""
        self.settings_controller.toggle_auto_refresh(enabled)

    def update_campaign_selectors(self) -> None:
        """Update campaign selectors."""
        self.settings_controller.update_campaign_selectors()

    def log_activity(self, message: str) -> None:
        """Log activity."""
        self.settings_controller.log_activity(message)

    def _validate_url(self, url: str) -> bool:
        """Validate URL."""
        return self.settings_controller._validate_url(url)

    def _validate_token(self, token: str) -> bool:
        """Validate token."""
        return self.settings_controller._validate_token(token)

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        return self.settings_controller._validate_api_key(api_key)

    # Connection Methods - Delegated to Connection Controller
    def connect_to_api(self) -> None:
        """Connect to API."""
        self.connection_controller.connect_to_api()

    def test_connection(self) -> None:
        """Test connection."""
        self.connection_controller.test_connection()

    def show_about(self) -> None:
        """Show about dialog."""
        self.connection_controller.show_about()

    def create_worker(self, func, *args, **kwargs):
        """Create worker."""
        return self.connection_controller.create_worker(func, *args, **kwargs)

    def closeEvent(self, event):
        """Handle application close event."""
        # Stop auto-refresh timer
        self.refresh_timer.stop()

        # Clean up workers
        for worker in self.active_workers[:]:  # Copy list to avoid modification during iteration
            if worker.isRunning():
                worker.quit()
                worker.wait()

        # Accept the close event
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Advertising Platform Admin Panel")
    app.setApplicationVersion("2.0.0")  # Updated with refactored controllers

    # Apply dark theme
    try:
        from ..presentation.styles import get_stylesheet
        DARK_THEME_AVAILABLE = True
        if DARK_THEME_AVAILABLE:
            app.setStyleSheet(get_stylesheet())
            print("🌙 Dark theme applied successfully!")
        else:
            app.setStyle('Fusion')
            print("⚠️  Dark theme not available, using Fusion style")
    except ImportError:
        app.setStyle('Fusion')
        print("⚠️  Dark theme not available, using Fusion style")

    # Create and show main window
    window = MainWindow()
    window.init_ui()
    window.load_config()
    window.show()

    sys.exit(app.exec())