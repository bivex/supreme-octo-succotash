"""In-memory analytics repository implementation."""

from typing import Optional, Dict, Any
from datetime import date

from ...domain.value_objects import Analytics
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import Money


class InMemoryAnalyticsRepository(AnalyticsRepository):
    """In-memory implementation of AnalyticsRepository."""

    def __init__(self,
                 click_repository: ClickRepository,
                 campaign_repository: CampaignRepository):
        self._click_repository = click_repository
        self._campaign_repository = campaign_repository
        self._analytics_cache: Dict[str, Analytics] = {}

    def get_campaign_analytics(self, campaign_id: str, start_date: date,
                              end_date: date, granularity: str = "day") -> Analytics:
        """Get analytics for a campaign within date range."""
        # Check cache first
        cache_key = f"{campaign_id}_{start_date}_{end_date}_{granularity}"
        if cache_key in self._analytics_cache:
            return self._analytics_cache[cache_key]

        # Get clicks in date range
        clicks = self._click_repository.get_clicks_in_date_range(
            campaign_id, start_date, end_date
        )

        # Calculate metrics
        valid_clicks = [c for c in clicks if c.is_valid]
        conversions = [c for c in clicks if c.has_conversion]

        total_clicks = len(valid_clicks)
        total_conversions = len(conversions)

        # Get campaign for cost/revenue calculations
        from ...domain.value_objects import CampaignId
        campaign = self._campaign_repository.find_by_id(CampaignId.from_string(campaign_id))

        # Calculate financial metrics
        currency = campaign.payout.currency if campaign and campaign.payout else "USD"

        # Simplified cost calculation (would need actual cost data)
        cost_per_click = 0.50  # Placeholder
        cost_amount = total_clicks * cost_per_click
        cost = Money.from_float(cost_amount, currency)

        # Calculate revenue from conversions
        payout_amount = float(campaign.payout.amount) if campaign and campaign.payout else 0.0
        revenue_amount = total_conversions * payout_amount
        revenue = Money.from_float(revenue_amount, currency)

        # Calculate rates
        ctr = (total_clicks / max(total_clicks, 1)) if total_clicks > 0 else 0.0
        cr = (total_conversions / total_clicks) if total_clicks > 0 else 0.0

        # EPC (Earnings Per Click)
        epc_amount = revenue_amount / total_clicks if total_clicks > 0 else 0.0
        epc = Money.from_float(epc_amount, currency)

        # ROI
        cost_float = float(cost.amount)
        roi = ((revenue_amount - cost_float) / cost_float) if cost_float > 0 else 0.0

        # Create analytics object
        analytics = Analytics(
            campaign_id=campaign_id,
            time_range={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'granularity': granularity
            },
            clicks=total_clicks,
            unique_clicks=total_clicks,  # Simplified - assuming all clicks are unique
            conversions=total_conversions,
            revenue=revenue,
            cost=cost,
            ctr=ctr,
            cr=cr,
            epc=epc,
            roi=roi,
            breakdowns={'by_date': []}  # Simplified - no breakdowns for now
        )

        # Cache the result
        self._analytics_cache[cache_key] = analytics

        return analytics

    def get_aggregated_metrics(self, campaign_id: str, start_date: date,
                              end_date: date) -> Dict[str, Any]:
        """Get aggregated metrics for a campaign."""
        analytics = self.get_campaign_analytics(campaign_id, start_date, end_date)

        return {
            'clicks': analytics.clicks,
            'conversions': analytics.conversions,
            'revenue': analytics.revenue,
            'cost': analytics.cost,
            'profit': analytics.profit,
            'ctr': analytics.ctr,
            'cr': analytics.cr,
            'epc': analytics.epc,
            'roi': analytics.roi,
        }

    def save_analytics_snapshot(self, analytics: Analytics) -> None:
        """Save analytics snapshot for caching."""
        cache_key = f"{analytics.campaign_id}_{analytics.time_range['start_date']}_{analytics.time_range['end_date']}_{analytics.time_range['granularity']}"
        self._analytics_cache[cache_key] = analytics

    def get_cached_analytics(self, campaign_id: str, start_date: date,
                           end_date: date) -> Optional[Analytics]:
        """Get cached analytics if available."""
        cache_key = f"{campaign_id}_{start_date}_{end_date}_day"
        return self._analytics_cache.get(cache_key)
