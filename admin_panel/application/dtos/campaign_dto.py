# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Campaign data transfer objects."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class CampaignDTO:
    """DTO for campaign data transfer between layers."""

    id: str
    name: str
    status: str
    budget_amount: float
    budget_currency: str
    budget_type: str
    target_url: str
    start_date: str
    end_date: Optional[str]
    created_at: datetime


@dataclass
class CreateCampaignRequest:
    """DTO for creating a new campaign."""

    name: str
    budget_amount: float
    budget_currency: str
    budget_type: str
    target_url: str
    start_date: str
    end_date: Optional[str] = None