"""Offer Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import List, Optional

DEFAULT_PAGE_SIZE = 20

from ..entities import Offer


class IOfferRepository(ABC):
    """
    Offer Repository Interface.

    Defines the contract for offer persistence operations.
    This is a PORT in hexagonal architecture - implementations are ADAPTERS.
    """

    @abstractmethod
    def find_by_id(self, offer_id: str) -> Optional[Offer]:
        """Find an offer by its ID."""
        pass

    @abstractmethod
    def find_by_campaign_id(self, campaign_id: str) -> List[Offer]:
        """Find all offers for a specific campaign."""
        pass

    @abstractmethod
    def find_all(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Offer]:
        """Find all offers with optional filtering and pagination."""
        pass

    @abstractmethod
    def count_all(
        self,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count offers with optional filters."""
        pass

    @abstractmethod
    def save(self, offer: Offer) -> Offer:
        """Save (create or update) an offer."""
        pass

    @abstractmethod
    def delete(self, offer_id: str) -> None:
        """Delete an offer by ID."""
        pass

    @abstractmethod
    def exists(self, offer_id: str) -> bool:
        """Check if an offer exists."""
        pass
