"""
Settings Controller - Handles settings management and validation.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

from admin_panel.infrastructure.config.settings import Settings

from .base_controller import BaseController

import logging

MS_MULTIPLIER = 1000

STATUS_BAR_MESSAGE_DURATION_MS = 5000
MIN_URL_LENGTH = 10
MIN_TOKEN_LENGTH = 10
MIN_API_KEY_LENGTH = 8

logger = logging.getLogger(__name__)


class SettingsController(BaseController):
    """Handles settings management and validation."""

    def initialize(self) -> None:
        """Initialize the settings controller."""
        pass

    def _validate_settings_inputs(self, api_url: str, bearer_token: str, api_key: str) -> list[str]:
        validation_errors = []

        if not api_url:
            validation_errors.append("API URL is required")
        elif not self._validate_url(api_url):
            validation_errors.append("Invalid API URL format")

        if bearer_token and not self._validate_token(bearer_token):
            validation_errors.append("Bearer token must be at least 10 characters")

        if api_key and not self._validate_api_key(api_key):
            validation_errors.append("API key must be at least 8 characters")
        
        return validation_errors

    def save_settings(self) -> None:
        """Save settings from UI to configuration."""
        try:
            # Get values from UI
            api_url = self.main_window.settings_api_url.text().strip()
            bearer_token = self.main_window.settings_bearer_token.text().strip()
            api_key = self.main_window.settings_api_key.text().strip()
            auto_refresh = self.main_window.settings_auto_refresh.isChecked()
            refresh_interval = self.main_window.settings_refresh_interval.value()
            log_level = self.main_window.settings_log_level.currentText()

            # Validate inputs
            validation_errors = self._validate_settings_inputs(api_url, bearer_token, api_key)

            if validation_errors:
                error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {error}" for error in validation_errors)
                QMessageBox.warning(self.main_window, "Validation Error", error_msg)
                return

            # Update app settings
            if self.main_window.app_settings:
                self.main_window.app_settings.api_base_url = api_url
                self.main_window.app_settings.bearer_token = bearer_token if bearer_token else None
                self.main_window.app_settings.api_key = api_key if api_key else None
                self.main_window.app_settings.auto_refresh_enabled = auto_refresh
                self.main_window.app_settings.auto_refresh_interval = refresh_interval * MS_MULTIPLIER  # Convert to milliseconds
                self.main_window.app_settings.log_level = log_level

                # Save to INI file
                self.main_window.app_settings.save_to_ini()

                # Update main window settings
                self.main_window.api_url_edit.setText(api_url)
                self.main_window.bearer_token_edit.setText(bearer_token)
                self.main_window.api_key_edit.setText(api_key)

                # Update auto-refresh timer
                self._update_auto_refresh_timer()

                QMessageBox.information(
                    self.main_window, "Success",
                    "Settings saved successfully!"
                )
            else:
                QMessageBox.warning(
                    self.main_window, "Warning",
                    "Settings object not available. Please restart the application."
                )

    def load_config(self) -> None:
        """Load configuration and populate UI fields."""
        try:
            if self.main_window.app_settings:
                # Reload settings from INI file
                new_settings = Settings.load_from_ini()
                self.main_window.app_settings = new_settings  # Update the main_window's settings instance

                # Populate UI with current settings
                self.main_window.settings_api_url.setText(self.main_window.app_settings.api_base_url)
                logger.debug(f"SettingsController: Loading Bearer Token: {self.main_window.app_settings.bearer_token}")
                self.main_window.bearer_token_edit.setText(
                    self.main_window.app_settings.bearer_token or ""
                )
                logger.debug(f"SettingsController: Loading API Key: {self.main_window.app_settings.api_key}")
                self.main_window.api_key_edit.setText(
                    self.main_window.app_settings.api_key or ""
                )
                self.main_window.settings_auto_refresh.setChecked(
                    self.main_window.app_settings.auto_refresh_enabled
                )
                self.main_window.settings_refresh_interval.setValue(
                    self.main_window.app_settings.auto_refresh_interval // 1000  # Convert from milliseconds
                )
                self.main_window.settings_log_level.setCurrentText(
                    self.main_window.app_settings.log_level
                )

                QMessageBox.information(
                    self.main_window, "Success",
                    "Configuration loaded successfully!"
                )
            else:
                QMessageBox.warning(
                    self.main_window, "Warning",
                    "Settings object not available."
                )

        except Exception as e:
            QMessageBox.critical(
                self.main_window, "Error",
                f"Failed to load configuration:\n{str(e)}"
            )

    def _update_auto_refresh_timer(self) -> None:
        """Update the auto-refresh timer based on settings."""
        if self.main_window.app_settings and self.main_window.app_settings.auto_refresh_enabled:
            interval_ms = self.main_window.app_settings.auto_refresh_interval
            self.main_window.refresh_timer.setInterval(interval_ms)
            if not self.main_window.refresh_timer.isActive():
                self.main_window.refresh_timer.start()
        else:
            self.main_window.refresh_timer.stop()

    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        if not url:
            return False

        # Basic URL validation
        url_lower = url.lower()
        return (
            url_lower.startswith(('http://', 'https://')) and
            len(url) > MIN_URL_LENGTH and  # Reasonable minimum length
            '.' in url  # Must contain a dot
        )

    def _validate_token(self, token: str) -> bool:
        """Validate bearer token format."""
        return len(token) >= MIN_TOKEN_LENGTH and token.strip() == token

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format."""
        return len(api_key) >= MIN_API_KEY_LENGTH and api_key.strip() == api_key

    def update_connection_fields(self, api_url: str, bearer_token: str, api_key: str) -> None:
        """Update connection fields in UI."""
        self.main_window.api_url_edit.setText(api_url)
        self.main_window.bearer_token_edit.setText(bearer_token)
        self.main_window.api_key_edit.setText(api_key)

    def get_connection_settings(self) -> Dict[str, str]:
        """Get current connection settings."""
        return {
            'api_url': self.main_window.api_url_edit.text().strip(),
            'bearer_token': self.main_window.bearer_token_edit.text().strip(),
            'api_key': self.main_window.api_key_edit.text().strip()
        }

    def validate_connection_settings(self) -> Optional[str]:
        """Validate connection settings and return error message if invalid."""
        settings = self.get_connection_settings()

        if not settings['api_url']:
            return "API URL is required"

        if not self._validate_url(settings['api_url']):
            return "Invalid API URL format"

        if not settings['bearer_token'] and not settings['api_key']:
            return "Either Bearer Token or API Key must be provided"

        if settings['bearer_token'] and not self._validate_token(settings['bearer_token']):
            return "Bearer token must be at least 10 characters"

        if settings['api_key'] and not self._validate_api_key(settings['api_key']):
            return "API key must be at least 8 characters"

        return None  # Valid

    def log_activity(self, message: str) -> None:
        """Log activity message."""
        # Log to status bar or activity log
        if hasattr(self.main_window, 'statusBar'):
            self.main_window.statusBar().showMessage(message, STATUS_BAR_MESSAGE_DURATION_MS)  # Show for 5 seconds

    def toggle_auto_refresh(self, enabled: bool) -> None:
        """Toggle auto-refresh functionality."""
        if self.main_window.app_settings:
            self.main_window.app_settings.auto_refresh_enabled = enabled
            self._update_auto_refresh_timer()

            status = "enabled" if enabled else "disabled"
            self.log_activity(f"Auto-refresh {status}")

    def update_campaign_selectors(self) -> None:
        """Update campaign selectors in analytics and other tabs."""
        # Clear existing items
        self.main_window.analytics_campaign_combo.clear()
        self.main_window.analytics_campaign_combo.addItem("All Campaigns", None)

        # Add current campaigns
        for campaign in self.main_window.current_campaigns:
            self.main_window.analytics_campaign_combo.addItem(
                campaign.name, campaign.id
            )