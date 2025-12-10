#!/usr/bin/env python3
"""
Initialize all database tables for the application.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.container import Container

def init_all_tables():
    """Initialize all database tables."""
    container = Container()

    # List of repository getter methods
    repo_getters = [
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

    print("🚀 Initializing database tables...")
    print("=" * 50)

    initialized = 0
    for getter_name in repo_getters:
        try:
            if hasattr(container, getter_name):
                repo = getattr(container, getter_name)()
                # This should trigger _initialize_db() in the repository
                print(f"✅ Initialized: {getter_name}")
                initialized += 1
            else:
                print(f"❌ Method not found: {getter_name}")
        except Exception as e:
            print(f"❌ Failed to initialize {getter_name}: {e}")

    print(f"\n🎉 Successfully initialized {initialized} repositories")
    print("Database tables should now be created!")

if __name__ == "__main__":
    init_all_tables()
