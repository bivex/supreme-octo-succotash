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

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.pre_click_data import PreClickData
from ..value_objects import ClickId


class PreClickDataRepository(ABC):
    """Abstract base class for PreClickData repository operations."""

    @abstractmethod
    async def save(self, pre_click_data: PreClickData) -> None:
        """Saves pre-click data."""
        pass

    @abstractmethod
    async def find_by_click_id(self, click_id: ClickId) -> Optional[PreClickData]:
        """Finds pre-click data by click ID."""
        pass

    @abstractmethod
    async def delete_by_click_id(self, click_id: ClickId) -> None:
        """Deletes pre-click data by click ID."""
        pass
