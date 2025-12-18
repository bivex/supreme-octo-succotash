# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:30
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Offer domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from ..value_objects import Money, Url


@dataclass
class Offer:
    """Domain entity representing an affiliate offer."""

    id: str
    campaign_id: str
    name: str
    url: Url
    offer_type: str  # 'direct', 'email', 'phone'

    # Financial
    payout: Money
    revenue_share: Decimal = Decimal('0.00')  # Percentage (0.00 - 1.00)
    cost_per_click: Optional[Money] = None

    # A/B testing
    weight: int = 100  # Selection weight (0-100)
    is_active: bool = True
    is_control: bool = False  # Control variant in A/B test

    # Performance tracking
    clicks: int = 0
    conversions: int = 0
    revenue: Money = field(default_factory=lambda: Money.zero("USD"))
    cost: Money = field(default_factory=lambda: Money.zero("USD"))

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate offer invariants."""
        self._validate_required_fields()
        self._validate_offer_type()
        self._validate_revenue_share()
        self._validate_weight()
        self._validate_currency_consistency()

    def _validate_required_fields(self) -> None:
        """Validate required string fields."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Offer ID is required")

        if not self.campaign_id or not isinstance(self.campaign_id, str):
            raise ValueError("Campaign ID is required")

        if not self.name or not isinstance(self.name, str):
            raise ValueError("Offer name is required")

        if len(self.name.strip()) == 0:
            raise ValueError("Offer name cannot be empty")

    def _validate_offer_type(self) -> None:
        """Validate offer type."""
        if self.offer_type not in ['direct', 'email', 'phone']:
            raise ValueError("Invalid offer type")

    def _validate_revenue_share(self) -> None:
        """Validate revenue share range."""
        if not (Decimal('0.00') <= self.revenue_share <= Decimal('1.00')):
            raise ValueError("Revenue share must be between 0.00 and 1.00")

    def _validate_weight(self) -> None:
        """Validate weight range."""
        if not (0 <= self.weight <= 100):
            raise ValueError("Weight must be between 0 and 100")

    def _validate_currency_consistency(self) -> None:
        """Validate currency consistency across money fields."""
        base_currency = self.payout.currency

        if self.cost_per_click and self.cost_per_click.currency != base_currency:
            raise ValueError("Cost per click and payout must use the same currency")

        if self.revenue.currency != base_currency:
            raise ValueError("Revenue and payout must use the same currency")

        if self.cost.currency != base_currency:
            raise ValueError("Cost and payout must use the same currency")

    def activate(self) -> None:
        """Activate the offer."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate the offer."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def record_click(self) -> None:
        """Record a click on the offer."""
        self.clicks += 1
        if self.cost_per_click:
            self.cost = self.cost.add(self.cost_per_click)

    def record_conversion(self, revenue_amount: Optional[Money] = None) -> None:
        """Record a conversion from this offer."""
        self.conversions += 1

        if revenue_amount:
            self.revenue = self.revenue.add(revenue_amount)
        else:
            # Use payout amount as revenue estimate
            self.revenue = self.revenue.add(self.payout)

    @property
    def cr(self) -> float:
        """Calculate conversion rate."""
        if self.clicks == 0:
            return 0.0
        return self.conversions / self.clicks

    @property
    def epc(self) -> Optional[Money]:
        """Calculate earnings per click."""
        if self.clicks == 0:
            return None
        total_earnings = float(self.revenue.amount) - float(self.cost.amount)
        return Money.from_float(total_earnings / self.clicks, self.payout.currency)

    @property
    def roi(self) -> float:
        """Calculate return on investment."""
        if self.cost.is_zero():
            return 0.0
        total_profit = float(self.revenue.amount) - float(self.cost.amount)
        return total_profit / float(self.cost.amount)

    @property
    def profit(self) -> Money:
        """Calculate total profit."""
        return self.revenue.subtract(self.cost)
