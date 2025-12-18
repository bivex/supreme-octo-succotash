"""Dialog for creating and editing landing pages."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QCheckBox
)


class LandingPageDialog(QDialog):
    """Dialog for creating/editing landing pages."""

    def __init__(self, parent=None, landing_page=None, campaigns=None):
        """
        Initialize landing page dialog.

        Args:
            parent: Parent widget
            landing_page: Existing landing page data for editing (None for new landing page)
            campaigns: List of available campaigns for campaign selection
        """
        super().__init__(parent)
        self.landing_page = landing_page
        self.campaigns = campaigns or []
        self.is_edit = landing_page is not None
        self.init_ui()

        if self.landing_page:
            self.populate_fields()

    def init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Edit Landing Page" if self.is_edit else "Create Landing Page")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # Form
        form_group = QGroupBox("Landing Page Details")
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
        self.name_edit.setPlaceholderText("Enter landing page name...")
        form_layout.addRow("Name *:", self.name_edit)

        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com/landing-page")
        form_layout.addRow("URL *:", self.url_edit)

        # Page Type
        self.page_type_combo = QComboBox()
        self.page_type_combo.addItems(["direct", "squeeze", "bridge", "thank_you"])
        form_layout.addRow("Page Type:", self.page_type_combo)

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
        """Populate fields with existing landing page data."""
        if not self.landing_page:
            return

        # Campaign
        campaign_id = self.landing_page.get('campaign_id', '')
        index = self.campaign_combo.findData(campaign_id)
        if index >= 0:
            self.campaign_combo.setCurrentIndex(index)

        self.name_edit.setText(self.landing_page.get('name', ''))
        self.url_edit.setText(self.landing_page.get('url', ''))
        self.page_type_combo.setCurrentText(self.landing_page.get('page_type', 'direct'))
        self.weight_spin.setValue(self.landing_page.get('weight', 100))
        self.is_control_check.setChecked(self.landing_page.get('is_control', False))

    def validate_and_accept(self):
        """Validate form data and accept dialog."""
        # Validate required fields
        if not self.campaign_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a campaign.")
            return

        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Landing page name is required.")
            return

        if not self.url_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Landing page URL is required.")
            return

        # Validate URL format
        url = self.url_edit.text().strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            QMessageBox.warning(self, "Validation Error", "URL must start with http:// or https://")
            return

        self.accept()

    def get_landing_page_data(self):
        """Get the landing page data from the form."""
        return {
            'campaign_id': self.campaign_combo.currentData(),
            'name': self.name_edit.text().strip(),
            'url': self.url_edit.text().strip(),
            'page_type': self.page_type_combo.currentText(),
            'weight': self.weight_spin.value(),
            'is_control': self.is_control_check.isChecked()
        }



