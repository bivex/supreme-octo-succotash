# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:22
# Last Updated: 2025-12-18T12:13:22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Analytics data transfer objects."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class GetAnalyticsRequest:
    """DTO for analytics request."""

    startDate: str
    endDate: str
    granularity: str = "day"
    breakdown: Optional[str] = None

    def to_query(self, campaign_id: str):
        """Convert to GetCampaignAnalyticsQuery."""
        from ...application.queries.get_campaign_analytics_query import GetCampaignAnalyticsQuery
        from datetime import date

        return GetCampaignAnalyticsQuery(
            campaign_id=campaign_id,
            start_date=date.fromisoformat(self.startDate),
            end_date=date.fromisoformat(self.endDate),
            granularity=self.granularity,
        )


@dataclass
class AnalyticsResponse:
    """DTO for analytics response."""

    campaignId: str
    timeRange: Dict[str, Any]
    metrics: Dict[str, Any]
    breakdowns: Dict[str, List[Dict[str, Any]]]

    @classmethod
    def from_analytics(cls, analytics):
        """Create response from Analytics value object."""
        return cls(
            campaignId=analytics.campaign_id,
            timeRange=analytics.time_range,
            metrics={
                "clicks": analytics.clicks,
                "uniqueClicks": analytics.unique_clicks,
                "conversions": analytics.conversions,
                "revenue": {"amount": float(analytics.revenue.amount), "currency": analytics.revenue.currency},
                "cost": {"amount": float(analytics.cost.amount), "currency": analytics.cost.currency},
                "ctr": analytics.ctr,
                "cr": analytics.cr,
                "epc": {"amount": float(analytics.epc.amount), "currency": analytics.epc.currency},
                "roi": analytics.roi,
            },
            breakdowns=analytics.breakdowns,
        )
