"""Conversion Entity."""

from dataclasses import dataclass
from typing import Optional

from ..value_objects import Money


@dataclass
class Conversion:
    """
    Conversion Entity.

    Represents a successful conversion event.
    """

    # Identity
    id: str
    campaign_id: str
    value: Money  # Required field must come before optional

    # Optional fields
    goal_id: Optional[str] = None
    click_id: Optional[str] = None
    created_at: Optional[str] = None

    def __str__(self) -> str:
        return f"Conversion(id={self.id}, value={self.value})"
