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

# Configuration
from infrastructure.config.settings import Settings

# Dependency Injection
from di.container import Container

# Presentation - Dark Theme
from presentation.styles import get_stylesheet

# Presentation - Views (importing from old file temporarily)
# TODO: Move these to presentation/views after full refactoring
from main_old import AdminPanel as LegacyAdminPanel


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
        self.settings = Settings.from_env()

        # Initialize DI container
        self.container = Container(self.settings)

        # Initialize Qt Application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("Advertising Platform Admin Panel")
        self.qt_app.setApplicationVersion("2.0.0")

        # Apply dark theme
        self.qt_app.setStyleSheet(get_stylesheet())
        print("🌙 Professional dark theme applied!")

    def run(self) -> int:
        """Run the application."""
        # Create main window (using legacy for now, will refactor)
        # TODO: Replace with new architecture-based MainWindow
        main_window = LegacyAdminPanel()

        # Inject container into window for access to use cases
        # This allows gradual migration from old to new architecture
        main_window.container = self.container

        main_window.show()

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
