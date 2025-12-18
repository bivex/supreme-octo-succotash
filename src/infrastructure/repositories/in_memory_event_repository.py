# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""In-memory event repository implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from ...domain.repositories.event_repository import EventRepository
from ...domain.entities.event import Event


class InMemoryEventRepository(EventRepository):
    """In-memory implementation of event repository."""

    def __init__(self):
        self._events: Dict[str, Event] = {}
        self._user_index: Dict[str, List[str]] = {}  # user_id -> list of event_ids
        self._session_index: Dict[str, List[str]] = {}  # session_id -> list of event_ids
        self._click_index: Dict[str, List[str]] = {}  # click_id -> list of event_ids
        self._campaign_index: Dict[int, List[str]] = {}  # campaign_id -> list of event_ids
        self._time_index: List[tuple] = []  # (timestamp, event_id) for time-based queries

    def save(self, event: Event) -> None:
        """Save an event."""
        self._events[event.id] = event

        # Update indexes
        if event.user_id:
            if event.user_id not in self._user_index:
                self._user_index[event.user_id] = []
            self._user_index[event.user_id].append(event.id)

        if event.session_id:
            if event.session_id not in self._session_index:
                self._session_index[event.session_id] = []
            self._session_index[event.session_id].append(event.id)

        if event.click_id:
            if event.click_id not in self._click_index:
                self._click_index[event.click_id] = []
            self._click_index[event.click_id].append(event.id)

        if event.campaign_id:
            if event.campaign_id not in self._campaign_index:
                self._campaign_index[event.campaign_id] = []
            self._campaign_index[event.campaign_id].append(event.id)

        # Add to time index
        self._time_index.append((event.timestamp, event.id))
        # Keep time index sorted
        self._time_index.sort(key=lambda x: x[0])

    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        return self._events.get(event_id)

    def get_by_user_id(self, user_id: str, limit: int = 100) -> List[Event]:
        """Get events by user ID."""
        event_ids = self._user_index.get(user_id, [])
        events = [self._events[wid] for wid in event_ids if wid in self._events]
        return events[-limit:]  # Return most recent

    def get_by_session_id(self, session_id: str, limit: int = 100) -> List[Event]:
        """Get events by session ID."""
        event_ids = self._session_index.get(session_id, [])
        events = [self._events[wid] for wid in event_ids if wid in self._events]
        return events[-limit:]  # Return most recent

    def get_by_click_id(self, click_id: str, limit: int = 100) -> List[Event]:
        """Get events by click ID."""
        event_ids = self._click_index.get(click_id, [])
        events = [self._events[wid] for wid in event_ids if wid in self._events]
        return events[-limit:]  # Return most recent

    def get_by_campaign_id(self, campaign_id: int, limit: int = 100) -> List[Event]:
        """Get events by campaign ID."""
        event_ids = self._campaign_index.get(campaign_id, [])
        events = [self._events[wid] for wid in event_ids if wid in self._events]
        return events[-limit:]  # Return most recent

    def get_events_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Event]:
        """Get events within a time range."""
        # Find events in time range
        matching_ids = []
        for timestamp, event_id in self._time_index:
            if start_time <= timestamp <= end_time:
                if event_id in self._events:
                    event = self._events[event_id]
                    if event_type is None or event.event_type == event_type:
                        matching_ids.append(event_id)
                        if len(matching_ids) >= limit:
                            break

        return [self._events[event_id] for event_id in matching_ids]

    def get_event_counts(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = 'event_type'
    ) -> Dict[str, int]:
        """Get event counts grouped by specified field."""
        counts = defaultdict(int)

        for timestamp, event_id in self._time_index:
            if start_time <= timestamp <= end_time:
                if event_id in self._events:
                    event = self._events[event_id]
                    if group_by == 'event_type':
                        counts[event.event_type] += 1
                    elif group_by == 'event_name':
                        event_name = event.event_name or 'unknown'
                        counts[event_name] += 1
                    elif group_by == 'campaign_id' and event.campaign_id:
                        counts[str(event.campaign_id)] += 1
                    elif group_by == 'landing_page_id' and event.landing_page_id:
                        counts[str(event.landing_page_id)] += 1

        return dict(counts)
