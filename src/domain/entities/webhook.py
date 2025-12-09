"""Telegram webhook entity."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TelegramWebhook:
    """Telegram webhook message entity."""

    id: str
    chat_id: int
    message_type: str  # 'text', 'photo', 'document', etc.
    message_text: Optional[str]
    user_id: Optional[int]
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    timestamp: datetime
    processed: bool = False

    @classmethod
    def create_from_telegram_update(cls, update_data: dict) -> 'TelegramWebhook':
        """Create webhook from Telegram update JSON."""
        import uuid
        from datetime import datetime

        message = update_data.get('message', {})
        user = message.get('from', {})

        return cls(
            id=str(uuid.uuid4()),
            chat_id=message.get('chat', {}).get('id'),
            message_type=cls._determine_message_type(message),
            message_text=message.get('text'),
            user_id=user.get('id'),
            username=user.get('username'),
            first_name=user.get('first_name'),
            last_name=user.get('last_name'),
            timestamp=datetime.fromtimestamp(message.get('date', 0)),
            processed=False
        )

    @staticmethod
    def _determine_message_type(message: dict) -> str:
        """Determine message type from Telegram message object."""
        if 'text' in message:
            return 'text'
        elif 'photo' in message:
            return 'photo'
        elif 'document' in message:
            return 'document'
        elif 'video' in message:
            return 'video'
        elif 'audio' in message:
            return 'audio'
        elif 'voice' in message:
            return 'voice'
        elif 'sticker' in message:
            return 'sticker'
        else:
            return 'unknown'
