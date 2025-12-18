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

"""Create campaign command."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ...domain.value_objects import Money, Url


@dataclass
class CreateCampaignCommand:
    """Command to create a new campaign."""

    name: str
    payout: Optional[Money] = None
    description: Optional[str] = None
    cost_model: str = "CPA"
    white_url: Optional[str] = None
    black_url: Optional[str] = None
    daily_budget: Optional[Money] = None
    total_budget: Optional[Money] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate command data."""
        if not self.name or not self.name.strip():
            raise ValueError("Campaign name is required")

        if self.cost_model not in ["CPA", "CPC", "CPM"]:
            raise ValueError("Invalid cost model")

        if self.white_url:
            Url(self.white_url)  # Validate URL format

        if self.black_url:
            Url(self.black_url)  # Validate URL format
