"""Dialog for creating and editing offers."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QLabel, QCheckBox
)
from PyQt6.QtCore import QTimer


class OfferDialog(QDialog):
    """Dialog for creating/editing offers."""

    def __init__(self, parent=None, offer=None, campaigns=None):
        """
        Initialize offer dialog.

        Args:
            parent: Parent widget
            offer: Existing offer data for editing (None for new offer)
            campaigns: List of available campaigns for campaign selection
        """
        super().__init__(parent)
        self.offer = offer
        self.campaigns = campaigns or []
        self.is_edit = offer is not None
        self.init_ui()

        if self.offer:
            self.populate_fields()

    def init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Edit Offer" if self.is_edit else "Create Offer")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # Form
        form_group = QGroupBox("Offer Details")
        form_layout = QFormLayout(form_group)

        # Campaign selection
        self.campaign_combo = QComboBox()
        self.campaign_combo.addItem("Select Campaign...", "")
        for campaign in self.campaigns:
            campaign_name = campaign.get('name', 'Unknown')
            campaign_id = campaign.get('id', '')
            self.campaign_combo.addItem(f"{campaign_name} ({campaign_id})", campaign_id)
        form_layout.addRow("Campaign *:", self.campaign_combo)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter offer name...")
        form_layout.addRow("Name *:", self.name_edit)

        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com/offer")
        form_layout.addRow("URL *:", self.url_edit)

        # Offer Type
        self.offer_type_combo = QComboBox()
        self.offer_type_combo.addItems(["direct", "email", "phone"])
        form_layout.addRow("Offer Type:", self.offer_type_combo)

        # Payout
        payout_layout = QHBoxLayout()
        self.payout_amount = QDoubleSpinBox()
        self.payout_amount.setRange(0, 1000000)
        self.payout_amount.setDecimals(2)
        self.payout_amount.setValue(10.00)
        payout_layout.addWidget(self.payout_amount)

        self.payout_currency = QComboBox()
        self.payout_currency.addItems(["USD", "EUR", "GBP", "RUB"])
        payout_layout.addWidget(self.payout_currency)
        form_layout.addRow("Payout *:", payout_layout)

        # Revenue Share
        self.revenue_share = QDoubleSpinBox()
        self.revenue_share.setRange(0.00, 1.00)
        self.revenue_share.setDecimals(3)
        self.revenue_share.setSingleStep(0.001)
        self.revenue_share.setValue(0.000)
        form_layout.addRow("Revenue Share (0.00-1.00):", self.revenue_share)

        # Cost per Click
        cpc_layout = QHBoxLayout()
        self.cost_per_click_amount = QDoubleSpinBox()
        self.cost_per_click_amount.setRange(0, 1000000)
        self.cost_per_click_amount.setDecimals(3)
        self.cost_per_click_amount.setValue(0.000)
        cpc_layout.addWidget(self.cost_per_click_amount)

        self.cost_per_click_currency = QComboBox()
        self.cost_per_click_currency.addItems(["USD", "EUR", "GBP", "RUB"])
        cpc_layout.addWidget(self.cost_per_click_currency)
        form_layout.addRow("Cost per Click:", cpc_layout)

        # Weight
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(0, 100)
        self.weight_spin.setValue(100)
        form_layout.addRow("Weight (0-100):", self.weight_spin)

        # Control variant checkbox
        self.is_control_check = QCheckBox("Control variant (A/B testing)")
        form_layout.addRow("", self.is_control_check)

        layout.addWidget(form_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def populate_fields(self):
        """Populate fields with existing offer data."""
        if not self.offer:
            return

        # Campaign
        campaign_id = self.offer.get('campaign_id', '')
        index = self.campaign_combo.findData(campaign_id)
        if index >= 0:
            self.campaign_combo.setCurrentIndex(index)

        self.name_edit.setText(self.offer.get('name', ''))
        self.url_edit.setText(self.offer.get('url', ''))
        self.offer_type_combo.setCurrentText(self.offer.get('offer_type', 'direct'))

        # Payout
        payout = self.offer.get('payout', {})
        self.payout_amount.setValue(payout.get('amount', 0.00))
        self.payout_currency.setCurrentText(payout.get('currency', 'USD'))

        self.revenue_share.setValue(self.offer.get('revenue_share', 0.000))

        # Cost per click
        cpc = self.offer.get('cost_per_click')
        if cpc:
            self.cost_per_click_amount.setValue(cpc.get('amount', 0.000))
            self.cost_per_click_currency.setCurrentText(cpc.get('currency', 'USD'))

        self.weight_spin.setValue(self.offer.get('weight', 100))
        self.is_control_check.setChecked(self.offer.get('is_control', False))

    def validate_and_accept(self):
        """Validate form data and accept dialog."""
        # Validate required fields
        if not self.campaign_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a campaign.")
            return

        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Offer name is required.")
            return

        if not self.url_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Offer URL is required.")
            return

        # Validate URL format
        url = self.url_edit.text().strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            QMessageBox.warning(self, "Validation Error", "URL must start with http:// or https://")
            return

        # Validate payout
        if self.payout_amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Payout amount must be greater than 0.")
            return

        self.accept()

    def get_offer_data(self):
        """Get the offer data from the form."""
        cpc_amount = self.cost_per_click_amount.value()
        cpc_data = None
        if cpc_amount > 0:
            cpc_data = {
                'amount': cpc_amount,
                'currency': self.cost_per_click_currency.currentText()
            }

        return {
            'campaign_id': self.campaign_combo.currentData(),
            'name': self.name_edit.text().strip(),
            'url': self.url_edit.text().strip(),
            'offer_type': self.offer_type_combo.currentText(),
            'payout_amount': self.payout_amount.value(),
            'payout_currency': self.payout_currency.currentText(),
            'revenue_share': self.revenue_share.value(),
            'cost_per_click_amount': cpc_amount if cpc_amount > 0 else None,
            'cost_per_click_currency': self.cost_per_click_currency.currentText() if cpc_amount > 0 else None,
            'weight': self.weight_spin.value(),
            'is_control': self.is_control_check.isChecked()
        }
