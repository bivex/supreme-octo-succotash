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

"""Dialog for generating click URLs."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QPushButton
)


class GenerateClickDialog(QDialog):
    """Dialog for generating click URLs."""

    def __init__(self, parent=None, campaigns=None):
        """
        Initialize click generation dialog.

        Args:
            parent: Parent widget
            campaigns: List of available campaigns
        """
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
        cancel_btn.setObjectName("secondaryButton")
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
