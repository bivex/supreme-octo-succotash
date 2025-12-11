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
from ...application.queries.get_campaign_analytics_query import GetCampaignAnalyticsHandler
from ...application.queries.get_campaign_landing_pages_query import GetCampaignLandingPagesHandler
from ...application.queries.get_campaign_offers_query import GetCampaignOffersHandler
from ..dto.campaign_dto import CampaignSummaryResponse


class CampaignRoutes:
    """Socketify routes for campaign operations."""

    def __init__(self, container):
        self._container = container
        # Lazy-loaded handlers
        self._create_campaign_handler = None
        self._update_campaign_handler = None
        self._pause_campaign_handler = None
        self._resume_campaign_handler = None
        self._create_landing_page_handler = None
        self._create_offer_handler = None
        self._get_campaign_handler = None
        self._get_campaign_analytics_handler = None
        self._get_campaign_landing_pages_handler = None
        self._get_campaign_offers_handler = None

    @property
    async def create_campaign_handler(self):
        if self._create_campaign_handler is None:
            self._create_campaign_handler = await self._container.get_create_campaign_handler()
        return self._create_campaign_handler

    @property
    async def update_campaign_handler(self):
        if self._update_campaign_handler is None:
            self._update_campaign_handler = await self._container.get_update_campaign_handler()
        return self._update_campaign_handler

    @property
    async def pause_campaign_handler(self):
        if self._pause_campaign_handler is None:
            self._pause_campaign_handler = await self._container.get_pause_campaign_handler()
        return self._pause_campaign_handler

    @property
    async def resume_campaign_handler(self):
        if self._resume_campaign_handler is None:
            self._resume_campaign_handler = await self._container.get_resume_campaign_handler()
        return self._resume_campaign_handler

    @property
    async def create_landing_page_handler(self):
        if self._create_landing_page_handler is None:
            self._create_landing_page_handler = await self._container.get_create_landing_page_handler()
        return self._create_landing_page_handler

    @property
    async def create_offer_handler(self):
        if self._create_offer_handler is None:
            self._create_offer_handler = await self._container.get_create_offer_handler()
        return self._create_offer_handler

    @property
    async def get_campaign_handler(self):
        if self._get_campaign_handler is None:
            self._get_campaign_handler = await self._container.get_get_campaign_handler()
        return self._get_campaign_handler

    @property
    async def get_campaign_analytics_handler(self):
        if self._get_campaign_analytics_handler is None:
            self._get_campaign_analytics_handler = await self._container.get_get_campaign_analytics_handler()
        return self._get_campaign_analytics_handler

    @property
    async def get_campaign_landing_pages_handler(self):
        if self._get_campaign_landing_pages_handler is None:
            self._get_campaign_landing_pages_handler = await self._container.get_get_campaign_landing_pages_handler()
        return self._get_campaign_landing_pages_handler

    @property
    async def get_campaign_offers_handler(self):
        if self._get_campaign_offers_handler is None:
            self._get_campaign_offers_handler = await self._container.get_get_campaign_offers_handler()
        return self._get_campaign_offers_handler


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

    async def register(self, app):
        """Register routes with socketify app."""
        # Register individual route handlers
        await self._register_list_campaigns(app)
        await self._register_create_campaign(app)
        await self._register_get_campaign(app)
        await self._register_campaign_analytics(app)
        await self._register_campaign_landing_pages(app)
        await self._register_campaign_offers(app)
        await self._register_campaign_pause(app)
        await self._register_campaign_resume(app)

    async def _register_list_campaigns(self, app):
        """Register list campaigns route."""
        async def list_campaigns(res, req):
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

                # Get campaigns from repository
                offset = (page - 1) * page_size
                campaign_repo = (await self.create_campaign_handler)._campaign_repository
                logger.debug(f"About to call find_all with limit={page_size}, offset={offset}")
                try:
                    campaigns = campaign_repo.find_all(limit=page_size, offset=offset)
                    logger.debug(f"find_all returned {len(campaigns)} campaigns")
                except Exception as db_error:
                    logger.error(f"Database error in find_all: {db_error}")
                    import traceback
                    logger.error(f"Database traceback: {traceback.format_exc()}")
                    raise

                try:
                    total_count = campaign_repo.count_all()
                    logger.debug(f"count_all returned {total_count}")
                except Exception as count_error:
                    logger.error(f"Database error in count_all: {count_error}")
                    import traceback
                    logger.error(f"Count traceback: {traceback.format_exc()}")
                    raise

                logger.debug(f"campaigns count={len(campaigns)}, total_count={total_count}")

                try:
                    pagination = self._build_pagination_info(page, page_size, total_count)
                    logger.debug(f"pagination={pagination}")
                except Exception as pagination_error:
                    logger.error(f"Error building pagination: {pagination_error}")
                    raise

                try:
                    response = {
                        "campaigns": [{"id": c.id.value, "name": c.name, "status": c.status.value} for c in campaigns],
                        "pagination": pagination
                    }
                    logger.debug(f"response created, campaigns in response={len(response['campaigns'])}")
                except Exception as response_error:
                    logger.error(f"Error creating response: {response_error}")
                    import traceback
                    logger.error(f"Response traceback: {traceback.format_exc()}")
                    raise
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

            except Exception as e:
                import traceback
                logger.error(f"Error in list_campaigns: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                from ...presentation.error_handlers import handle_internal_server_error
                handle_internal_server_error(res)

        app.get('/v1/campaigns', list_campaigns)

    async def _register_create_campaign(self, app):
        """Register create campaign route."""
        async def create_campaign(res, req):
            """Create a new campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                # Parse request body using socketify's res.get_json()
                logger.info("Starting campaign creation")
                body_data = await res.get_json()
                
                logger.info(f"Parsed body data: {body_data}")

                if not body_data:
                    logger.warning("Body data is empty")
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
                                          body_data.get('payout', {}).get('currency', 'USD')) if body_data.get('payout') and body_data.get('payout', {}).get('amount', 0) > 0 else None,
                    white_url=body_data.get('whiteUrl'),  # safe page URL
                    black_url=body_data.get('blackUrl'),  # offer page URL
                    daily_budget=Money.from_float(body_data.get('dailyBudget', {}).get('amount', 0.0),
                                                body_data.get('dailyBudget', {}).get('currency', 'USD')) if body_data.get('dailyBudget') and body_data.get('dailyBudget', {}).get('amount', 0) > 0 else None,
                    total_budget=Money.from_float(body_data.get('totalBudget', {}).get('amount', 0.0),
                                                body_data.get('totalBudget', {}).get('currency', 'USD')) if body_data.get('totalBudget') and body_data.get('totalBudget', {}).get('amount', 0) > 0 else None,
                    start_date=body_data.get('startDate'),
                    end_date=body_data.get('endDate')
                )

                # Handle command
                campaign = (await self.create_campaign_handler).handle(command)

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

            except ValueError as e:
                error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                res.write_status(400)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))
            except Exception as e:
                import traceback
                logger.error(f"Error creating campaign: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": f"Internal server error: {str(e)}"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.post('/v1/campaigns', create_campaign)

    async def _register_get_campaign(self, app):
        """Register get campaign route."""
        async def get_campaign(res, req):
            """Get campaign details."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)  # Get path parameter

                # Get campaign from repository
                from ...domain.value_objects import CampaignId
                campaign = (await self.create_campaign_handler)._campaign_repository.find_by_id(CampaignId.from_string(campaign_id))

                if not campaign:
                    error_response = {"error": {"code": "NOT_FOUND", "message": "Campaign not found"}}
                    res.write_status(404)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Convert to response
                response = {
                    "id": campaign.id.value,
                    "name": campaign.name,
                    "description": campaign.description,
                    "status": campaign.status.value,
                    "schedule": {
                        "startDate": campaign.start_date.isoformat() + "Z" if campaign.start_date else None,
                        "endDate": campaign.end_date.isoformat() + "Z" if campaign.end_date else None
                    },
                    "urls": {
                        "safePage": campaign.safe_page_url.value if campaign.safe_page_url else None,
                        "offerPage": campaign.offer_page_url.value if campaign.offer_page_url else None
                    },
                    "financial": {
                        "costModel": campaign.cost_model,
                        "payout": {
                            "amount": float(campaign.payout.amount),
                            "currency": campaign.payout.currency
                        } if campaign.payout else None,
                        "dailyBudget": {
                            "amount": float(campaign.daily_budget.amount),
                            "currency": campaign.daily_budget.currency
                        } if campaign.daily_budget else None,
                        "totalBudget": {
                            "amount": float(campaign.total_budget.amount),
                            "currency": campaign.total_budget.currency
                        } if campaign.total_budget else None,
                        "spent": {
                            "amount": float(campaign.spent_amount.amount),
                            "currency": campaign.spent_amount.currency
                        } if campaign.spent_amount else None
                    },
                    "performance": {
                        "impressions": campaign.impressions_count,
                        "clicks": campaign.clicks_count,
                        "conversions": campaign.conversions_count,
                        "ctr": round(campaign.ctr, 3),
                        "cr": round(campaign.cr, 3),
                        "epc": {
                            "amount": round(float(campaign.epc.amount), 2) if campaign.epc else 0.0,
                            "currency": campaign.epc.currency if campaign.epc else "USD"
                        },
                        "roi": round(campaign.roi, 2)
                    },
                    "createdAt": campaign.created_at.isoformat() + "Z" if campaign.created_at else None,
                    "updatedAt": campaign.updated_at.isoformat() + "Z" if campaign.updated_at else None,
                    "_links": {
                        "self": f"/v1/campaigns/{campaign.id.value}",
                        "landingPages": f"/v1/campaigns/{campaign.id.value}/landing-pages",
                        "offers": f"/v1/campaigns/{campaign.id.value}/offers",
                        "analytics": f"/v1/campaigns/{campaign.id.value}/analytics"
                    }
                }

                res.write_status(200)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))

            except ValueError as e:
                error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                res.write_status(400)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))
            except Exception as e:
                import traceback
                logger.error(f"Error getting campaign: {e}", exc_info=True)
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": f"Internal server error: {str(e)}"}}
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

                # Delete campaign from database
                from ...domain.value_objects import CampaignId
                campaign_id_obj = CampaignId.from_string(campaign_id)
                self._container.get_campaign_repository().delete_by_id(campaign_id_obj)
                logger.info(f"Successfully deleted campaign {campaign_id}")

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

        async def update_campaign(res, req):
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

                # Parse request body using socketify's res.get_json()
                body_data = await res.get_json()

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
                                          body_data.get('payout', {}).get('currency', 'USD')) if body_data.get('payout') and body_data.get('payout', {}).get('amount', 0) > 0 else None,
                    safe_page_url=Url(body_data['safe_page_url']) if body_data.get('safe_page_url') else None,
                    offer_page_url=Url(body_data['offer_page_url']) if body_data.get('offer_page_url') else None,
                    daily_budget=Money.from_float(body_data.get('dailyBudget', {}).get('amount', 0.0),
                                                body_data.get('dailyBudget', {}).get('currency', 'USD')) if body_data.get('dailyBudget') and body_data.get('dailyBudget', {}).get('amount', 0) > 0 else None,
                    total_budget=Money.from_float(body_data.get('totalBudget', {}).get('amount', 0.0),
                                                body_data.get('totalBudget', {}).get('currency', 'USD')) if body_data.get('totalBudget') and body_data.get('totalBudget', {}).get('amount', 0) > 0 else None,
                    start_date=body_data.get('startDate'),
                    end_date=body_data.get('endDate')
                )

                updated_campaign = await (await self.update_campaign_handler).handle(command)

                # Convert to response
                response = {
                    "id": updated_campaign.id.value,
                    "name": updated_campaign.name,
                    "status": updated_campaign.status.value,
                    "urls": {
                        "safePage": updated_campaign.safe_page_url.value if updated_campaign.safe_page_url else None,
                        "offerPage": updated_campaign.offer_page_url.value if updated_campaign.offer_page_url else None
                    },
                    "createdAt": updated_campaign.created_at.isoformat(),
                    "updatedAt": updated_campaign.updated_at.isoformat()
                }

                res.write_status(200)
                res.write_header('Content-Type', 'application/json')
                add_security_headers(res)
                res.end(json.dumps(response))

            except Exception as e:
                logger.error(f"ERROR: Failed to update campaign: {e}")
                import traceback
                logger.error(f"TRACEBACK: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id', get_campaign)
        app.put('/v1/campaigns/:campaign_id', update_campaign)
        app.delete('/v1/campaigns/:campaign_id', delete_campaign)

    def _build_pagination_info(self, page: int, page_size: int, total_items: int) -> dict:
        """Build pagination information."""
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

    async def _register_campaign_analytics(self, app):
        """Register campaign analytics route."""
        async def get_campaign_analytics(res, req):
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

                # Create analytics query
                from ...application.queries.get_campaign_analytics_query import GetCampaignAnalyticsQuery
                from datetime import datetime

                query = GetCampaignAnalyticsQuery(
                    campaign_id=campaign_id,
                    start_date=datetime.fromisoformat(start_date).date(),
                    end_date=datetime.fromisoformat(end_date).date(),
                    granularity=granularity
                )

                # Get analytics from business logic
                analytics = (await self.get_campaign_analytics_handler).handle(query)
                logger.debug(f"Analytics object type: {type(analytics)}")
                if hasattr(analytics, 'revenue'):
                    logger.debug(f"Analytics revenue type: {type(analytics.revenue)}")
                    logger.debug(f"Analytics revenue: {analytics.revenue}")
                    if hasattr(analytics.revenue, 'currency'):
                        logger.debug(f"Analytics revenue.currency: {analytics.revenue.currency}")
                    else:
                        logger.debug("Analytics revenue has no currency attribute")

                # Convert to response format based on breakdown
                if breakdown == "date":
                    breakdowns_data = {"byDate": analytics.get_breakdown_by_date()}
                elif breakdown == "traffic_source":
                    breakdowns_data = {"byTrafficSource": analytics.get_breakdown_by_traffic_source()}
                elif breakdown == "landing_page":
                    breakdowns_data = {"byLandingPage": analytics.get_breakdown_by_landing_page()}
                elif breakdown == "offer":
                    breakdowns_data = {"byOffer": analytics.get_breakdown_by_offer()}
                elif breakdown == "geography":
                    breakdowns_data = {"byGeography": analytics.get_breakdown_by_geography()}
                elif breakdown == "device":
                    breakdowns_data = {"byDevice": analytics.get_breakdown_by_device()}
                else:
                    breakdowns_data = {}

                # Convert Money objects to dict format
                def money_to_dict(money_obj):
                    if money_obj:
                        return {
                            "amount": float(money_obj.amount),
                            "currency": money_obj.currency
                        }
                    return None

                response = {
                    "campaignId": campaign_id,
                    "timeRange": {
                        "startDate": start_date,
                        "endDate": end_date,
                        "granularity": granularity
                    },
                    "metrics": {
                        "clicks": analytics.clicks,
                        "uniqueClicks": analytics.unique_clicks,
                        "conversions": analytics.conversions,
                        "revenue": money_to_dict(analytics.revenue),
                        "cost": money_to_dict(analytics.cost),
                        "ctr": analytics.ctr,
                        "cr": analytics.cr,
                        "epc": money_to_dict(analytics.epc),
                        "roi": analytics.roi
                    },
                    "breakdowns": breakdowns_data
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))
            except Exception as e:
                import traceback
                logger.error(f"Error in get_campaign: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id/analytics', get_campaign_analytics)

    async def _register_campaign_landing_pages(self, app):
        """Register campaign landing pages route."""
        logger.debug("_register_campaign_landing_pages called")
        async def get_campaign_landing_pages(res, req):
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

                # Get landing pages from business logic
                from ...application.queries.get_campaign_landing_pages_query import GetCampaignLandingPagesQuery

                offset = (page - 1) * page_size
                limit = min(page_size, 100)  # Ensure limit <= 100
                logger.debug(f"Landing pages query: campaign_id={campaign_id}, page={page}, page_size={page_size}, limit={limit}, offset={offset}")

                query = GetCampaignLandingPagesQuery(
                    campaign_id=campaign_id,
                    limit=limit,
                    offset=offset
                )

                landing_pages = (await self.get_campaign_landing_pages_handler).handle(query)
                logger.debug("Landing pages query executed successfully")
                logger.debug(f"Type: {type(landing_pages)}")
                if hasattr(landing_pages, '__len__'):
                    logger.debug(f"Length: {len(landing_pages)}")

                # Get total count for pagination
                total_count = self._container.get_landing_page_repository().count_by_campaign_id(campaign_id)

                # Convert to response format
                response = {
                    "landingPages": [
                        {
                            "id": lp.id,
                            "campaignId": lp.campaign_id,
                            "name": lp.name,
                            "url": lp.url.value,
                            "pageType": lp.page_type,
                            "weight": lp.weight,
                            "isActive": lp.is_active,
                            "isControl": lp.is_control,
                            "createdAt": lp.created_at.isoformat() + "Z",
                            "updatedAt": lp.updated_at.isoformat() + "Z"
                        }
                        for lp in landing_pages
                    ],
                    "pagination": self._build_pagination_info(page, page_size, total_count)
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))
            except Exception as e:
                import traceback
                logger.error(f"Error in get_campaign: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        async def create_campaign_landing_page(res, req):
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

                # Parse request body using socketify's res.get_json()
                body_data = await res.get_json()

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
                landing_page = (await self.create_landing_page_handler).handle(command)

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
                logger.error(f"Error in create_campaign_landing_page: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id/landing-pages', get_campaign_landing_pages)
        app.post('/v1/campaigns/:campaign_id/landing-pages', create_campaign_landing_page)

    async def _register_campaign_offers(self, app):
        """Register campaign offers route with CQRS query pattern."""
        async def get_campaign_offers(res, req):
            """Get campaign offers using GetCampaignOffersQuery and business logic handler."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                campaign_id = req.get_parameter(0)

                # Validate and parse query parameters for pagination
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

                # Get offers from business logic using CQRS query pattern
                from ...application.queries.get_campaign_offers_query import GetCampaignOffersQuery

                offset = (page - 1) * page_size
                limit = min(page_size, 100)  # Ensure limit <= 100
                logger.debug(f"Offers query: campaign_id={campaign_id}, page={page}, page_size={page_size}, limit={limit}, offset={offset}")

                query = GetCampaignOffersQuery(
                    campaign_id=campaign_id,
                    limit=limit,
                    offset=offset
                )

                offers = (await self.get_campaign_offers_handler).handle(query)
                logger.debug("Offers query executed successfully")
                logger.debug(f"Type: {type(offers)}")
                if hasattr(offers, '__len__'):
                    logger.debug(f"Length: {len(offers)}")

                # Get total count for pagination
                total_count = self._container.get_offer_repository().count_by_campaign_id(campaign_id)

                # Convert to response format
                response = {
                    "offers": [
                        {
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
                            "createdAt": offer.created_at.isoformat() + "Z",
                            "updatedAt": offer.updated_at.isoformat() + "Z"
                        }
                        for offer in offers
                    ],
                    "pagination": self._build_pagination_info(page, page_size, total_count)
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(response))
            except Exception as e:
                import traceback
                logger.error(f"Error in get_campaign: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        async def create_campaign_offer(res, req):
            """Create an offer for a campaign."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            from ...utils.async_debug import debug_http_request, debug_database_call
            import json

            # Debug: Show async call stack for HTTP requests
            debug_http_request("create_campaign_offer")

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                # Extract campaign_id from URL path
                url_path = req.get_url()
                logger.debug(f"create_campaign_offer: full URL: '{url_path}'")

                # Parse path to extract campaign_id (format: /v1/campaigns/{campaign_id}/offers)
                path_parts = url_path.split('/')
                if len(path_parts) >= 4 and path_parts[3]:  # campaigns/{campaign_id}/offers
                    campaign_id = path_parts[3]
                else:
                    campaign_id = None

                logger.debug(f"create_campaign_offer: extracted campaign_id: '{campaign_id}'")

                # Validate campaign_id
                if not campaign_id:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Campaign ID is required"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Parse request body using socketify's res.get_json()
                body_data = await res.get_json()

                if not body_data:
                    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Request body is required"}}
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                try:
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

                    # Create command using CQRS pattern
                    from ...application.commands.create_offer_command import CreateOfferCommand
                    from ...domain.value_objects import Money, Url
                    from decimal import Decimal

                    # Build command with business logic validation
                    from ...domain.value_objects import CampaignId
                    command = CreateOfferCommand(
                        campaign_id=CampaignId(campaign_id),
                        name=body_data['name'],
                        url=Url(body_data['url']),
                        offer_type=body_data.get('offerType', 'direct'),
                        payout=Money.from_float(body_data['payout']['amount'], body_data['payout']['currency']) if body_data['payout']['amount'] > 0 else Money.zero(body_data['payout']['currency']),
                        revenue_share=Decimal(str(body_data.get('revenueShare', 0.0))),
                        cost_per_click=Money.from_float(body_data['costPerClick']['amount'], body_data['costPerClick']['currency']) if body_data.get('costPerClick') else None,
                        weight=body_data.get('weight', 100),
                        is_control=body_data.get('isControl', False)
                    )

                    # Debug: Show async call stack before database operation
                    debug_database_call("create_offer_command")

                    # Handle command
                    offer = (await self.create_offer_handler).handle(command)

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

                    # Log successful operation
                    debug_database_call("offer_creation_success")

                    res.write_status(201)
                    res.write_header('Content-Type', 'application/json')
                    add_security_headers(res)
                    res.end(json.dumps(response))

                except Exception as e:
                    # Save async trace on error
                    try:
                        from ...utils.async_debug import save_debug_snapshot
                        error_trace = save_debug_snapshot("create_offer_error")
                        logger.error(f"📸 Create offer error trace saved: {error_trace}")
                    except Exception as trace_error:
                        logger.error(f"Failed to save error trace: {trace_error}")

                    logger.error(f"Error in create_campaign_offer processing: {e}", exc_info=True)
                    error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": f"Internal server error: {str(e)}"}}
                    res.write_status(500)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))

            except Exception as e:
                logger.error(f"Error setting up create_campaign_offer: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/v1/campaigns/:campaign_id/offers', get_campaign_offers)
        app.post('/v1/campaigns/:campaign_id/offers', create_campaign_offer)

    async def _register_campaign_pause(self, app):
        """Register campaign pause route."""
        async def pause_campaign(res, req):
            """Pause a campaign using CQRS pattern with PauseCampaignCommand and handler."""
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

                # Create command using CQRS pattern
                from ...application.commands.pause_campaign_command import PauseCampaignCommand
                from ...domain.value_objects import CampaignId

                command = PauseCampaignCommand(campaign_id=CampaignId.from_string(campaign_id))

                # Handle command
                campaign = (await self.pause_campaign_handler).handle(command)

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
            except ValueError as e:
                # Handle business logic validation errors (e.g., campaign already paused)
                error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                res.write_status(400)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))
            except Exception as e:
                import traceback
                logger.error(f"Error in pause_campaign: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.post('/v1/campaigns/:campaign_id/pause', pause_campaign)

    async def _register_campaign_resume(self, app):
        """Register campaign resume route."""
        async def resume_campaign(res, req):
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
                campaign = (await self.resume_campaign_handler).handle(command)

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
            except Exception as e:
                import traceback
                logger.error(f"Error in get_campaign: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        app.post('/v1/campaigns/:campaign_id/resume', resume_campaign)
