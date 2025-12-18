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

"""List Offers Use Case."""

from typing import List, Optional

DEFAULT_PAGE_SIZE = 20

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
        page_size: int = DEFAULT_PAGE_SIZE,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[OfferDTO]:
        """
        Execute the list offers use case.

        Args:
            page: The page number (1-based) for pagination.
            page_size: The number of items to return per page.
            campaign_id: Optional filter to retrieve offers by campaign ID.
            is_active: Optional filter to retrieve offers by their active status.

        Returns:
            A list of offers as Data Transfer Objects (DTOs).
        """
        offers = self._offer_repository.find_all(
            page=page,
            page_size=page_size,
            campaign_id=campaign_id,
            is_active=is_active
        )

        return [OfferDTO.from_entity(offer) for offer in offers]
