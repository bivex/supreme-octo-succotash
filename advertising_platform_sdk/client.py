"""
Advertising Platform API Client

Generated Python SDK for the Advertising Platform API.
Supports both sync and async operations with full type safety.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlencode

import httpx
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .models import *
from .exceptions import *


class AdvertisingPlatformClient:
    """
    Client for the Advertising Platform API

    Supports JWT Bearer token and API key authentication.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:5000/v1",
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API
            bearer_token: JWT bearer token for authentication
            api_key: API key for authentication (deprecated, use JWT)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            username: Username for JWT authentication
            password: Password for JWT authentication
        """
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.api_key = api_key  # Kept for backward compatibility
        self.timeout = timeout
        self.max_retries = max_retries
        self.username = username
        self.password = password

        # Create HTTP clients
        self._sync_client = None
        self._async_client = None

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with username/password and obtain JWT token.

        Args:
            username: Username for authentication
            password: Password for authentication

        Returns:
            Authentication response with JWT token
        """
        auth_data = {"username": username, "password": password}

        # Make direct request to auth endpoint (without authentication headers)
        url = urljoin(self.base_url + "/", "auth/token")

        for attempt in range(self.max_retries):
            try:
                if self._sync_client is None:
                    self._sync_client = httpx.Client(timeout=self.timeout)

                response = self._sync_client.post(url, json=auth_data)

                if response.status_code == 200:
                    token_data = response.json()
                    self.bearer_token = token_data.get("access_token")
                    logger.info("Successfully authenticated and obtained JWT token")
                    return token_data
                else:
                    error_data = response.json()
                    raise AuthenticationError(f"Authentication failed: {error_data.get('error', {}).get('message', 'Unknown error')}")

            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise APIConnectionError(f"Authentication request failed after {self.max_retries} attempts: {e}")
                continue

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Prioritize JWT token over API key for authentication
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        elif self.api_key:
            # Fallback to API key for backward compatibility
            headers["X-API-Key"] = self.api_key

        return headers

    def _get_sync_client(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._async_client

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        async_mode: bool = False,
    ) -> Union[httpx.Response, Any]:
        """Make HTTP request with retry logic."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        logger.debug(f"Making request: {method} {url} with params={params}, data={data}")

        if params:
            url += "?" + urlencode(params)

        client = self._get_async_client() if async_mode else self._get_sync_client()

        for attempt in range(self.max_retries):
            try:
                if async_mode:
                    response = asyncio.run(client.request(method, url, json=data))
                else:
                    response = client.request(method, url, json=data)
                logger.debug(f"Received response (status {response.status_code}): {response.text}")
                return response
            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise APIConnectionError(f"Request failed after {self.max_retries} attempts: {e}")
                continue

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        logger.debug(f"Handling response with status code: {response.status_code}")
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 201:
            return response.json() if response.content else {}
        elif response.status_code == 204:
            return {}
        elif response.status_code == 400:
            error_data = response.json()
            raise ValidationError(error_data.get("message", "Validation error"))
        elif response.status_code == 401:
            raise AuthenticationError("Authentication required")
        elif response.status_code == 403:
            raise AuthorizationError("Insufficient permissions")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found")
        elif response.status_code == 409:
            raise ConflictError("Resource conflict")
        elif response.status_code == 422:
            raise ValidationError("Unprocessable entity")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            raise APIError(f"HTTP {response.status_code}: {response.text}")

    # ============================================================================
    # HEALTH CHECK
    # ============================================================================

    def get_health(self) -> Dict[str, Any]:
        """
        Health check endpoint.

        Returns:
            Health status information
        """
        response = self._make_request("GET", "/health")
        return self._handle_response(response)

    async def get_health_async(self) -> Dict[str, Any]:
        """
        Health check endpoint (async).

        Returns:
            Health status information
        """
        response = await self._make_request("GET", "/health", async_mode=True)
        return self._handle_response(response)

    # ============================================================================
    # CAMPAIGNS
    # ============================================================================

    def get_campaigns(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get list of campaigns.

        Args:
            page: Page number for pagination
            page_size: Number of items per page
            status: Filter by campaign status
            search: Search term for campaign name

        Returns:
            Campaigns list with pagination
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if status is not None:
            params["status"] = status
        if search is not None:
            params["search"] = search

        response = self._make_request("GET", "/campaigns", params=params)
        return self._handle_response(response)

    def create_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new campaign.

        Args:
            campaign: Campaign data

        Returns:
            Created campaign data
        """
        response = self._make_request("POST", "/campaigns", data=campaign)
        return self._handle_response(response)

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign data
        """
        response = self._make_request("GET", f"/campaigns/{campaign_id}")
        return self._handle_response(response)

    def update_campaign(self, campaign_id: str, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update campaign.

        Args:
            campaign_id: Campaign identifier
            campaign: Updated campaign data

        Returns:
            Updated campaign data
        """
        response = self._make_request("PUT", f"/campaigns/{campaign_id}", data=campaign)
        return self._handle_response(response)

    def delete_campaign(self, campaign_id: str) -> None:
        """
        Delete campaign.

        Args:
            campaign_id: Campaign identifier
        """
        response = self._make_request("DELETE", f"/campaigns/{campaign_id}")
        self._handle_response(response)

    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Pause campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Updated campaign data
        """
        response = self._make_request("POST", f"/campaigns/{campaign_id}/pause")
        return self._handle_response(response)

    def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Resume campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Updated campaign data
        """
        response = self._make_request("POST", f"/campaigns/{campaign_id}/resume")
        return self._handle_response(response)

    # ============================================================================
    # ANALYTICS
    # ============================================================================

    def get_campaign_analytics(
        self,
        campaign_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        breakdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get campaign analytics.

        Args:
            campaign_id: Campaign identifier
            start_date: Start date for analytics (ISO format)
            end_date: End date for analytics (ISO format)
            breakdown: Analytics breakdown type

        Returns:
            Analytics data
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if breakdown:
            params["breakdown"] = breakdown

        response = self._make_request("GET", f"/campaigns/{campaign_id}/analytics", params=params)
        return self._handle_response(response)

    def get_real_time_analytics(
        self,
        campaign_id: Optional[str] = None,
        metric: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get real-time analytics.

        Args:
            campaign_id: Optional campaign filter
            metric: Specific metric to retrieve

        Returns:
            Real-time analytics data
        """
        params = {}
        if campaign_id:
            params["campaignId"] = campaign_id
        if metric:
            params["metric"] = metric

        response = self._make_request("GET", "/analytics/real-time", params=params)
        return self._handle_response(response)

    # ============================================================================
    # CLICKS
    # ============================================================================

    def track_click(self, click_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track a click event.

        Args:
            click_data: Click tracking data

        Returns:
            Click tracking response
        """
        response = self._make_request("POST", "/click", data=click_data)
        return self._handle_response(response)

    def get_click(self, click_id: str) -> Dict[str, Any]:
        """
        Get click by ID.

        Args:
            click_id: Click identifier

        Returns:
            Click data
        """
        response = self._make_request("GET", f"/click/{click_id}")
        return self._handle_response(response)

    def get_clicks(
        self,
        campaign_id: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get clicks list.

        Args:
            campaign_id: Filter by campaign
            page: Page number
            page_size: Items per page

        Returns:
            Clicks list with pagination
        """
        params = {}
        if campaign_id:
            params["campaignId"] = campaign_id
        if page:
            params["page"] = page
        if page_size:
            params["pageSize"] = page_size

        response = self._make_request("GET", "/clicks", params=params)
        return self._handle_response(response)

    def generate_click(self, click_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a click URL.

        Args:
            click_request: Click generation request

        Returns:
            Generated click data
        """
        response = self._make_request("POST", "/clicks/generate", data=click_request)
        return self._handle_response(response)

    def validate_click(self, click_id: str) -> Dict[str, Any]:
        """
        Validate click.

        Args:
            click_id: Click identifier

        Returns:
            Validation result
        """
        response = self._make_request("GET", f"/clicks/validate/{click_id}")
        return self._handle_response(response)

    # ============================================================================
    # CONVERSIONS
    # ============================================================================

    def track_conversion(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track a conversion event.

        Args:
            conversion_data: Conversion tracking data

        Returns:
            Conversion tracking response
        """
        response = self._make_request("POST", "/conversions/track", data=conversion_data)
        return self._handle_response(response)

    # ============================================================================
    # GOALS
    # ============================================================================

    def get_goals(
        self,
        campaign_id: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get goals list.

        Args:
            campaign_id: Filter by campaign
            page: Page number
            page_size: Items per page

        Returns:
            Goals list with pagination
        """
        params = {}
        if campaign_id:
            params["campaignId"] = campaign_id
        if page:
            params["page"] = page
        if page_size:
            params["pageSize"] = page_size

        response = self._make_request("GET", "/goals", params=params)
        return self._handle_response(response)

    def create_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new goal.

        Args:
            goal: Goal data

        Returns:
            Created goal data
        """
        response = self._make_request("POST", "/goals", data=goal)
        return self._handle_response(response)

    def get_goal(self, goal_id: str) -> Dict[str, Any]:
        """
        Get goal by ID.

        Args:
            goal_id: Goal identifier

        Returns:
            Goal data
        """
        response = self._make_request("GET", f"/goals/{goal_id}")
        return self._handle_response(response)

    def update_goal(self, goal_id: str, goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update goal.

        Args:
            goal_id: Goal identifier
            goal: Updated goal data

        Returns:
            Updated goal data
        """
        response = self._make_request("PUT", f"/goals/{goal_id}", data=goal)
        return self._handle_response(response)

    def delete_goal(self, goal_id: str) -> None:
        """
        Delete goal.

        Args:
            goal_id: Goal identifier
        """
        response = self._make_request("DELETE", f"/goals/{goal_id}")
        self._handle_response(response)

    def duplicate_goal(self, goal_id: str) -> Dict[str, Any]:
        """
        Duplicate goal.

        Args:
            goal_id: Goal identifier to duplicate

        Returns:
            Duplicated goal data
        """
        response = self._make_request("POST", f"/goals/{goal_id}/duplicate")
        return self._handle_response(response)

    def get_goal_templates(self) -> List[Dict[str, Any]]:
        """
        Get goal templates.

        Returns:
            List of goal templates
        """
        response = self._make_request("GET", "/goals/templates")
        return self._handle_response(response)

    # ============================================================================
    # CONTEXT MANAGEMENT
    # ============================================================================

    def close(self):
        """Close HTTP clients."""
        if self._sync_client:
            self._sync_client.close()
        if self._async_client:
            asyncio.run(self._async_client.aclose())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()