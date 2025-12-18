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

"""Track click command."""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class TrackClickCommand:
    """Command to track a user click."""

    campaign_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

    # Tracking parameters
    sub1: Optional[str] = None
    sub2: Optional[str] = None
    sub3: Optional[str] = None
    sub4: Optional[str] = None
    sub5: Optional[str] = None

    # External tracking IDs
    click_id_param: Optional[str] = None
    affiliate_sub: Optional[str] = None
    affiliate_sub2: Optional[str] = None
    affiliate_sub3: Optional[str] = None
    affiliate_sub4: Optional[str] = None
    affiliate_sub5: Optional[str] = None

    # Attribution
    landing_page_id: Optional[int] = None
    campaign_offer_id: Optional[int] = None
    traffic_source_id: Optional[int] = None

    # Test flags
    force_bot: bool = False
    test_mode: bool = False

    def __post_init__(self) -> None:
        """Validate command data."""
        if not self.campaign_id or not self.campaign_id.strip():
            raise ValueError("Campaign ID is required")

    @property
    def tracking_params(self) -> Dict[str, Optional[str]]:
        """Get all tracking parameters as a dictionary."""
        params = {
            'sub1': self.sub1,
            'sub2': self.sub2,
            'sub3': self.sub3,
            'sub4': self.sub4,
            'sub5': self.sub5,
        }
        affiliate_params = {
            'aff_sub': self.affiliate_sub,
            'aff_sub2': self.affiliate_sub2,
            'aff_sub3': self.affiliate_sub3,
            'aff_sub4': self.affiliate_sub4,
            'aff_sub5': self.affiliate_sub5,
        }
        params.update(affiliate_params)
        return params
