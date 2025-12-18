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

"""Webhook repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.webhook import TelegramWebhook


class WebhookRepository(ABC):
    """Abstract base class for webhook repositories."""

    @abstractmethod
    def save(self, webhook: TelegramWebhook) -> None:
        """Save a webhook message."""
        pass

    @abstractmethod
    def get_by_id(self, webhook_id: str) -> Optional[TelegramWebhook]:
        """Get webhook by ID."""
        pass

    @abstractmethod
    def get_unprocessed(self, limit: int = 100) -> List[TelegramWebhook]:
        """Get unprocessed webhook messages."""
        pass

    @abstractmethod
    def mark_processed(self, webhook_id: str) -> None:
        """Mark webhook as processed."""
        pass

    @abstractmethod
    def get_by_chat_id(self, chat_id: int, limit: int = 50) -> List[TelegramWebhook]:
        """Get webhooks by chat ID."""
        pass
