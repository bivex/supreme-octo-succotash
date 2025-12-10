"""Impression repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date

from ..entities.impression import Impression
from ..value_objects import ImpressionId


class ImpressionRepository(ABC):
    """Abstract repository for impression data access."""

    @abstractmethod
    def save(self, impression: Impression) -> None:
        """Save an impression."""
        pass

    @abstractmethod
    def find_by_id(self, impression_id: ImpressionId) -> Optional[Impression]:
        """Find impression by ID."""
        pass

    @abstractmethod
    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                           offset: int = 0) -> List[Impression]:
        """Find impressions by campaign ID."""
        pass

    @abstractmethod
    def find_by_filters(self, filters) -> List[Impression]:
        """Find impressions by filter criteria."""
        pass

    @abstractmethod
    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count impressions for a campaign."""
        pass

    @abstractmethod
    def get_impressions_in_date_range(self, campaign_id: str,
                                    start_date: date, end_date: date) -> List[Impression]:
        """Get impressions within date range for analytics."""
        pass
