# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Get campaign analytics query."""

from dataclasses import dataclass
from datetime import date

from ...domain.value_objects import Analytics
from ...domain.repositories.analytics_repository import AnalyticsRepository


@dataclass
class GetCampaignAnalyticsQuery:
    """Query to get campaign analytics."""

    campaign_id: str
    start_date: date
    end_date: date
    granularity: str = "day"

    def __post_init__(self) -> None:
        """Validate query data."""
        if not self.campaign_id or not self.campaign_id.strip():
            raise ValueError("Campaign ID is required")

        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

        if self.granularity not in ["hour", "day", "week", "month"]:
            raise ValueError("Invalid granularity")


class GetCampaignAnalyticsHandler:
    """Handler for getting campaign analytics."""

    def __init__(self, analytics_repository: AnalyticsRepository):
        self._analytics_repository = analytics_repository

    def handle(self, query: GetCampaignAnalyticsQuery) -> Analytics:
        """Handle get campaign analytics query."""
        analytics_params = {
            'campaign_id': query.campaign_id,
            'start_date': query.start_date,
            'end_date': query.end_date,
            'granularity': query.granularity,
        }
        return self._analytics_repository.get_campaign_analytics(**analytics_params)
