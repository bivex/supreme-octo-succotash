"""Landing Page data transfer objects."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LandingPageDTO:
    """DTO for landing page data transfer between layers."""

    id: str
    campaign_id: str
    name: str
    url: str
    page_type: str
    weight: int
    is_active: bool
    is_control: bool
    impressions: int
    clicks: int
    conversions: int
    created_at: str
    updated_at: str

    # Computed properties
    ctr: float
    cr: float

    @classmethod
    def from_entity(cls, landing_page) -> 'LandingPageDTO':
        """Create DTO from domain entity."""
        return cls(
            id=landing_page.id,
            campaign_id=landing_page.campaign_id,
            name=landing_page.name,
            url=str(landing_page.url),
            page_type=landing_page.page_type,
            weight=landing_page.weight,
            is_active=landing_page.is_active,
            is_control=landing_page.is_control,
            impressions=landing_page.impressions,
            clicks=landing_page.clicks,
            conversions=landing_page.conversions,
            created_at=landing_page.created_at.isoformat(),
            updated_at=landing_page.updated_at.isoformat(),
            ctr=landing_page.ctr,
            cr=landing_page.cr
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI consumption."""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'url': self.url,
            'page_type': self.page_type,
            'weight': self.weight,
            'is_active': self.is_active,
            'is_control': self.is_control,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'ctr': self.ctr,
            'cr': self.cr
        }


@dataclass
class CreateLandingPageDTO:
    """DTO for creating a new landing page."""

    campaign_id: str
    name: str
    url: str
    page_type: str
    weight: int = 100
    is_control: bool = False


@dataclass
class UpdateLandingPageDTO:
    """DTO for updating an existing landing page."""

    name: Optional[str] = None
    url: Optional[str] = None
    page_type: Optional[str] = None
    weight: Optional[int] = None
    is_active: Optional[bool] = None
    is_control: Optional[bool] = None


