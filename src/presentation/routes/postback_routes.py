"""Postback HTTP routes."""

import json
from loguru import logger
from ...application.handlers.send_postback_handler import SendPostbackHandler


class PostbackRoutes:
    """Socketify routes for postback operations."""

    def __init__(self, send_postback_handler: SendPostbackHandler):
        self.send_postback_handler = send_postback_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_send_postback(app)

    def _register_send_postback(self, app):
        """Register postback sending route."""
        def send_postback(res, req):
            """Send postback notification to external system."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Postback send request received")

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
                                        logger.error("Invalid JSON in postback send request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Send postback
                            result = self.send_postback_handler.handle(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            elif result["status"] == "failed":
                                res.write_status(502)  # Bad Gateway - external service error
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing postback send data: {e}", exc_info=True)
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
                logger.error(f"Error in send_postback: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the postback endpoint
        app.post('/postbacks/send', send_postback)
