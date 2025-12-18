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

"""Conversion repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..entities.conversion import Conversion


class ConversionRepository(ABC):
    """Abstract base class for conversion repositories."""

    @abstractmethod
    def save(self, conversion: Conversion) -> None:
        """Save a conversion."""
        pass

    @abstractmethod
    def get_by_id(self, conversion_id: str) -> Optional[Conversion]:
        """Get conversion by ID."""
        pass

    @abstractmethod
    def get_by_click_id(self, click_id: str) -> List[Conversion]:
        """Get conversions by click ID."""
        pass

    @abstractmethod
    def get_by_order_id(self, order_id: str) -> Optional[Conversion]:
        """Get conversion by order ID."""
        pass

    @abstractmethod
    def get_unprocessed(self, limit: int = 100) -> List[Conversion]:
        """Get unprocessed conversions for postback sending."""
        pass

    @abstractmethod
    def mark_processed(self, conversion_id: str) -> None:
        """Mark conversion as processed (postbacks sent)."""
        pass

    @abstractmethod
    def get_conversions_in_timeframe(
            self,
            start_time: datetime,
            end_time: datetime,
            conversion_type: Optional[str] = None,
            limit: int = 1000
    ) -> List[Conversion]:
        """Get conversions within a time range."""
        pass

    @abstractmethod
    def get_conversion_stats(
            self,
            start_time: datetime,
            end_time: datetime,
            group_by: str = 'conversion_type'
    ) -> Dict[str, Any]:
        """Get conversion statistics grouped by specified field."""
        pass

    @abstractmethod
    def get_total_revenue(
            self,
            start_time: datetime,
            end_time: datetime,
            conversion_type: Optional[str] = None
    ) -> float:
        """Get total revenue from conversions in time range."""
        pass
