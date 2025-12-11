"""Click generation HTTP routes."""

import json
from loguru import logger
from ...application.handlers.generate_click_handler import GenerateClickHandler


class ClickGenerationRoutes:
    """Socketify routes for click generation operations."""

    def __init__(self, generate_click_handler: GenerateClickHandler):
        self.generate_click_handler = generate_click_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_generate_click(app)

    def _register_generate_click(self, app):
        """Register click generation route."""
        async def generate_click(res, req):
            """Generate personalized click tracking URLs."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Click generation request received")

                # Parse request body
                data_parts = []

                async def on_data(res, chunk, is_last, *args):
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
                                        logger.error("Invalid JSON in click generation request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Generate click URL(s)
                            result = await self.generate_click_handler.handle(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing click generation data: {e}", exc_info=True)
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
                logger.error(f"Error in generate_click: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the click generation endpoint
        app.post('/v1/clicks/generate', generate_click)
