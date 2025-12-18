# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Postback service for sending notifications."""

from typing import Dict, Any, Optional, Tuple

import aiohttp
from loguru import logger

from ...entities.postback import Postback


class PostbackService:
    """Service for sending postback notifications."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize HTTP session."""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self):
        """Cleanup HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def send_postback(self, postback: Postback) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """Send a postback notification."""
        try:
            await self.initialize()

            if not self._session:
                return None, None, "HTTP session not initialized"

            # Prepare request data
            url = postback.url
            method = postback.method.upper()
            headers = postback.headers or {}
            headers.setdefault('User-Agent', 'Affiliate-API-Postback/1.0')

            # Prepare payload
            data = None
            params = None

            if postback.payload:
                if method == 'GET':
                    # For GET requests, add payload as query parameters
                    params = postback.payload
                else:
                    # For POST/PUT, send as JSON
                    data = postback.payload
                    headers.setdefault('Content-Type', 'application/json')

            logger.info(f"Sending {method} postback to {url}")

            # Send request
            async with self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data if isinstance(data, dict) else None,
                    data=data if not isinstance(data, dict) else None
            ) as response:
                response_code = response.status
                response_text = await response.text()

                logger.info(f"Postback response: {response_code} from {url}")

                return response_code, response_text, None

        except aiohttp.ClientError as e:
            error_msg = f"HTTP client error: {str(e)}"
            logger.error(f"Postback failed for {postback.url}: {error_msg}")
            return None, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Postback failed for {postback.url}: {error_msg}")
            return None, None, error_msg

    def validate_postback_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate postback configuration."""
        try:
            if 'url' not in config:
                return False, "URL is required"

            url = config['url']
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                return False, "Invalid URL format"

            method = config.get('method', 'GET').upper()
            if method not in ['GET', 'POST', 'PUT']:
                return False, f"Unsupported HTTP method: {method}"

            max_attempts = config.get('max_attempts', 3)
            if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 10:
                return False, "max_attempts must be between 1 and 10"

            return True, None

        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"

    def build_postback_url(self, base_url: str, conversion_data: Dict[str, Any]) -> str:
        """Build postback URL with conversion parameters."""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        # Parse the base URL
        parsed = urlparse(base_url)

        # Get existing query parameters
        existing_params = parse_qs(parsed.query)

        # Add conversion parameters (these will override existing ones)
        conversion_params = {
            'click_id': conversion_data.get('click_id', ''),
            'conversion_id': conversion_data.get('conversion_id', ''),
            'conversion_type': conversion_data.get('conversion_type', ''),
            'order_id': conversion_data.get('order_id', ''),
            'product_id': conversion_data.get('product_id', ''),
        }

        # Add revenue if available
        if 'conversion_value' in conversion_data and conversion_data['conversion_value']:
            value_data = conversion_data['conversion_value']
            if isinstance(value_data, dict):
                conversion_params['revenue'] = str(value_data.get('amount', '0'))
                conversion_params['currency'] = value_data.get('currency', 'USD')

        # Merge parameters (conversion params take precedence)
        merged_params = {**existing_params, **conversion_params}

        # Build new query string
        new_query = urlencode(merged_params, doseq=True)

        # Reconstruct URL
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
