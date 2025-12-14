"""List Offers Use Case."""

from typing import List, Optional

from ...dtos import OfferDTO
from ....domain.repositories import IOfferRepository


class ListOffersUseCase:
    """Use case for listing offers."""

    def __init__(self, offer_repository: IOfferRepository):
        """Initialize use case with dependencies."""
        self._offer_repository = offer_repository

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[OfferDTO]:
        """
        Execute the list offers use case.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            campaign_id: Optional filter by campaign ID
            is_active: Optional filter by active status

        Returns:
            List of offers as DTOs
        """
        offers = self._offer_repository.find_all(
            page=page,
            page_size=page_size,
            campaign_id=campaign_id,
            is_active=is_active
        )

        return [OfferDTO.from_entity(offer) for offer in offers]
