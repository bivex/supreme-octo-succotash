# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:36
# Last Updated: 2025-12-18T12:12:36
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
Tests for Advertising Platform API Client

Comprehensive test suite covering all client functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import httpx

from advertising_platform_sdk.client import AdvertisingPlatformClient
from advertising_platform_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    APIError,
)


class TestAdvertisingPlatformClient:
    """Test cases for the Advertising Platform API client."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return AdvertisingPlatformClient(
            base_url="https://api.example.com/v1",
            bearer_token="test-token",
            timeout=10.0,
        )

    def test_client_initialization(self):
        """Test client initialization with different parameters."""
        # Test with bearer token
        client = AdvertisingPlatformClient(bearer_token="test-token")
        assert client.bearer_token == "test-token"
        assert client.api_key is None

        # Test with API key
        client = AdvertisingPlatformClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.bearer_token is None

        # Test custom base URL
        client = AdvertisingPlatformClient(base_url="https://custom.example.com/api")
        assert client.base_url == "https://custom.example.com/api"

    def test_get_headers(self, client):
        """Test header generation for authentication."""
        # Test with bearer token
        client.bearer_token = "test-token"
        client.api_key = None
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test-token"
        assert "X-API-Key" not in headers

        # Test with API key
        client.bearer_token = None
        client.api_key = "test-key"
        headers = client._get_headers()
        assert headers["X-API-Key"] == "test-key"
        assert "Authorization" not in headers

        # Test without authentication
        client.bearer_token = None
        client.api_key = None
        headers = client._get_headers()
        assert "Authorization" not in headers
        assert "X-API-Key" not in headers

    @patch('httpx.Client.request')
    def test_health_check(self, mock_request, client):
        """Test health check endpoint."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_request.return_value = mock_response

        result = client.get_health()

        assert result == {"status": "healthy"}
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert "health" in args[1]

    @patch('httpx.Client.request')
    def test_get_campaigns(self, mock_request, client):
        """Test get campaigns endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "1", "name": "Test Campaign"}],
            "pagination": {"page": 1, "total": 1}
        }
        mock_request.return_value = mock_response

        result = client.get_campaigns(page=1, page_size=20, status="active")

        assert result["data"][0]["name"] == "Test Campaign"
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert "campaigns" in args[1]
        assert "page=1" in args[1]
        assert "pageSize=20" in args[1]
        assert "status=active" in args[1]

    @patch('httpx.Client.request')
    def test_create_campaign(self, mock_request, client):
        """Test create campaign endpoint."""
        campaign_data = {
            "name": "New Campaign",
            "status": "active",
            "budget": {"amount": 1000.0, "currency": "USD"}
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {**campaign_data, "id": "123"}
        mock_request.return_value = mock_response

        result = client.create_campaign(campaign_data)

        assert result["id"] == "123"
        assert result["name"] == "New Campaign"
        mock_request.assert_called_once_with(
            "POST",
            "https://api.example.com/v1/campaigns",
            json=campaign_data
        )

    @patch('httpx.Client.request')
    def test_get_campaign(self, mock_request, client):
        """Test get campaign by ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "Test Campaign"}
        mock_request.return_value = mock_response

        result = client.get_campaign("123")

        assert result["id"] == "123"
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://api.example.com/v1/campaigns/123"

    @patch('httpx.Client.request')
    def test_update_campaign(self, mock_request, client):
        """Test update campaign."""
        update_data = {"name": "Updated Campaign", "status": "paused"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", **update_data}
        mock_request.return_value = mock_response

        result = client.update_campaign("123", update_data)

        assert result["name"] == "Updated Campaign"
        mock_request.assert_called_once_with(
            "PUT",
            "https://api.example.com/v1/campaigns/123",
            json=update_data
        )

    @patch('httpx.Client.request')
    def test_delete_campaign(self, mock_request, client):
        """Test delete campaign."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        client.delete_campaign("123")

        mock_request.assert_called_once_with(
            "DELETE",
            "https://api.example.com/v1/campaigns/123",
            json=None
        )

    @patch('httpx.Client.request')
    def test_pause_campaign(self, mock_request, client):
        """Test pause campaign."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "status": "paused"}
        mock_request.return_value = mock_response

        result = client.pause_campaign("123")

        assert result["status"] == "paused"
        mock_request.assert_called_once_with(
            "POST",
            "https://api.example.com/v1/campaigns/123/pause",
            json=None
        )

    @patch('httpx.Client.request')
    def test_resume_campaign(self, mock_request, client):
        """Test resume campaign."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "status": "active"}
        mock_request.return_value = mock_response

        result = client.resume_campaign("123")

        assert result["status"] == "active"
        mock_request.assert_called_once_with(
            "POST",
            "https://api.example.com/v1/campaigns/123/resume",
            json=None
        )

    @patch('httpx.Client.request')
    def test_track_click(self, mock_request, client):
        """Test click tracking."""
        click_data = {
            "campaign_id": "123",
            "click_id": "click-456",
            "user_agent": "Mozilla/5.0...",
            "ip_address": "192.168.1.1"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"click_id": "click-456", "tracked": True}
        mock_request.return_value = mock_response

        result = client.track_click(click_data)

        assert result["tracked"] is True
        mock_request.assert_called_once_with(
            "POST",
            "https://api.example.com/v1/click",
            json=click_data
        )

    @patch('httpx.Client.request')
    def test_track_conversion(self, mock_request, client):
        """Test conversion tracking."""
        conversion_data = {
            "click_id": "click-456",
            "goal_id": "goal-123",
            "revenue": {"amount": 25.50, "currency": "USD"}
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"conversion_id": "conv-789", "tracked": True}
        mock_request.return_value = mock_response

        result = client.track_conversion(conversion_data)

        assert result["tracked"] is True
        mock_request.assert_called_once_with(
            "POST",
            "https://api.example.com/v1/conversions/track",
            json=conversion_data
        )

    @patch('httpx.Client.request')
    def test_get_goals(self, mock_request, client):
        """Test get goals."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "1", "name": "Purchase Goal"}],
            "pagination": {"page": 1, "total": 1}
        }
        mock_request.return_value = mock_response

        result = client.get_goals(campaign_id="123", page=1, page_size=10)

        assert result["data"][0]["name"] == "Purchase Goal"
        args, kwargs = mock_request.call_args
        assert "campaignId=123" in args[1]
        assert "page=1" in args[1]
        assert "pageSize=10" in args[1]

    @patch('httpx.Client.request')
    def test_create_goal(self, mock_request, client):
        """Test create goal."""
        goal_data = {
            "name": "Purchase Goal",
            "campaign_id": "123",
            "type": "purchase",
            "value": {"amount": 50.0, "currency": "USD"}
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {**goal_data, "id": "goal-456"}
        mock_request.return_value = mock_response

        result = client.create_goal(goal_data)

        assert result["id"] == "goal-456"
        mock_request.assert_called_once_with(
            "POST",
            "https://api.example.com/v1/goals",
            json=goal_data
        )

    @patch('httpx.Client.request')
    def test_get_goal_templates(self, mock_request, client):
        """Test get goal templates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "template-1", "name": "Purchase Template"},
            {"id": "template-2", "name": "Lead Template"}
        ]
        mock_request.return_value = mock_response

        result = client.get_goal_templates()

        assert len(result) == 2
        assert result[0]["name"] == "Purchase Template"
        mock_request.assert_called_once_with(
            "GET",
            "https://api.example.com/v1/goals/templates",
            json=None
        )

    # Error handling tests
    @patch('httpx.Client.request')
    def test_authentication_error(self, mock_request, client):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid token"}
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.get_health()

    @patch('httpx.Client.request')
    def test_authorization_error(self, mock_request, client):
        """Test authorization error handling."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"message": "Insufficient permissions"}
        mock_request.return_value = mock_response

        with pytest.raises(AuthorizationError):
            client.get_campaigns()

    @patch('httpx.Client.request')
    def test_not_found_error(self, mock_request, client):
        """Test not found error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Campaign not found"}
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError):
            client.get_campaign("nonexistent")

    @patch('httpx.Client.request')
    def test_validation_error(self, mock_request, client):
        """Test validation error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid campaign data"}
        mock_request.return_value = mock_response

        with pytest.raises(ValidationError):
            client.create_campaign({})

    @patch('httpx.Client.request')
    def test_rate_limit_error(self, mock_request, client):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError):
            client.get_health()

    @patch('httpx.Client.request')
    def test_server_error(self, mock_request, client):
        """Test server error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_request.return_value = mock_response

        with pytest.raises(APIError):
            client.get_health()