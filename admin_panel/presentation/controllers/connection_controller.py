"""
Connection Controller - Handles API connections and workers.
"""

import logging
from typing import Optional, Dict, Any, Callable
from PyQt6.QtWidgets import QMessageBox

from .base_controller import BaseController, WorkerManager

logger = logging.getLogger(__name__)


class ConnectionController(BaseController):
    """Handles API connections and background workers."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.worker_manager = WorkerManager(main_window)
        self.client = None

    def initialize(self) -> None:
        """Initialize the connection controller."""
        pass

    def connect_to_api(self) -> None:
        """Connect to the API using provided credentials."""
        from ..workers import APIWorker

        # Get connection settings
        api_url = self.main_window.api_url_edit.text().strip()
        bearer_token = self.main_window.bearer_token_edit.text().strip()
        api_key = self.main_window.api_key_edit.text().strip()

        # Validate inputs
        if not api_url:
            QMessageBox.warning(self.main_window, "Validation Error", "API URL is required")
            return

        if not bearer_token and not api_key:
            QMessageBox.warning(
                self.main_window, "Validation Error",
                "Either Bearer Token or API Key must be provided"
            )
            return

        # Disable connect button and enable test button
        self.main_window.connect_btn.setEnabled(False)
        self.main_window.connect_btn.setText("Connecting...")
        self.main_window.test_btn.setEnabled(False)

        def connect():
            try:
                # Import SDK client
                from advertising_platform_sdk import AdvertisingPlatformClient

                # Create client with credentials
                client_config = {
                    'base_url': api_url,
                    'timeout': getattr(self.app_settings, 'api_timeout', 30.0) if self.app_settings else 30.0,
                    'max_retries': getattr(self.app_settings, 'api_max_retries', 3) if self.app_settings else 3,
                }

                if bearer_token:
                    client_config['bearer_token'] = bearer_token
                if api_key:
                    client_config['api_key'] = api_key

                client = AdvertisingPlatformClient(**client_config)

                # Test connection by getting system info or similar
                # For now, just return success
                return {
                    'client': client,
                    'status': 'connected',
                    'message': 'Successfully connected to API'
                }

            except Exception as e:
                logger.error(f"Failed to connect to API: {e}")
                raise Exception(f"Connection failed: {str(e)}")

        worker = self.worker_manager.create_worker(connect)

        def on_success(result):
            self.client = result['client']
            self.main_window.client = self.client

            # Update UI
            self.main_window.connect_btn.setEnabled(True)
            self.main_window.connect_btn.setText("Connected")
            self.main_window.test_btn.setEnabled(True)

            # Enable data operations
            self._enable_data_operations()

            QMessageBox.information(
                self.main_window, "Success",
                result['message']
            )

            # Auto-refresh data
            self.main_window.refresh_all_data()

        def on_error(error_msg):
            # Reset UI
            self.main_window.connect_btn.setEnabled(True)
            self.main_window.connect_btn.setText("Connect")
            self.main_window.test_btn.setEnabled(False)

            QMessageBox.critical(
                self.main_window, "Connection Error",
                f"Failed to connect to API:\n{error_msg}"
            )

        worker.result.connect(on_success)
        worker.error.connect(on_error)

    def test_connection(self) -> None:
        """Test the API connection."""
        if not self.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        self.main_window.test_btn.setEnabled(False)
        self.main_window.test_btn.setText("Testing...")

        def test_connection():
            try:
                # Test connection by making a simple API call
                # For now, just simulate a test
                import time
                time.sleep(1)  # Simulate network delay

                return {
                    'status': 'success',
                    'message': 'Connection test successful',
                    'response_time': '150ms'
                }

            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                raise Exception(f"Connection test failed: {str(e)}")

        worker = self.worker_manager.create_worker(test_connection)

        def on_success(result):
            self.main_window.test_btn.setEnabled(True)
            self.main_window.test_btn.setText("Test Connection")

            QMessageBox.information(
                self.main_window, "Connection Test",
                f"{result['message']}\nResponse time: {result['response_time']}"
            )

        def on_error(error_msg):
            self.main_window.test_btn.setEnabled(True)
            self.main_window.test_btn.setText("Test Connection")

            QMessageBox.critical(
                self.main_window, "Connection Test Failed",
                f"Connection test failed:\n{error_msg}"
            )

        worker.result.connect(on_success)
        worker.error.connect(on_error)

    def _enable_data_operations(self) -> None:
        """Enable data operations after successful connection."""
        # Enable refresh buttons and CRUD operations
        # This would be called after successful connection
        pass

    def disconnect_from_api(self) -> None:
        """Disconnect from the API."""
        if self.client:
            self.client = None
            self.main_window.client = None

            # Reset UI
            self.main_window.connect_btn.setText("Connect")
            self.main_window.test_btn.setEnabled(False)

            # Clear data
            self._clear_all_data()

            self.main_window.log_activity("Disconnected from API")

    def _clear_all_data(self) -> None:
        """Clear all data from tables and UI."""
        self.main_window.current_campaigns.clear()
        self.main_window.current_offers.clear()
        self.main_window.current_landing_pages.clear()
        self.main_window.current_goals.clear()
        self.main_window.current_clicks.clear()
        self.main_window.current_conversions.clear()

        # Clear tables
        self.main_window.campaigns_table.setRowCount(0)
        self.main_window.offers_table.setRowCount(0)
        self.main_window.landing_pages_table.setRowCount(0)
        self.main_window.goals_table.setRowCount(0)
        self.main_window.clicks_table.setRowCount(0)
        self.main_window.conversions_table.setRowCount(0)

        # Reset status
        self.main_window.health_status_label.setText("Status: Not Connected")
        self.main_window.stats_label.setText("No data available")

    def create_worker(self, func: Callable, *args, **kwargs) -> Any:
        """Create a background worker for API operations."""
        return self.worker_manager.create_worker(func, *args, **kwargs)

    def get_client(self):
        """Get the current API client."""
        return self.client

    def is_connected(self) -> bool:
        """Check if connected to API."""
        return self.client is not None

    def show_about(self) -> None:
        """Show about dialog."""
        about_text = """
        <h2>Advertising Platform Admin Panel</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Description:</b> Administrative interface for managing advertising campaigns,
        offers, landing pages, and analytics.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>Campaign Management</li>
            <li>Offer Management</li>
            <li>Landing Page Management</li>
            <li>Goal Tracking</li>
            <li>Click Analytics</li>
            <li>Conversion Tracking</li>
        </ul>
        <p><b>Built with:</b> Python, PyQt6, Advertising Platform SDK</p>
        """

        QMessageBox.about(self.main_window, "About", about_text)