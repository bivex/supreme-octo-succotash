# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""In-memory conversion repository implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from ...domain.repositories.conversion_repository import ConversionRepository
from ...domain.entities.conversion import Conversion


class InMemoryConversionRepository(ConversionRepository):
    """In-memory implementation of conversion repository."""

    def __init__(self):
        self._conversions: Dict[str, Conversion] = {}
        self._click_index: Dict[str, List[str]] = {}  # click_id -> list of conversion_ids
        self._order_index: Dict[str, str] = {}  # order_id -> conversion_id
        self._time_index: List[tuple] = []  # (timestamp, conversion_id) for time-based queries

    def save(self, conversion: Conversion) -> None:
        """Save a conversion."""
        self._conversions[conversion.id] = conversion

        # Update indexes
        if conversion.click_id not in self._click_index:
            self._click_index[conversion.click_id] = []
        self._click_index[conversion.click_id].append(conversion.id)

        if conversion.order_id:
            self._order_index[conversion.order_id] = conversion.id

        # Add to time index
        self._time_index.append((conversion.timestamp, conversion.id))
        # Keep time index sorted
        self._time_index.sort(key=lambda x: x[0])

    def get_by_id(self, conversion_id: str) -> Optional[Conversion]:
        """Get conversion by ID."""
        return self._conversions.get(conversion_id)

    def get_by_click_id(self, click_id: str) -> List[Conversion]:
        """Get conversions by click ID."""
        conversion_ids = self._click_index.get(click_id, [])
        conversions = [self._conversions[wid] for wid in conversion_ids if wid in self._conversions]
        return conversions

    def get_by_order_id(self, order_id: str) -> Optional[Conversion]:
        """Get conversion by order ID."""
        conversion_id = self._order_index.get(order_id)
        if conversion_id:
            return self._conversions.get(conversion_id)
        return None

    def get_unprocessed(self, limit: int = 100) -> List[Conversion]:
        """Get unprocessed conversions for postback sending."""
        unprocessed = [c for c in self._conversions.values() if not c.processed]
        return unprocessed[:limit]

    def mark_processed(self, conversion_id: str) -> None:
        """Mark conversion as processed (postbacks sent)."""
        if conversion_id in self._conversions:
            conversion = self._conversions[conversion_id]
            # Create updated conversion (since Conversion is a dataclass)
            updated_conversion = Conversion(
                id=conversion.id,
                click_id=conversion.click_id,
                conversion_type=conversion.conversion_type,
                conversion_value=conversion.conversion_value,
                order_id=conversion.order_id,
                product_id=conversion.product_id,
                campaign_id=conversion.campaign_id,
                offer_id=conversion.offer_id,
                landing_page_id=conversion.landing_page_id,
                user_id=conversion.user_id,
                session_id=conversion.session_id,
                ip_address=conversion.ip_address,
                user_agent=conversion.user_agent,
                referrer=conversion.referrer,
                metadata=conversion.metadata,
                timestamp=conversion.timestamp,
                processed=True
            )
            self._conversions[conversion_id] = updated_conversion

    def get_conversions_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        conversion_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Conversion]:
        """Get conversions within a time range."""
        # Find conversions in time range
        matching_ids = []
        for timestamp, conversion_id in self._time_index:
            if start_time <= timestamp <= end_time:
                if conversion_id in self._conversions:
                    conversion = self._conversions[conversion_id]
                    if conversion_type is None or conversion.conversion_type == conversion_type:
                        matching_ids.append(conversion_id)
                        if len(matching_ids) >= limit:
                            break

        return [self._conversions[conversion_id] for conversion_id in matching_ids]

    def get_conversion_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = 'conversion_type'
    ) -> Dict[str, Any]:
        """Get conversion statistics grouped by specified field."""
        stats = defaultdict(lambda: {'count': 0, 'revenue': 0.0})

        for timestamp, conversion_id in self._time_index:
            if start_time <= timestamp <= end_time:
                if conversion_id in self._conversions:
                    conversion = self._conversions[conversion_id]

                    key = getattr(conversion, group_by, 'unknown') if hasattr(conversion, group_by) else 'unknown'
                    if key is None:
                        key = 'unknown'

                    stats[str(key)]['count'] += 1
                    if conversion.conversion_value:
                        stats[str(key)]['revenue'] += conversion.conversion_value.amount

        return dict(stats)

    def get_total_revenue(
        self,
        start_time: datetime,
        end_time: datetime,
        conversion_type: Optional[str] = None
    ) -> float:
        """Get total revenue from conversions in time range."""
        total = 0.0

        for timestamp, conversion_id in self._time_index:
            if start_time <= timestamp <= end_time:
                if conversion_id in self._conversions:
                    conversion = self._conversions[conversion_id]
                    if conversion_type is None or conversion.conversion_type == conversion_type:
                        if conversion.conversion_value:
                            total += conversion.conversion_value.amount

        return total
