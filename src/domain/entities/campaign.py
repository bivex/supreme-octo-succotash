"""Campaign domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ..value_objects import CampaignId, CampaignStatus, Money, Url


@dataclass
class Campaign:
    """Domain entity representing a marketing campaign."""

    id: CampaignId
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT

    # URLs
    safe_page_url: Optional[Url] = None
    offer_page_url: Optional[Url] = None

    # Financial
    cost_model: str = "CPA"  # CPA, CPC, CPM
    payout: Optional[Money] = None
    daily_budget: Optional[Money] = None
    total_budget: Optional[Money] = None

    # Schedule
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Performance tracking
    clicks_count: int = 0
    conversions_count: int = 0
    spent_amount: Money = field(default_factory=lambda: Money.zero("USD"))

    def __post_init__(self) -> None:
        """Validate campaign invariants."""
        self._validate_name()
        self._validate_description()
        self._validate_cost_model()
        self._validate_money_objects()
        self._validate_dates()
        self._validate_budget_constraints()

    def _validate_name(self) -> None:
        """Validate campaign name."""
        from ..constants import MAX_CAMPAIGN_NAME_LENGTH

        if not self.name or not isinstance(self.name, str):
            raise ValueError("Campaign name is required and must be a string")

        if len(self.name.strip()) == 0:
            raise ValueError("Campaign name cannot be empty")

        if len(self.name) > MAX_CAMPAIGN_NAME_LENGTH:
            raise ValueError(f"Campaign name must be at most {MAX_CAMPAIGN_NAME_LENGTH} characters")

    def _validate_description(self) -> None:
        """Validate campaign description."""
        from ..constants import MAX_DESCRIPTION_LENGTH

        if self.description and len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"Campaign description must be at most {MAX_DESCRIPTION_LENGTH} characters")

    def _validate_cost_model(self) -> None:
        """Validate cost model."""
        if self.cost_model not in ["CPA", "CPC", "CPM"]:
            raise ValueError("Cost model must be CPA, CPC, or CPM")

    def _validate_money_objects(self) -> None:
        """Validate money objects have consistent currency."""
        money_objects = [m for m in [self.payout, self.daily_budget, self.total_budget] if m is not None]
        if len(money_objects) > 1:
            currencies = {m.currency for m in money_objects}
            if len(currencies) > 1:
                raise ValueError("All money amounts must use the same currency")

    def _validate_dates(self) -> None:
        """Validate campaign dates."""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

    def _validate_budget_constraints(self) -> None:
        """Validate budget constraints."""
        if self.daily_budget and self.total_budget:
            if self.daily_budget.amount > self.total_budget.amount:
                raise ValueError("Daily budget cannot exceed total budget")

    def activate(self) -> None:
        """Activate the campaign."""
        if not self.status.can_be_activated:
            raise ValueError(f"Cannot activate campaign with status: {self.status}")

        # Additional business rule checks
        if not self.is_within_schedule():
            raise ValueError("Cannot activate campaign outside schedule")

        self.status = CampaignStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def pause(self) -> None:
        """Pause the campaign."""
        if not self.status.can_be_paused:
            raise ValueError(f"Cannot pause campaign with status: {self.status}")
        self.status = CampaignStatus.PAUSED
        self.updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Mark campaign as completed."""
        self.status = CampaignStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Cancel the campaign."""
        self.status = CampaignStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)

    def update_performance(self, clicks_increment: int = 0, conversions_increment: int = 0,
                          spent_increment: Optional[Money] = None) -> None:
        """Update campaign performance metrics."""
        self.clicks_count += clicks_increment
        self.conversions_count += conversions_increment

        if spent_increment:
            self.spent_amount = self.spent_amount.add(spent_increment)

        self.updated_at = datetime.now(timezone.utc)

    def is_within_schedule(self, check_time: Optional[datetime] = None) -> bool:
        """Check if campaign is within its schedule."""
        if check_time is None:
            check_time = datetime.now(timezone.utc)

        if self.start_date and check_time < self.start_date:
            return False

        if self.end_date and check_time > self.end_date:
            return False

        return True

    def is_within_budget(self) -> bool:
        """Check if campaign is within budget limits."""
        if self.total_budget and self.spent_amount >= self.total_budget:
            return False

        # Daily budget check would require daily spending tracking
        # For now, just check total budget
        return True

    @property
    def ctr(self) -> float:
        """Calculate click-through rate."""
        if self.clicks_count == 0:
            return 0.0
        return self.clicks_count / max(self.clicks_count, 1)  # Simplified

    @property
    def cr(self) -> float:
        """Calculate conversion rate."""
        if self.clicks_count == 0:
            return 0.0
        return self.conversions_count / self.clicks_count

    @property
    def epc(self) -> Optional[Money]:
        """Calculate earnings per click."""
        if self.clicks_count == 0 or self.payout is None:
            return None
        return self.payout.multiply(self.cr)

    @property
    def roi(self) -> float:
        """Calculate return on investment."""
        if self.spent_amount.is_zero():
            return 0.0

        total_earnings = self.conversions_count * float(self.payout.amount) if self.payout else 0.0
        return (total_earnings - float(self.spent_amount.amount)) / float(self.spent_amount.amount)
