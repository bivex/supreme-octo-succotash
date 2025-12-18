# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:09
# Last Updated: 2025-12-18T12:13:09
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Conversion tracking HTTP routes."""

import json
from loguru import logger
from ...application.handlers.track_conversion_handler import TrackConversionHandler


class ConversionRoutes:
    """Socketify routes for conversion tracking operations."""

    def __init__(self, track_conversion_handler: TrackConversionHandler):
        self.track_conversion_handler = track_conversion_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_track_conversion(app)

    def _register_track_conversion(self, app):
        """Register conversion tracking route."""
        def track_conversion(res, req):
            """Track conversions from external systems."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Conversion tracking request received")

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
                                        logger.error("Invalid JSON in conversion tracking request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Track conversion
                            result = self.track_conversion_handler.handle(body_data)

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
                        logger.error(f"Error processing conversion tracking data: {e}", exc_info=True)
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
                logger.error(f"Error in track_conversion: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the conversion tracking endpoint
        app.post('/conversions/track', track_conversion)
