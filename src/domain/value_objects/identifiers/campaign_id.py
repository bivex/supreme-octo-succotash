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

"""Campaign ID value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignId:
    """Value object representing a campaign identifier."""

    value: str

    def __post_init__(self) -> None:
        """Validate campaign ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Campaign ID must be a non-empty string")

        # Basic validation - should be reasonable length
        if len(self.value.strip()) == 0:
            raise ValueError("Campaign ID cannot be empty or whitespace")

    @classmethod
    def from_string(cls, value: str) -> 'CampaignId':
        """Create CampaignId from string."""
        return cls(value.strip())

    @classmethod
    def generate(cls) -> 'CampaignId':
        """Generate a new campaign ID."""
        import random
        return cls(f"camp_{random.randint(1000, 9999)}")

    def __str__(self) -> str:
        return self.value
