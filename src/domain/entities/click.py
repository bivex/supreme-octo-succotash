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

"""Click domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address
from typing import Optional

from ..value_objects import ClickId, CampaignId


@dataclass
class Click:
    """Domain entity representing a user click."""

    id: ClickId
    campaign_id: Optional[CampaignId] = None

    # Client information
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
    click_id_param: Optional[str] = None  # External click ID parameter
    affiliate_sub: Optional[str] = None
    affiliate_sub2: Optional[str] = None
    affiliate_sub3: Optional[str] = None
    affiliate_sub4: Optional[str] = None
    affiliate_sub5: Optional[str] = None

    # Attribution
    landing_page_id: Optional[int] = None
    campaign_offer_id: Optional[int] = None
    traffic_source_id: Optional[int] = None

    # Validation and fraud detection
    is_valid: bool = True
    fraud_score: float = 0.0
    fraud_reason: Optional[str] = None

    # Conversion tracking
    conversion_type: Optional[str] = None
    converted_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate click invariants."""
        self._validate_fraud_score()
        self._validate_ip_address()
        self._validate_tracking_parameters()

    def _validate_fraud_score(self) -> None:
        """Validate fraud score range."""
        min_score = 0.0
        max_score = 1.0
        if self.fraud_score < min_score or self.fraud_score > max_score:
            raise ValueError(f"Fraud score must be between {min_score} and {max_score}")

    def _validate_ip_address(self) -> None:
        """Validate IP address format."""
        if self.ip_address:
            try:
                IPv4Address(self.ip_address)
            except ValueError:
                try:
                    IPv6Address(self.ip_address)
                except ValueError:
                    raise ValueError("Invalid IP address format")

    def _validate_tracking_parameters(self) -> None:
        """Validate tracking parameters format."""
        tracking_params = [self.sub1, self.sub2, self.sub3, self.sub4, self.sub5,
                           self.affiliate_sub, self.affiliate_sub2, self.affiliate_sub3,
                           self.affiliate_sub4, self.affiliate_sub5, self.click_id_param]

        import re
        pattern = re.compile(r'^[a-zA-Z0-9._-]*$')

        for param in tracking_params:
            if param is not None and not pattern.match(param):
                raise ValueError(f"Invalid tracking parameter format: {param}")

    def mark_as_fraudulent(self, reason: str, score: float = 1.0) -> None:
        """Mark click as fraudulent."""
        self.is_valid = False
        self.fraud_score = score
        self.fraud_reason = reason

    def mark_as_converted(self, conversion_type: str = "sale") -> None:
        """Mark click as converted."""
        self.conversion_type = conversion_type
        self.converted_at = datetime.now(timezone.utc)

    def is_suspicious(self) -> bool:
        """Check if click appears suspicious based on fraud score."""
        from ..constants import FRAUD_SCORE_THRESHOLD
        return self.fraud_score > FRAUD_SCORE_THRESHOLD

    def is_bot_traffic(self) -> bool:
        """Check if click is likely from a bot."""
        if not self.user_agent:
            return True

        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'headless', 'selenium',
            'chrome-lighthouse', 'googlebot', 'bingbot', 'yahoo', 'baidu',
            'yandex', 'duckduckbot', 'facebookexternalhit', 'twitterbot'
        ]

        ua_lower = self.user_agent.lower()
        return any(indicator in ua_lower for indicator in bot_indicators)

    @property
    def tracking_params(self) -> dict[str, Optional[str]]:
        """Get all tracking parameters as a dictionary."""
        return {
            'sub1': self.sub1,
            'sub2': self.sub2,
            'sub3': self.sub3,
            'sub4': self.sub4,
            'sub5': self.sub5,
            'aff_sub': self.affiliate_sub,
            'aff_sub2': self.affiliate_sub2,
            'aff_sub3': self.affiliate_sub3,
            'aff_sub4': self.affiliate_sub4,
            'aff_sub5': self.affiliate_sub5,
        }

    @property
    def has_conversion(self) -> bool:
        """Check if click has resulted in a conversion."""
        return self.conversion_type is not None and self.converted_at is not None
