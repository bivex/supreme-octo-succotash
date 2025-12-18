# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:19
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Campaign data transfer objects."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from ...domain.value_objects import Money


@dataclass
class CreateCampaignRequest:
    """DTO for campaign creation request."""

    name: str
    payout: Dict[str, Any]  # Money object as dict
    description: Optional[str] = None
    costModel: str = "CPA"
    whiteUrl: Optional[str] = None
    blackUrl: Optional[str] = None
    dailyBudget: Optional[Dict[str, Any]] = None
    totalBudget: Optional[Dict[str, Any]] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

    def to_command(self):
        """Convert to CreateCampaignCommand."""
        from ...application.commands.create_campaign_command import CreateCampaignCommand

        # Parse money objects
        payout_money = Money.from_float(float(self.payout['amount']), self.payout['currency'])
        daily_budget_money = None
        if self.dailyBudget:
            daily_budget_money = Money.from_float(float(self.dailyBudget['amount']), self.dailyBudget['currency'])
        total_budget_money = None
        if self.totalBudget:
            total_budget_money = Money.from_float(float(self.totalBudget['amount']), self.totalBudget['currency'])

        # Parse dates
        start_date = None
        if self.startDate:
            start_date = datetime.fromisoformat(self.startDate.replace('Z', '+00:00'))
        end_date = None
        if self.endDate:
            end_date = datetime.fromisoformat(self.endDate.replace('Z', '+00:00'))

        return CreateCampaignCommand(
            name=self.name,
            description=self.description,
            cost_model=self.costModel,
            payout=payout_money,
            white_url=self.whiteUrl,
            black_url=self.blackUrl,
            daily_budget=daily_budget_money,
            total_budget=total_budget_money,
            start_date=start_date,
            end_date=end_date,
        )


@dataclass
class CampaignResponse:
    """DTO for campaign response."""

    id: str
    name: str
    description: Optional[str]
    status: str
    costModel: str
    payout: Dict[str, Any]
    urls: Dict[str, Optional[str]]
    financial: Dict[str, Any]
    performance: Dict[str, Any]
    schedule: Dict[str, Optional[str]]
    createdAt: str
    updatedAt: str
    _links: Dict[str, str]

    @classmethod
    def from_campaign(cls, campaign):
        """Create response from Campaign entity."""
        return cls(
            id=campaign.id.value,
            name=campaign.name,
            description=campaign.description,
            status=campaign.status.value,
            costModel=campaign.cost_model,
            payout={"amount": float(campaign.payout.amount), "currency": campaign.payout.currency} if campaign.payout else None,
            urls={
                "safePage": str(campaign.safe_page_url) if campaign.safe_page_url else None,
                "offerPage": str(campaign.offer_page_url) if campaign.offer_page_url else None,
            },
            financial={
                "dailyBudget": {"amount": float(campaign.daily_budget.amount), "currency": campaign.daily_budget.currency} if campaign.daily_budget else None,
                "totalBudget": {"amount": float(campaign.total_budget.amount), "currency": campaign.total_budget.currency} if campaign.total_budget else None,
                "spent": {"amount": float(campaign.spent_amount.amount), "currency": campaign.spent_amount.currency},
            },
            performance={
                "clicks": campaign.clicks_count,
                "conversions": campaign.conversions_count,
                "ctr": campaign.ctr,
                "cr": campaign.cr,
                "epc": {"amount": float(campaign.epc.amount), "currency": campaign.epc.currency} if campaign.epc else None,
                "roi": campaign.roi,
            },
            schedule={
                "startDate": campaign.start_date.isoformat() if campaign.start_date else None,
                "endDate": campaign.end_date.isoformat() if campaign.end_date else None,
            },
            createdAt=campaign.created_at.isoformat(),
            updatedAt=campaign.updated_at.isoformat(),
            _links={
                "self": f"/api/v1/campaigns/{campaign.id.value}",
                "landingPages": f"/api/v1/campaigns/{campaign.id.value}/landing-pages",
                "offers": f"/api/v1/campaigns/{campaign.id.value}/offers",
                "analytics": f"/api/v1/campaigns/{campaign.id.value}/analytics",
            }
        )


@dataclass
class CampaignSummaryResponse:
    """DTO for campaign summary response (used in lists)."""

    id: str
    name: str
    status: str
    performance: Dict[str, Any]
    _links: Dict[str, str]

    @classmethod
    def from_campaign(cls, campaign):
        """Create response from Campaign entity."""
        return cls(
            id=campaign.id.value,
            name=campaign.name,
            status=campaign.status.value,
            performance={
                "clicks": campaign.clicks_count,
                "conversions": campaign.conversions_count,
                "ctr": float(campaign.ctr),
                "cr": float(campaign.cr),
                "epc": {"amount": float(campaign.epc.amount), "currency": campaign.epc.currency} if campaign.epc else None,
                "roi": float(campaign.roi),
            },
            _links={"self": f"/api/v1/campaigns/{campaign.id.value}"}
        )
