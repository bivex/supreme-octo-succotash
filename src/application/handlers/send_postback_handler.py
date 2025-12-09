"""Send postback handler."""

import json
from typing import Dict, Any, List
from loguru import logger
from ...domain.repositories.postback_repository import PostbackRepository
from ...domain.repositories.conversion_repository import ConversionRepository
from ...domain.services.postback.postback_service import PostbackService
from ...domain.entities.postback import Postback, PostbackStatus


class SendPostbackHandler:
    """Handler for sending postback notifications."""

    def __init__(
        self,
        postback_repository: PostbackRepository,
        conversion_repository: ConversionRepository,
        postback_service: PostbackService
    ):
        self.postback_repository = postback_repository
        self.conversion_repository = conversion_repository
        self.postback_service = postback_service

    def handle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send postback notification."""
        try:
            logger.info("Processing postback send request")

            # Validate request
            if 'conversion_id' not in request_data:
                return {
                    "status": "error",
                    "message": "conversion_id is required"
                }

            if 'postback_config' not in request_data:
                return {
                    "status": "error",
                    "message": "postback_config is required"
                }

            conversion_id = request_data['conversion_id']
            postback_config = request_data['postback_config']

            # Validate postback configuration
            is_valid, error_message = self.postback_service.validate_postback_config(postback_config)
            if not is_valid:
                return {
                    "status": "error",
                    "message": f"Invalid postback configuration: {error_message}"
                }

            # Get conversion
            conversion = self.conversion_repository.get_by_id(conversion_id)
            if not conversion:
                return {
                    "status": "error",
                    "message": f"Conversion not found: {conversion_id}"
                }

            # Build postback URL with conversion data
            base_url = postback_config['url']
            conversion_data = {
                'click_id': conversion.click_id,
                'conversion_id': conversion.id,
                'conversion_type': conversion.conversion_type,
                'conversion_value': {
                    'amount': conversion.conversion_value.amount if conversion.conversion_value else 0,
                    'currency': conversion.conversion_value.currency if conversion.conversion_value else 'USD'
                } if conversion.conversion_value else None,
                'order_id': conversion.order_id,
                'product_id': conversion.product_id,
            }

            postback_url = self.postback_service.build_postback_url(base_url, conversion_data)

            # Update config with built URL
            updated_config = postback_config.copy()
            updated_config['url'] = postback_url

            # Create postback entity
            postback = Postback.create_from_conversion(conversion_id, updated_config)

            # Save postback
            self.postback_repository.save(postback)

            # Try to send immediately (synchronous for this handler)
            # In production, this would be done asynchronously
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response_code, response_body, error_message = loop.run_until_complete(
                    self.postback_service.send_postback(postback)
                )
                loop.close()

                # Update postback with result
                postback.mark_attempted(response_code, response_body, error_message)
                self.postback_repository.save(postback)

                success = response_code and 200 <= response_code < 300

                return {
                    "status": "success" if success else "failed",
                    "postback_id": postback.id,
                    "response_code": response_code,
                    "response_body": response_body,
                    "error_message": error_message,
                    "attempt_count": postback.attempt_count
                }

            except Exception as e:
                logger.error(f"Error sending postback: {e}")
                postback.mark_attempted(None, None, str(e))
                self.postback_repository.save(postback)

                return {
                    "status": "error",
                    "postback_id": postback.id,
                    "message": f"Failed to send postback: {str(e)}"
                }

        except Exception as e:
            logger.error(f"Error in send_postback handler: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
