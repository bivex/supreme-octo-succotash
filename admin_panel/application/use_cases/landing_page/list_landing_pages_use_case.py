"""List Landing Pages Use Case."""

from typing import List, Optional

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
        page_size: int = 20,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LandingPageDTO]:
        """
        Execute the list landing pages use case.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            campaign_id: Optional filter by campaign ID
            is_active: Optional filter by active status

        Returns:
            List of landing pages as DTOs
        """
        landing_pages = self._landing_page_repository.find_all(
            page=page,
            page_size=page_size,
            campaign_id=campaign_id,
            is_active=is_active
        )

        return [LandingPageDTO.from_entity(lp) for lp in landing_pages]