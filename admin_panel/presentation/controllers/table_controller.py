"""
Table Controller - Handles table population and filtering.
"""

from typing import List, Any, Dict
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QMessageBox
from PyQt6.QtCore import Qt

from .base_controller import BaseController


class TableController(BaseController):
    """Handles table population and filtering."""

    def initialize(self) -> None:
        """Initialize the table controller."""
        pass

    def populate_campaigns_table(self) -> None:
        """Populate campaigns table."""
        table = self.main_window.campaigns_table
        campaigns = self.main_window.current_campaigns

        table.setRowCount(len(campaigns))

        for row, campaign in enumerate(campaigns):
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(campaign.id)))

            # Name
            table.setItem(row, 1, QTableWidgetItem(campaign.name))

            # Status
            table.setItem(row, 2, QTableWidgetItem(campaign.status.value.title()))

            # Budget
            budget_text = f"${campaign.budget.amount} {campaign.budget.currency}"
            table.setItem(row, 3, QTableWidgetItem(budget_text))

            # Date Range
            date_range = f"{campaign.date_range.start_date} - {campaign.date_range.end_date}"
            table.setItem(row, 4, QTableWidgetItem(date_range))

            # Actions
            actions_widget = self._create_campaign_actions(campaign)
            table.setCellWidget(row, 5, actions_widget)

        table.resizeColumnsToContents()

    def _create_campaign_actions(self, campaign):
        """Create action buttons for campaign row."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.main_window.edit_campaign(campaign))
        layout.addWidget(edit_btn)

        # Toggle status button
        status_text = "Pause" if campaign.status.value == "active" else "Resume"
        status_btn = QPushButton(status_text)
        status_btn.clicked.connect(lambda: self.main_window.toggle_campaign_status(campaign))
        layout.addWidget(status_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.main_window.delete_campaign(campaign))
        layout.addWidget(delete_btn)

        return widget

    def populate_offers_table(self) -> None:
        """Populate offers table."""
        table = self.main_window.offers_table
        offers = self.main_window.current_offers

        table.setRowCount(len(offers))

        for row, offer in enumerate(offers):
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(offer.id)))

            # Name
            table.setItem(row, 1, QTableWidgetItem(offer.name))

            # URL
            table.setItem(row, 2, QTableWidgetItem(str(offer.url)))

            # Weight
            table.setItem(row, 3, QTableWidgetItem(str(offer.weight)))

            # Status
            status_text = "Active" if offer.is_active else "Inactive"
            table.setItem(row, 4, QTableWidgetItem(status_text))

            # Campaign
            campaign_name = "N/A"  # Would need to look up campaign name
            table.setItem(row, 5, QTableWidgetItem(campaign_name))

            # Actions
            actions_widget = self._create_offer_actions(offer)
            table.setCellWidget(row, 6, actions_widget)

        table.resizeColumnsToContents()

    def _create_offer_actions(self, offer):
        """Create action buttons for offer row."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.main_window.show_edit_offer_dialog(offer))
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.main_window.delete_offer(offer))
        layout.addWidget(delete_btn)

        return widget

    def populate_landing_pages_table(self) -> None:
        """Populate landing pages table."""
        table = self.main_window.landing_pages_table
        landing_pages = self.main_window.current_landing_pages

        table.setRowCount(len(landing_pages))

        for row, landing_page in enumerate(landing_pages):
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(landing_page.id)))

            # Name
            table.setItem(row, 1, QTableWidgetItem(landing_page.name))

            # URL
            table.setItem(row, 2, QTableWidgetItem(str(landing_page.url)))

            # Weight
            table.setItem(row, 3, QTableWidgetItem(str(landing_page.weight)))

            # Status
            status_text = "Active" if landing_page.is_active else "Inactive"
            table.setItem(row, 4, QTableWidgetItem(status_text))

            # Actions
            actions_widget = self._create_landing_page_actions(landing_page)
            table.setCellWidget(row, 5, actions_widget)

        table.resizeColumnsToContents()

    def _create_landing_page_actions(self, landing_page):
        """Create action buttons for landing page row."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.main_window.show_edit_landing_page_dialog(landing_page))
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.main_window.delete_landing_page(landing_page))
        layout.addWidget(delete_btn)

        return widget

    def populate_goals_table(self) -> None:
        """Populate goals table."""
        table = self.main_window.goals_table
        goals = self.main_window.current_goals

        table.setRowCount(len(goals))

        for row, goal in enumerate(goals):
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(goal.id)))

            # Name
            table.setItem(row, 1, QTableWidgetItem(goal.name))

            # Type
            table.setItem(row, 2, QTableWidgetItem(goal.goal_type.value))

            # Value
            table.setItem(row, 3, QTableWidgetItem(str(goal.target_value)))

            # Actions
            actions_widget = self._create_goal_actions(goal)
            table.setCellWidget(row, 4, actions_widget)

        table.resizeColumnsToContents()

    def _create_goal_actions(self, goal):
        """Create action buttons for goal row."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.main_window.edit_goal(goal))
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.main_window.delete_goal(goal))
        layout.addWidget(delete_btn)

        return widget

    def populate_clicks_table(self) -> None:
        """Populate clicks table."""
        table = self.main_window.clicks_table
        clicks = self.main_window.current_clicks

        table.setRowCount(len(clicks))

        for row, click in enumerate(clicks):
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(click.id)))

            # Campaign
            campaign_name = "N/A"  # Would need to look up campaign name
            table.setItem(row, 1, QTableWidgetItem(campaign_name))

            # Offer
            offer_name = "N/A"  # Would need to look up offer name
            table.setItem(row, 2, QTableWidgetWidgetItem(offer_name))

            # Landing Page
            landing_page_name = "N/A"  # Would need to look up landing page name
            table.setItem(row, 3, QTableWidgetItem(landing_page_name))

            # IP
            table.setItem(row, 4, QTableWidgetItem(click.ip_address or "N/A"))

            # User Agent
            table.setItem(row, 5, QTableWidgetItem(click.user_agent or "N/A"))

            # Timestamp
            table.setItem(row, 6, QTableWidgetItem(str(click.timestamp)))

        table.resizeColumnsToContents()

    def filter_campaigns(self) -> None:
        """Filter campaigns based on status."""
        status_filter = self.main_window.campaign_filter_combo.currentData()

        if status_filter is None:
            # Show all campaigns
            filtered_campaigns = self.main_window.current_campaigns
        else:
            # Filter by status
            filtered_campaigns = [
                c for c in self.main_window.current_campaigns
                if c.status.value == status_filter
            ]

        # Update table with filtered data
        table = self.main_window.campaigns_table
        table.setRowCount(len(filtered_campaigns))

        for row, campaign in enumerate(filtered_campaigns):
            # Same logic as populate_campaigns_table but with filtered data
            table.setItem(row, 0, QTableWidgetItem(str(campaign.id)))
            table.setItem(row, 1, QTableWidgetItem(campaign.name))
            table.setItem(row, 2, QTableWidgetItem(campaign.status.value.title()))

            budget_text = f"${campaign.budget.amount} {campaign.budget.currency}"
            table.setItem(row, 3, QTableWidgetItem(budget_text))

            date_range = f"{campaign.date_range.start_date} - {campaign.date_range.end_date}"
            table.setItem(row, 4, QTableWidgetItem(date_range))

            actions_widget = self._create_campaign_actions(campaign)
            table.setCellWidget(row, 5, actions_widget)

        table.resizeColumnsToContents()

    def display_analytics(self, data) -> None:
        """Display analytics data."""
        if isinstance(data, dict) and "message" in data:
            self.main_window.analytics_text.setPlainText(data["message"])
        else:
            # Format analytics data for display
            text = "Analytics Data:\n\n"
            for key, value in data.items():
                text += f"{key}: {value}\n"
            self.main_window.analytics_text.setPlainText(text)