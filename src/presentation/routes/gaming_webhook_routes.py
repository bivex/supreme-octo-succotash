# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:07
# Last Updated: 2025-12-18T12:13:07
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Gaming platform webhook HTTP routes."""

import json
from loguru import logger
from ...application.handlers.gaming_webhook_handler import GamingWebhookHandler


class GamingWebhookRoutes:
    """Socketify routes for gaming platform webhook operations."""

    def __init__(self, gaming_webhook_handler: GamingWebhookHandler):
        self.gaming_webhook_handler = gaming_webhook_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_deposit_webhook(app)
        self._register_registration_webhook(app)

    def _register_deposit_webhook(self, app):
        """Register deposit webhook route."""
        def deposit_webhook(res, req):
            """Handle deposit webhooks from gaming platforms."""
            from ...presentation.middleware.security_middleware import add_security_headers
            import json

            try:
                logger.info("Gaming deposit webhook received")

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
                                        logger.error("Invalid JSON in deposit webhook request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Process deposit webhook
                            result = self.gaming_webhook_handler.handle_deposit(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            elif result["status"] == "duplicate":
                                res.write_status(200)  # Still successful, just duplicate
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing deposit webhook data: {e}", exc_info=True)
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
                logger.error(f"Error in deposit_webhook: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the deposit webhook endpoint
        app.post('/webhooks/gaming/deposit', deposit_webhook)

    def _register_registration_webhook(self, app):
        """Register user registration webhook route."""
        def registration_webhook(res, req):
            """Handle user registration webhooks from gaming platforms."""
            from ...presentation.middleware.security_middleware import add_security_headers
            import json

            try:
                logger.info("Gaming registration webhook received")

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
                                        logger.error("Invalid JSON in registration webhook request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Process registration webhook
                            result = self.gaming_webhook_handler.handle_registration(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing registration webhook data: {e}", exc_info=True)
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
                logger.error(f"Error in registration_webhook: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the registration webhook endpoint
        app.post('/webhooks/gaming/registration', registration_webhook)