# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""List Landing Pages Use Case."""

from typing import List, Optional

DEFAULT_PAGE_SIZE = 20

from ...dtos import LandingPageDTO
from ....domain.repositories import ILandingPageRepository


class ListLandingPagesUseCase:
    """Use case for listing landing pages."""

    def __init__(self, landing_page_repository: ILandingPageRepository):
        """Initialize use case with dependencies."""
        self._landing_page_repository = landing_page_repository

    def execute(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LandingPageDTO]:
        """
        Execute the list landing pages use case.

        Args:
            page: The page number (1-based) for pagination.
            page_size: The number of items to return per page.
            campaign_id: Optional filter to retrieve landing pages by campaign ID.
            is_active: Optional filter to retrieve landing pages by their active status.

        Returns:
            A list of landing pages as Data Transfer Objects (DTOs).
        """
        landing_pages = self._landing_page_repository.find_all(
            page=page,
            page_size=page_size,
            campaign_id=campaign_id,
            is_active=is_active
        )

        landing_page_dtos = [
            LandingPageDTO.from_entity(lp) for lp in landing_pages
        ]
        return landing_page_dtos
