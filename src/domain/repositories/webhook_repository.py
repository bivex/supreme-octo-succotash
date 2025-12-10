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
