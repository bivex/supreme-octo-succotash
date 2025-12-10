"""Update campaign command."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ...domain.value_objects import CampaignId, Money, Url


@dataclass
class UpdateCampaignCommand:
    """Command to update an existing campaign."""

    campaign_id: CampaignId
    name: Optional[str] = None
    description: Optional[str] = None
    cost_model: Optional[str] = None
    payout: Optional[Money] = None
    safe_page_url: Optional[Url] = None
    offer_page_url: Optional[Url] = None
    daily_budget: Optional[Money] = None
    total_budget: Optional[Money] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
