"""Campaign Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import List, Optional

DEFAULT_PAGE_SIZE = 20

from ..entities import Campaign, CampaignStatus


class ICampaignRepository(ABC):
    """
    Campaign Repository Interface.

    Defines the contract for campaign persistence operations.
    This is a PORT in hexagonal architecture - implementations are ADAPTERS.
    """

    @abstractmethod
    def find_by_id(self, campaign_id: str) -> Optional[Campaign]:
        """Find a campaign by its ID."""
        pass

    @abstractmethod
    def find_all(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status: Optional[CampaignStatus] = None
    ) -> List[Campaign]:
        """Find all campaigns with optional filtering and pagination."""
        pass

    @abstractmethod
    def count_all(self, status: Optional[CampaignStatus] = None) -> int:
        """Count campaigns with optional status filter."""
        pass

    @abstractmethod
    def save(self, campaign: Campaign) -> Campaign:
        """Save (create or update) a campaign."""
        pass

    @abstractmethod
    def delete(self, campaign_id: str) -> None:
        """Delete a campaign by ID."""
        pass

    @abstractmethod
    def exists(self, campaign_id: str) -> bool:
        """Check if a campaign exists."""
        pass
