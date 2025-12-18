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

"""Click Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

DEFAULT_PAGE_SIZE = 20

from ..entities import Click


class IClickRepository(ABC):
    """Click Repository Interface."""

    @abstractmethod
    def find_all(
        self,
        campaign_id: Optional[str] = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE
    ) -> List[Click]:
        """Find clicks with optional campaign filter."""
        pass

    @abstractmethod
    def generate_click_url(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a tracking URL for clicks."""
        pass
