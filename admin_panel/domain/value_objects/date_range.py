# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""DateRange Value Object - Represents time periods."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from ..exceptions import InvalidDateRangeError


@dataclass(frozen=True)
class DateRange:
    """
    Immutable DateRange value object.

    Represents a period with start and optionally end date.
    """

    start_date: date
    end_date: Optional[date] = None

    def __post_init__(self):
        """Validate date range invariants."""
        if self.end_date and self.start_date > self.end_date:
            raise InvalidDateRangeError(
                f"Start date {self.start_date} cannot be after end date {self.end_date}"
            )

    @classmethod
    def from_strings(cls, start: str, end: Optional[str] = None) -> 'DateRange':
        """
        Create DateRange from ISO date strings.

        Args:
            start: Start date in YYYY-MM-DD format
            end: Optional end date in YYYY-MM-DD format
        """
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date() if end else None
        return cls(start_date, end_date)

    def contains(self, check_date: date) -> bool:
        """Check if a date falls within this range."""
        if check_date < self.start_date:
            return False
        if self.end_date and check_date > self.end_date:
            return False
        return True

    def is_active(self, reference_date: Optional[date] = None) -> bool:
        """Check if the range is currently active."""
        ref = reference_date or date.today()
        return self.contains(ref)

    def duration_days(self) -> Optional[int]:
        """Get duration in days (None if no end date)."""
        if not self.end_date:
            return None
        return (self.end_date - self.start_date).days

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None
        }

    def __str__(self) -> str:
        if self.end_date:
            return f"{self.start_date} to {self.end_date}"
        return f"From {self.start_date}"
