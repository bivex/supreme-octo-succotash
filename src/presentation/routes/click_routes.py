# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:11
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Click tracking HTTP routes."""

import json
import os
import sys
from typing import Optional

from loguru import logger

from ...application.handlers.track_click_handler import TrackClickHandler

# Import shared URL shortener
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from shared_url_shortener import url_shortener, recover_unknown_code


# Cache functions removed - now using Supreme API for URL generation


class ClickRoutes:
    """Socketify routes for click tracking operations."""

    def __init__(self, track_click_handler: TrackClickHandler):
        self.track_click_handler = track_click_handler
        self.local_landing_url = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev"

        # Default URLs for campaigns that are not properly configured
        self.default_offer_url = "https://example.com/default-offer"
        self.default_safe_url = "https://example.com/default-safe"

    def register(self, app):
        """Register routes with socketify app."""
        logger.info(f"🔧 ClickRoutes.register() called with app: {type(app)}")

        async def track_click(res, req):
            """Handle click tracking and redirection."""
            logger.info("🔥 TRACK_CLICK HANDLER CALLED")
            try:
                logger.info("🔥 ENTERING TRY BLOCK")
                # Log incoming click request details
                user_agent = req.get_header('user-agent') or req.get_header('User-Agent') or 'Unknown'
                referrer = req.get_header('referer') or req.get_header('Referer') or 'Direct'
                client_ip = self._get_client_ip(req)
                logger.debug(f"Client IP after _get_client_ip: {client_ip}")

                logger.info("=== CLICK RECEIVED ===")
                logger.info(f"IP Address: {client_ip}")
                logger.info(f"User Agent: {user_agent}")
                logger.info(f"Referrer: {referrer}")

                # Extract only campaign_id and click_id from the URL
                campaign_id_param = req.get_query('cid')
                click_id_param = req.get_query('click_id')

                logger.info(f"Campaign ID from URL: {campaign_id_param}")
                logger.info(f"Click ID from URL: {click_id_param}")

                if not campaign_id_param or not click_id_param:
                    logger.warning("Missing required campaign_id or click_id parameter")
                    error_html = "<html><body><h1>Error</h1><p>Campaign or Click ID not found</p></body></html>"
                    res.write_status(404)
                    res.write_header("Content-Type", "text/html")
                    res.end(error_html)
                    return

                # Check if test mode
                test_mode = req.get_query('test_mode') == '1'
                logger.info(f"Test mode: {test_mode}")

                # Create track click command
                from ...application.commands.track_click_command import TrackClickCommand

                command = TrackClickCommand(
                    campaign_id=campaign_id_param,
                    click_id_param=click_id_param,
                    ip_address=client_ip if client_ip is not None else '127.0.0.1',
                    user_agent=user_agent,
                    referrer=referrer,
                    test_mode=test_mode
                    # Other parameters will be fetched from PreClickData inside the handler
                )

                logger.info("TrackClickCommand created successfully with short parameters")

                # Handle click tracking
                logger.info("Processing click through TrackClickHandler...")
                click, redirect_url, is_valid = await self.track_click_handler.handle(command)

                logger.info("=== CLICK PROCESSING RESULT ===")
                logger.info(f"Click ID: {click.id.value}")
                logger.info(f"Campaign ID: {click.campaign_id}")
                logger.info(f"Is Valid: {is_valid}")
                logger.info(f"Redirect URL: {redirect_url.value}")
                logger.info(f"Created At: {click.created_at.isoformat()}")

                # Check if we got fallback URL and campaign needs configuration
                if redirect_url.value == "http://localhost:5000/mock-safe-page":
                    logger.warning(f"Campaign {campaign_id_param} is not properly configured with offer/safe URLs")

                    if is_valid:
                        logger.warning(
                            f"VALID click for campaign {campaign_id_param} redirected to fallback - campaign needs proper URLs!")
                        logger.warning(
                            f"Set offer_page_url for campaign {campaign_id_param} via: PUT /v1/campaigns/{campaign_id_param}")
                    else:
                        logger.info(
                            f"Invalid/fraud click for campaign {campaign_id_param} - correctly using safe fallback")

                    # Provide helpful setup instructions
                    logger.warning("To configure campaign URLs:")
                    logger.warning(f"  curl -X PUT http://localhost:5000/v1/campaigns/{campaign_id_param} \\")
                    logger.warning("    -H 'Content-Type: application/json' \\")
                    logger.warning(
                        "    -d '{\"offer_page_url\": \"https://your-offer.com\", \"safe_page_url\": \"https://your-safe.com\"}'")

                if test_mode:
                    logger.info("Test mode: returning HTML response")
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
                logger.info(f"Redirecting user to: {redirect_url.value}")
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
                    error_response = {
                        "error": {"code": "VALIDATION_ERROR", "message": "Invalid UUID format for click ID"}}
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
                        total_clicks = self.track_click_handler._click_repository.count_by_campaign_id(
                            filters.campaign_id)
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

        def handle_short_link_redirect(res, req):
            """Handle short link redirection with encoded parameters."""
            try:
                short_code = req.get_parameter(0)
                logger.info("=== SHORT LINK REDIRECT ===")
                logger.info(f"Short code received: {short_code}")
                logger.info(f"Client IP: {self._get_client_ip(req)}")
                logger.info(f"User Agent: {req.get_header('user-agent') or 'Unknown'}")

                if not short_code:
                    logger.warning("Empty short code received")
                    error_html = "<html><body><h1>Error</h1><p>Invalid short link</p></body></html>"
                    res.write_status(404)
                    res.write_header("Content-Type", "text/html")
                    res.end(error_html)
                    return

                # Decode short link using new URLShortener
                try:
                    url_params = url_shortener.decode(short_code)

                    # If normal decoding fails, try recovery
                    if not url_params:
                        logger.warning(f"Normal decoding failed, trying recovery for: {short_code}")
                        url_params = recover_unknown_code(short_code)

                    if not url_params:
                        # Provide detailed diagnostic info
                        logger.warning(f"Failed to decode/recover short link: {short_code} (length: {len(short_code)})")

                        # Analyze the code structure
                        diagnostics = []
                        if short_code.startswith(('s', 'c', 'h')):
                            strategy = "Sequential" if short_code.startswith(
                                's') else "Compressed" if short_code.startswith('c') else "Hybrid"
                            diagnostics.append(f"Format: {strategy}")
                        else:
                            diagnostics.append("Format: Unknown (should start with s/c/h)")
                            diagnostics.append("This may be from a different URL shortener system")

                        # Check for common issues
                        if len(short_code) != 10:
                            diagnostics.append(f"Length: {len(short_code)} (expected 10 for current system)")
                        else:
                            diagnostics.append("Length: Correct (10 characters)")

                        if short_code.startswith('c'):
                            # Try to decode campaign_id
                            try:
                                campaign_code = short_code[1:2]
                                campaign_id = url_shortener._decode_base62(campaign_code)
                                diagnostics.append(f"Campaign ID: {campaign_id}")
                            except:
                                diagnostics.append("Campaign ID: Invalid base62 encoding")

                        # Log diagnostics
                        for diag in diagnostics:
                            logger.warning(f"  {diag}")

                        # Return informative error page
                        diag_html = "".join(f"<li>{d}</li>" for d in diagnostics)
                        error_html = f"""<html><body>
                        <h1>Short Link Error</h1>
                        <p>Unable to decode short link: <code>{short_code}</code></p>
                        <h2>Technical Details:</h2>
                        <ul>{diag_html}</ul>
                        <p><strong>Possible causes:</strong></p>
                        <ul>
                        <li>Old or corrupted link from previous system version</li>
                        <li>Link was truncated or modified</li>
                        <li>Link from different URL shortener service</li>
                        </ul>
                        <p>Please contact support with this code if you believe this is an error.</p>
                        </body></html>"""
                        res.write_status(404)
                        res.write_header("Content-Type", "text/html")
                        res.end(error_html)
                        return

                    # Reconstruct tracking URL from decoded parameters
                    params_dict = url_params.to_dict()
                    query_string = "&".join(f"{k}={v}" for k, v in params_dict.items() if v is not None)
                    tracking_url = f"{self.local_landing_url}/v1/click?{query_string}"

                    # Log successful decoding with details
                    strategy_info = url_shortener.get_strategy_info(short_code)
                    param_count = len([v for v in params_dict.values() if v is not None])

                    logger.info("=== SHORT LINK DECODED SUCCESSFULLY ===")
                    logger.info(f"Short code: {short_code}")
                    logger.info(f"Encoding strategy: {strategy_info}")
                    logger.info(f"Parameters count: {param_count}, Code length: {len(short_code)}")
                    logger.info("Decoded parameters:")
                    logger.info(f"  cid (campaign): {url_params.cid}")
                    logger.info(f"  sub1 (source): {url_params.sub1}")
                    logger.info(f"  sub2 (medium): {url_params.sub2}")
                    logger.info(f"  sub3 (campaign): {url_params.sub3}")
                    logger.info(f"  sub4 (user_id): {url_params.sub4}")
                    logger.info(f"  sub5 (content): {url_params.sub5}")
                    logger.info(f"  click_id: {url_params.click_id}")
                    logger.info(f"Final redirect URL: {tracking_url}")

                except Exception as decode_error:
                    logger.error(f"Error decoding short link {short_code}: {decode_error}")
                    error_html = f"""<html><body>
                    <h1>Decoding Error</h1>
                    <p>Failed to process short link: <code>{short_code}</code></p>
                    <p>Error: {str(decode_error)}</p>
                    </body></html>"""
                    res.write_status(400)
                    res.write_header("Content-Type", "text/html")
                    res.end(error_html)
                    return

                # Redirect to the click tracking endpoint
                res.write_status(302)
                res.write_header("Location", tracking_url)
                res.end('')

            except Exception as e:
                logger.error(f"Error handling short link redirect: {e}")
                error_html = "<html><body><h1>Error</h1><p>Internal server error</p></body></html>"
                res.write_status(500)
                res.write_header("Content-Type", "text/html")
                res.end(error_html)

        # Register all routes
        logger.info("🔧 Registering click routes with socketify app...")
        app.post('/clicks', create_click)
        logger.info("🔧 Registered POST /clicks")
        app.get('/v1/click', track_click)
        logger.info("🔧 Registered GET /v1/click")
        app.get('/v1/click/:click_id', get_click_details)
        logger.info("🔧 Registered GET /v1/click/:click_id")
        app.get('/v1/clicks', list_clicks)
        logger.info("🔧 Registered GET /v1/clicks")
        app.get('/s/:encoded_data', handle_short_link_redirect)
        logger.info("🔧 Registered GET /s/:encoded_data")
        app.get('/mock-offer', mock_offer)
        logger.info("🔧 Registered GET /mock-offer")

        logger.info("✅ Click routes registration completed")

    def _safe_int_convert(self, value) -> Optional[int]:
        """Safely convert value to int, handling various formats."""
        if not value:
            return None

        # Handle string values
        if isinstance(value, str):
            # Remove common prefixes like 'lp_', 'offer_', etc.
            clean_value = value.strip()
            if clean_value.startswith(('lp_', 'offer_', 'ts_')):
                clean_value = clean_value.split('_', 1)[1] if '_' in clean_value else clean_value

            try:
                return int(clean_value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert '{value}' to int")
                return None

        # Handle numeric values
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert '{value}' (type: {type(value)}) to int")
            return None

    def _safe_int_convert(self, value) -> Optional[int]:
        """Safely convert value to int, handling various formats."""
        if not value:
            return None

        # Handle string values
        if isinstance(value, str):
            # Remove common prefixes like 'lp_', 'offer_', etc.
            clean_value = value.strip()
            if clean_value.startswith(('lp_', 'offer_', 'ts_')):
                clean_value = clean_value.split('_', 1)[1] if '_' in clean_value else clean_value

            try:
                return int(clean_value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert '{value}' to int")
                return None

        # Handle numeric values
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert '{value}' (type: {type(value)}) to int")
            return None

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
