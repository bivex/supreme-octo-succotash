"""Customer journey analysis routes."""

import json
from loguru import logger
from ...application.handlers.analyze_journey_handler import AnalyzeJourneyHandler


class JourneyRoutes:
    """Routes for customer journey analysis."""

    def __init__(self, analyze_journey_handler: AnalyzeJourneyHandler):
        self.analyze_journey_handler = analyze_journey_handler

    def register(self, app):
        """Register routes."""
        self._register_journey_funnel(app)
        self._register_drop_off_analysis(app)

    def _register_journey_funnel(self, app):
        """Register journey funnel analysis route."""
        def get_journey_funnel(res, req):
            """Get customer journey funnel analysis."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters
                campaign_id_str = req.get_query('campaign_id')
                campaign_id = int(campaign_id_str) if campaign_id_str else None

                days_str = req.get_query('days')
                days = int(days_str) if days_str else 30

                # Get funnel analysis
                result = self.analyze_journey_handler.get_journey_funnel(campaign_id, days)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in journey funnel: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/journeys/funnel', get_journey_funnel)

    def _register_drop_off_analysis(self, app):
        """Register drop-off analysis route."""
        def get_drop_off_analysis(res, req):
            """Get customer journey drop-off analysis."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters
                campaign_id_str = req.get_query('campaign_id')
                campaign_id = int(campaign_id_str) if campaign_id_str else None

                days_str = req.get_query('days')
                days = int(days_str) if days_str else 30

                # Get drop-off analysis
                result = self.analyze_journey_handler.get_drop_off_analysis(campaign_id, days)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in drop-off analysis: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/journeys/drop-off', get_drop_off_analysis)
