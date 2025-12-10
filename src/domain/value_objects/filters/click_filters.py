"""Click filters value object for search parameters."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ClickFilters:
    """Value object for click filtering parameters."""

    campaign_id: Optional[str] = None
    is_valid: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate filter parameters."""
        from ...constants import DEFAULT_PAGE_SIZE

        if self.limit < 1 or self.limit > DEFAULT_PAGE_SIZE * 2:
            raise ValueError(f"Limit must be between 1 and {DEFAULT_PAGE_SIZE * 2}")

        if self.offset < 0:
            raise ValueError("Offset must be non-negative")

        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
