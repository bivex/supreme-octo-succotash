"""Get campaign offers query."""

from dataclasses import dataclass
from typing import List

from ...domain.entities.offer import Offer
from ...domain.repositories.offer_repository import OfferRepository


@dataclass
class GetCampaignOffersQuery:
    """Query to get campaign offers."""

    campaign_id: str
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate query data."""
        if not self.campaign_id or not self.campaign_id.strip():
            raise ValueError("Campaign ID is required")

        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


class GetCampaignOffersHandler:
    """Handler for getting campaign offers."""

    def __init__(self, offer_repository: OfferRepository):
        self._offer_repository = offer_repository

    def handle(self, query: GetCampaignOffersQuery) -> List[Offer]:
        """Handle get campaign offers query."""
        # Note: Current repository interface doesn't support pagination
        # For now, we'll get all offers and apply pagination in memory
        offers = self._offer_repository.find_by_campaign_id(query.campaign_id)
        return offers[query.offset:query.offset + query.limit]
