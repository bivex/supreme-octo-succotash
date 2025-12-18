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