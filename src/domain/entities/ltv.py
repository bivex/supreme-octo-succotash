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

"""LTV (Lifetime Value) domain entities."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from ..value_objects.financial import Money


@dataclass
class Cohort:
    """Customer cohort for LTV analysis."""

    id: str
    name: str
    acquisition_date: datetime
    customer_count: int
    total_revenue: Money
    average_ltv: Money
    retention_rates: Dict[str, float]  # period -> retention rate
    created_at: datetime
    updated_at: datetime

    @property
    def cohort_month(self) -> str:
        """Get cohort month in YYYY-MM format."""
        return self.acquisition_date.strftime("%Y-%m")

    @property
    def retention_rate_1m(self) -> float:
        """Get 1-month retention rate."""
        return self.retention_rates.get("1m", 0.0)

    @property
    def retention_rate_3m(self) -> float:
        """Get 3-month retention rate."""
        return self.retention_rates.get("3m", 0.0)

    @property
    def retention_rate_6m(self) -> float:
        """Get 6-month retention rate."""
        return self.retention_rates.get("6m", 0.0)

    @property
    def retention_rate_12m(self) -> float:
        """Get 12-month retention rate."""
        return self.retention_rates.get("12m", 0.0)


@dataclass
class CustomerLTV:
    """Customer Lifetime Value entity."""

    customer_id: str
    total_revenue: Money
    total_purchases: int
    average_order_value: Money
    purchase_frequency: float  # purchases per month
    customer_lifetime_months: int
    predicted_clv: Money
    actual_clv: Money
    segment: str
    cohort_id: Optional[str]
    first_purchase_date: datetime
    last_purchase_date: datetime
    created_at: datetime
    updated_at: datetime

    @property
    def is_active_customer(self) -> bool:
        """Check if customer is still active."""
        from datetime import timedelta
        return (datetime.now() - self.last_purchase_date) < timedelta(days=90)

    @property
    def customer_age_days(self) -> int:
        """Get customer age in days."""
        return (datetime.now() - self.first_purchase_date).days

    @property
    def clv_accuracy(self) -> float:
        """Calculate CLV prediction accuracy."""
        if self.actual_clv.amount == 0:
            return 0.0
        return min(self.predicted_clv.amount / self.actual_clv.amount, 1.0)


@dataclass
class LTVSegment:
    """LTV customer segment."""

    id: str
    name: str
    min_ltv: Money
    max_ltv: Optional[Money]
    customer_count: int
    total_value: Money
    average_ltv: Money
    retention_rate: float
    description: str
    created_at: datetime
    updated_at: datetime

    @property
    def segment_range(self) -> str:
        """Get segment range as string."""
        if self.max_ltv:
            return f"{self.min_ltv.amount}-{self.max_ltv.amount} {self.min_ltv.currency}"
        return f"{self.min_ltv.amount}+ {self.min_ltv.currency}"

    @property
    def is_high_value(self) -> bool:
        """Check if this is a high-value segment."""
        return self.min_ltv.amount >= 500
