# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Create offer command."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from ...domain.value_objects import Money, Url


@dataclass
class CreateOfferCommand:
    """Command to create a new offer."""

    campaign_id: str
    name: str
    url: Url
    payout: Money
    offer_type: str = "direct"
    revenue_share: Decimal = Decimal('0.00')
    cost_per_click: Optional[Money] = None
    weight: int = 100
    is_control: bool = False
