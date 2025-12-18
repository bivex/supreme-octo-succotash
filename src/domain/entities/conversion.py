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

"""Conversion tracking entity."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from ..value_objects.financial.money import Money


@dataclass
class Conversion:
    """Conversion tracking entity."""

    id: str
    click_id: str  # Links back to the original click
    conversion_type: str  # 'lead', 'sale', 'install', 'registration', 'signup'
    conversion_value: Optional[Money]  # Revenue from conversion
    order_id: Optional[str]  # External order/transaction ID
    product_id: Optional[str]  # Product/service identifier
    campaign_id: Optional[int]
    offer_id: Optional[int]
    landing_page_id: Optional[int]
    user_id: Optional[str]  # Anonymous user identifier
    session_id: Optional[str]  # Session identifier
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]
    metadata: Dict[str, Any]  # Additional conversion data
    timestamp: datetime
    processed: bool = False  # Whether postbacks have been sent
    created_at: Optional[datetime] = None  # Database creation timestamp
    updated_at: Optional[datetime] = None  # Database update timestamp

    @classmethod
    def create_from_request(cls, conversion_data: Dict[str, Any]) -> 'Conversion':
        """Create conversion from API request data."""
        import uuid
        from datetime import datetime
        from ..value_objects.financial.money import Money

        # Handle monetary value
        conversion_value = None
        if 'conversion_value' in conversion_data and conversion_data['conversion_value']:
            value_data = conversion_data['conversion_value']
            if isinstance(value_data, dict) and 'amount' in value_data:
                conversion_value = Money(
                    amount=value_data['amount'],
                    currency=value_data.get('currency', 'USD')
                )

        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            click_id=conversion_data['click_id'],
            conversion_type=conversion_data.get('conversion_type', 'lead'),
            conversion_value=conversion_value,
            order_id=conversion_data.get('order_id'),
            product_id=conversion_data.get('product_id'),
            campaign_id=conversion_data.get('campaign_id'),
            offer_id=conversion_data.get('offer_id'),
            landing_page_id=conversion_data.get('landing_page_id'),
            user_id=conversion_data.get('user_id'),
            session_id=conversion_data.get('session_id'),
            ip_address=conversion_data.get('ip_address'),
            user_agent=conversion_data.get('user_agent'),
            referrer=conversion_data.get('referrer'),
            metadata=conversion_data.get('metadata', {}),
            timestamp=now,
            processed=False,
            created_at=now,
            updated_at=now
        )

    def calculate_payout(self, payout_rate: float, payout_type: str = 'percentage') -> Optional[Money]:
        """Calculate affiliate payout for this conversion."""
        if not self.conversion_value:
            return None

        if payout_type == 'percentage':
            payout_amount = self.conversion_value.amount * (payout_rate / 100)
        elif payout_type == 'fixed':
            payout_amount = payout_rate
        else:
            return None

        return Money(amount=payout_amount, currency=self.conversion_value.currency)
