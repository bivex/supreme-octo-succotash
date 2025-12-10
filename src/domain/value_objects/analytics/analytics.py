"""Analytics value object for campaign performance data."""

from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any

from ..financial.money import Money


@dataclass(frozen=True)
class Analytics:
    """Value object representing campaign analytics data."""

    campaign_id: str
    time_range: Dict[str, Any]  # start_date, end_date, granularity

    # Overall metrics
    impressions: int
    clicks: int
    unique_clicks: int
    conversions: int
    revenue: Money
    cost: Money
    ctr: float
    cr: float
    epc: Money
    roi: float

    # Breakdowns
    breakdowns: Dict[str, List[Dict[str, Any]]] = None

    def __post_init__(self) -> None:
        """Validate analytics data."""
        self._validate_counts()
        self._validate_ratios()
        self._validate_time_range()

    def _validate_counts(self) -> None:
        """Validate count fields."""
        if self.clicks < 0:
            raise ValueError("Clicks cannot be negative")

        if self.unique_clicks < 0:
            raise ValueError("Unique clicks cannot be negative")

        if self.conversions < 0:
            raise ValueError("Conversions cannot be negative")

        if self.unique_clicks > self.clicks:
            raise ValueError("Unique clicks cannot exceed total clicks")

    def _validate_ratios(self) -> None:
        """Validate ratio fields."""
        if not (0.0 <= self.ctr <= 1.0):
            raise ValueError("CTR must be between 0.0 and 1.0")

        if not (0.0 <= self.cr <= 1.0):
            raise ValueError("CR must be between 0.0 and 1.0")

    def _validate_time_range(self) -> None:
        """Validate time range structure."""
        if 'start_date' not in self.time_range or 'end_date' not in self.time_range:
            raise ValueError("Time range must include start_date and end_date")

    @property
    def profit(self) -> Money:
        """Calculate total profit."""
        return self.revenue.subtract(self.cost)

    @property
    def profit_margin(self) -> float:
        """Calculate profit margin."""
        if self.revenue.is_zero():
            return 0.0
        return float(self.profit.amount) / float(self.revenue.amount)

    def get_breakdown_by_date(self) -> List[Dict[str, Any]]:
        """Get date-based breakdown."""
        return self.breakdowns.get('by_date', []) if self.breakdowns else []

    def get_traffic_breakdown(self) -> List[Dict[str, Any]]:
        """Get traffic source breakdown."""
        return self.breakdowns.get('by_traffic_source', []) if self.breakdowns else []

    def get_breakdown_by_landing_page(self) -> List[Dict[str, Any]]:
        """Get landing page breakdown."""
        return self.breakdowns.get('by_landing_page', []) if self.breakdowns else []

    @classmethod
    def empty(cls, campaign_id: str, start_date: date, end_date: date) -> 'Analytics':
        """Create empty analytics for a campaign."""
        currency = "USD"  # Default currency
        return cls(
            campaign_id=campaign_id,
            time_range={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'granularity': 'day'
            },
            impressions=0,
            clicks=0,
            unique_clicks=0,
            conversions=0,
            revenue=Money.zero(currency),
            cost=Money.zero(currency),
            ctr=0.0,
            cr=0.0,
            epc=Money.zero(currency),
            roi=0.0,
            breakdowns={'by_date': []}
        )
