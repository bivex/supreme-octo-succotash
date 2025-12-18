# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Campaign status value object."""

from enum import Enum


class CampaignStatus(Enum):
    """Campaign status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @property
    def is_active(self) -> bool:
        """Check if campaign is in active state."""
        return self == CampaignStatus.ACTIVE

    @property
    def is_paused(self) -> bool:
        """Check if campaign is paused."""
        return self == CampaignStatus.PAUSED

    @property
    def can_be_activated(self) -> bool:
        """Check if campaign can be activated."""
        return self in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]

    @property
    def can_be_paused(self) -> bool:
        """Check if campaign can be paused."""
        return self == CampaignStatus.ACTIVE

    def __str__(self) -> str:
        return self.value
