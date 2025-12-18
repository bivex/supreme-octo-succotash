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

"""In-memory webhook repository implementation."""

from typing import Dict, List, Optional
from ...domain.repositories.webhook_repository import WebhookRepository
from ...domain.entities.webhook import TelegramWebhook


class InMemoryWebhookRepository(WebhookRepository):
    """In-memory implementation of webhook repository."""

    def __init__(self):
        self._webhooks: Dict[str, TelegramWebhook] = {}
        self._chat_index: Dict[int, List[str]] = {}  # chat_id -> list of webhook_ids

    def save(self, webhook: TelegramWebhook) -> None:
        """Save a webhook message."""
        self._webhooks[webhook.id] = webhook

        # Update chat index
        if webhook.chat_id not in self._chat_index:
            self._chat_index[webhook.chat_id] = []
        self._chat_index[webhook.chat_id].append(webhook.id)

    def get_by_id(self, webhook_id: str) -> Optional[TelegramWebhook]:
        """Get webhook by ID."""
        return self._webhooks.get(webhook_id)

    def get_unprocessed(self, limit: int = 100) -> List[TelegramWebhook]:
        """Get unprocessed webhook messages."""
        unprocessed = [w for w in self._webhooks.values() if not w.processed]
        return unprocessed[:limit]

    def mark_processed(self, webhook_id: str) -> None:
        """Mark webhook as processed."""
        if webhook_id in self._webhooks:
            webhook = self._webhooks[webhook_id]
            self._webhooks[webhook_id] = TelegramWebhook(
                id=webhook.id,
                chat_id=webhook.chat_id,
                message_type=webhook.message_type,
                message_text=webhook.message_text,
                user_id=webhook.user_id,
                username=webhook.username,
                first_name=webhook.first_name,
                last_name=webhook.last_name,
                timestamp=webhook.timestamp,
                processed=True
            )

    def get_by_chat_id(self, chat_id: int, limit: int = 50) -> List[TelegramWebhook]:
        """Get webhooks by chat ID."""
        webhook_ids = self._chat_index.get(chat_id, [])
        webhooks = [self._webhooks[wid] for wid in webhook_ids if wid in self._webhooks]
        return webhooks[-limit:]  # Return most recent
