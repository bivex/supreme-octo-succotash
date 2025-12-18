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

"""In-memory click repository implementation."""

from typing import Optional, List
from datetime import datetime, timezone, date

from ...domain.entities.click import Click
from ...domain.repositories.click_repository import ClickRepository
from ...domain.value_objects import ClickId


class InMemoryClickRepository(ClickRepository):
    """In-memory implementation of ClickRepository for testing and development."""

    def __init__(self):
        self._clicks: List[Click] = []


    def save(self, click: Click) -> None:
        """Save a click."""
        # Check if click already exists
        existing_index = None
        for i, existing_click in enumerate(self._clicks):
            if existing_click.id == click.id:
                existing_index = i
                break

        if existing_index is not None:
            self._clicks[existing_index] = click
        else:
            self._clicks.append(click)

    def find_by_id(self, click_id: ClickId) -> Optional[Click]:
        """Find click by ID."""
        for click in self._clicks:
            if click.id == click_id:
                return click
        return None

    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                           offset: int = 0) -> List[Click]:
        """Find clicks by campaign ID."""
        matching_clicks = [c for c in self._clicks if c.campaign_id == campaign_id]
        # Sort by creation time descending
        matching_clicks.sort(key=lambda x: x.created_at, reverse=True)
        return matching_clicks[offset:offset + limit]

    def find_by_filters(self, filters) -> List[Click]:
        """Find clicks by filter criteria."""
        filtered_clicks = self._clicks.copy()

        if filters.campaign_id is not None:
            filtered_clicks = [c for c in filtered_clicks if c.campaign_id == filters.campaign_id]

        if filters.is_valid is not None:
            filtered_clicks = [c for c in filtered_clicks if c.is_valid == filters.is_valid]

        if filters.start_date is not None:
            filtered_clicks = [c for c in filtered_clicks if c.created_at >= filters.start_date]

        if filters.end_date is not None:
            filtered_clicks = [c for c in filtered_clicks if c.created_at <= filters.end_date]

        # Sort by creation time descending
        filtered_clicks.sort(key=lambda x: x.created_at, reverse=True)
        return filtered_clicks[filters.offset:filters.offset + filters.limit]

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count clicks for a campaign."""
        return len([c for c in self._clicks if c.campaign_id == campaign_id])

    def count_conversions(self, campaign_id: str) -> int:
        """Count conversions for a campaign."""
        return len([c for c in self._clicks
                   if c.campaign_id == campaign_id and c.has_conversion])

    def get_clicks_in_date_range(self, campaign_id: str,
                                start_date: date, end_date: date) -> List[Click]:
        """Get clicks within date range for analytics."""
        start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        return [c for c in self._clicks
                if c.campaign_id == campaign_id
                and start_datetime <= c.created_at <= end_datetime]
