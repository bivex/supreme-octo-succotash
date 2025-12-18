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

"""Event repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..entities.event import Event


class EventRepository(ABC):
    """Abstract base class for event repositories."""

    @abstractmethod
    def save(self, event: Event) -> None:
        """Save an event."""
        pass

    @abstractmethod
    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str, limit: int = 100) -> List[Event]:
        """Get events by user ID."""
        pass

    @abstractmethod
    def get_by_session_id(self, session_id: str, limit: int = 100) -> List[Event]:
        """Get events by session ID."""
        pass

    @abstractmethod
    def get_by_click_id(self, click_id: str, limit: int = 100) -> List[Event]:
        """Get events by click ID."""
        pass

    @abstractmethod
    def get_by_campaign_id(self, campaign_id: int, limit: int = 100) -> List[Event]:
        """Get events by campaign ID."""
        pass

    @abstractmethod
    def get_events_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Event]:
        """Get events within a time range."""
        pass

    @abstractmethod
    def get_event_counts(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = 'event_type'
    ) -> Dict[str, int]:
        """Get event counts grouped by specified field."""
        pass
