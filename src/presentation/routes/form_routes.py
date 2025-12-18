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

"""Form integration routes."""

import json
from loguru import logger


class FormRoutes:
    """Routes for form integration."""

    def __init__(self, form_handler):
        self._form_handler = form_handler

    def register(self, app):
        """Register routes."""
        self._register_form_submit(app)
        self._register_lead_details(app)
        self._register_form_analytics(app)
        self._register_hot_leads(app)

    def _register_form_submit(self, app):
        """Register form submission route."""
        def submit_form(res, req):
            """Handle form submission."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse request body
                try:
                    # Try socketify's method first
                    raw_body = req.get_raw_body()
                    if raw_body:
                        body = json.loads(raw_body.decode('utf-8') if isinstance(raw_body, bytes) else raw_body)
                    else:
                        body = {}
                except (AttributeError, json.JSONDecodeError):
                    # Fallback - assume empty body
                    body = {}

                if not body:
                    error_response = {"status": "error", "message": "Request body is required"}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Extract form data and context
                form_data = body.get('form_data', {})
                campaign_id = body.get('campaign_id')
                click_id = body.get('click_id')

                # Get IP address and user agent
                ip_address = req.get_header('x-forwarded-for') or req.get_header('x-real-ip') or '127.0.0.1'
                user_agent = req.get_header('user-agent') or ''
                referrer = req.get_header('referer') or None

                # Submit form through handler
                result = self._form_handler.submit_form(
                    form_data=form_data,
                    campaign_id=campaign_id,
                    click_id=click_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Determine HTTP status code
                status_code = 200
                if result["status"] == "duplicate":
                    status_code = 409  # Conflict
                elif result["status"] == "spam":
                    status_code = 400  # Bad Request
                elif result["status"] == "error":
                    status_code = 500

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(status_code)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in form submission: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.post('/forms/submit', submit_form)

    def _register_lead_details(self, app):
        """Register lead details route."""
        def get_lead_details(res, req):
            """Get detailed information about a lead."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Get lead_id from URL path
                lead_id = req.get_parameter(0)  # Assuming URL like /forms/lead/{lead_id}

                if not lead_id:
                    error_response = {"status": "error", "message": "Lead ID is required"}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Get lead details from handler
                result = self._form_handler.get_lead_details(lead_id)

                status_code = 200 if result["status"] == "success" else 404
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(status_code)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error getting lead details: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/forms/lead/{lead_id}', get_lead_details)

    def _register_form_analytics(self, app):
        """Register form analytics route."""
        def get_form_analytics(res, req):
            """Get form submission analytics."""
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

                # Get form analytics from handler
                result = self._form_handler.get_form_analytics(start_date=start_dt, end_date=end_dt)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in form analytics: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/forms/analytics', get_form_analytics)

    def _register_hot_leads(self, app):
        """Register hot leads route."""
        def get_hot_leads(res, req):
            """Get hot leads above score threshold."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters
                query = req.get_query()
                score_threshold = int(query.get('score_threshold', 70))
                limit = int(query.get('limit', 50))

                # Get hot leads from handler
                result = self._form_handler.get_hot_leads(score_threshold=score_threshold, limit=limit)

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error getting hot leads: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/forms/hot-leads', get_hot_leads)
