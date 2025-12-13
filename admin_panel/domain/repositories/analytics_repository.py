"""Analytics Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IAnalyticsRepository(ABC):
    """Analytics Repository Interface."""

    @abstractmethod
    def get_real_time_analytics(
        self,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get real-time analytics data."""
        pass

    @abstractmethod
    def get_campaign_analytics(
        self,
        campaign_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get analytics for a specific campaign."""
        pass
