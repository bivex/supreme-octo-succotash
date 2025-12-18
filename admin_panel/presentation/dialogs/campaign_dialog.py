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

"""Dialog for creating and editing campaigns."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import QDate


class CampaignDialog(QDialog):
    """Dialog for creating/editing campaigns."""

    def __init__(self, parent=None, campaign=None):
        """
        Initialize campaign dialog.

        Args:
            parent: Parent widget
            campaign: Existing campaign data for editing (None for new campaign)
        """
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
