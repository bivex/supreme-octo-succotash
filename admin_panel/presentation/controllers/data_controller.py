# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
Data Controller - Handles data refresh and loading operations.
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QMessageBox

import logging

logger = logging.getLogger(__name__)

from .base_controller import BaseController, WorkerManager


class DataController(BaseController):
    """Handles data refresh and loading operations."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.worker_manager = WorkerManager(main_window)

    def initialize(self) -> None:
        """Initialize the data controller."""
        pass

    def refresh_dashboard(self) -> None:
        """Refresh dashboard data."""
        if not self.main_window.client:
            return

        self.main_window.health_progress.setVisible(True)
        self.main_window.health_status_label.setText("Checking health...")

        def check_health():
            try:
                # Health check logic would go here
                return {"status": "healthy", "campaigns_count": 0, "goals_count": 0}
            except Exception as e:
                raise Exception(f"Health check failed: {str(e)}")

        worker = self.worker_manager.create_worker(check_health)

        def on_health_success(result):
            self.main_window.health_progress.setVisible(False)
            self.main_window.health_status_label.setText(f"Status: {result['status'].title()}")

            stats_text = f"Campaigns: {result['campaigns_count']}\n"
            stats_text += f"Goals: {result['goals_count']}"
            self.main_window.stats_label.setText(stats_text)

        def on_health_error(error_msg):
            self.main_window.health_progress.setVisible(False)
            self.main_window.health_status_label.setText(f"Status: Error - {error_msg}")

        worker.finished.connect(on_health_success)
        worker.error.connect(on_health_error)

    def refresh_campaigns(self) -> None:
        """Refresh campaigns data."""
        if not self.main_window.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        def load_campaigns():
            try:
                logger.debug("DataController: Attempting to load campaigns from API...")
                logger.debug(f"DataController: Type of self.main_window.container: {type(self.main_window.container)}")
                # Load campaigns logic would go here
                campaigns = self.main_window.container.campaign_repository.find_all()
                logger.debug(f"DataController: Loaded {len(campaigns)} campaigns: {campaigns}")
                return campaigns
            except Exception as e:
                raise Exception(f"Failed to load campaigns: {str(e)}")

        worker = self.worker_manager.create_worker(load_campaigns)

        def on_success(result):
            logger.debug(f"DataController: Campaigns loaded successfully in on_success: {len(result)} items")
            self.main_window.current_campaigns = result
            self.main_window.populate_campaigns_table()

        def on_error(error_msg):
            QMessageBox.critical(self.main_window, "Error", f"Failed to load campaigns:\n{error_msg}")

        worker.finished.connect(on_success)
        worker.error.connect(on_error)

    def refresh_offers(self) -> None:
        """Refresh offers data."""
        if not self.main_window.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        def load_offers():
            try:
                # Load offers logic would go here
                return []
            except Exception as e:
                raise Exception(f"Failed to load offers: {str(e)}")

        worker = self.worker_manager.create_worker(load_offers)

        def on_success(result):
            self.main_window.current_offers = result
            self.main_window.populate_offers_table()

        def on_error(error_msg):
            QMessageBox.critical(self.main_window, "Error", f"Failed to load offers:\n{error_msg}")

        worker.finished.connect(on_success)
        worker.error.connect(on_error)

    def refresh_landing_pages(self) -> None:
        """Refresh landing pages data."""
        if not self.main_window.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        def load_landing_pages():
            try:
                # Load landing pages logic would go here
                return []
            except Exception as e:
                raise Exception(f"Failed to load landing pages: {str(e)}")

        worker = self.worker_manager.create_worker(load_landing_pages)

        def on_success(result):
            self.main_window.current_landing_pages = result
            self.main_window.populate_landing_pages_table()

        def on_error(error_msg):
            QMessageBox.critical(self.main_window, "Error", f"Failed to load landing pages:\n{error_msg}")

        worker.finished.connect(on_success)
        worker.error.connect(on_error)

    def refresh_goals(self) -> None:
        """Refresh goals data."""
        if not self.main_window.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        def load_goals():
            try:
                # Load goals logic would go here
                return []
            except Exception as e:
                raise Exception(f"Failed to load goals: {str(e)}")

        worker = self.worker_manager.create_worker(load_goals)

        def on_success(result):
            self.main_window.current_goals = result
            self.main_window.populate_goals_table()

        def on_error(error_msg):
            QMessageBox.critical(self.main_window, "Error", f"Failed to load goals:\n{error_msg}")

        worker.finished.connect(on_success)
        worker.error.connect(on_error)

    def refresh_clicks(self) -> None:
        """Refresh clicks data."""
        if not self.main_window.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        def load_clicks():
            try:
                # Load clicks logic would go here
                return []
            except Exception as e:
                raise Exception(f"Failed to load clicks: {str(e)}")

        worker = self.worker_manager.create_worker(load_clicks)

        def on_success(result):
            self.main_window.current_clicks = result
            self.main_window.populate_clicks_table()

        def on_error(error_msg):
            QMessageBox.critical(self.main_window, "Error", f"Failed to load clicks:\n{error_msg}")

        worker.finished.connect(on_success)
        worker.error.connect(on_error)

    def load_analytics(self) -> None:
        """Load analytics data."""
        if not self.main_window.client:
            QMessageBox.warning(self.main_window, "Warning", "Not connected to API")
            return

        campaign_id = self.main_window.analytics_campaign_combo.currentData()

        def load_analytics_data():
            try:
                # Load analytics logic would go here
                return {"message": "Analytics data would be loaded here"}
            except Exception as e:
                raise Exception(f"Failed to load analytics: {str(e)}")

        worker = self.worker_manager.create_worker(load_analytics_data)

        def on_success(result):
            self.main_window.display_analytics(result)

        def on_error(error_msg):
            QMessageBox.critical(self.main_window, "Error", f"Failed to load analytics:\n{error_msg}")

        worker.finished.connect(on_success)
        worker.error.connect(on_error)

    def refresh_conversions(self) -> None:
        """Refresh conversions data."""
        # Implementation for refreshing conversions
        pass

    def refresh_all_data(self) -> None:
        """Refresh all data."""
        self.refresh_dashboard()
        self.refresh_campaigns()
        self.refresh_offers()
        self.refresh_landing_pages()
        self.refresh_goals()
        self.refresh_clicks()
        self.refresh_conversions()

    def auto_refresh_data(self) -> None:
        """Auto refresh data based on timer."""
        if self.main_window.refresh_timer.isActive():
            self.refresh_all_data()