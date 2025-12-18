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

"""Offer repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.offer import Offer


class OfferRepository(ABC):
    """Abstract base class for offer repositories."""

    @abstractmethod
    def save(self, offer: Offer) -> None:
        """Save an offer."""
        pass

    @abstractmethod
    def find_by_id(self, offer_id: str) -> Optional[Offer]:
        """Get offer by ID."""
        pass

    @abstractmethod
    def find_by_campaign_id(self, campaign_id: str) -> List[Offer]:
        """Get offers by campaign ID."""
        pass

    @abstractmethod
    def update(self, offer: Offer) -> None:
        """Update an offer."""
        pass

    @abstractmethod
    def delete_by_id(self, offer_id: str) -> bool:
        """Delete offer by ID."""
        pass

    @abstractmethod
    def exists_by_id(self, offer_id: str) -> bool:
        """Check if offer exists by ID."""
        pass

    @abstractmethod
    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count offers by campaign ID."""
        pass
