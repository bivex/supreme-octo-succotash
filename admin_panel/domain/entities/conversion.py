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
