"""Create offer command."""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

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
