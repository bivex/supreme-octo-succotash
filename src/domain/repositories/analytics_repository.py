"""Analytics repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import date

from ..value_objects import Analytics


class AnalyticsRepository(ABC):
    """Abstract repository for analytics data access."""

    @abstractmethod
    def get_campaign_analytics(self, campaign_id: str, start_date: date,
                              end_date: date, granularity: str = "day") -> Analytics:
        """Get analytics for a campaign within date range."""
        pass

    @abstractmethod
    def get_aggregated_metrics(self, campaign_id: str, start_date: date,
                              end_date: date) -> Dict[str, Any]:
        """Get aggregated metrics for a campaign."""
        pass

    @abstractmethod
    def save_analytics_snapshot(self, analytics: Analytics) -> None:
        """Save analytics snapshot for caching."""
        pass

    @abstractmethod
    def get_cached_analytics(self, campaign_id: str, start_date: date,
                           end_date: date) -> Optional[Analytics]:
        """Get cached analytics if available."""
        pass
