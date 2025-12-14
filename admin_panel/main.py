#!/usr/bin/env python3
"""
Advertising Platform Admin Panel - Clean Architecture Implementation

This application follows:
- Domain-Driven Design (DDD)
- Clean Architecture
- Hexagonal Architecture (Ports & Adapters)
- SOLID Principles
- Dependency Injection
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Configuration
from admin_panel.infrastructure.config.settings import Settings

# Dependency Injection
from admin_panel.di.container import Container

# Presentation - Dark Theme
from admin_panel.presentation.styles import get_stylesheet

# Presentation - Views
from admin_panel.presentation import MainWindow


class Application:
    """
    Main Application Class.

    Responsibilities:
    - Initialize dependency injection container
    - Configure application settings
    - Launch UI with injected dependencies
    """

    def __init__(self):
        """Initialize application."""
        # Load configuration
        try:
            self.settings = Settings.from_env()
            if self.settings is None:
                raise ValueError("Failed to load settings - settings object is None")
        except Exception as e:
            print(f"❌ Error loading settings: {e}")
            print("🔧 Creating default settings...")
            # Create default settings if loading fails
            self.settings = Settings()

        # Initialize DI container
        try:
            self.container = Container(self.settings)
        except Exception as e:
            print(f"❌ Error initializing container: {e}")
            raise

        # Initialize Qt Application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("Advertising Platform Admin Panel")
        self.qt_app.setApplicationVersion("2.0.0")

        # macOS-specific attributes to fix TSM (Text Input Services Manager) errors
        if sys.platform == "darwin":
            # Fix for TSM communication issues - disable foreground application transform
            import os
            os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
            # Additional macOS compatibility settings
            os.environ['QT_QPA_PLATFORM'] = 'cocoa'  # Force Cocoa platform
            os.environ['QT_MAC_WANTS_LAYER'] = '1'    # Enable layer-backed views
            # Ensure proper macOS integration
            self.qt_app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)

        # Apply dark theme
        try:
            self.qt_app.setStyleSheet(get_stylesheet())
            print("🌙 Professional dark theme applied!")
        except Exception as e:
            print(f"⚠️  Warning: Failed to apply dark theme: {e}")
            print("🔧 Using default theme")

    def run(self) -> int:
        """Run the application."""
        # Create main window with Clean Architecture
        try:
            main_window = MainWindow()

            # Inject dependencies into window
            # This allows gradual migration to use cases in the future
            main_window.container = self.container
            main_window.app_settings = self.settings

            # Reload config now that settings are injected
            main_window.load_config()

            main_window.show()
        except Exception as e:
            print(f"❌ Error creating main window: {e}")
            raise

        print("🚀 Application started with Clean Architecture!")
        print(f"📊 API URL: {self.settings.api_base_url}")
        print(f"🔄 Auto-refresh: {'enabled' if self.settings.auto_refresh_enabled else 'disabled'}")

        # Run Qt event loop
        return self.qt_app.exec()

    def cleanup(self):
        """Cleanup resources."""
        self.container.close()


def main():
    """Application entry point."""
    print("=" * 70)
    print("  Advertising Platform Admin Panel")
    print("  Clean Architecture | DDD | SOLID | Hexagonal Pattern")
    print("=" * 70)

    app = Application()

    try:
        exit_code = app.run()
    finally:
        app.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
