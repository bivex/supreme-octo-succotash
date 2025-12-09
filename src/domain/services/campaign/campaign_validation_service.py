"""Campaign validation service for business rules validation."""

from typing import Optional

from ...entities.campaign import Campaign
from ...value_objects.financial.money import Money


class CampaignValidationService:
    """Domain service for campaign validation business rules."""

    def can_activate_campaign(self, campaign: Campaign) -> tuple[bool, Optional[str]]:
        """
        Check if a campaign can be activated.

        Returns:
            Tuple of (can_activate, reason)
        """
        if not campaign.status.can_be_activated:
            return False, f"Campaign status '{campaign.status}' does not allow activation"

        # Check if required fields are present
        if not campaign.name.strip():
            return False, "Campaign name is required"

        if not campaign.payout:
            return False, "Campaign payout is required"

        # Check if within schedule
        if not campaign.is_within_schedule():
            return False, "Campaign is not within schedule dates"

        # Check budget constraints
        if not campaign.is_within_budget():
            return False, "Campaign has exceeded budget limits"

        return True, None

    def validate_campaign_budget(self, campaign: Campaign) -> tuple[bool, Optional[str]]:
        """
        Validate campaign budget constraints.

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check currency consistency
        money_objects = [campaign.payout, campaign.daily_budget, campaign.total_budget]
        money_objects = [m for m in money_objects if m is not None]

        if len(money_objects) > 1:
            currencies = {m.currency for m in money_objects}
            if len(currencies) > 1:
                return False, f"Inconsistent currencies: {currencies}"

        # Validate budget amounts
        if campaign.daily_budget and campaign.total_budget:
            if campaign.daily_budget.amount > campaign.total_budget.amount:
                return False, "Daily budget cannot exceed total budget"

        # Check for reasonable amounts
        from ...constants import MAX_BUDGET_AMOUNT
        max_budget = Money.from_float(MAX_BUDGET_AMOUNT, "USD")
        if campaign.total_budget and campaign.total_budget > max_budget:
            return False, f"Total budget {campaign.total_budget} exceeds maximum allowed amount {max_budget}"

        return True, None
