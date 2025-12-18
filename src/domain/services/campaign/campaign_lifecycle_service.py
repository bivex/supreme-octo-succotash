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

"""Campaign lifecycle service for campaign state management."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ...entities.campaign import Campaign
from ...value_objects import CampaignStatus


class CampaignLifecycleService:
    """Domain service for campaign lifecycle management."""

    def should_pause_campaign(self, campaign: Campaign, current_time: Optional[datetime] = None) -> tuple[
        bool, Optional[str]]:
        """
        Determine if campaign should be paused based on business rules.

        Returns:
            Tuple of (should_pause, reason)
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Check if campaign has ended
        if campaign.end_date and current_time > campaign.end_date:
            return True, "Campaign end date has passed"

        # Check budget limits
        if campaign.total_budget and campaign.spent_amount >= campaign.total_budget:
            return True, "Campaign has reached total budget limit"

        # Check daily budget (simplified - would need daily tracking)
        # For now, just check if spent amount is approaching total budget
        if campaign.total_budget:
            from ...constants import BUDGET_APPROACH_RATIO
            spent_ratio = float(campaign.spent_amount.amount) / float(campaign.total_budget.amount)
            if spent_ratio > BUDGET_APPROACH_RATIO:
                return True, "Campaign is approaching budget limit"

        return False, None

    def update_status_from_performance(self, campaign: Campaign,
                                       performance_metrics: Dict[str, Any]) -> CampaignStatus:
        """
        Determine appropriate campaign status based on performance.

        This is a business rule that could automatically pause underperforming campaigns.
        """
        # If campaign is not active, don't change status
        if not campaign.status.is_active:
            return campaign.status

        from ...constants import ROI_NEGATIVE_THRESHOLD, CAMPAIGN_CR_VERY_LOW_THRESHOLD, CAMPAIGN_CLICKS_LOW_THRESHOLD

        # Check ROI - pause if consistently negative
        roi = performance_metrics.get('roi', 0.0)
        if roi < ROI_NEGATIVE_THRESHOLD:
            return CampaignStatus.PAUSED

        # Check conversion rate - pause if too low
        cr = performance_metrics.get('cr', 0.0)
        if cr < CAMPAIGN_CR_VERY_LOW_THRESHOLD and campaign.clicks_count > CAMPAIGN_CLICKS_LOW_THRESHOLD:
            return CampaignStatus.PAUSED

        # Keep active otherwise
        return CampaignStatus.ACTIVE
