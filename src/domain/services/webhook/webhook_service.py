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

"""Webhook processing service."""

import re
from typing import Optional, Dict, Any

from loguru import logger

from ...entities.webhook import TelegramWebhook


class WebhookService:
    """Service for processing Telegram webhooks."""

    def __init__(self):
        self._bot_token_pattern = re.compile(r'^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$')

    def validate_telegram_update(self, update_data: Dict[str, Any]) -> bool:
        """Validate Telegram update structure."""
        try:
            if not isinstance(update_data, dict):
                return False

            # Must have update_id
            if 'update_id' not in update_data:
                return False

            # Must have message or another update type
            if 'message' not in update_data:
                logger.warning(f"Unsupported update type: {list(update_data.keys())}")
                return False

            message = update_data['message']

            # Validate message structure
            required_fields = ['message_id', 'from', 'chat', 'date']
            for field in required_fields:
                if field not in message:
                    logger.warning(f"Missing required field: {field}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating Telegram update: {e}")
            return False

    def extract_command(self, text: Optional[str]) -> Optional[str]:
        """Extract bot command from message text."""
        if not text or not text.startswith('/'):
            return None

        # Extract command (first word after /)
        parts = text.split()
        if not parts:
            return None

        command = parts[0].lstrip('/').split('@')[0]  # Remove @botname suffix
        return command.lower()

    def should_process_message(self, webhook: TelegramWebhook) -> bool:
        """Determine if webhook message should be processed."""
        # Skip messages from bots
        if webhook.username and webhook.username.endswith('_bot'):
            return False

        # Process text messages and commands
        if webhook.message_type == 'text':
            return True

        # Could extend to process other types (photos, documents, etc.)
        return False

    def generate_response(self, webhook: TelegramWebhook) -> Optional[Dict[str, Any]]:
        """Generate automated response based on webhook content."""
        if not webhook.message_text:
            return None

        command = self.extract_command(webhook.message_text)

        if command == 'start':
            return {
                'chat_id': webhook.chat_id,
                'text': '👋 Добро пожаловать! Я бот для управления кампаниями.',
                'reply_markup': {
                    'inline_keyboard': [
                        [
                            {'text': '📊 Статистика', 'callback_data': 'stats'},
                            {'text': '🎯 Кампании', 'callback_data': 'campaigns'}
                        ],
                        [
                            {'text': '💰 Финансы', 'callback_data': 'finance'},
                            {'text': '⚙️ Настройки', 'callback_data': 'settings'}
                        ]
                    ]
                }
            }
        elif command == 'help':
            return {
                'chat_id': webhook.chat_id,
                'text': '📖 Доступные команды:\n/start - Начать работу\n/help - Справка\n/stats - Статистика\n/campaigns - Кампании'
            }
        elif command == 'stats':
            return {
                'chat_id': webhook.chat_id,
                'text': '📊 Статистика кампаний:\n• Клики: 1,250\n• Конверсии: 45\n• Выручка: $750.00\n• ROI: 200%'
            }

        # Default response for unknown commands
        return {
            'chat_id': webhook.chat_id,
            'text': '❓ Неизвестная команда. Используйте /help для списка команд.'
        }
