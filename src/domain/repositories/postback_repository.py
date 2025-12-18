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

"""Postback repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.postback import Postback, PostbackStatus


class PostbackRepository(ABC):
    """Abstract base class for postback repositories."""

    @abstractmethod
    def save(self, postback: Postback) -> None:
        """Save a postback."""
        pass

    @abstractmethod
    def get_by_id(self, postback_id: str) -> Optional[Postback]:
        """Get postback by ID."""
        pass

    @abstractmethod
    def get_by_conversion_id(self, conversion_id: str) -> List[Postback]:
        """Get postbacks by conversion ID."""
        pass

    @abstractmethod
    def get_pending(self, limit: int = 100) -> List[Postback]:
        """Get pending postbacks ready for delivery."""
        pass

    @abstractmethod
    def get_by_status(self, status: PostbackStatus, limit: int = 100) -> List[Postback]:
        """Get postbacks by status."""
        pass

    @abstractmethod
    def update_status(self, postback_id: str, status: PostbackStatus) -> None:
        """Update postback status."""
        pass

    @abstractmethod
    def get_retry_candidates(self, current_time: datetime, limit: int = 50) -> List[Postback]:
        """Get postbacks that should be retried now."""
        pass
