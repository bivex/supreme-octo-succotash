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

"""LTV tracking routes."""

import json
from loguru import logger


class LtvRoutes:
    """Routes for LTV tracking."""

    def __init__(self, ltv_handler):
        self._ltv_handler = ltv_handler

    def register(self, app):
        """Register routes."""
        self._register_ltv_analysis(app)
        self._register_customer_ltv_details(app)
        self._register_ltv_segments(app)

    def _register_ltv_analysis(self, app):
        """Register LTV analysis route."""
        def get_ltv_analysis(res, req):
            """Get LTV analysis."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters for date range
                from urllib.parse import parse_qs, urlparse
                url = req.get_url()
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)

                start_date = query_params.get('start_date', [None])[0]
                end_date = query_params.get('end_date', [None])[0]

                # Convert string dates to datetime if provided
                start_dt = None
                end_dt = None
                if start_date:
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if end_date:
                    from datetime import datetime
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                # Get LTV analysis from handler
                result = self._ltv_handler.get_ltv_analysis(start_date=start_dt, end_date=end_dt)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in LTV analysis: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/ltv/analysis', get_ltv_analysis)

    def _register_customer_ltv_details(self, app):
        """Register customer LTV details route."""
        def get_customer_ltv_details(res, req):
            """Get detailed LTV information for a specific customer."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Get customer_id from URL path
                customer_id = req.get_parameter(0)  # Assuming URL like /ltv/customer/{customer_id}

                if not customer_id:
                    error_response = {"status": "error", "message": "Customer ID is required"}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Get customer LTV details from handler
                result = self._ltv_handler.get_customer_ltv_details(customer_id)

                status_code = 200 if result["status"] == "success" else 404
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(status_code)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error getting customer LTV details: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/ltv/customer/{customer_id}', get_customer_ltv_details)

    def _register_ltv_segments(self, app):
        """Register LTV segments overview route."""
        def get_ltv_segments(res, req):
            """Get overview of LTV segments."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Get LTV segments overview from handler
                result = self._ltv_handler.get_ltv_segments_overview()

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error getting LTV segments: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/ltv/segments', get_ltv_segments)
