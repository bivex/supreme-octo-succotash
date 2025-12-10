"""Campaign performance service for metrics calculation."""

from typing import Dict, Any, List

from ...entities.campaign import Campaign
from ...entities.click import Click
from ...value_objects import Money


class CampaignPerformanceService:
    """Domain service for campaign performance calculations."""

    def calculate_campaign_performance(self, campaign: Campaign, clicks: List[Click]) -> Dict[str, Any]:
        """
        Calculate campaign performance metrics from click data.

        Returns:
            Dictionary with performance metrics
        """
        valid_clicks = [c for c in clicks if c.is_valid]
        conversions = [c for c in clicks if c.has_conversion]

        total_clicks = len(valid_clicks)
        total_conversions = len(conversions)

        # Calculate cost (simplified - would need actual cost data)
        cost_amount = total_clicks * 0.5  # Placeholder CPC
        cost = Money.from_float(cost_amount, campaign.payout.currency) if campaign.payout else Money.zero("USD")

        # Calculate revenue
        revenue_amount = total_conversions * float(campaign.payout.amount) if campaign.payout else 0.0
        revenue = Money.from_float(revenue_amount, campaign.payout.currency) if campaign.payout else Money.zero("USD")

        # Calculate metrics
        # TODO: Implement impressions calculation from impressions repository
        # For now, use clicks as approximation (this will be replaced)
        total_impressions = total_clicks * 10  # Placeholder: assume 10% CTR
        ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
        cr = (total_conversions / total_clicks) if total_clicks > 0 else 0.0

        # EPC (Earnings Per Click)
        epc_amount = revenue_amount / total_clicks if total_clicks > 0 else 0.0
        epc = Money.from_float(epc_amount, campaign.payout.currency) if campaign.payout else Money.zero("USD")

        # ROI
        cost_float = float(cost.amount)
        roi = ((revenue_amount - cost_float) / cost_float) if cost_float > 0 else 0.0

        return {
            'impressions': total_impressions,
            'clicks': total_clicks,
            'conversions': total_conversions,
            'revenue': revenue,
            'cost': cost,
            'ctr': ctr,
            'cr': cr,
            'epc': epc,
            'roi': roi,
            'profit': revenue.subtract(cost)
        }
