"""Dialog for creating and editing goals."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox
)


class GoalDialog(QDialog):
    """Dialog for creating/editing goals."""

    def __init__(self, parent=None, goal=None, campaigns=None, templates=None):
        """
        Initialize goal dialog.

        Args:
            parent: Parent widget
            goal: Existing goal data for editing (None for new goal)
            campaigns: List of available campaigns
            templates: List of goal templates
        """
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
