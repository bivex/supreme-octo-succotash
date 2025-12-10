"""Bulk operations HTTP routes."""

import json
from loguru import logger
from ...application.handlers.bulk_click_handler import BulkClickHandler
from ...application.handlers.click_validation_handler import ClickValidationHandler


class BulkOperationsRoutes:
    """Socketify routes for bulk operations."""

    def __init__(self, bulk_click_handler: BulkClickHandler, click_validation_handler: ClickValidationHandler):
        self.bulk_click_handler = bulk_click_handler
        self.click_validation_handler = click_validation_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_bulk_click_generate(app)
        self._register_click_validation(app)

    def _register_bulk_click_generate(self, app):
        """Register bulk click generation route."""
        def bulk_generate_clicks(res, req):
            """Generate multiple click tracking URLs in bulk."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                logger.debug("Bulk click generation request received")

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
                                        logger.error("Invalid JSON in bulk click generation request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Validate bulk request
                            urls = body_data.get('urls', [])
                            if not urls:
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps({
                                    "status": "error",
                                    "message": "No URLs provided for generation"
                                }))
                                return

                            if len(urls) > 1000:
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps({
                                    "status": "error",
                                    "message": "Maximum 1000 URLs allowed per request"
                                }))
                                return

                            # Generate bulk clicks
                            result = self.bulk_click_handler.handle(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing bulk click generation data: {e}", exc_info=True)
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
                logger.error(f"Error in bulk_generate_clicks: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the bulk click generation endpoint
        app.post('/v1/clicks/bulk-generate', bulk_generate_clicks)

    def _register_click_validation(self, app):
        """Register click validation route."""
        def validate_click(res, req):
            """Validate click before redirect."""
            try:
                # This is a public endpoint, no authentication required
                click_id = req.get_parameter(0)

                # Validate UUID format
                import uuid
                try:
                    uuid.UUID(click_id)
                except (ValueError, TypeError):
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    res.end(json.dumps({
                        "clickId": click_id,
                        "isValid": False,
                        "fraudScore": 1.0,
                        "validationReason": "invalid_click_id_format",
                        "blockedReason": "Invalid UUID format"
                    }))
                    return

                # Get additional parameters for validation
                user_agent = req.get_query('user_agent')
                ip_address = req.get_query('ip_address')
                referrer = req.get_query('referrer')

                # Call validation handler
                validation_result = self.click_validation_handler.validate_click(
                    click_id=click_id,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    referrer=referrer
                )

                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(validation_result))

            except Exception as e:
                logger.error(f"Error in validate_click: {e}", exc_info=True)
                error_response = {
                    "clickId": click_id if 'click_id' in locals() else "unknown",
                    "isValid": False,
                    "fraudScore": 1.0,
                    "validationReason": "internal_error",
                    "blockedReason": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        # Register the click validation endpoint
        app.get('/v1/clicks/validate/:clickid', validate_click)
