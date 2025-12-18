# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:35
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Integration tests for JWT authentication end-to-end flow."""

import pytest
import json
from unittest.mock import Mock
import jwt
from datetime import datetime, timedelta

from src.config.settings import settings


class TestJWTIntegration:
    """Integration tests for JWT authentication flow."""

    def test_token_generation_endpoint_flow(self, client):
        """Test the complete flow of JWT token generation."""
        # Prepare test data
        auth_data = {
            "username": "test_user",
            "password": "test_password"
        }

        # Make request to token endpoint
        response = client.post(
            '/v1/auth/token',
            data=json.dumps(auth_data),
            headers={'Content-Type': 'application/json'}
        )

        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)

        # Check response structure
        assert 'access_token' in response_data
        assert 'token_type' in response_data
        assert 'expires_in' in response_data
        assert 'expires_at' in response_data
        assert response_data['token_type'] == 'Bearer'

        # Verify token is valid JWT
        token = response_data['access_token']
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.jwt_algorithm],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )

        assert decoded['sub'] == 'test_user'
        assert decoded['iss'] == 'supreme-octo-succotash-api'
        assert decoded['aud'] == 'supreme-octo-succotash-client'

    def test_protected_endpoint_with_valid_jwt(self, client):
        """Test accessing protected endpoint with valid JWT token."""
        # First, generate a valid JWT token
        now = datetime.utcnow()
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

        # Make request to protected endpoint with JWT
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Test with a protected endpoint (campaigns list)
        response = client.get('/v1/campaigns', headers=headers)

        # Should not return 401 (unauthenticated)
        assert response.status_code != 401

    def test_protected_endpoint_with_expired_jwt(self, client):
        """Test accessing protected endpoint with expired JWT token."""
        # Generate an expired JWT token
        now = datetime.utcnow()
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

        # Make request to protected endpoint with expired JWT
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = client.get('/v1/campaigns', headers=headers)

        # Should return 401 due to expired token
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['error']['code'] == 'TOKEN_EXPIRED'

    def test_protected_endpoint_with_invalid_jwt(self, client):
        """Test accessing protected endpoint with invalid JWT token."""
        # Use an obviously invalid token
        invalid_token = "invalid.jwt.token"

        headers = {
            'Authorization': f'Bearer {invalid_token}',
            'Content-Type': 'application/json'
        }

        response = client.get('/v1/campaigns', headers=headers)

        # Should return 401 due to invalid token
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['error']['code'] == 'INVALID_TOKEN'

    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        headers = {'Content-Type': 'application/json'}

        response = client.get('/v1/campaigns', headers=headers)

        # Should return 401 due to missing authentication
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['error']['code'] == 'UNAUTHENTICATED'

    def test_public_endpoint_without_auth(self, client):
        """Test accessing public endpoint without authentication."""
        # Health endpoint should be accessible without auth
        response = client.get('/v1/health')

        # Should succeed without authentication
        assert response.status_code == 200

    def test_token_generation_validation_errors(self, client):
        """Test token generation endpoint validation errors."""
        # Test missing username
        auth_data = {"password": "test_password"}
        response = client.post(
            '/v1/auth/token',
            data=json.dumps(auth_data),
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400

        # Test missing password
        auth_data = {"username": "test_user"}
        response = client.post(
            '/v1/auth/token',
            data=json.dumps(auth_data),
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400

        # Test empty request body
        response = client.post(
            '/v1/auth/token',
            data=json.dumps({}),
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400

    def test_token_generation_with_wrong_content_type(self, client):
        """Test token generation with wrong content type."""
        auth_data = {
            "username": "test_user",
            "password": "test_password"
        }

        # Wrong content type should be rejected
        response = client.post(
            '/v1/auth/token',
            data=json.dumps(auth_data),
            headers={'Content-Type': 'text/plain'}
        )
        assert response.status_code == 415  # Unsupported Media Type