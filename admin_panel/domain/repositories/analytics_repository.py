# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

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
