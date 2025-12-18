# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:19
# Last Updated: 2025-12-18T12:13:22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Click data transfer objects."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TrackClickRequest:
    """DTO for click tracking request (query parameters)."""

    cid: Optional[str] = None
    landing_page_id: Optional[str] = None
    campaign_offer_id: Optional[str] = None
    traffic_source_id: Optional[str] = None
    sub1: Optional[str] = None
    sub2: Optional[str] = None
    sub3: Optional[str] = None
    sub4: Optional[str] = None
    sub5: Optional[str] = None
    click_id: Optional[str] = None
    aff_sub: Optional[str] = None
    aff_sub2: Optional[str] = None
    aff_sub3: Optional[str] = None
    aff_sub4: Optional[str] = None
    aff_sub5: Optional[str] = None
    bot_user_agent: Optional[str] = None
    test_mode: Optional[str] = None

    def to_command(self, ip_address: str, user_agent: str, referrer: Optional[str]):
        """Convert to TrackClickCommand."""
        from ...application.commands.track_click_command import TrackClickCommand

        return TrackClickCommand(
            campaign_id=self.cid or "camp_123",  # Default for testing
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            sub1=self.sub1,
            sub2=self.sub2,
            sub3=self.sub3,
            sub4=self.sub4,
            sub5=self.sub5,
            click_id_param=self.click_id,
            affiliate_sub=self.aff_sub,
            affiliate_sub2=self.aff_sub2,
            affiliate_sub3=self.aff_sub3,
            affiliate_sub4=self.aff_sub4,
            affiliate_sub5=self.aff_sub5,
            landing_page_id=int(self.landing_page_id) if self.landing_page_id else None,
            campaign_offer_id=int(self.campaign_offer_id) if self.campaign_offer_id else None,
            traffic_source_id=int(self.traffic_source_id) if self.traffic_source_id else None,
            force_bot=self.bot_user_agent == "1",
            test_mode=self.test_mode == "1",
        )


@dataclass
class ClickResponse:
    """DTO for click response."""

    id: str
    cid: Optional[str]
    ip: Optional[str]
    ua: Optional[str]
    ref: Optional[str]
    isValid: bool
    ts: int
    sub1: Optional[str]
    sub2: Optional[str]
    sub3: Optional[str]
    sub4: Optional[str]
    sub5: Optional[str]
    clickId: Optional[str]
    affSub: Optional[str]
    affSub2: Optional[str]
    affSub3: Optional[str]
    affSub4: Optional[str]
    affSub5: Optional[str]
    fraudScore: float
    fraudReason: Optional[str]
    landingPageId: Optional[int]
    campaignOfferId: Optional[int]
    trafficSourceId: Optional[int]
    conversionType: Optional[str]

    @classmethod
    def from_click(cls, click):
        """Create response from Click entity."""
        return cls(
            id=str(click.id),
            cid=click.campaign_id,
            ip=click.ip_address,
            ua=click.user_agent,
            ref=click.referrer,
            isValid=click.is_valid,
            ts=int(click.created_at.timestamp()),
            sub1=click.sub1,
            sub2=click.sub2,
            sub3=click.sub3,
            sub4=click.sub4,
            sub5=click.sub5,
            clickId=click.click_id_param,
            affSub=click.affiliate_sub,
            affSub2=click.affiliate_sub2,
            affSub3=click.affiliate_sub3,
            affSub4=click.affiliate_sub4,
            affSub5=click.affiliate_sub5,
            fraudScore=click.fraud_score,
            fraudReason=click.fraud_reason,
            landingPageId=click.landing_page_id,
            campaignOfferId=click.campaign_offer_id,
            trafficSourceId=click.traffic_source_id,
            conversionType=click.conversion_type,
        )
