"""PostgreSQL webhook repository implementation."""

import psycopg2
from typing import Optional, List
from datetime import datetime

from ...domain.entities.webhook import TelegramWebhook
from ...domain.repositories.webhook_repository import WebhookRepository


class PostgresWebhookRepository(WebhookRepository):
    """PostgreSQL implementation of WebhookRepository."""

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
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                message_type TEXT NOT NULL,
                message_text TEXT,
                user_id BIGINT,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                timestamp TIMESTAMP NOT NULL,
                processed BOOLEAN DEFAULT FALSE
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_chat_id ON webhooks(chat_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_processed ON webhooks(processed)")

        conn.commit()

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
            timestamp=row["timestamp"],
            processed=row["processed"]
        )

    def save(self, webhook: TelegramWebhook) -> None:
        """Save a webhook message."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO webhooks
            (id, chat_id, message_type, message_text, user_id, username,
             first_name, last_name, timestamp, processed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                message_type = EXCLUDED.message_type,
                message_text = EXCLUDED.message_text,
                user_id = EXCLUDED.user_id,
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                processed = EXCLUDED.processed
        """, (
            webhook.id, webhook.chat_id, webhook.message_type, webhook.message_text,
            webhook.user_id, webhook.username, webhook.first_name, webhook.last_name,
            webhook.timestamp, webhook.processed
        ))

        conn.commit()

    def get_by_id(self, webhook_id: str) -> Optional[TelegramWebhook]:
        """Get webhook by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM webhooks WHERE id = %s", (webhook_id,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_webhook(row_dict)
        return None

    def get_unprocessed(self, limit: int = 100) -> List[TelegramWebhook]:
        """Get unprocessed webhook messages."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM webhooks
            WHERE processed = FALSE
            ORDER BY timestamp ASC
            LIMIT %s
        """, (limit,))

        webhooks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            webhooks.append(self._row_to_webhook(row_dict))

        return webhooks

    def mark_processed(self, webhook_id: str) -> None:
        """Mark webhook as processed."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE webhooks SET processed = TRUE
            WHERE id = %s
        """, (webhook_id,))

        conn.commit()

    def get_by_chat_id(self, chat_id: int, limit: int = 50) -> List[TelegramWebhook]:
        """Get webhooks by chat ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM webhooks
            WHERE chat_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (chat_id, limit))

        webhooks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            webhooks.append(self._row_to_webhook(row_dict))

        return webhooks
