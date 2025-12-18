
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Test script to verify all imports work correctly."""

import sys
import os
from loguru import logger

# Add current directory and src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

try:
    logger.info("Testing imports...")

    # Test config first
    from config.settings import settings
    logger.info("OK: config.settings imported")

    # Test domain modules first
    from src.domain.constants import MAX_CAMPAIGN_NAME_LENGTH
    from src.domain.entities.campaign import Campaign
    from src.domain.entities.click import Click
    from src.domain.services.campaign.campaign_service import CampaignService
    from src.domain.services.click.click_validation_service import ClickValidationService
    logger.info("OK: domain modules imported")

    # Test infrastructure
    from src.infrastructure.repositories.in_memory_campaign_repository import InMemoryCampaignRepository
    from src.infrastructure.repositories.in_memory_click_repository import InMemoryClickRepository
    logger.info("OK: infrastructure modules imported")

    # Test presentation
    from src.presentation.dto.campaign_dto import CreateCampaignRequest
    from src.presentation.routes.campaign_routes import CampaignRoutes
    from src.presentation.error_handlers import register_error_handlers
    logger.info("OK: presentation modules imported")

    # Test container
    from src.container import container
    logger.info("OK: container imported")

    # Test main modules (this will test all together)
    from src.main import create_app
    logger.info("OK: main.create_app imported")

    # Verify all imports are accessible (suppress pyflakes warnings)
    _ = settings
    _ = MAX_CAMPAIGN_NAME_LENGTH
    _ = Campaign
    _ = Click
    _ = CampaignService
    _ = ClickValidationService
    _ = InMemoryCampaignRepository
    _ = InMemoryClickRepository
    _ = CreateCampaignRequest
    _ = CampaignRoutes
    _ = register_error_handlers
    _ = container

    # Test app creation
    logger.info("Creating Flask app...")
    app = create_app()
    logger.info("OK: Flask app created successfully")

    logger.info("\nSUCCESS: All imports and app creation successful!")

except Exception as e:
    logger.info(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
