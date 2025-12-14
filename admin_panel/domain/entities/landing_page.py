"""Landing Page domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..value_objects import Url
from ..exceptions import ValidationError

MIN_WEIGHT_VALUE = 0
MAX_WEIGHT_VALUE = 100


@dataclass
class LandingPage:
    """Domain entity representing a landing page."""

    id: str
    campaign_id: str
    name: str
    url: Url
    page_type: str  # 'direct', 'squeeze', 'bridge', 'thank_you'
    weight: int = 100  # For A/B testing weight (0-100)

    # Status
    is_active: bool = True
    is_control: bool = False  # Control variant in A/B test

    # Performance tracking
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate landing page invariants."""
        self._validate_required_fields()
        self._validate_page_type()
        self._validate_weight()

    def _validate_required_fields(self) -> None:
        """Validate required string fields."""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("Landing page ID is required")

        if not self.campaign_id or not isinstance(self.campaign_id, str):
            raise ValidationError("Campaign ID is required")

        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Landing page name is required")

        if len(self.name.strip()) == 0:
            raise ValidationError("Landing page name cannot be empty")

    def _validate_page_type(self) -> None:
        """Validate page type."""
        if self.page_type not in ['direct', 'squeeze', 'bridge', 'thank_you']:
            raise ValidationError("Invalid page type")

    def _validate_weight(self) -> None:
        """Validate weight range."""
        if not (MIN_WEIGHT_VALUE <= self.weight <= MAX_WEIGHT_VALUE):
            raise ValidationError("Weight must be between 0 and 100")

    def activate(self) -> None:
        """Activate the landing page."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate the landing page."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def record_impression(self) -> None:
        """Record a page impression."""
        self.impressions += 1

    def record_click(self) -> None:
        """Record a click on the page."""
        self.clicks += 1

    def record_conversion(self) -> None:
        """Record a conversion from this page."""
        self.conversions += 1

    @property
    def ctr(self) -> float:
        """Calculate click-through rate."""
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions

    @property
    def cr(self) -> float:
        """Calculate conversion rate."""
        if self.clicks == 0:
            return 0.0
        return self.conversions / self.clicks

    @property
    def epc(self) -> float:
        """Calculate earnings per click (placeholder)."""
        # This would need payout information from campaign/offer
        return 0.0
