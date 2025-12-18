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

"""Create landing page command handler."""

import uuid

from ..commands.create_landing_page_command import CreateLandingPageCommand
from ...domain.entities.landing_page import LandingPage
from ...domain.repositories.landing_page_repository import LandingPageRepository


class CreateLandingPageHandler:
    """Handler for creating landing pages."""

    def __init__(self, landing_page_repository: LandingPageRepository):
        self._landing_page_repository = landing_page_repository

    def handle(self, command: CreateLandingPageCommand) -> LandingPage:
        """
        Handle create landing page command.

        Args:
            command: Create landing page command

        Returns:
            Created landing page entity
        """
        # Generate ID
        landing_page_id = f"lp_{str(uuid.uuid4())[:8]}"

        # Create landing page entity
        landing_page = LandingPage(
            id=landing_page_id,
            campaign_id=command.campaign_id,
            name=command.name,
            url=command.url,
            page_type=command.page_type,
            weight=command.weight,
            is_control=command.is_control
        )

        # Save to repository
        self._landing_page_repository.save(landing_page)

        return landing_page
