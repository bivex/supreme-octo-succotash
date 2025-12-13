"""Customer LTV entity for gaming deposits."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date


@dataclass
class CustomerLtv:
    """Customer Lifetime Value entity for gaming platform."""

    customer_id: str
    total_revenue: float
    total_purchases: int
    average_order_value: float
    purchase_frequency: float
    customer_lifetime_months: int
    predicted_clv: float
    actual_clv: float
    segment: str
    cohort_id: Optional[str]
    first_purchase_date: Optional[date]
    last_purchase_date: Optional[date]
    created_at: datetime
    updated_at: datetime