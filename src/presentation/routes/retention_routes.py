# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:06
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Retention campaign routes."""

import json
from loguru import logger


class RetentionRoutes:
    """Routes for retention campaigns."""

    def __init__(self, retention_handler):
        self._retention_handler = retention_handler

    def register(self, app):
        """Register routes."""
        self._register_retention_campaigns(app)
        self._register_campaign_performance(app)
        self._register_user_retention_analysis(app)
        self._register_retention_analytics(app)

    def _register_retention_campaigns(self, app):
        """Register retention campaigns route."""
        def get_retention_campaigns(res, req):
            """Get retention campaigns."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters
                query = req.get_query()
                status_filter = query.get('status')

                # Get retention campaigns from handler
                result = self._retention_handler.get_retention_campaigns(status_filter=status_filter)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in retention campaigns: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/retention/campaigns', get_retention_campaigns)

    def _register_campaign_performance(self, app):
        """Register campaign performance route."""
        def get_campaign_performance(res, req):
            """Get performance data for a specific campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Get campaign_id from URL path
                campaign_id = req.get_parameter(0)  # Assuming URL like /retention/campaign/{campaign_id}/performance

                if not campaign_id:
                    error_response = {"status": "error", "message": "Campaign ID is required"}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Get campaign performance from handler
                result = self._retention_handler.get_campaign_performance(campaign_id)

                status_code = 200 if result["status"] == "success" else 404
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(status_code)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error getting campaign performance: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/retention/campaign/{campaign_id}/performance', get_campaign_performance)

    def _register_user_retention_analysis(self, app):
        """Register user retention analysis route."""
        def get_user_retention_analysis(res, req):
            """Analyze retention profile for a specific user."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Get customer_id from URL path
                customer_id = req.get_parameter(0)  # Assuming URL like /retention/user/{customer_id}/analysis

                if not customer_id:
                    error_response = {"status": "error", "message": "Customer ID is required"}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Get user retention analysis from handler
                result = self._retention_handler.analyze_user_retention(customer_id)

                status_code = 200 if result["status"] == "success" else 404
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(status_code)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in user retention analysis: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/retention/user/{customer_id}/analysis', get_user_retention_analysis)

    def _register_retention_analytics(self, app):
        """Register retention analytics route."""
        def get_retention_analytics(res, req):
            """Get retention analytics data."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters for date range
                query = req.get_query()
                start_date = query.get('start_date')
                end_date = query.get('end_date')

                # Convert string dates to datetime if provided
                start_dt = None
                end_dt = None
                if start_date:
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if end_date:
                    from datetime import datetime
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                # Get retention analytics from handler
                result = self._retention_handler.get_retention_analytics(start_date=start_dt, end_date=end_dt)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in retention analytics: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/retention/analytics', get_retention_analytics)
