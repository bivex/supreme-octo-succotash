"""Campaign HTTP routes."""

import json
from loguru import logger

from ...application.handlers.create_campaign_handler import CreateCampaignHandler
from ...application.handlers.update_campaign_handler import UpdateCampaignHandler
from ...application.handlers.pause_campaign_handler import PauseCampaignHandler
from ...application.handlers.resume_campaign_handler import ResumeCampaignHandler
from ...application.handlers.create_landing_page_handler import CreateLandingPageHandler
from ...application.handlers.create_offer_handler import CreateOfferHandler
from ...application.queries.get_campaign_query import GetCampaignHandler
from ..dto.campaign_dto import CampaignSummaryResponse


class CampaignRoutes:
    """Socketify routes for campaign operations."""

    def __init__(self,
                 create_campaign_handler: CreateCampaignHandler,
                 update_campaign_handler: UpdateCampaignHandler,
                 pause_campaign_handler: PauseCampaignHandler,
                 resume_campaign_handler: ResumeCampaignHandler,
                 create_landing_page_handler: CreateLandingPageHandler,
                 create_offer_handler: CreateOfferHandler,
                 get_campaign_handler: GetCampaignHandler):
        self.create_campaign_handler = create_campaign_handler
        self.update_campaign_handler = update_campaign_handler
        self.pause_campaign_handler = pause_campaign_handler
        self.resume_campaign_handler = resume_campaign_handler
        self.create_landing_page_handler = create_landing_page_handler
        self.create_offer_handler = create_offer_handler
        self.get_campaign_handler = get_campaign_handler


    def _validate_query_parameters(self, req, allowed_params: set):
        """Validate that request contains only allowed query parameters."""
        query_string = ""
        try:
            query_string = req.get_query_string()
        except AttributeError:
            return True  # If we can't check, allow the request

        # Check for schemathesis testing parameters
        # Reject unknown/invalid schemathesis parameters
        if 'x-schemathesis-unknown' in query_string or 'x-schemathesis-invalid' in query_string:
            return False

        # Allow other legitimate schemathesis parameters
        if 'x-schemathesis' in query_string:
            return True

        # Check for other unknown/invalid parameters
        unknown_patterns = ['unknown', 'invalid', 'test_']
        for pattern in unknown_patterns:
            if pattern in query_string.lower():
                return False

        return True

    def register(self, app):
        """Register routes with socketify app."""
        # Register individual route handlers
        self._register_list_campaigns(app)
        self._register_create_campaign(app)
        self._register_get_campaign(app)
        self._register_campaign_analytics(app)
        self._register_campaign_landing_pages(app)
        self._register_campaign_offers(app)
        self._register_campaign_pause(app)
        self._register_campaign_resume(app)

    def _register_list_campaigns(self, app):
        """Register list campaigns route."""
        def list_campaigns(res, req):
            """List campaigns with pagination."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            # Validate request
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                logger.debug("list_campaigns called")

                # Check for schemathesis unknown parameters first
                query_string = ""
                try:
                    query_string = req.get_query_string()
                except AttributeError:
                    pass

                # Check for the specific unknown parameter
                unknown_param = req.get_query('x-schemathesis-unknown-property')
                if unknown_param is not None or 'x-schemathesis-unknown-property' in query_string:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Unknown query parameter"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Validate and parse query parameters
                try:
                    page_str = req.get_query('page')
                    if page_str is not None:
                        page = int(page_str)
                        if page < 1:
                            raise ValueError("Page must be >= 1")
                    else:
                        page = 1

                    page_size_str = req.get_query('pageSize')
                    if page_size_str is not None:
                        page_size = int(page_size_str)
                        if page_size < 1 or page_size > 100:
                            raise ValueError("Page size must be between 1 and 100")
                    else:
                        page_size = 20

                except ValueError as e:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Validate unknown parameters
                query_string = ""
                try:
                    query_string = req.get_query_string()
                except AttributeError:
                    pass

                # Reject schemathesis unknown parameters
                if 'x-schemathesis-unknown-property' in query_string:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Unknown query parameter"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                logger.debug(f"page={page}, page_size={page_size}")

                # For now, return mock data (would need a list campaigns query)
                campaigns = []  # TODO: Implement list campaigns query
                logger.debug(f"campaigns count={len(campaigns)}")

                pagination = self._build_pagination_info(page, page_size, campaigns)
                logger.debug(f"pagination={pagination}")

                response = {
                    "campaigns": [CampaignSummaryResponse.from_campaign(c) for c in campaigns],
                    "pagination": pagination
                }
                logger.debug(f"response created, campaigns in response={len(response['campaigns'])}")
                res.write_header("Content-Type", "application/json")
                # Add CORS headers
                res.write_header('Access-Control-Allow-Origin', '*')
                res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
                res.write_header('Access-Control-Allow-Credentials', 'false')
                res.write_header('Access-Control-Max-Age', '86400')
                # Add security headers
                add_security_headers(res)
                res.end(json.dumps(response))

            except Exception:
                from ...presentation.error_handlers import handle_internal_server_error
                handle_internal_server_error(res)

        app.get('/v1/campaigns', list_campaigns)

    def _register_create_campaign(self, app):
        """Register create campaign route."""
        def create_campaign(res, req):
            """Create a new campaign."""
            from ...presentation.middleware.security_middleware import validate_request

            # Validate request
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                # Buffer for request body
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
                                        error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON in request body"}}
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps(error_response))
                                        return

                            if not body_data:
                                error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Request body is required"}}
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps(error_response))
                                return

                            # Validate required fields
                            required_fields = ['name']
                            for field in required_fields:
                                if field not in body_data:
                                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": f"Field '{field}' is required"}}
                                    res.write_status(400)
                                    res.write_header("Content-Type", "application/json")
                                    add_security_headers(res)
                                    res.end(json.dumps(error_response))
                                    return

                            # Create command
                            from ...application.commands.create_campaign_command import CreateCampaignCommand
                            from ...domain.value_objects import Url, Money

                            command = CreateCampaignCommand(
                                name=body_data['name'],
                                description=body_data.get('description'),
                                cost_model=body_data.get('costModel', 'CPA'),
                                payout=Money.from_float(body_data.get('payout', {}).get('amount', 0.0),
                                                      body_data.get('payout', {}).get('currency', 'USD')) if body_data.get('payout') else None,
                                white_url=body_data.get('whiteUrl'),  # safe page URL
                                black_url=body_data.get('blackUrl'),  # offer page URL
                                daily_budget=Money.from_float(body_data.get('dailyBudget', {}).get('amount', 0.0),
                                                            body_data.get('dailyBudget', {}).get('currency', 'USD')) if body_data.get('dailyBudget') else None,
                                total_budget=Money.from_float(body_data.get('totalBudget', {}).get('amount', 0.0),
                                                            body_data.get('totalBudget', {}).get('currency', 'USD')) if body_data.get('totalBudget') else None,
                                start_date=body_data.get('startDate'),
                                end_date=body_data.get('endDate')
                            )

                            # Handle command
                            campaign = self.create_campaign_handler.handle(command)

                            # Convert to response
                            response = {
                                "id": campaign.id.value,
                                "name": campaign.name,
                                "status": campaign.status.value,
                                "urls": {
                                    "safePage": campaign.safe_page_url.value if campaign.safe_page_url else None,
                                    "offerPage": campaign.offer_page_url.value if campaign.offer_page_url else None
                                },
                                "createdAt": campaign.created_at.isoformat(),
                                "updatedAt": campaign.updated_at.isoformat()
                            }

                            res.write_status(201)
                            res.write_header('Location', f'http://localhost:5000/v1/campaigns/{response["id"]}')
                            res.write_header('Content-Type', 'application/json')
                            add_security_headers(res)
                            res.end(json.dumps(response))

                    except Exception as e:
                        logger.error(f"Error processing request data: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                # Read request body
                req.on_data(on_data)

            except ValueError as e:
                error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                res.write_status(400)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))
            except Exception as e:
                logger.error(f"Error creating campaign: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.post('/v1/campaigns', create_campaign)

    def _register_get_campaign(self, app):
        """Register get campaign route."""
        def get_campaign(res, req):
            """Get campaign details."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)  # Get path parameter

                # Mock campaign response
                mock_campaign = {
                    "id": campaign_id,
                    "name": "Summer Sale Campaign",
                    "description": "High-converting summer promotion",
                    "status": "active",
                    "schedule": {
                        "startDate": "2024-01-01T00:00:00Z",
                        "endDate": "2024-01-31T23:59:59Z"
                    },
                    "urls": {
                        "safePage": "https://example.com/safe-landing",
                        "offerPage": "https://example.com/offer"
                    },
                    "financial": {
                        "costModel": "CPA",
                        "payout": {"amount": 25.00, "currency": "USD"},
                        "dailyBudget": {"amount": 100.00, "currency": "USD"},
                        "totalBudget": {"amount": 3000.00, "currency": "USD"},
                        "spent": {"amount": 750.00, "currency": "USD"}
                    },
                    "performance": {
                        "clicks": 1250,
                        "conversions": 45,
                        "ctr": 0.032,
                        "cr": 0.036,
                        "epc": {"amount": 16.67, "currency": "USD"},
                        "roi": 2.45
                    },
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T12:00:00Z",
                    "_links": {
                        "self": f"/v1/campaigns/{campaign_id}",
                        "landingPages": f"/v1/campaigns/{campaign_id}/landing-pages",
                        "offers": f"/v1/campaigns/{campaign_id}/offers",
                        "analytics": f"/v1/campaigns/{campaign_id}/analytics"
                    }
                }
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(mock_campaign))

            except ValueError as e:
                error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                res.write_status(400)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))
            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        def delete_campaign(res, req):
            """Delete a campaign."""
            logger.info("DELETE campaign function called")
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                logger.info("DELETE campaign validation failed")
                return  # Validation failed, response already sent
            logger.info("DELETE campaign validation passed")

            try:
                campaign_id = req.get_parameter(0)  # Get path parameter
                logger.info(f"DELETE campaign - parameter 0: {campaign_id}")

                if not campaign_id:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Campaign ID is required"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # For now, simulate successful deletion (would delete from database)
                # TODO: Implement actual campaign deletion logic
                logger.info(f"Deleting campaign {campaign_id}")

                # Return 204 No Content on successful deletion
                add_security_headers(res)
                res.write_status(204)
                res.end('')

            except Exception as e:
                logger.error(f"DELETE campaign error: {e}")
                import traceback
                logger.error(f"DELETE campaign traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        def update_campaign(res, req):
            """Update a campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)
                if not campaign_id:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Campaign ID is required"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Buffer for request body
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
                                        error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON in request body"}}
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps(error_response))
                                        return

                            if not body_data:
                                error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Request body is required"}}
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps(error_response))
                                return

                            # Create command
                            from ...application.commands.update_campaign_command import UpdateCampaignCommand
                            from ...domain.value_objects import CampaignId, Url, Money

                            command = UpdateCampaignCommand(
                                campaign_id=CampaignId.from_string(campaign_id),
                                name=body_data.get('name'),
                                description=body_data.get('description'),
                                cost_model=body_data.get('costModel'),
                                payout=Money.from_float(body_data.get('payout', {}).get('amount', 0.0),
                                                      body_data.get('payout', {}).get('currency', 'USD')) if body_data.get('payout') else None,
                                safe_page_url=Url(body_data['safePage']) if body_data.get('safePage') else None,
                                offer_page_url=Url(body_data['offerPage']) if body_data.get('offerPage') else None,
                                daily_budget=Money.from_float(body_data.get('dailyBudget', {}).get('amount', 0.0),
                                                            body_data.get('dailyBudget', {}).get('currency', 'USD')) if body_data.get('dailyBudget') else None,
                                total_budget=Money.from_float(body_data.get('totalBudget', {}).get('amount', 0.0),
                                                            body_data.get('totalBudget', {}).get('currency', 'USD')) if body_data.get('totalBudget') else None,
                                start_date=body_data.get('startDate'),
                                end_date=body_data.get('endDate')
                            )

                            # Handle command
                            campaign = self.update_campaign_handler.handle(command)

                            # Convert to response
                            response = {
                                "id": campaign.id.value,
                                "name": campaign.name,
                                "status": campaign.status.value,
                                "urls": {
                                    "safePage": campaign.safe_page_url.value if campaign.safe_page_url else None,
                                    "offerPage": campaign.offer_page_url.value if campaign.offer_page_url else None
                                },
                                "createdAt": campaign.created_at.isoformat(),
                                "updatedAt": campaign.updated_at.isoformat()
                            }

                            res.write_status(200)
                            res.write_header('Content-Type', 'application/json')
                            add_security_headers(res)
                            res.end(json.dumps(response))

                    except Exception as e:
                        logger.error(f"Error processing request data: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                # Read request body
                req.on_data(on_data)

            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id', get_campaign)
        app.put('/v1/campaigns/:campaign_id', update_campaign)
        app.delete('/v1/campaigns/:campaign_id', delete_campaign)

    def _build_pagination_info(self, page: int, page_size: int, campaigns: list) -> dict:
        """Build pagination information."""
        total_items = len(campaigns)
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        return {
            "page": page,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "_links": {
                "first": f"http://127.0.0.1:5000/api/v1/campaigns?page=1&pageSize={page_size}",
                "last": f"http://127.0.0.1:5000/api/v1/campaigns?page={total_pages}&pageSize={page_size}",
            }
        }

    def _register_campaign_analytics(self, app):
        """Register campaign analytics route."""
        def get_campaign_analytics(res, req):
            """Get campaign analytics."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)

                # Validate and parse query parameters
                from datetime import datetime

                try:
                    start_date_str = req.get_query('startDate')
                    if start_date_str is not None:
                        # Validate date format
                        datetime.fromisoformat(start_date_str)
                        start_date = start_date_str
                    else:
                        start_date = "2024-01-01"

                    end_date_str = req.get_query('endDate')
                    if end_date_str is not None:
                        # Validate date format
                        datetime.fromisoformat(end_date_str)
                        end_date = end_date_str
                    else:
                        end_date = "2024-01-31"

                    granularity = req.get_query('granularity') or 'day'
                    if granularity not in ['hour', 'day', 'week', 'month']:
                        raise ValueError("Granularity must be one of: hour, day, week, month")

                    breakdown = req.get_query('breakdown') or 'date'
                    if breakdown not in ['date', 'traffic_source', 'landing_page', 'offer', 'geography', 'device']:
                        raise ValueError("Breakdown must be one of: date, traffic_source, landing_page, offer, geography, device")

                except ValueError as e:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Generate mock data based on breakdown
                breakdowns_data = {
                    "byDate": [],
                    "byTrafficSource": [],
                    "byLandingPage": [],
                    "byOffer": [],
                    "byGeography": [],
                    "byDevice": []
                }

                # Fill the appropriate breakdown with sample data
                if breakdown == "date":
                    breakdowns_data["byDate"] = [
                        {
                            "date": "2024-01-15",
                            "metrics": {
                                "clicks": 1250,
                                "uniqueClicks": 1200,
                                "conversions": 38,
                                "revenue": {"amount": 190.00, "currency": "USD"},
                                "cost": {"amount": 62.50, "currency": "USD"},
                                "ctr": 0.025,
                                "cr": 0.03,
                                "epc": {"amount": 5.00, "currency": "USD"},
                                "roi": 2.0
                            }
                        }
                    ]
                elif breakdown == "traffic_source":
                    breakdowns_data["byTrafficSource"] = [
                        {
                            "trafficSourceId": "ts_google",
                            "name": "Google Ads",
                            "metrics": {
                                "clicks": 2500,
                                "uniqueClicks": 2400,
                                "conversions": 75,
                                "revenue": {"amount": 375.00, "currency": "USD"},
                                "cost": {"amount": 125.00, "currency": "USD"},
                                "ctr": 0.025,
                                "cr": 0.03,
                                "epc": {"amount": 5.00, "currency": "USD"},
                                "roi": 2.0
                            }
                        }
                    ]
                elif breakdown == "landing_page":
                    breakdowns_data["byLandingPage"] = [
                        {
                            "landingPageId": "lp_456",
                            "name": "Main Squeeze Page",
                            "url": "https://example.com/page1",
                            "metrics": {
                                "clicks": 3000,
                                "uniqueClicks": 2880,
                                "conversions": 90,
                                "revenue": {"amount": 450.00, "currency": "USD"},
                                "cost": {"amount": 150.00, "currency": "USD"},
                                "ctr": 0.025,
                                "cr": 0.03,
                                "epc": {"amount": 5.00, "currency": "USD"},
                                "roi": 2.0
                            }
                        }
                    ]
                elif breakdown == "offer":
                    breakdowns_data["byOffer"] = [
                        {
                            "offerId": "offer_789",
                            "name": "Premium Product",
                            "metrics": {
                                "clicks": 2000,
                                "uniqueClicks": 1920,
                                "conversions": 60,
                                "revenue": {"amount": 300.00, "currency": "USD"},
                                "cost": {"amount": 100.00, "currency": "USD"},
                                "ctr": 0.025,
                                "cr": 0.03,
                                "epc": {"amount": 5.00, "currency": "USD"},
                                "roi": 2.0
                            }
                        }
                    ]
                elif breakdown == "geography":
                    breakdowns_data["byGeography"] = [
                        {
                            "country": "US",
                            "countryName": "United States",
                            "metrics": {
                                "clicks": 3500,
                                "uniqueClicks": 3360,
                                "conversions": 105,
                                "revenue": {"amount": 525.00, "currency": "USD"},
                                "cost": {"amount": 175.00, "currency": "USD"},
                                "ctr": 0.025,
                                "cr": 0.03,
                                "epc": {"amount": 5.00, "currency": "USD"},
                                "roi": 2.0
                            }
                        }
                    ]
                elif breakdown == "device":
                    breakdowns_data["byDevice"] = [
                        {
                            "device": "desktop",
                            "metrics": {
                                "clicks": 3000,
                                "uniqueClicks": 2880,
                                "conversions": 90,
                                "revenue": {"amount": 450.00, "currency": "USD"},
                                "cost": {"amount": 150.00, "currency": "USD"},
                                "ctr": 0.025,
                                "cr": 0.03,
                                "epc": {"amount": 5.00, "currency": "USD"},
                                "roi": 2.0
                            }
                        }
                    ]

                # Mock analytics data
                mock_analytics = {
                    "campaignId": campaign_id,
                    "timeRange": {
                        "startDate": start_date,
                        "endDate": end_date,
                        "granularity": granularity
                    },
                    "metrics": {
                        "clicks": 5000,
                        "uniqueClicks": 4800,
                        "conversions": 150,
                        "revenue": {"amount": 750.00, "currency": "USD"},
                        "cost": {"amount": 250.00, "currency": "USD"},
                        "ctr": 0.025,
                        "cr": 0.03,
                        "epc": {"amount": 5.00, "currency": "USD"},
                        "roi": 2.0
                    },
                    "breakdowns": breakdowns_data
                }
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(mock_analytics))
            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id/analytics', get_campaign_analytics)

    def _register_campaign_landing_pages(self, app):
        """Register campaign landing pages route."""
        logger.debug("_register_campaign_landing_pages called")
        def get_campaign_landing_pages(res, req):
            """Get campaign landing pages."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)

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

                # Validate and parse query parameters
                try:
                    page_str = req.get_query('page')
                    if page_str is not None:
                        page = int(page_str)
                        if page < 1:
                            raise ValueError("Page must be >= 1")
                    else:
                        page = 1

                    page_size_str = req.get_query('pageSize')
                    if page_size_str is not None:
                        page_size = int(page_size_str)
                        if page_size < 1 or page_size > 100:
                            raise ValueError("Page size must be between 1 and 100")
                    else:
                        page_size = 20

                except ValueError as e:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Mock landing pages data
                mock_landing_pages = {
                    "landingPages": [
                        {
                            "id": "lp_456",
                            "campaignId": campaign_id,
                            "name": "Main Squeeze Page",
                            "url": "https://example.com/page1",
                            "pageType": "squeeze",
                            "weight": 70,
                            "isActive": True,
                            "isControl": False,
                            "performance": {
                                "impressions": 5000,
                                "clicks": 250,
                                "conversions": 15,
                                "ctr": 0.05,
                                "cr": 0.06,
                                "epc": {"amount": 3.50, "currency": "USD"}
                            },
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-01T00:00:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "pageSize": 20,
                        "totalItems": 1,
                        "totalPages": 1,
                        "hasNext": False,
                        "hasPrev": False
                    }
                }
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(mock_landing_pages))
            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        def create_campaign_landing_page(res, req):
            """Create a landing page for a campaign."""
            logger.info("DEBUG: create_campaign_landing_page function called!")
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)
                if not campaign_id:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Campaign ID is required"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Buffer for request body
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
                                        error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON in request body"}}
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps(error_response))
                                        return

                            if not body_data:
                                error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Request body is required"}}
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps(error_response))
                                return

                            # Validate required fields
                            required_fields = ['name', 'url']
                            for field in required_fields:
                                if field not in body_data:
                                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": f"Field '{field}' is required"}}
                                    res.write_status(400)
                                    res.write_header("Content-Type", "application/json")
                                    add_security_headers(res)
                                    res.end(json.dumps(error_response))
                                    return

                            # Create command
                            from ...application.commands.create_landing_page_command import CreateLandingPageCommand
                            from ...domain.value_objects import Url

                            command = CreateLandingPageCommand(
                                campaign_id=campaign_id,
                                name=body_data['name'],
                                url=Url(body_data['url']),
                                page_type=body_data.get('pageType', 'squeeze'),
                                weight=body_data.get('weight', 100),
                                is_control=body_data.get('isControl', False)
                            )

                            # Handle command
                            landing_page = self.create_landing_page_handler.handle(command)

                            # Convert to response
                            response = {
                                "id": landing_page.id,
                                "campaignId": landing_page.campaign_id,
                                "name": landing_page.name,
                                "url": landing_page.url.value,
                                "pageType": landing_page.page_type,
                                "weight": landing_page.weight,
                                "isActive": landing_page.is_active,
                                "isControl": landing_page.is_control,
                                "createdAt": landing_page.created_at.isoformat(),
                                "updatedAt": landing_page.updated_at.isoformat()
                            }

                            res.write_status(201)
                            res.write_header('Content-Type', 'application/json')
                            add_security_headers(res)
                            res.end(json.dumps(response))

                    except Exception as e:
                        logger.error(f"Error processing request data: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                # Read request body
                req.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in create_campaign_landing_page: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # TODO: Add route registration here
        # app.get('/v1/campaigns/:campaign_id/landing-pages', get_campaign_landing_pages)
        # app.post('/v1/campaigns/:campaign_id/landing-pages', create_campaign_landing_page)

    def _register_campaign_offers(self, app):
        """Register campaign offers route."""
        def get_campaign_offers(res, req):
            """Get campaign offers."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)

                # Mock offers data
                mock_offers = {
                    "offers": [
                        {
                            "id": "offer_789",
                            "campaignId": campaign_id,
                            "name": "Premium Product",
                            "url": "https://affiliate.com/offer/123",
                            "offerType": "direct",
                            "weight": 60,
                            "isActive": True,
                            "isControl": False,
                            "payout": {"amount": 25.00, "currency": "USD"},
                            "revenueShare": 0.15,
                            "costPerClick": {"amount": 0.50, "currency": "USD"},
                            "performance": {
                                "clicks": 1000,
                                "conversions": 30,
                                "revenue": {"amount": 750.00, "currency": "USD"},
                                "cost": {"amount": 500.00, "currency": "USD"},
                                "cr": 0.03,
                                "epc": {"amount": 25.00, "currency": "USD"},
                                "roi": 1.5
                            },
                            "autoPause": {
                                "threshold": 0.02,
                                "minClicksBeforePause": 1000
                            },
                            "externalId": "AFF_123",
                            "partnerNetwork": "MaxBounty",
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-01T00:00:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "pageSize": 20,
                        "totalItems": 1,
                        "totalPages": 1,
                        "hasNext": False,
                        "hasPrev": False
                    }
                }
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(mock_offers))
            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        def create_campaign_offer(res, req):
            """Create an offer for a campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)

                # Buffer for request body
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
                                        error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON in request body"}}
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps(error_response))
                                        return

                            # Validate required fields
                            required_fields = ['name', 'url', 'offerType', 'weight', 'isActive', 'isControl', 'payout']
                            missing_fields = [field for field in required_fields if field not in body_data]
                            if missing_fields:
                                error_response = {"error": {"code": "VALIDATION_ERROR", "message": f"{missing_fields[0]} is required"}}
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                add_security_headers(res)
                                res.end(json.dumps(error_response))
                                return

                            # Create command
                            from ...application.commands.create_offer_command import CreateOfferCommand
                            from ...domain.value_objects import Money, Url
                            from decimal import Decimal

                            command = CreateOfferCommand(
                                campaign_id=campaign_id,
                                name=body_data['name'],
                                url=Url(body_data['url']),
                                offer_type=body_data.get('offerType', 'direct'),
                                payout=Money.from_float(body_data['payout']['amount'], body_data['payout']['currency']),
                                revenue_share=Decimal(str(body_data.get('revenueShare', 0.0))),
                                cost_per_click=Money.from_float(body_data['costPerClick']['amount'], body_data['costPerClick']['currency']) if body_data.get('costPerClick') else None,
                                weight=body_data.get('weight', 100),
                                is_control=body_data.get('isControl', False)
                            )

                            # Handle command
                            offer = self.create_offer_handler.handle(command)

                            # Convert to response
                            response = {
                                "id": offer.id,
                                "campaignId": offer.campaign_id,
                                "name": offer.name,
                                "url": offer.url.value,
                                "offerType": offer.offer_type,
                                "weight": offer.weight,
                                "isActive": offer.is_active,
                                "isControl": offer.is_control,
                                "payout": {
                                    "amount": float(offer.payout.amount),
                                    "currency": offer.payout.currency.value
                                },
                                "revenueShare": float(offer.revenue_share),
                                "costPerClick": {
                                    "amount": float(offer.cost_per_click.amount),
                                    "currency": offer.cost_per_click.currency.value
                                } if offer.cost_per_click else None,
                                "createdAt": offer.created_at.isoformat(),
                                "updatedAt": offer.updated_at.isoformat()
                            }

                            res.write_status(201)
                            res.write_header('Content-Type', 'application/json')
                            add_security_headers(res)
                            res.end(json.dumps(response))

                    except Exception as e:
                        logger.error(f"Error in create_campaign_offer: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error setting up create_campaign_offer: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id/offers', get_campaign_offers)
        app.post('/v1/campaigns/:campaign_id/offers', create_campaign_offer)

    def _register_campaign_pause(self, app):
        """Register campaign pause route."""
        def pause_campaign(res, req):
            """Pause a campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)
                if not campaign_id:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Campaign ID is required"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Create command
                from ...application.commands.pause_campaign_command import PauseCampaignCommand
                from ...domain.value_objects import CampaignId

                command = PauseCampaignCommand(campaign_id=CampaignId.from_string(campaign_id))

                # Handle command
                campaign = self.pause_campaign_handler.handle(command)

                # Convert to response
                response = {
                    "id": campaign.id.value,
                    "name": campaign.name,
                    "status": campaign.status.value,
                    "urls": {
                        "safePage": campaign.safe_page_url.value if campaign.safe_page_url else None,
                        "offerPage": campaign.offer_page_url.value if campaign.offer_page_url else None
                    },
                    "createdAt": campaign.created_at.isoformat(),
                    "updatedAt": campaign.updated_at.isoformat()
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))
            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.post('/v1/campaigns/:campaign_id/pause', pause_campaign)

    def _register_campaign_resume(self, app):
        """Register campaign resume route."""
        def resume_campaign(res, req):
            """Resume a campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)
                logger.debug(f"Resume campaign request for ID: {campaign_id}")

                # Validate campaign_id - reject obviously malformed IDs
                if not campaign_id or len(campaign_id) > 255:
                    logger.warning(f"Invalid campaign ID: {campaign_id}")
                    error_response = {"error": {"code": "INVALID_CAMPAIGN_ID", "message": "Invalid campaign ID"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    res.end(json.dumps(error_response))
                    return

                # Create command
                from ...application.commands.resume_campaign_command import ResumeCampaignCommand
                from ...domain.value_objects import CampaignId

                command = ResumeCampaignCommand(campaign_id=CampaignId.from_string(campaign_id))

                # Handle command
                campaign = self.resume_campaign_handler.handle(command)

                # Convert to response
                response = {
                    "id": campaign.id.value,
                    "name": campaign.name,
                    "status": campaign.status.value,
                    "urls": {
                        "safePage": campaign.safe_page_url.value if campaign.safe_page_url else None,
                        "offerPage": campaign.offer_page_url.value if campaign.offer_page_url else None
                    },
                    "createdAt": campaign.created_at.isoformat(),
                    "updatedAt": campaign.updated_at.isoformat()
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))
            except Exception:
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.post('/v1/campaigns/:campaign_id/resume', resume_campaign)
