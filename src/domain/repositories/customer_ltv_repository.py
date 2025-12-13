"""Customer LTV repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from ..entities.customer_ltv import CustomerLtv


class CustomerLtvRepository(ABC):
    """Abstract repository for customer LTV data access."""

    @abstractmethod
    def save(self, customer_ltv: CustomerLtv) -> None:
        """Save customer LTV data."""
        pass

    @abstractmethod
    def find_by_customer_id(self, customer_id: str) -> Optional[CustomerLtv]:
        """Get customer LTV by customer ID."""
        pass

    @abstractmethod
    def update_revenue(self, customer_id: str, additional_revenue: float) -> None:
        """Update customer total revenue."""
        pass