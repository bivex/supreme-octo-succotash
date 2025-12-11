"""
Module for tracking clicks and conversions
Integrates with Advertising Platform API for comprehensive tracking
"""

import asyncio
import base64
import hashlib
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import aiohttp
from loguru import logger

# Cache functions removed - now using Supreme API for URL generation
# Import config directly

# Default tracking parameters (inline to avoid import issues)
DEFAULT_TRACKING_PARAMS = {
    "sub1": "telegram_bot",
    "sub2": "local_landing",
    "sub3": "supreme_company",
    "sub4": "direct_message",
    "sub5": "premium_offer"
}

# Note: Now using Advertising Platform API instead of direct URL shortener calls


class TrackingManager:
    """Tracking manager for Advertising Platform API integration"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        # Advertising Platform API base URL
        self.api_base_url = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev"
        # Fallback URL for manual URL building
        self.local_landing_url = self.api_base_url

    async def __aenter__(self):
        # Initialize HTTP session for API calls
        self.session = aiohttp.ClientSession(
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'TelegramBot/1.0'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_click_id(self, user_id: int, timestamp: Optional[float] = None) -> str:
        """Generate unique click_id"""
        if timestamp is None:
            timestamp = time.time()

        # Create unique string based on user_id and timestamp
        unique_string = f"{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}"

        # Hash to get short ID
        click_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]

        return click_id

    def _build_tracking_url(self, click_id: str, additional_params: Optional[Dict[str, Any]] = None) -> str:
        """Build tracking URL using simple URL construction as fallback"""

        # Simple fallback URL construction
        params = {
            "click_id": click_id,
            "source": "telegram_bot_fallback",
            "cid": "camp_9061",
            **DEFAULT_TRACKING_PARAMS
        }

        # Add additional parameters
        if additional_params:
            params.update(additional_params)

        # Form URL
        query_string = urlencode(params, safe='')
        tracking_url = f"{self.api_base_url}/v1/click?{query_string}"

        logger.info(f"Generated fallback tracking URL: {tracking_url}")
        return tracking_url

    async def generate_tracking_link(self,
                                   user_id: int,
                                   source: str = "telegram_bot",
                                   additional_params: Optional[Dict[str, Any]] = None,
                                   lp_id: Optional[int] = None,
                                   offer_id: Optional[int] = None,
                                   ts_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate tracking link for user using API URL generation

        Args:
            user_id: Telegram user ID
            source: Traffic source
            additional_params: Additional tracking parameters

        Returns:
            Dictionary with click_id and tracking_url
        """

        timestamp = time.time()
        click_id = self._generate_click_id(user_id, timestamp)

        # Объединить параметры с ID для разрешения
        api_params = additional_params.copy() if additional_params else {}
        if lp_id:
            api_params["lp_id"] = lp_id
        if offer_id:
            api_params["offer_id"] = offer_id
        if ts_id:
            api_params["ts_id"] = ts_id

        # Use API to generate tracking URL with direct parameters
        tracking_url = await self._generate_short_tracking_url(user_id, click_id, source, api_params)

        # Save click information (if database exists)
        click_data = {
            "click_id": click_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "source": source,
            "tracking_url": tracking_url,
            "status": "generated"
        }

        logger.info(f"Generated tracking link for user {user_id}: {click_id}")

        # TODO: Save to database if needed
        # await self._save_click_data(click_data)

        return {
            "click_id": click_id,
            "tracking_url": tracking_url,
            "click_data": click_data
        }

    async def _generate_short_tracking_url(self, user_id: int, click_id: str, source: str, additional_params: Dict[str, Any]) -> str:
        """Generate tracking URL using Advertising Platform API"""
        try:
            logger.info("Generating tracking URL via Advertising Platform API...")

            # Prepare payload for API call
            payload = {
                "base_url": self.api_base_url,
                "campaign_id": 9061,  # Numeric ID as required by API
                "click_id": click_id,
                "source": source,
                "sub1": additional_params.get("sub1", source),
                "sub2": additional_params.get("sub2", "telegram"),
                "sub3": additional_params.get("sub3", "callback_offer"),
                "sub4": str(user_id),
                "sub5": additional_params.get("sub5", "premium_offer"),
                # Добавить параметры для разрешения по ID
                "lp_id": additional_params.get("lp_id"),  # Landing Page ID
                "offer_id": additional_params.get("offer_id"),  # Offer ID
                "ts_id": additional_params.get("ts_id"),  # Traffic Source ID
                "metadata": {
                    "user_id": user_id,
                    "bot_source": "telegram",
                    "generated_at": int(time.time())
                }
            }

            # Call Advertising Platform API
            url = f"{self.api_base_url}/clicks/generate"
            logger.info(f"Calling API: {url} with payload: {payload}")

            async with self.session.post(url, json=payload) as response:
                logger.info(f"API response status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    api_url = result.get("short_url") or result.get("tracking_url")

                    if api_url:
                        # Convert API URL format to expected /v1/click format
                        from urllib.parse import urlparse, parse_qs, urlencode
                        parsed = urlparse(api_url)
                        params = parse_qs(parsed.query)

                        # Keep ALL parameters from API response, including lp_id, offer_id, ts_id
                        # Remove any conflicting parameters and ensure proper format
                        final_params = {}
                        for key, values in params.items():
                            if key in ['cid', 'lp_id', 'offer_id', 'ts_id', 'sub1', 'sub2', 'sub3', 'sub4', 'sub5', 'click_id']:
                                final_params[key] = values[0] if isinstance(values, list) else values

                        # Ensure we have at least cid
                        if 'cid' not in final_params:
                            final_params['cid'] = 'camp_9061'

                        # Build proper URL format with ALL parameters
                        query_string = urlencode(final_params)
                        short_url = f"{self.api_base_url}/v1/click?{query_string}"

                        logger.info(f"Successfully generated short tracking URL: {short_url} (from API: {api_url})")
                        logger.info(f"Preserved parameters: {list(final_params.keys())}")
                        return short_url
                    else:
                        logger.error(f"API response missing URL: {result}")
                        raise ValueError("API response missing tracking URL")

                else:
                    response_text = await response.text()
                    logger.error(f"API call failed (status {response.status}): {response_text}")
                    raise Exception(f"API call failed: {response.status}")

        except Exception as e:
            logger.error(f"Error generating tracking URL via API: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Check if it's a network/connectivity issue
            if "503" in str(e) or "Connection" in str(e) or "timeout" in str(e).lower():
                logger.warning("API appears to be unavailable, using fallback URL generation")
            else:
                logger.warning("API returned error, using fallback URL generation")

            # Fallback to manual URL building
            logger.info("Falling back to manual URL generation")
            return self._build_tracking_url(click_id, additional_params)

    async def track_event(self,
                         click_id: str,
                         event_type: str,
                         event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send event to tracker

        Args:
            click_id: Click ID
            event_type: Event type (page_view, button_click, etc.)
            event_data: Additional event data

        Returns:
            True if successful
        """

        if not self.session:
            logger.warning("HTTP session not initialized - skipping event tracking")
            return False

        # Use Advertising Platform API for tracking
        logger.info(f"Tracking event via Advertising Platform API: {event_type} for click_id {click_id}")
        return await self._track_event_locally(click_id, event_type, event_data)

        try:
            payload = {
                "click_id": click_id,
                "event_type": event_type,
                "timestamp": int(time.time()),
                **(event_data or {})
            }

            url = f"{self.tracker_base_url}{API_ENDPOINTS['event_track']}"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Event tracked: {event_type} for click_id {click_id}")
                    return result.get("recorded", False)
                else:
                    logger.warning(f"Failed to track event (status {response.status}) - continuing without tracking")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking event (network issue): {e} - continuing without tracking")
            return False

    async def _track_event_locally(self, click_id: str, event_type: str, event_data: Optional[Dict[str, Any]] = None) -> bool:
        """Track event via Advertising Platform API"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping event tracking")
            return False

        try:
            # Prepare payload according to API docs
            payload = {
                "click_id": click_id,
                "event_type": event_type,
                "event_name": event_data.get("event_name", event_type) if event_data else event_type,
                "campaign_id": "camp_9061",  # String ID for events API
                "url": event_data.get("url", f"{self.local_landing_url}/landing") if event_data else f"{self.local_landing_url}/landing",
                "timestamp": int(time.time()),
                "properties": {
                    "source": "telegram_bot",
                    "user_agent": event_data.get("user_agent") if event_data else None,
                    "ip_address": event_data.get("ip_address") if event_data else None,
                    **(event_data.get("properties", {}) if event_data else {})
                }
            }

            # Remove None values
            payload["properties"] = {k: v for k, v in payload["properties"].items() if v is not None}

            url = f"{self.api_base_url}/events/track"

            logger.info(f"Sending event to API: {url}")
            logger.info(f"Event payload: {payload}")

            async with self.session.post(url, json=payload) as response:
                logger.info(f"Event tracking response status: {response.status}")
                response_text = await response.text()
                logger.info(f"Event tracking response: {response_text}")

                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success":
                        logger.info(f"Event tracked successfully: {event_type} for click_id {click_id}")
                        return True
                    else:
                        logger.warning(f"Event tracking failed: {result}")
                        return False
                else:
                    logger.warning(f"Event tracking failed (status {response.status}): {response_text}")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking event: {e}")
            return False

    async def track_conversion(self,
                             click_id: str,
                             conversion_type: str,
                             conversion_value: float = 0.0,
                             conversion_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send conversion to tracker

        Args:
            click_id: Click ID
            conversion_type: Conversion type (lead, sale, etc.)
            conversion_value: Conversion value
            conversion_data: Additional data

        Returns:
            True if successful
        """

        if not self.session:
            logger.warning("HTTP session not initialized - skipping conversion tracking")
            return False

        # Use Advertising Platform API for conversion tracking
        logger.info(f"Tracking conversion via Advertising Platform API: {conversion_type} for click_id {click_id}")
        return await self._track_conversion_locally(click_id, conversion_type, conversion_value, conversion_data)

        try:
            payload = {
                "click_id": click_id,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "currency": "RUB",
                "timestamp": int(time.time()),
                **(conversion_data or {})
            }

            url = f"{self.tracker_base_url}{API_ENDPOINTS['conversion_track']}"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Conversion tracked: {conversion_type} for click_id {click_id}")
                    return result.get("recorded", False)
                else:
                    logger.warning(f"Failed to track conversion (status {response.status}) - continuing without tracking")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking conversion (network issue): {e} - continuing without tracking")
            return False

    async def _track_conversion_locally(self, click_id: str, conversion_type: str, conversion_value: float = 0.0, conversion_data: Optional[Dict[str, Any]] = None) -> bool:
        """Track conversion via Advertising Platform API"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping conversion tracking")
            return False

        try:
            # Prepare payload according to API docs
            payload = {
                "click_id": click_id,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "currency": "RUB",
                "campaign_id": "camp_9061",  # String ID for conversions API
                "timestamp": int(time.time()),
                "properties": {
                    "source": "telegram_bot",
                    "user_id": conversion_data.get("user_id") if conversion_data else None,
                    "order_id": conversion_data.get("order_id") if conversion_data else None,
                    **(conversion_data or {})
                }
            }

            # Remove None values
            payload["properties"] = {k: v for k, v in payload["properties"].items() if v is not None}

            url = f"{self.api_base_url}/conversions/track"

            logger.info(f"Sending conversion to API: {url}")
            logger.info(f"Conversion payload: {payload}")

            async with self.session.post(url, json=payload) as response:
                logger.info(f"Conversion tracking response status: {response.status}")
                response_text = await response.text()
                logger.info(f"Conversion tracking response: {response_text}")

                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success" or result.get("recorded"):
                        logger.info(f"Conversion tracked successfully: {conversion_type} for click_id {click_id}")
                        return True
                    else:
                        logger.warning(f"Conversion tracking failed: {result}")
                        return False
                else:
                    logger.warning(f"Conversion tracking failed (status {response.status}): {response_text}")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking conversion: {e}")
            return False

    async def send_postback(self,
                          click_id: str,
                          postback_type: str,
                          postback_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send postback notification

        Args:
            click_id: Click ID
            postback_type: Postback type
            postback_data: Data to send

        Returns:
            True if successful
        """

        if not self.session:
            logger.warning("HTTP session not initialized - skipping postback")
            return False

        # Use Advertising Platform API for postback sending
        logger.info(f"Sending postback via Advertising Platform API: {postback_type} for click_id {click_id}")
        return await self._send_postback_locally(click_id, postback_type, postback_data)

        try:
            payload = {
                "click_id": click_id,
                "postback_type": postback_type,
                "timestamp": int(time.time()),
                **(postback_data or {})
            }

            url = f"{self.tracker_base_url}{API_ENDPOINTS['postback_send']}"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Postback sent: {postback_type} for click_id {click_id}")
                    return result.get("delivered", False)
                else:
                    logger.warning(f"Failed to send postback (status {response.status}) - continuing without postback")
                    return False

        except Exception as e:
            logger.warning(f"Error sending postback (network issue): {e} - continuing without postback")
            return False

    async def _send_postback_locally(self, click_id: str, postback_type: str, postback_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send postback via Advertising Platform API"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping postback")
            return False

        try:
            # Prepare payload according to API docs
            payload = {
                "click_id": click_id,
                "postback_type": postback_type,
                "campaign_id": "camp_9061",  # String ID for postbacks API
                "timestamp": int(time.time()),
                "properties": {
                    "source": "telegram_bot",
                    "webhook_url": postback_data.get("webhook_url") if postback_data else None,
                    "partner_id": postback_data.get("partner_id") if postback_data else None,
                    **(postback_data or {})
                }
            }

            # Remove None values
            payload["properties"] = {k: v for k, v in payload["properties"].items() if v is not None}

            url = f"{self.api_base_url}/postbacks/send"

            logger.info(f"Sending postback to API: {url}")
            logger.info(f"Postback payload: {payload}")

            async with self.session.post(url, json=payload) as response:
                logger.info(f"Postback response status: {response.status}")
                response_text = await response.text()
                logger.info(f"Postback response: {response_text}")

                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success" or result.get("delivered"):
                        logger.info(f"Postback sent successfully: {postback_type} for click_id {click_id}")
                        return True
                    else:
                        logger.warning(f"Postback failed: {result}")
                        return False
                else:
                    logger.warning(f"Postback failed (status {response.status}): {response_text}")
                    return False

        except Exception as e:
            logger.warning(f"Error sending postback: {e}")
            return False

    def extract_click_id_from_url(self, url: str) -> Optional[str]:
        """Extract click_id from landing URL"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            click_id = params.get('click_id', [None])[0]
            return click_id
        except Exception as e:
            logger.error(f"Error extracting click_id from URL: {e}")
            return None


# Global instance for use in handlers
tracking_manager = TrackingManager()


def get_tracking_manager() -> TrackingManager:
    """Get the current tracking manager instance"""
    return tracking_manager


async def init_tracking():
    """Initialize tracking manager"""
    global tracking_manager
    tracking_manager = TrackingManager()
    await tracking_manager.__aenter__()
    logger.info("Tracking manager initialized")


def get_tracking_manager() -> TrackingManager:
    """Get the initialized tracking manager instance"""
    return tracking_manager


async def close_tracking():
    """Close tracking manager connections"""
    global tracking_manager
    await tracking_manager.__aexit__(None, None, None)
    logger.info("Tracking manager closed")
