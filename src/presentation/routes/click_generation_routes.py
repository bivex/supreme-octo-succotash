"""Click generation HTTP routes."""

import json
from loguru import logger
from ...application.handlers.generate_click_handler import GenerateClickHandler


class ClickGenerationRoutes:
    """Socketify routes for click generation operations."""

    def __init__(self, generate_click_handler: GenerateClickHandler):
        self.generate_click_handler = generate_click_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_generate_click(app)
        # self._register_tracking_redirect(app) # Remove this line as the redirect route has been moved

    def _register_generate_click(self, app):
        """Register click generation route."""
        async def generate_click(res, req):
            """Generate personalized click tracking URLs."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Click generation request received")

                # Parse request body
                data_parts = []

                async def on_data(res, chunk, is_last, *args):
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
                                        logger.error("Invalid JSON in click generation request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Generate click URL(s)
                            result = await self.generate_click_handler.handle(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing click generation data: {e}", exc_info=True)
                        error_response = {
                            "status": "error",
                            "message": "Internal server error"
                        }
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in generate_click: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the click generation endpoint
        app.post('/v1/clicks/generate', generate_click)

    # The _register_tracking_redirect method is moved to click_routes.py
    # def _register_tracking_redirect(self, app):
    #     """Register the route for handling short tracking URLs and redirecting."""
    #     from ...presentation.middleware.security_middleware import add_security_headers
    #     from shared_url_shortener import URLShortener, TrackingURLDecoder, DecodedTrackingParams
    #     from urllib.parse import urlencode, urlunparse, urlparse
    #     from src.container import container # Import the container to access dependencies
    #     from src.domain.value_objects import ClickId # Correct import for ClickId

    #     async def tracking_redirect(res, req):
    #         """Handle short tracking URL redirects."""
    #         try:
    #             short_code = req.get_parameter(0) # Get the dynamic part of the URL (the code)
    #             logger.info(f"Received redirect request for short code: {short_code}")

    #             # Get TrackingURLDecoder instance from the container
    #             url_shortener_service = await container.get_url_shortening_service()
                
    #             # The URLShortener from shared_url_shortener already includes decoding logic
    #             decoded_params_obj = url_shortener_service.decode(short_code)

    #             if not decoded_params_obj:
    #                 logger.warning(f"Failed to decode short code: {short_code}")
    #                 res.write_status(404)
    #                 res.write_header("Content-Type", "application/json")
    #                 add_security_headers(res)
    #                 res.end(json.dumps({
    #                     "status": "error",
    #                     "message": "Tracking URL not found or invalid"
    #                 }))
    #                 return

    #             # Assuming decoded_params_obj is an instance of URLParams (or similar)
    #             # and contains 'click_id' and 'cid'
    #             decoded_dict = decoded_params_obj.to_dict()
    #             click_id_from_code = decoded_dict.get('click_id')
    #             campaign_id_from_code = decoded_dict.get('cid')

    #             if not click_id_from_code:
    #                 logger.warning(f"Decoded parameters missing click_id for code: {short_code}")
    #                 res.write_status(400)
    #                 res.write_header("Content-Type", "application/json")
    #                 add_security_headers(res)
    #                 res.end(json.dumps({"status": "error", "message": "Missing click_id in tracking parameters"}))
    #                 return

    #             # Fetch full PreClickData from the repository using the click_id
    #             pre_click_data_repo = await container.get_postgres_pre_click_data_repository()
    #             pre_click_data = await pre_click_data_repo.find_by_click_id(ClickId(click_id_from_code))

    #             if not pre_click_data:
    #                 logger.warning(f"PreClickData not found for click_id: {click_id_from_code}")
    #                 res.write_status(404)
    #                 res.write_header("Content-Type", "application/json")
    #                 add_security_headers(res)
    #                 res.end(json.dumps({"status": "error", "message": "Tracking data not found for click_id"}))
    #                 return
                
    #             # Retrieve the original base URL from metadata
    #             redirect_base_url = pre_click_data.metadata.get('original_base_url')
    #             if not redirect_base_url:
    #                 logger.error(f"Original base URL not found in PreClickData metadata for click_id: {click_id_from_code}")
    #                 res.write_status(500)
    #                 res.write_header("Content-Type", "application/json")
    #                 add_security_headers(res)
    #                 res.end(json.dumps({"status": "error", "message": "Internal server error: Missing redirect base URL"}))
    #                 return

    #             # Combine original tracking parameters with any additional data from PreClickData
    #             all_params = pre_click_data.tracking_params.copy()
    #             all_params['click_id'] = pre_click_data.click_id.value # Ensure click_id is in params
    #             all_params['cid'] = pre_click_data.campaign_id.value.replace('camp_', '') # Clean campaign ID

    #             # Construct query string
    #             query_string = urlencode({k: v for k, v in all_params.items() if v is not None})
    #             redirect_url = f"{redirect_base_url}?{query_string}"

    #             logger.info(f"Redirecting to: {redirect_url}")
    #             res.write_status(302) # Found (Temporary Redirect)
    #             res.write_header("Location", redirect_url)
    #             add_security_headers(res)
    #             res.end()

    #         except Exception as e:
    #             logger.error(f"Error in tracking_redirect for code {req.get_parameter(0)}: {e}", exc_info=True)
    #             error_response = {"status": "error", "message": "Internal server error during redirect"}
    #             res.write_status(500)
    #             res.write_header("Content-Type", "application/json")
    #             add_security_headers(res)
    #             res.end(json.dumps(error_response))

    #     app.get('/s/:code', tracking_redirect) # Register the route to handle /s/CODE
