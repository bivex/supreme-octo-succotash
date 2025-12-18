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

"""SQLite webhook repository implementation."""

import sqlite3
from datetime import datetime
from typing import Optional, List

from ...domain.entities.webhook import TelegramWebhook
from ...domain.repositories.webhook_repository import WebhookRepository


class SQLiteWebhookRepository(WebhookRepository):
    """SQLite implementation of WebhookRepository for stress testing."""

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
                       CREATE TABLE IF NOT EXISTS webhooks
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           chat_id
                           INTEGER
                           NOT
                           NULL,
                           message_type
                           TEXT
                           NOT
                           NULL,
                           message_text
                           TEXT,
                           user_id
                           INTEGER,
                           username
                           TEXT,
                           first_name
                           TEXT,
                           last_name
                           TEXT,
                           timestamp
                           TEXT
                           NOT
                           NULL,
                           processed
                           INTEGER
                           DEFAULT
                           0
                       )
                       """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_chat_id ON webhooks(chat_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_processed ON webhooks(processed)")

        conn.commit()

    def save(self, webhook: TelegramWebhook) -> None:
        """Save a webhook."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO webhooks
            (id, chat_id, message_type, message_text, user_id, username,
             first_name, last_name, timestamp, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            webhook.id, webhook.chat_id, webhook.message_type, webhook.message_text,
            webhook.user_id, webhook.username, webhook.first_name, webhook.last_name,
            webhook.timestamp.isoformat(), 1 if webhook.processed else 0
        ))

        conn.commit()

    def get_by_id(self, webhook_id: str) -> Optional[TelegramWebhook]:
        """Get webhook by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))

        row = cursor.fetchone()
        return self._row_to_webhook(row) if row else None

    def get_unprocessed(self, limit: int = 100) -> List[TelegramWebhook]:
        """Get unprocessed webhook messages."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT *
                       FROM webhooks
                       WHERE processed = 0
                       ORDER BY timestamp ASC
                           LIMIT ?
                       """, (limit,))

        return [self._row_to_webhook(row) for row in cursor.fetchall()]

    def mark_processed(self, webhook_id: str) -> None:
        """Mark webhook as processed."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE webhooks SET processed = 1 WHERE id = ?", (webhook_id,))

        conn.commit()

    def get_by_chat_id(self, chat_id: int, limit: int = 50) -> List[TelegramWebhook]:
        """Get webhooks by chat ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT *
                       FROM webhooks
                       WHERE chat_id = ?
                       ORDER BY timestamp DESC
                           LIMIT ?
                       """, (chat_id, limit))

        return [self._row_to_webhook(row) for row in cursor.fetchall()]

    def _row_to_webhook(self, row) -> TelegramWebhook:
        """Convert database row to TelegramWebhook entity."""
        return TelegramWebhook(
            id=row["id"],
            chat_id=row["chat_id"],
            message_type=row["message_type"],
            message_text=row["message_text"],
            user_id=row["user_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            processed=bool(row["processed"])
        )
