"""Generate click handler."""

import json
from typing import Dict, Any, List
from loguru import logger
from ...domain.services.click.click_generation_service import ClickGenerationService


class GenerateClickHandler:
    """Handler for generating click tracking URLs."""

    def __init__(self, click_generation_service: ClickGenerationService):
        self.click_generation_service = click_generation_service

    def handle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate click tracking URL(s)."""
        try:
            logger.info("Processing click generation request")

            # Validate request
            if not request_data:
                return {
                    "status": "error",
                    "message": "Request body is required"
                }

            # Check if bulk generation or single URL
            if 'variations' in request_data:
                # Bulk generation
                return self._handle_bulk_generation(request_data)
            else:
                # Single URL generation
                return self._handle_single_generation(request_data)

        except Exception as e:
            logger.error(f"Error in generate_click handler: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def _handle_single_generation(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle single URL generation."""
        try:
            # Validate required fields
            required_fields = ['campaign_id', 'base_url']
            missing_fields = [field for field in required_fields if field not in request_data]

            if missing_fields:
                return {
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }

            # Extract parameters
            campaign_id = request_data['campaign_id']
            base_url = request_data['base_url']
            tracking_params = request_data.get('params', {})
            landing_page_id = request_data.get('lp_id') or request_data.get('landing_page_id')
            offer_id = request_data.get('offer_id')
            traffic_source_id = request_data.get('ts_id')

            # Validate parameters
            validation_params = {
                'campaign_id': campaign_id,
                'base_url': base_url,
                **tracking_params
            }
            if landing_page_id is not None:
                validation_params['landing_page_id'] = landing_page_id
            if offer_id is not None:
                validation_params['offer_id'] = offer_id
            if traffic_source_id is not None:
                validation_params['traffic_source_id'] = traffic_source_id

            is_valid, error_message = self.click_generation_service.validate_tracking_parameters(validation_params)
            if not is_valid:
                return {
                    "status": "error",
                    "message": error_message
                }

            # Optimize parameters
            optimized_params = self.click_generation_service.optimize_tracking_parameters(tracking_params)

            # Generate tracking URL
            logger.info("=== CLICK HANDLER DEBUG ===")
            logger.info(f"Calling generate_tracking_url with:")
            logger.info(f"  base_url: {base_url}")
            logger.info(f"  campaign_id: {campaign_id}")
            logger.info(f"  landing_page_id: {landing_page_id}")
            logger.info(f"  offer_id: {offer_id}")
            logger.info(f"  traffic_source_id: {traffic_source_id}")
            logger.info(f"  optimized_params: {optimized_params}")

            tracking_url = self.click_generation_service.generate_tracking_url(
                base_url=base_url,
                campaign_id=campaign_id,
                tracking_params=optimized_params,
                landing_page_id=landing_page_id,
                offer_id=offer_id,
                traffic_source_id=traffic_source_id
            )

            return {
                "status": "success",
                "tracking_url": tracking_url,
                "campaign_id": campaign_id,
                "params": optimized_params,
                "landing_page_id": landing_page_id,
                "offer_id": offer_id,
                "traffic_source_id": traffic_source_id
            }

        except Exception as e:
            logger.error(f"Error in single click generation: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate tracking URL: {str(e)}"
            }

    def _handle_bulk_generation(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bulk URL generation."""
        try:
            # Validate required fields for bulk generation
            if 'base_url' not in request_data:
                return {
                    "status": "error",
                    "message": "base_url is required for bulk generation"
                }

            if 'campaign_id' not in request_data:
                return {
                    "status": "error",
                    "message": "campaign_id is required for bulk generation"
                }

            variations = request_data.get('variations', [])
            if not variations or not isinstance(variations, list):
                return {
                    "status": "error",
                    "message": "variations must be a non-empty array"
                }

            if len(variations) > 100:  # Limit bulk generation
                return {
                    "status": "error",
                    "message": "Maximum 100 variations allowed in bulk generation"
                }

            base_url = request_data['base_url']
            campaign_id = request_data['campaign_id']

            # Generate bulk URLs
            results = self.click_generation_service.generate_bulk_tracking_urls(
                base_url=base_url,
                campaign_id=campaign_id,
                variations=variations
            )

            # Count successes and failures
            successful = len([r for r in results if r['status'] == 'success'])
            failed = len([r for r in results if r['status'] == 'error'])

            return {
                "status": "success",
                "total_variations": len(variations),
                "successful": successful,
                "failed": failed,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in bulk click generation: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate tracking URLs: {str(e)}"
            }
