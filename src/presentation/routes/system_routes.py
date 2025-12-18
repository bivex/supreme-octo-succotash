# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:06
# Last Updated: 2025-12-18T12:28:56
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""System administration HTTP routes."""

import json
from loguru import logger
from ...application.handlers.system_handler import SystemHandler


class SystemRoutes:
    """Socketify routes for system administration operations."""

    def __init__(self, system_handler: SystemHandler):
        self.system_handler = system_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_cache_flush(app)

    def _register_cache_flush(self, app):
        """Register cache flush route."""
        def flush_cache(res, req):
            """Flush application cache with selective options."""
            # Temporarily disable security middleware for testing
            # from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
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
                                        logger.error("Invalid JSON in cache flush request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        res.end(json.dumps({
                                            "error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON format"}
                                        }))
                                        return

                            # Validate cache types if provided
                            cache_types = body_data.get('types', [])
                            valid_types = ['campaigns', 'landing_pages', 'offers', 'analytics', 'all']

                            if cache_types:
                                invalid_types = [t for t in cache_types if t not in valid_types]
                                if invalid_types:
                                    res.write_status(400)
                                    res.write_header("Content-Type", "application/json")
                                    res.end(json.dumps({
                                        "error": {"code": "VALIDATION_ERROR", "message": f"Invalid cache types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_types)}"}
                                    }))
                                    return
                            else:
                                # Default to flush all if no types specified
                                cache_types = ['all']

                            # Flush cache
                            result = self.system_handler.flush_cache(cache_types)

                            res.write_header("Content-Type", "application/json")
                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing cache flush data: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in flush_cache: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        def health_check(res, req):
            """Simple health check endpoint."""
            from ...container import container
            import json

            try:
                # Check database connectivity
                db_status = "ok"
                try:
                    # Try to get a connection from pool
                    conn = container.get_db_connection()
                    container.release_db_connection(conn)
                except Exception as e:
                    db_status = f"error: {str(e)[:50]}"

                response = {
                    "status": "healthy",
                    "timestamp": req.get_query('timestamp') or "unknown",
                    "database": db_status,
                    "version": "1.0.0"
                }

                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(response))

            except Exception as e:
                error_response = {
                    "status": "unhealthy",
                    "error": str(e)[:100]
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        # Register endpoints
        app.get('/health', health_check)
        app.post('/v1/cache/flush', flush_cache)
