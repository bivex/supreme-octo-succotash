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

"""Goal Entity."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import uuid4

from ..value_objects import Money
from ..exceptions import ValidationError


class GoalType(Enum):
    """Goal type enumeration."""
    CONVERSION = "conversion"
    CLICK = "click"
    IMPRESSION = "impression"
    LEAD = "lead"
    SALE = "sale"


@dataclass
class Goal:
    """
    Goal Entity.

    Represents a trackable goal for a campaign.
    """

    # Identity
    id: str
    name: str
    campaign_id: str

    # Core attributes
    goal_type: GoalType
    value: Money
    url_match: Optional[str] = None

    # Metadata
    created_at: Optional[str] = None

    def __post_init__(self):
        """Validate goal invariants."""
        if not self.name or not self.name.strip():
            raise ValidationError("Goal name cannot be empty")

        if not self.campaign_id:
            raise ValidationError("Goal must be associated with a campaign")

    def matches_url(self, url: str) -> bool:
        """Check if URL matches goal criteria."""
        if not self.url_match:
            return True  # No URL filter
        return self.url_match in url

    @classmethod
    def create(
        cls,
        name: str,
        campaign_id: str,
        goal_type: GoalType,
        value: Money,
        url_match: Optional[str] = None,
        goal_id: Optional[str] = None
    ) -> 'Goal':
        """Factory method to create a new goal."""
        return cls(
            id=goal_id or str(uuid4()),
            name=name,
            campaign_id=campaign_id,
            goal_type=goal_type,
            value=value,
            url_match=url_match
        )

    def __str__(self) -> str:
        return f"Goal(id={self.id}, name={self.name}, type={self.goal_type.value})"
