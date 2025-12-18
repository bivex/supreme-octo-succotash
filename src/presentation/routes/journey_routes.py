# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:07
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

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
        self._register_populate_journeys(app)

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

    def _register_populate_journeys(self, app):
        """Register populate journeys route."""
        def populate_journeys(res, req):
            """Populate journey data from clicks and impressions."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                campaign_id_str = req.get_query('campaign_id')
                campaign_id = int(campaign_id_str) if campaign_id_str else None

                # Get click and impression data from repositories
                click_data = []
                impression_data = []

                try:
                    # Get click repository
                    from ...container import container
                    click_repo = container.get_click_repository()

                    # Get clicks for campaign (limit for performance)
                    if campaign_id:
                        clicks = click_repo.find_by_campaign_id(campaign_id, limit=1000)
                        click_data = [
                            {
                                'id': click.id,
                                'campaign_id': click.campaign_id,
                                'ip_address': click.ip_address,
                                'user_agent': click.user_agent,
                                'referrer': click.referrer,
                                'created_at': click.created_at
                            }
                            for click in clicks
                        ]
                except Exception as e:
                    logger.warning(f"Could not load click data: {e}")

                try:
                    # Get impression repository
                    impression_repo = container.get_impression_repository()

                    # Get impressions for campaign (limit for performance)
                    if campaign_id:
                        impressions = impression_repo.find_by_campaign_id(str(campaign_id), limit=1000)
                        impression_data = [
                            {
                                'id': impression.id,
                                'campaign_id': impression.campaign_id,
                                'ip_address': impression.ip_address,
                                'user_agent': impression.user_agent,
                                'referrer': impression.referrer,
                                'created_at': impression.created_at
                            }
                            for impression in impressions
                        ]
                except Exception as e:
                    logger.warning(f"Could not load impression data: {e}")

                # Populate journeys
                result = self.analyze_journey_handler.populate_journeys_from_data(
                    click_data, impression_data
                )

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in populate journeys: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.post('/journeys/populate', populate_journeys)
