"""Analytics HTTP routes."""

import json
from loguru import logger
from ...application.handlers.analytics_handler import AnalyticsHandler


class AnalyticsRoutes:
    """Socketify routes for analytics operations."""

    def __init__(self, analytics_handler: AnalyticsHandler):
        self.analytics_handler = analytics_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_real_time_analytics(app)

    def _register_real_time_analytics(self, app):
        """Register real-time analytics route."""
        def get_real_time_analytics(res, req):
            """Get real-time analytics data for the last 5 minutes."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                logger.info("Fetching real-time analytics data")

                # Get real-time analytics data
                result = self.analytics_handler.get_real_time_analytics()

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error getting real-time analytics: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the real-time analytics endpoint
        app.get('/v1/analytics/real-time', get_real_time_analytics)
