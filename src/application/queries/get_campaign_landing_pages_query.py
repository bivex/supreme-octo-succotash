"""Get campaign landing pages query."""

from dataclasses import dataclass
from typing import List

from ...domain.entities.landing_page import LandingPage
from ...domain.repositories.landing_page_repository import LandingPageRepository


@dataclass
class GetCampaignLandingPagesQuery:
    """Query to get campaign landing pages."""

    campaign_id: str
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate query data."""
        print(f"DEBUG: GetCampaignLandingPagesQuery __post_init__: campaign_id={self.campaign_id}, limit={self.limit}, offset={self.offset}")

        if not self.campaign_id or not self.campaign_id.strip():
            raise ValueError("Campaign ID is required")

        if self.limit < 1 or self.limit > 100:
            raise ValueError(f"Limit must be between 1 and 100, got {self.limit}")

        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


class GetCampaignLandingPagesHandler:
    """Handler for getting campaign landing pages."""

    def __init__(self, landing_page_repository: LandingPageRepository):
        self._landing_page_repository = landing_page_repository

    def handle(self, query: GetCampaignLandingPagesQuery) -> List[LandingPage]:
        """Handle get campaign landing pages query."""
        # Note: Current repository interface doesn't support pagination
        # For now, we'll get all landing pages and apply pagination in memory
        landing_pages = self._landing_page_repository.find_by_campaign_id(query.campaign_id)
        return landing_pages[query.offset:query.offset + query.limit]
