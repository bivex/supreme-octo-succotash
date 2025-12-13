"""Click Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..entities import Click


class IClickRepository(ABC):
    """Click Repository Interface."""

    @abstractmethod
    def find_all(
        self,
        campaign_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Click]:
        """Find clicks with optional campaign filter."""
        pass

    @abstractmethod
    def generate_click_url(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a tracking URL for clicks."""
        pass
