"""In-memory campaign repository implementation."""

from typing import Optional, List, Dict
from datetime import datetime, timezone

from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId, Money, Url


class InMemoryCampaignRepository(CampaignRepository):
    """In-memory implementation of CampaignRepository for testing and development."""

    def __init__(self):
        self._campaigns: Dict[str, Campaign] = {}
        self._deleted_campaigns: set[str] = set()

    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        self._campaigns[campaign.id.value] = campaign

    def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """Find campaign by ID."""
        if campaign_id.value in self._deleted_campaigns:
            return None
        return self._campaigns.get(campaign_id.value)

    def find_all(self, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Find all campaigns with pagination."""
        campaigns = list(self._campaigns.values())
        # Filter out deleted campaigns
        campaigns = [c for c in campaigns if c.id.value not in self._deleted_campaigns]
        return campaigns[offset:offset + limit]

    def exists_by_id(self, campaign_id: CampaignId) -> bool:
        """Check if campaign exists by ID."""
        return (campaign_id.value in self._campaigns and
                campaign_id.value not in self._deleted_campaigns)

    def delete_by_id(self, campaign_id: CampaignId) -> None:
        """Delete campaign by ID."""
        self._deleted_campaigns.add(campaign_id.value)

    def count_all(self) -> int:
        """Count total campaigns."""
        return len([c for c in self._campaigns.values()
                   if c.id.value not in self._deleted_campaigns])
