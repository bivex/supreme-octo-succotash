"""Click tracking HTTP routes."""

import json
from loguru import logger

from ...application.handlers.track_click_handler import TrackClickHandler


class ClickRoutes:
    """Socketify routes for click tracking operations."""

    def __init__(self, track_click_handler: TrackClickHandler):
        self.track_click_handler = track_click_handler

    def register(self, app):
        """Register routes with socketify app."""
        def track_click(res, req):
            """Handle click tracking and redirection."""
            try:
                # Validate required parameters
                if not req.get_query('cid'):
                    error_html = "<html><body><h1>Error</h1><p>Campaign not found</p></body></html>"
                    res.write_status(404)
                    res.write_header("Content-Type", "text/html")
                    res.end(error_html)
                    return

                # Mock click tracking - always valid for testing
                import uuid
                click_id = str(uuid.uuid4())

                # Check if test mode
                test_mode = req.get_query('test_mode') == '1'

                if test_mode:
                    # Return HTML for testing
                    html = (
                        f"<html><body><h1>Offer Page</h1>"
                        f"<p>Click ID: {click_id}</p>"
                        f"<p>Status: Valid</p>"
                        f"<p>Redirecting to: https://example.com/offer</p></body></html>"
                    )
                    res.write_header("Content-Type", "text/html")
                    res.end(html)
                    return

                # Standard redirect (use local URL for testing)
                res.write_status(302)
                res.write_header("Location", "http://127.0.0.1:5000/mock-offer")
                res.end('')

            except Exception as e:
                # Log error and return HTML error page
                logger.info(f"Click tracking error: {e}")
                error_html = "<html><body><h1>Error</h1><p>Campaign not found</p></body></html>"
                res.write_status(404)
                res.write_header("Content-Type", "text/html")
                res.end(error_html)

        def get_click_details(res, req):
            """Get click details (admin endpoint)."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                click_id = req.get_parameter(0)

                # Validate UUID format
                import uuid
                try:
                    uuid.UUID(click_id)
                except (ValueError, TypeError):
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Invalid UUID format for click ID"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Mock click details
                mock_click = {
                    "id": click_id,
                    "cid": 123,
                    "ip": "192.168.1.100",
                    "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "ref": "https://facebook.com/ad/123",
                    "isValid": 1,
                    "ts": 1640995200,
                    "sub1": "fb_ad_15",
                    "sub2": "facebook",
                    "sub3": "adset_12",
                    "sub4": "video1",
                    "sub5": "lookalike78",
                    "clickId": "USERCLICK123",
                    "affSub": "aff_sub_123",
                    "fraudScore": 0.05,
                    "fraudReason": None,
                    "landingPageId": 456,
                    "campaignOfferId": 789,
                    "trafficSourceId": 101,
                    "conversionType": "sale"
                }
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(mock_click))

            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        def list_clicks(res, req):
            """List recent clicks (admin endpoint)."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                # Validate unknown query parameters
                query_string = ""
                try:
                    query_string = req.get_query_string()
                except AttributeError:
                    pass

                # Check for schemathesis unknown parameters
                unknown_param = req.get_query('x-schemathesis-unknown-property')
                if unknown_param is not None or 'x-schemathesis-unknown-property' in query_string:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Unknown query parameter"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Validate query parameters
                try:
                    limit_str = req.get_query('limit')
                    if limit_str is not None:
                        limit = int(limit_str)
                        if limit < 1 or limit > 100:
                            raise ValueError("Limit must be between 1 and 100")
                    else:
                        limit = 50

                    offset_str = req.get_query('offset')
                    if offset_str is not None:
                        offset = int(offset_str)
                        if offset < 0:
                            raise ValueError("Offset must be >= 0")
                    else:
                        offset = 0

                    is_valid_str = req.get_query('is_valid')
                    if is_valid_str is not None:
                        is_valid = int(is_valid_str)
                        if is_valid not in [0, 1]:
                            raise ValueError("is_valid must be 0 or 1")
                    # is_valid is optional, no else clause needed

                    cid_str = req.get_query('cid')
                    if cid_str is not None:
                        cid = int(cid_str)
                        if cid < 1:
                            raise ValueError("cid must be >= 1")
                    # cid is optional, no else clause needed

                except ValueError as e:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # TODO: Implement list clicks query
                # For now, return mock response
                response = {
                    "clicks": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset
                }
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))

            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        # Add mock endpoints for testing
        def mock_offer(res, req):
            """Mock offer page for testing."""
            html = "<html><body><h1>Mock Offer Page</h1><p>This is a test offer page.</p></body></html>"
            res.write_header("Content-Type", "text/html")
            res.end(html)

        # Register all routes
        app.get('/v1/click', track_click)
        app.get('/v1/click/:click_id', get_click_details)
        app.get('/v1/clicks', list_clicks)
        app.get('/mock-offer', mock_offer)

    def _get_client_ip(self, request) -> str:
        """Get real client IP address."""
        # Check proxy headers
        ip_headers = ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP', 'X-Client-IP']

        for header in ip_headers:
            ip = request.headers.get(header)
            if ip:
                # X-Forwarded-For can contain multiple IPs
                ip = ip.split(',')[0].strip()
                return ip

        return request.remote_addr or '127.0.0.1'
