"""Data Transfer Objects for application layer."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CampaignDTO:
    """Campaign Data Transfer Object."""
    id: str
    name: str
    status: str
    budget_amount: float
    budget_currency: str
    budget_type: str
    target_url: str
    start_date: str
    end_date: Optional[str]
    created_at: Optional[str] = None


@dataclass
class GoalDTO:
    """Goal Data Transfer Object."""
    id: str
    name: str
    campaign_id: str
    type: str
    value: float
    currency: str
    url_match: Optional[str] = None


@dataclass
class CreateCampaignRequest:
    """Request DTO for creating a campaign."""
    name: str
    budget_amount: float
    budget_currency: str
    budget_type: str
    target_url: str
    start_date: str
    end_date: Optional[str] = None
