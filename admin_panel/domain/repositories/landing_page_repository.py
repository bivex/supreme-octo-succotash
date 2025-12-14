"""Landing Page Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import LandingPage


class ILandingPageRepository(ABC):
    """
    Landing Page Repository Interface.

    Defines the contract for landing page persistence operations.
    This is a PORT in hexagonal architecture - implementations are ADAPTERS.
    """

    @abstractmethod
    def find_by_id(self, landing_page_id: str) -> Optional[LandingPage]:
        """Find a landing page by its ID."""
        pass

    @abstractmethod
    def find_by_campaign_id(self, campaign_id: str) -> List[LandingPage]:
        """Find all landing pages for a specific campaign."""
        pass

    @abstractmethod
    def find_all(
        self,
        page: int = 1,
        page_size: int = 20,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LandingPage]:
        """Find all landing pages with optional filtering and pagination."""
        pass

    @abstractmethod
    def count_all(
        self,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count landing pages with optional filters."""
        pass

    @abstractmethod
    def save(self, landing_page: LandingPage) -> LandingPage:
        """Save (create or update) a landing page."""
        pass

    @abstractmethod
    def delete(self, landing_page_id: str) -> None:
        """Delete a landing page by ID."""
        pass

    @abstractmethod
    def exists(self, landing_page_id: str) -> bool:
        """Check if a landing page exists."""
        pass
