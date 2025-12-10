"""PostgreSQL postback repository implementation."""

import psycopg2
import json
from typing import Optional, List
from datetime import datetime

from ...domain.entities.postback import Postback, PostbackStatus
from ...domain.repositories.postback_repository import PostbackRepository


class PostgresPostbackRepository(PostbackRepository):
    """PostgreSQL implementation of PostbackRepository."""

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
            CREATE TABLE IF NOT EXISTS postbacks (
                id TEXT PRIMARY KEY,
                conversion_id TEXT NOT NULL,
                url TEXT NOT NULL,
                method TEXT NOT NULL,
                payload JSONB,
                headers JSONB,
                status TEXT NOT NULL,
                response_status_code INTEGER,
                response_body TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                next_retry_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postbacks_conversion_id ON postbacks(conversion_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postbacks_status ON postbacks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postbacks_next_retry ON postbacks(next_retry_at)")

        conn.commit()

    def _row_to_postback(self, row) -> Postback:
        """Convert database row to Postback entity."""
        return Postback(
            id=row["id"],
            conversion_id=row["conversion_id"],
            url=row["url"],
            method=row["method"],
            payload=row["payload"],
            headers=row["headers"],
            status=PostbackStatus(row["status"]),
            response_status_code=row["response_status_code"],
            response_body=row["response_body"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            next_retry_at=row["next_retry_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save(self, postback: Postback) -> None:
        """Save a postback."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO postbacks
            (id, conversion_id, url, method, payload, headers, status,
             response_status_code, response_body, retry_count, max_retries,
             next_retry_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                conversion_id = EXCLUDED.conversion_id,
                url = EXCLUDED.url,
                method = EXCLUDED.method,
                payload = EXCLUDED.payload,
                headers = EXCLUDED.headers,
                status = EXCLUDED.status,
                response_status_code = EXCLUDED.response_status_code,
                response_body = EXCLUDED.response_body,
                retry_count = EXCLUDED.retry_count,
                max_retries = EXCLUDED.max_retries,
                next_retry_at = EXCLUDED.next_retry_at,
                updated_at = EXCLUDED.updated_at
        """, (
            postback.id, postback.conversion_id, postback.url, postback.method,
            json.dumps(postback.payload), json.dumps(postback.headers),
            postback.status.value, postback.response_status_code,
            postback.response_body, postback.retry_count, postback.max_retries,
            postback.next_retry_at, postback.created_at, postback.updated_at
        ))

        conn.commit()

    def get_by_id(self, postback_id: str) -> Optional[Postback]:
        """Get postback by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM postbacks WHERE id = %s", (postback_id,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_postback(row_dict)
        return None

    def get_by_conversion_id(self, conversion_id: str) -> List[Postback]:
        """Get postbacks by conversion ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE conversion_id = %s
            ORDER BY created_at DESC
        """, (conversion_id,))

        postbacks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            postbacks.append(self._row_to_postback(row_dict))

        return postbacks

    def get_pending(self, limit: int = 100) -> List[Postback]:
        """Get pending postbacks ready for delivery."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status = 'pending' AND (next_retry_at IS NULL OR next_retry_at <= %s)
            ORDER BY created_at ASC
            LIMIT %s
        """, (datetime.now(), limit))

        postbacks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            postbacks.append(self._row_to_postback(row_dict))

        return postbacks

    def get_by_status(self, status: PostbackStatus, limit: int = 100) -> List[Postback]:
        """Get postbacks by status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (status.value, limit))

        postbacks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            postbacks.append(self._row_to_postback(row_dict))

        return postbacks

    def update_status(self, postback_id: str, status: PostbackStatus) -> None:
        """Update postback status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE postbacks SET status = %s, updated_at = %s
            WHERE id = %s
        """, (status.value, datetime.now(), postback_id))

        conn.commit()

    def get_retry_candidates(self, current_time: datetime, limit: int = 50) -> List[Postback]:
        """Get postbacks that should be retried now."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status IN ('retry', 'failed')
              AND next_retry_at <= %s
              AND retry_count < max_retries
            ORDER BY next_retry_at ASC
            LIMIT %s
        """, (current_time, limit))

        postbacks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            postbacks.append(self._row_to_postback(row_dict))

        return postbacks
