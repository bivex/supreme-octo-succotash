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

"""SQLite postback repository implementation."""

import sqlite3
from typing import Optional, List
from datetime import datetime, timezone

from ...domain.entities.postback import Postback, PostbackStatus
from ...domain.repositories.postback_repository import PostbackRepository


class SQLitePostbackRepository(PostbackRepository):
    """SQLite implementation of PostbackRepository for stress testing."""

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
            CREATE TABLE IF NOT EXISTS postbacks (
                id TEXT PRIMARY KEY,
                conversion_id TEXT NOT NULL,
                url TEXT NOT NULL,
                method TEXT NOT NULL,
                payload TEXT,  -- JSON string
                headers TEXT,  -- JSON string
                status TEXT NOT NULL,
                response_status_code INTEGER,
                response_body TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                next_retry_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postbacks_conversion_id ON postbacks(conversion_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postbacks_status ON postbacks(status)")

        conn.commit()

    def save(self, postback: Postback) -> None:
        """Save a postback."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO postbacks
            (id, conversion_id, url, method, payload, headers, status,
             response_status_code, response_body, retry_count, max_retries,
             next_retry_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            postback.id.value, postback.conversion_id, postback.url, postback.method,
            json.dumps(postback.payload) if postback.payload else None,
            json.dumps(dict(postback.headers)) if postback.headers else None,
            postback.status, postback.response_status_code, postback.response_body,
            postback.retry_count, postback.max_retries,
            postback.next_retry_at.isoformat() if postback.next_retry_at else None,
            postback.created_at.isoformat(), postback.updated_at.isoformat()
        ))

        conn.commit()

    def find_by_id(self, postback_id: str) -> Optional[Postback]:
        """Find postback by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM postbacks WHERE id = ?", (postback_id,))

        row = cursor.fetchone()
        return self._row_to_postback(row) if row else None

    def find_by_conversion_id(self, conversion_id: str) -> List[Postback]:
        """Find postbacks by conversion ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE conversion_id = ?
            ORDER BY created_at DESC
        """, (conversion_id,))

        return [self._row_to_postback(row) for row in cursor.fetchall()]

    def get_by_id(self, postback_id: str) -> Optional[Postback]:
        """Get postback by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM postbacks WHERE id = ?", (postback_id,))

        row = cursor.fetchone()
        return self._row_to_postback(row) if row else None

    def get_by_conversion_id(self, conversion_id: str) -> List[Postback]:
        """Get postbacks by conversion ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE conversion_id = ?
            ORDER BY created_at DESC
        """, (conversion_id,))

        return [self._row_to_postback(row) for row in cursor.fetchall()]

    def get_pending(self, limit: int = 100) -> List[Postback]:
        """Get pending postbacks ready for delivery."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))

        return [self._row_to_postback(row) for row in cursor.fetchall()]

    def get_by_status(self, status: PostbackStatus, limit: int = 100) -> List[Postback]:
        """Get postbacks by status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (status.value, limit))

        return [self._row_to_postback(row) for row in cursor.fetchall()]

    def update_status(self, postback_id: str, status: PostbackStatus) -> None:
        """Update postback status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE postbacks
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status.value, datetime.now(timezone.utc).isoformat(), postback_id))

        conn.commit()

    def get_retry_candidates(self, current_time: datetime, limit: int = 50) -> List[Postback]:
        """Get postbacks that should be retried now."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status = 'retry'
              AND next_retry_at <= ?
            ORDER BY next_retry_at ASC
            LIMIT ?
        """, (current_time.isoformat(), limit))

        return [self._row_to_postback(row) for row in cursor.fetchall()]

    def find_pending_postbacks(self, limit: int = 100) -> List[Postback]:
        """Find postbacks that are pending or need retry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            SELECT * FROM postbacks
            WHERE status IN ('pending', 'retry')
              AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY created_at ASC
            LIMIT ?
        """, (now, limit))

        return [self._row_to_postback(row) for row in cursor.fetchall()]

    def _row_to_postback(self, row) -> Postback:
        """Convert database row to Postback entity."""
        import json
        from ...domain.value_objects.identifiers import PostbackId

        return Postback(
            id=PostbackId.from_string(row["id"]),
            conversion_id=row["conversion_id"],
            url=row["url"],
            method=row["method"],
            payload=json.loads(row["payload"]) if row["payload"] else None,
            headers=json.loads(row["headers"]) if row["headers"] else {},
            status=PostbackStatus(row["status"]),
            response_status_code=row["response_status_code"],
            response_body=row["response_body"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            next_retry_at=datetime.fromisoformat(row["next_retry_at"]) if row["next_retry_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
