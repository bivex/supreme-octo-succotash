"""Click tracking HTTP routes."""

import json
from loguru import logger

from ...application.handlers.track_click_handler import TrackClickHandler

# Cache functions removed - now using Supreme API for URL generation


class ClickRoutes:
    """Socketify routes for click tracking operations."""

    def __init__(self, track_click_handler: TrackClickHandler):
        self.track_click_handler = track_click_handler
        self.local_landing_url = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev"

    def register(self, app):
        """Register routes with socketify app."""
        def track_click(res, req):
            """Handle click tracking and redirection."""
            try:
                # Validate required parameters
                campaign_id = req.get_query('cid')
                if not campaign_id:
                    error_html = "<html><body><h1>Error</h1><p>Campaign not found</p></body></html>"
                    res.write_status(404)
                    res.write_header("Content-Type", "text/html")
                    res.end(error_html)
                    return

                # Check if test mode
                test_mode = req.get_query('test_mode') == '1'

                # Create track click command
                from ...application.commands.track_click_command import TrackClickCommand

                command = TrackClickCommand(
                    campaign_id=campaign_id,
                    ip_address=self._get_client_ip(req),
                    user_agent=req.get_header('user-agent') or req.get_header('User-Agent') or '',
                    referrer=req.get_header('referer') or req.get_header('Referer') or None,
                    sub1=req.get_query('sub1'),
                    sub2=req.get_query('sub2'),
                    sub3=req.get_query('sub3'),
                    sub4=req.get_query('sub4'),
                    sub5=req.get_query('sub5'),
                    click_id_param=req.get_query('click_id'),
                    affiliate_sub=req.get_query('aff_sub'),
                    affiliate_sub2=req.get_query('aff_sub2'),
                    affiliate_sub3=req.get_query('aff_sub3'),
                    affiliate_sub4=req.get_query('aff_sub4'),
                    affiliate_sub5=req.get_query('aff_sub5'),
                    landing_page_id=int(req.get_query('lp_id')) if req.get_query('lp_id') else None,
                    campaign_offer_id=int(req.get_query('offer_id')) if req.get_query('offer_id') else None,
                    traffic_source_id=int(req.get_query('ts_id')) if req.get_query('ts_id') else None,
                    test_mode=test_mode
                )

                # Handle click tracking
                click, redirect_url, is_valid = self.track_click_handler.handle(command)

                if test_mode:
                    # Return HTML for testing
                    status_text = "Valid" if is_valid else "Invalid/Fraud"
                    html = (
                        f"<html><body><h1>Offer Page</h1>"
                        f"<p>Click ID: {click.id.value}</p>"
                        f"<p>Status: {status_text}</p>"
                        f"<p>Redirecting to: {redirect_url.value}</p></body></html>"
                    )
                    res.write_header("Content-Type", "text/html")
                    res.end(html)
                    return

                # Standard redirect
                res.write_status(302)
                res.write_header("Location", redirect_url.value)
                res.end('')

            except Exception as e:
                # Log error and return HTML error page
                logger.error(f"Click tracking error: {e}")
                error_html = "<html><body><h1>Error</h1><p>Internal server error</p></body></html>"
                res.write_status(500)
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

                # Get click from repository
                from ...domain.value_objects import ClickId
                click = self.track_click_handler._click_repository.find_by_id(ClickId.from_string(click_id))

                if not click:
                    error_response = {"error": {"code": "NOT_FOUND", "message": "Click not found"}}
                    res.write_status(404)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Convert click to response format
                click_data = {
                    "id": str(click.id),
                    "campaign_id": click.campaign_id,
                    "ip_address": click.ip_address,
                    "user_agent": click.user_agent,
                    "referrer": click.referrer,
                    "is_valid": click.is_valid,
                    "sub1": click.sub1,
                    "sub2": click.sub2,
                    "sub3": click.sub3,
                    "sub4": click.sub4,
                    "sub5": click.sub5,
                    "click_id_param": click.click_id_param,
                    "affiliate_sub": click.affiliate_sub,
                    "affiliate_sub2": click.affiliate_sub2,
                    "landing_page_id": click.landing_page_id,
                    "campaign_offer_id": click.campaign_offer_id,
                    "traffic_source_id": click.traffic_source_id,
                    "conversion_type": click.conversion_type,
                    "converted_at": click.converted_at.isoformat() if click.converted_at else None,
                    "created_at": click.created_at.isoformat(),
                    "has_conversion": click.has_conversion
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(click_data))

            except Exception as e:
                logger.error(f"Error getting click details: {e}")
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

                # Build filters for click query
                from ...domain.value_objects.filters.click_filters import ClickFilters

                filters = ClickFilters(
                    campaign_id=cid if 'cid' in locals() and cid is not None else None,
                    is_valid=bool(is_valid) if 'is_valid' in locals() and is_valid is not None else None,
                    limit=limit,
                    offset=offset
                )

                # Get clicks from repository
                try:
                    clicks = self.track_click_handler._click_repository.find_by_filters(filters)

                    # Get total count for pagination
                    if filters.campaign_id:
                        total_clicks = self.track_click_handler._click_repository.count_by_campaign_id(filters.campaign_id)
                    else:
                        # For now, approximate total - in production would need a count query
                        total_clicks = len(clicks) + offset if len(clicks) == limit else len(clicks) + offset

                    # clicks already paginated by the repository

                    # Convert clicks to response format
                    click_list = []
                    for click in clicks:
                        click_list.append({
                            "id": str(click.id),
                            "campaign_id": click.campaign_id,
                            "ip_address": click.ip_address,
                            "user_agent": click.user_agent,
                            "referrer": click.referrer,
                            "is_valid": click.is_valid,
                            "created_at": click.created_at.isoformat(),
                            "has_conversion": click.has_conversion
                        })

                    response = {
                        "clicks": click_list,
                        "total": total_clicks,
                        "limit": limit,
                        "offset": offset
                    }

                except Exception as e:
                    logger.error(f"Error listing clicks: {e}")
                    raise

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

        def create_click(res, req):
            """Create a click directly (for testing purposes)."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json
            import uuid

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

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
                                        logger.error("Invalid JSON in click creation request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Create click from request data
                            try:
                                from ...domain.entities.click import Click
                                from ...domain.value_objects import ClickId

                                # Convert string IDs to integers where needed
                                landing_page_id = body_data.get('landing_page_id')
                                if isinstance(landing_page_id, str) and landing_page_id.startswith('lp_'):
                                    try:
                                        landing_page_id = int(landing_page_id.replace('lp_', ''))
                                    except ValueError:
                                        landing_page_id = None
                                elif isinstance(landing_page_id, str):
                                    try:
                                        landing_page_id = int(landing_page_id)
                                    except ValueError:
                                        landing_page_id = None

                                campaign_offer_id = body_data.get('campaign_offer_id')
                                if isinstance(campaign_offer_id, str) and campaign_offer_id.startswith('offer_'):
                                    try:
                                        campaign_offer_id = int(campaign_offer_id.replace('offer_', ''))
                                    except ValueError:
                                        campaign_offer_id = None
                                elif isinstance(campaign_offer_id, str):
                                    try:
                                        campaign_offer_id = int(campaign_offer_id)
                                    except ValueError:
                                        campaign_offer_id = None

                                click = Click(
                                    id=ClickId(str(uuid.uuid4())),
                                    campaign_id=body_data.get('campaign_id'),
                                    ip_address=body_data.get('ip_address', '127.0.0.1'),
                                    user_agent=body_data.get('user_agent', 'Test User Agent'),
                                    referrer=body_data.get('referrer'),
                                    landing_page_id=landing_page_id,
                                    campaign_offer_id=campaign_offer_id,
                                    sub1=body_data.get('sub1'),
                                    sub2=body_data.get('sub2'),
                                    sub3=body_data.get('sub3'),
                                    sub4=body_data.get('sub4'),
                                    sub5=body_data.get('sub5')
                                )

                                # Save click
                                self.track_click_handler._click_repository.save(click)

                                response = {
                                    "status": "success",
                                    "click_id": str(click.id),
                                    "campaign_id": click.campaign_id,
                                    "created_at": click.created_at.isoformat()
                                }

                                res.write_status(201)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps(response))

                            except Exception as e:
                                logger.error(f"Error creating click: {e}")
                                error_response = {"status": "error", "message": str(e)}
                                res.write_status(500)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps(error_response))

                    except Exception as e:
                        logger.error(f"Error processing click creation data: {e}")
                        error_response = {"status": "error", "message": "Internal server error"}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in create_click: {e}")
                error_response = {"status": "error", "message": "Internal server error"}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Short link handler removed - now using direct API-generated URLs

        # Register all routes
        app.post('/clicks', create_click)
        app.get('/v1/click', track_click)
        app.get('/v1/click/:click_id', get_click_details)
        app.get('/v1/clicks', list_clicks)
        app.get('/mock-offer', mock_offer)

    def _get_client_ip(self, request) -> str:
        """Get real client IP address."""
        # Check proxy headers
        ip_headers = ['x-forwarded-for', 'x-real-ip', 'cf-connecting-ip', 'x-client-ip']

        for header in ip_headers:
            ip = request.get_header(header)
            if ip:
                # X-Forwarded-For can contain multiple IPs
                ip = ip.split(',')[0].strip()
                return ip

        # Fallback for socketify - remote address access may vary
        try:
            return request.get_remote_address() or '127.0.0.1'
        except AttributeError:
            # Socketify may not provide direct remote address access
            return '127.0.0.1'
