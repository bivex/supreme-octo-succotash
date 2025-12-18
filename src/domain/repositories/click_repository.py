# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Click repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date

from ..entities.click import Click
from ..value_objects import ClickId


class ClickRepository(ABC):
    """Abstract repository for click data access."""

    @abstractmethod
    def save(self, click: Click) -> None:
        """Save a click."""
        pass

    @abstractmethod
    def find_by_id(self, click_id: ClickId) -> Optional[Click]:
        """Find click by ID."""
        pass

    @abstractmethod
    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                           offset: int = 0) -> List[Click]:
        """Find clicks by campaign ID."""
        pass

    @abstractmethod
    def find_by_filters(self, filters) -> List[Click]:
        """Find clicks by filter criteria."""
        pass

    @abstractmethod
    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count clicks for a campaign."""
        pass

    @abstractmethod
    def count_conversions(self, campaign_id: str) -> int:
        """Count conversions for a campaign."""
        pass

    @abstractmethod
    def get_clicks_in_date_range(self, campaign_id: str,
                                start_date: date, end_date: date) -> List[Click]:
        """Get clicks within date range for analytics."""
        pass
