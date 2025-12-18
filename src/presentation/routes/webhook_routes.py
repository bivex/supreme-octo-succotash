# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:05
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Webhook HTTP routes."""

import json
from loguru import logger
from ...application.handlers.process_webhook_handler import ProcessWebhookHandler


class WebhookRoutes:
    """Socketify routes for webhook operations."""

    def __init__(self, process_webhook_handler: ProcessWebhookHandler):
        self.process_webhook_handler = process_webhook_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_telegram_webhook(app)

    def _register_telegram_webhook(self, app):
        """Register Telegram webhook route."""
        def telegram_webhook(res, req):
            """Handle incoming Telegram webhook."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.info("Telegram webhook received")

                # For webhooks, we might want minimal validation
                # since they come from external services

                # Parse request body
                data_parts = []

                def on_data(res, chunk, is_last, *args):
                    try:
                        if chunk:
                            data_parts.append(chunk)

                        if is_last:
                            # Parse body
                            body_data = {}
                            if data_parts:
                                full_body = b"".join(data_parts)
                                if full_body:
                                    try:
                                        body_data = json.loads(full_body)
                                    except (ValueError, json.JSONDecodeError):
                                        logger.error("Invalid JSON in webhook request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Process webhook
                            result = self.process_webhook_handler.handle(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            elif result["status"] == "skipped":
                                res.write_status(200)  # Telegram expects 200 even for skipped
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing webhook data: {e}", exc_info=True)
                        error_response = {
                            "status": "error",
                            "message": "Internal server error"
                        }
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in telegram_webhook: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the webhook endpoint
        app.post('/webhooks/telegram', telegram_webhook)
