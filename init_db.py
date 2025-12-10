#!/usr/bin/env python3
"""
Initialize all database tables for the application.
"""

import sys
import os
import logging
from typing import List, Callable

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.container import Container


class DatabaseInitializer:
    """Handles database table initialization."""

    def __init__(self):
        self.container = Container()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for initialization process."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_repository_getters(self) -> List[str]:
        """Get list of repository getter method names."""
        return [
            'get_campaign_repository',
            'get_click_repository',
            'get_conversion_repository',
            'get_event_repository',
            'get_webhook_repository',
            'get_postback_repository',
            'get_goal_repository',
            'get_landing_page_repository',
            'get_offer_repository',
            'get_form_repository',
            'get_ltv_repository',
            'get_retention_repository',
            'get_analytics_repository'
        ]

    def initialize_repository(self, getter_name: str) -> bool:
        """Initialize a single repository."""
        try:
            if not hasattr(self.container, getter_name):
                self.logger.error(f"Repository getter not found: {getter_name}")
                return False

            repository = getattr(self.container, getter_name)()
            # This triggers _initialize_db() in the repository
            self.logger.info(f"Successfully initialized: {getter_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize {getter_name}: {str(e)}")
            return False

    def initialize_all_repositories(self) -> int:
        """Initialize all repositories and return count of successful initializations."""
        self.logger.info("Starting database table initialization")
        self.logger.info("=" * 50)

        repository_getters = self.get_repository_getters()
        initialized_count = 0

        for getter_name in repository_getters:
            if self.initialize_repository(getter_name):
                initialized_count += 1

        self.logger.info(f"Initialization complete. Successfully initialized {initialized_count} repositories")
        return initialized_count


def main() -> None:
    """Main entry point for database initialization."""
    try:
        initializer = DatabaseInitializer()
        initialized_count = initializer.initialize_all_repositories()

        if initialized_count > 0:
            print(f"Database tables should now be created for {initialized_count} repositories.")
        else:
            print("No repositories were initialized. Check logs for details.")
            sys.exit(1)

    except Exception as e:
        print(f"Critical error during initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
