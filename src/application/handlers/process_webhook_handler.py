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

"""Process webhook handler."""

import json
from typing import Dict, Any, Optional
from loguru import logger
from ...domain.repositories.webhook_repository import WebhookRepository
from ...domain.services.webhook.webhook_service import WebhookService
from ...domain.entities.webhook import TelegramWebhook


class ProcessWebhookHandler:
    """Handler for processing Telegram webhooks."""

    def __init__(
        self,
        webhook_repository: WebhookRepository,
        webhook_service: WebhookService
    ):
        self.webhook_repository = webhook_repository
        self.webhook_service = webhook_service

    def handle(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Telegram webhook update."""
        try:
            logger.info(f"Processing webhook update: {update_data.get('update_id')}")

            # Validate the update
            if not self.webhook_service.validate_telegram_update(update_data):
                logger.warning("Invalid Telegram update received")
                return {"status": "error", "message": "Invalid update format"}

            # Create webhook entity
            webhook = TelegramWebhook.create_from_telegram_update(update_data)

            # Check if we should process this message
            if not self.webhook_service.should_process_message(webhook):
                logger.info(f"Skipping message from {webhook.username} (type: {webhook.message_type})")
                return {"status": "skipped", "reason": "message type not supported"}

            # Save webhook
            self.webhook_repository.save(webhook)
            logger.info(f"Webhook saved with ID: {webhook.id}")

            # Generate response
            response = self.webhook_service.generate_response(webhook)

            # Mark as processed if response was generated
            if response:
                self.webhook_repository.mark_processed(webhook.id)
                logger.info(f"Webhook processed and response generated for chat {webhook.chat_id}")

            return {
                "status": "success",
                "webhook_id": webhook.id,
                "response": response
            }

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
