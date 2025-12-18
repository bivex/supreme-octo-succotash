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

"""Update campaign command."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
