# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Bulk click generation handler."""

import uuid
from typing import Dict, Any

from loguru import logger


class BulkClickHandler:
    """Handler for bulk click generation operations."""

    def __init__(self):
        """Initialize bulk click handler."""
        pass

    def handle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bulk click generation request.

        Args:
            request_data: Request data containing campaign info and URLs to generate

        Returns:
            Dict containing generated click URLs and metadata
        """
        try:
            logger.info("Processing bulk click generation request")

            campaign_id = request_data.get('campaignId')
            landing_page_id = request_data.get('landingPageId')
            offer_id = request_data.get('offerId')
            urls = request_data.get('urls', [])

            if not campaign_id:
                return {
                    "status": "error",
                    "message": "campaignId is required"
                }

            if not urls:
                return {
                    "status": "error",
                    "message": "urls array is required and cannot be empty"
                }

            if len(urls) > 1000:
                return {
                    "status": "error",
                    "message": "Maximum 1000 URLs allowed per request"
                }

            # Generate bulk click URLs
            generated_clicks = []
            base_url = "http://127.0.0.1:5000/v1/click"

            for i, url_data in enumerate(urls):
                try:
                    # Generate unique click ID
                    click_id = str(uuid.uuid4())

                    # Build tracking URL
                    tracking_url = f"{base_url}?cid={campaign_id}"

                    # Add sub-parameters if provided
                    if isinstance(url_data, dict):
                        for sub_param in ['sub1', 'sub2', 'sub3', 'sub4', 'sub5']:
                            if sub_param in url_data:
                                tracking_url += f"&{sub_param}={url_data[sub_param]}"

                    # Add landing page and offer targeting
                    if landing_page_id:
                        tracking_url += f"&landing_page_id={landing_page_id}"
                    if offer_id:
                        tracking_url += f"&campaign_offer_id={offer_id}"

                    # Add click ID for tracking
                    tracking_url += f"&click_id={click_id}"

                    generated_clicks.append({
                        "id": click_id,
                        "url": tracking_url,
                        "campaignId": campaign_id,
                        "landingPageId": landing_page_id,
                        "offerId": offer_id,
                        "parameters": url_data if isinstance(url_data, dict) else {"custom": url_data}
                    })

                except Exception as e:
                    logger.error(f"Error generating click URL {i}: {e}")
                    continue

            logger.info(f"Successfully generated {len(generated_clicks)} click URLs")

            return {
                "status": "success",
                "message": f"Generated {len(generated_clicks)} click tracking URLs",
                "data": {
                    "campaignId": campaign_id,
                    "totalGenerated": len(generated_clicks),
                    "totalRequested": len(urls),
                    "clicks": generated_clicks
                }
            }

        except Exception as e:
            logger.error(f"Error in bulk click generation: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error during bulk generation"
            }
