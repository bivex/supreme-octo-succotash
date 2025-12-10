"""PostgreSQL event repository implementation."""

import psycopg2
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...domain.entities.event import Event
from ...domain.repositories.event_repository import EventRepository


class PostgresEventRepository(EventRepository):
    """PostgreSQL implementation of EventRepository."""

    def __init__(self, container):
        self._container = container
        self._connection = None
        self._db_initialized = False

    def _get_connection(self):


        """Get database connection."""


        if self._connection is None:


            self._connection = self._container.get_db_connection()


        if not self._db_initialized:


            self._initialize_db()


            self._db_initialized = True


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
                event_data JSONB,
                created_at TIMESTAMP NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_click_id ON events(click_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)")

        conn.commit()

    def _row_to_event(self, row) -> Event:
        """Convert database row to Event entity."""
        return Event(
            id=row["id"],
            click_id=row["click_id"],
            event_type=row["event_type"],
            event_data=row["event_data"],
            created_at=row["created_at"]
        )

    def save(self, event: Event) -> None:
        """Save an event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events
            (id, click_id, event_type, event_data, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                click_id = EXCLUDED.click_id,
                event_type = EXCLUDED.event_type,
                event_data = EXCLUDED.event_data
        """, (
            event.id, event.click_id, event.event_type,
            json.dumps(event.event_data), event.created_at
        ))

        conn.commit()

    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_event(row_dict)
        return None

    def get_by_user_id(self, user_id: str, limit: int = 100) -> List[Event]:
        """Get events by user ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM events
            WHERE event_data->>'user_id' = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))

        events = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            events.append(self._row_to_event(row_dict))

        return events

    def get_by_session_id(self, session_id: str, limit: int = 100) -> List[Event]:
        """Get events by session ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM events
            WHERE event_data->>'session_id' = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (session_id, limit))

        events = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            events.append(self._row_to_event(row_dict))

        return events

    def get_by_click_id(self, click_id: str, limit: int = 100) -> List[Event]:
        """Get events by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM events
            WHERE click_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (click_id, limit))

        events = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            events.append(self._row_to_event(row_dict))

        return events

    def get_by_campaign_id(self, campaign_id: int, limit: int = 100) -> List[Event]:
        """Get events by campaign ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM events
            WHERE event_data->>'campaign_id' = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (str(campaign_id), limit))

        events = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            events.append(self._row_to_event(row_dict))

        return events

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

        if event_type:
            cursor.execute("""
                SELECT * FROM events
                WHERE created_at >= %s AND created_at <= %s AND event_type = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (start_time, end_time, event_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM events
                WHERE created_at >= %s AND created_at <= %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (start_time, end_time, limit))

        events = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            events.append(self._row_to_event(row_dict))

        return events

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
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY event_type
            """, (start_time, end_time))
        elif group_by == 'user_id':
            cursor.execute("""
                SELECT event_data->>'user_id' as user_id, COUNT(*) as count
                FROM events
                WHERE created_at >= %s AND created_at <= %s AND event_data->>'user_id' IS NOT NULL
                GROUP BY event_data->>'user_id'
            """, (start_time, end_time))
        elif group_by == 'campaign_id':
            cursor.execute("""
                SELECT event_data->>'campaign_id' as campaign_id, COUNT(*) as count
                FROM events
                WHERE created_at >= %s AND created_at <= %s AND event_data->>'campaign_id' IS NOT NULL
                GROUP BY event_data->>'campaign_id'
            """, (start_time, end_time))
        else:
            # Default to event_type
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM events
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY event_type
            """, (start_time, end_time))

        result = {}
        for row in cursor.fetchall():
            key = row[0] if row[0] is not None else 'unknown'
            result[key] = row[1]

        return result
