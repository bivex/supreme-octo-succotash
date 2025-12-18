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

"""Customer LTV entity for gaming deposits."""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


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
