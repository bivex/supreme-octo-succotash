"""Offer data transfer objects."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from decimal import Decimal


@dataclass
class OfferDTO:
    """DTO for offer data transfer between layers."""

    id: str
    campaign_id: str
    name: str
    url: str
    offer_type: str
    payout_amount: float
    payout_currency: str
    revenue_share: float
    cost_per_click_amount: Optional[float]
    cost_per_click_currency: Optional[str]
    weight: int
    is_active: bool
    is_control: bool
    clicks: int
    conversions: int
    revenue_amount: float
    revenue_currency: str
    cost_amount: float
    cost_currency: str
    created_at: str
    updated_at: str

    # Computed properties
    cr: float
    epc_amount: Optional[float]
    epc_currency: Optional[str]
    roi: float
    profit_amount: float
    profit_currency: str

    @classmethod
    def from_entity(cls, offer) -> 'OfferDTO':
        """Create DTO from domain entity."""
        epc = offer.epc
        return cls(
            id=offer.id,
            campaign_id=offer.campaign_id,
            name=offer.name,
            url=str(offer.url),
            offer_type=offer.offer_type,
            payout_amount=float(offer.payout.amount),
            payout_currency=offer.payout.currency,
            revenue_share=float(offer.revenue_share),
            cost_per_click_amount=float(offer.cost_per_click.amount) if offer.cost_per_click else None,
            cost_per_click_currency=offer.cost_per_click.currency if offer.cost_per_click else None,
            weight=offer.weight,
            is_active=offer.is_active,
            is_control=offer.is_control,
            clicks=offer.clicks,
            conversions=offer.conversions,
            revenue_amount=float(offer.revenue.amount),
            revenue_currency=offer.revenue.currency,
            cost_amount=float(offer.cost.amount),
            cost_currency=offer.cost.currency,
            created_at=offer.created_at.isoformat(),
            updated_at=offer.updated_at.isoformat(),
            cr=offer.cr,
            epc_amount=float(epc.amount) if epc else None,
            epc_currency=epc.currency if epc else None,
            roi=offer.roi,
            profit_amount=float(offer.profit.amount),
            profit_currency=offer.profit.currency
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI consumption."""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'url': self.url,
            'offer_type': self.offer_type,
            'payout': {
                'amount': self.payout_amount,
                'currency': self.payout_currency
            },
            'revenue_share': self.revenue_share,
            'cost_per_click': {
                'amount': self.cost_per_click_amount,
                'currency': self.cost_per_click_currency
            } if self.cost_per_click_amount is not None else None,
            'weight': self.weight,
            'is_active': self.is_active,
            'is_control': self.is_control,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'revenue': {
                'amount': self.revenue_amount,
                'currency': self.revenue_currency
            },
            'cost': {
                'amount': self.cost_amount,
                'currency': self.cost_currency
            },
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'cr': self.cr,
            'epc': {
                'amount': self.epc_amount,
                'currency': self.epc_currency
            } if self.epc_amount is not None else None,
            'roi': self.roi,
            'profit': {
                'amount': self.profit_amount,
                'currency': self.profit_currency
            }
        }


@dataclass
class CreateOfferDTO:
    """DTO for creating a new offer."""

    campaign_id: str
    name: str
    url: str
    offer_type: str
    payout_amount: float
    payout_currency: str
    revenue_share: float = 0.0
    cost_per_click_amount: Optional[float] = None
    cost_per_click_currency: Optional[str] = None
    weight: int = 100
    is_control: bool = False


@dataclass
class UpdateOfferDTO:
    """DTO for updating an existing offer."""

    name: Optional[str] = None
    url: Optional[str] = None
    offer_type: Optional[str] = None
    payout_amount: Optional[float] = None
    payout_currency: Optional[str] = None
    revenue_share: Optional[float] = None
    cost_per_click_amount: Optional[float] = None
    cost_per_click_currency: Optional[str] = None
    weight: Optional[int] = None
    is_active: Optional[bool] = None
    is_control: Optional[bool] = None