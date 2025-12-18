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

"""SQLite event repository implementation."""

import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, timezone

from ...domain.entities.event import Event
from ...domain.repositories.event_repository import EventRepository


class SQLiteEventRepository(EventRepository):
    """SQLite implementation of EventRepository for stress testing."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._connection = None
        self._initialize_db()

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                click_id TEXT,
                event_type TEXT NOT NULL,
                event_data TEXT,  -- JSON string
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_click_id ON events(click_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)")

        conn.commit()

    def save(self, event: Event) -> None:
        """Save an event."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO events
            (id, click_id, event_type, event_data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event.id, event.click_id, event.event_type,
            json.dumps(event.event_data) if event.event_data else None,
            event.timestamp.isoformat()
        ))

        conn.commit()

    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))

        row = cursor.fetchone()
        return self._row_to_event(row) if row else None

    def get_by_user_id(self, user_id: str, limit: int = 100) -> List[Event]:
        """Get events by user ID."""
        # Note: Event entity doesn't have user_id, so we return empty list
        return []

    def get_by_session_id(self, session_id: str, limit: int = 100) -> List[Event]:
        """Get events by session ID."""
        # Note: Event entity doesn't have session_id, so we return empty list
        return []

    def get_by_click_id(self, click_id: str, limit: int = 100) -> List[Event]:
        """Get events by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM events
            WHERE click_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (click_id, limit))

        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_by_campaign_id(self, campaign_id: int, limit: int = 100) -> List[Event]:
        """Get events by campaign ID."""
        # Note: This would require joining with clicks table, simplified implementation
        return []

    def get_events_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Event]:
        """Get events within a time range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM events
            WHERE created_at >= ? AND created_at <= ?
        """
        params = [start_time.isoformat(), end_time.isoformat()]

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_event_counts(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = 'event_type'
    ) -> Dict[str, int]:
        """Get event counts grouped by specified field."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if group_by == 'event_type':
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM events
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY event_type
            """, (start_time.isoformat(), end_time.isoformat()))
        else:
            # For other group_by fields, return empty dict as they're not implemented
            return {}

        counts = {}
        for row in cursor.fetchall():
            counts[row[0]] = row[1]

        return counts

    def _row_to_event(self, row) -> Event:
        """Convert database row to Event entity."""
        import json
        from ...domain.value_objects.identifiers import EventId

        return Event(
            id=EventId.from_string(row["id"]),
            click_id=row["click_id"],
            event_type=row["event_type"],
            event_data=json.loads(row["event_data"]) if row["event_data"] else None,
            created_at=datetime.fromisoformat(row["created_at"])
        )
