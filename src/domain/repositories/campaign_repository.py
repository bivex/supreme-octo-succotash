"""Campaign repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..entities.campaign import Campaign
from ..value_objects import CampaignId


class CampaignRepository(ABC):
    """Abstract repository for campaign data access."""

    @abstractmethod
    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        pass

    @abstractmethod
    def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """Find campaign by ID."""
        pass

    @abstractmethod
    def find_all(self, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Find all campaigns with pagination."""
        pass

    @abstractmethod
    def exists_by_id(self, campaign_id: CampaignId) -> bool:
        """Check if campaign exists by ID."""
        pass

    @abstractmethod
    def delete_by_id(self, campaign_id: CampaignId) -> None:
        """Delete campaign by ID."""
        pass

    @abstractmethod
    def count_all(self) -> int:
        """Count total campaigns."""
        pass
