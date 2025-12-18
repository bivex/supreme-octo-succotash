"""Unit tests for JWT authentication functionality."""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.config.settings import settings


class TestJWTAuthentication:
    """Test JWT authentication functionality."""

    def test_jwt_token_generation(self):
        """Test JWT token generation with valid payload."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(
            payload,
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )

        # Decode and verify
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.jwt_algorithm],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )

        assert decoded["sub"] == "test_user"
        assert decoded["iss"] == "supreme-octo-succotash-api"
        assert decoded["aud"] == "supreme-octo-succotash-client"

    def test_jwt_token_validation_success(self):
        """Test successful JWT token validation."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(
            payload,
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )

        # Should not raise an exception
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.jwt_algorithm],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )

        assert decoded["sub"] == "test_user"

    def test_jwt_token_expired(self):
        """Test JWT token validation with expired token."""
        now = datetime.now(timezone.utc)
        expired_at = now - timedelta(hours=1)  # Already expired

        payload = {
            "sub": "test_user",
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int(expired_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(
            payload,
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )

        # Should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                settings.security.secret_key,
                algorithms=[settings.security.jwt_algorithm],
                audience="supreme-octo-succotash-client",
                issuer="supreme-octo-succotash-api"
            )

    def test_jwt_token_invalid_signature(self):
        """Test JWT token validation with invalid signature."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(
            payload,
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )

        # Try to decode with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                token,
                "wrong_secret_key",
                algorithms=[settings.security.jwt_algorithm],
                audience="supreme-octo-succotash-client",
                issuer="supreme-octo-succotash-api"
            )

    def test_jwt_token_wrong_audience(self):
        """Test JWT token validation with wrong audience."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(
            payload,
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )

        # Try to decode with wrong audience
        with pytest.raises(jwt.InvalidAudienceError):
            jwt.decode(
                token,
                settings.security.secret_key,
                algorithms=[settings.security.jwt_algorithm],
                audience="wrong-audience",
                issuer="supreme-octo-succotash-api"
            )

    def test_jwt_token_wrong_issuer(self):
        """Test JWT token validation with wrong issuer."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(
            payload,
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )

        # Try to decode with wrong issuer
        with pytest.raises(jwt.InvalidIssuerError):
            jwt.decode(
                token,
                settings.security.secret_key,
                algorithms=[settings.security.jwt_algorithm],
                audience="supreme-octo-succotash-client",
                issuer="wrong-issuer"
            )


class TestSDKAuthentication:
    """Test SDK authentication functionality."""

    @patch('advertising_platform_sdk.client.httpx.Client')
    def test_sdk_authenticate_success(self, mock_client_class):
        """Test successful SDK authentication."""
        from advertising_platform_sdk import AdvertisingPlatformClient

        # Mock the HTTP client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test.jwt.token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create client and authenticate
        client = AdvertisingPlatformClient(base_url="http://test.com")
        result = client.authenticate("testuser", "testpass")

        # Verify the result
        assert result["access_token"] == "test.jwt.token"
        assert result["token_type"] == "Bearer"
        assert client.bearer_token == "test.jwt.token"

        # Verify the request was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://test.com/auth/token"
        assert call_args[1]["json"] == {"username": "testuser", "password": "testpass"}

    @patch('advertising_platform_sdk.client.httpx.Client')
    def test_sdk_authenticate_failure(self, mock_client_class):
        """Test SDK authentication failure."""
        from advertising_platform_sdk import AdvertisingPlatformClient
        from advertising_platform_sdk.exceptions import AuthenticationError

        # Mock the HTTP client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {"message": "Invalid credentials"}
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create client and try to authenticate
        client = AdvertisingPlatformClient(base_url="http://test.com")

        with pytest.raises(AuthenticationError):
            client.authenticate("wronguser", "wrongpass")

    def test_sdk_headers_prioritize_jwt(self):
        """Test that SDK prioritizes JWT tokens over API keys."""
        from advertising_platform_sdk import AdvertisingPlatformClient

        # Test with JWT token
        client = AdvertisingPlatformClient(
            base_url="http://test.com",
            bearer_token="test.jwt.token",
            api_key="test_api_key"
        )

        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test.jwt.token"
        assert "X-API-Key" not in headers

    def test_sdk_headers_fallback_to_api_key(self):
        """Test that SDK falls back to API key when no JWT token."""
        from advertising_platform_sdk import AdvertisingPlatformClient

        # Test with only API key
        client = AdvertisingPlatformClient(
            base_url="http://test.com",
            api_key="test_api_key"
        )

        headers = client._get_headers()
        assert headers["X-API-Key"] == "test_api_key"
        assert "Authorization" not in headers