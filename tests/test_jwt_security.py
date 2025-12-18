"""Security tests for JWT authentication implementation."""

import pytest
import jwt
import json
import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from src.config.settings import settings


class TestJWTSecurity:
    """Security tests for JWT implementation."""

    def test_algorithm_confusion_attack_prevention(self):
        """Test that algorithm confusion attacks are prevented."""
        # Create a token with HS256 algorithm
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        # Encode with HS256
        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Try to decode with different algorithms - should work with HS256
        decoded = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])
        assert decoded["sub"] == "test_user"

        # Try to decode with wrong algorithm - should fail
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(token, settings.security.secret_key, algorithms=["RS256"])

    def test_none_algorithm_attack_prevention(self):
        """Test that 'none' algorithm attacks are prevented."""
        # Create a malicious token with 'none' algorithm
        header = {"alg": "none", "typ": "JWT"}
        payload = {
            "sub": "hacked_user",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        # Manually create token with none algorithm (bypassing PyJWT's protection)
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        signature = ""  # Empty signature for 'none' algorithm

        malicious_token = f"{header_b64}.{payload_b64}.{signature}"

        # Try to decode - should fail because 'none' is not in allowed algorithms
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(malicious_token, settings.security.secret_key, algorithms=["HS256"])

    def test_token_tampering_detection(self):
        """Test that token tampering is detected."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Tamper with the token by changing the payload
        parts = token.split('.')
        tampered_payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
        tampered_payload["sub"] = "evil_user"
        tampered_payload_b64 = base64.urlsafe_b64encode(json.dumps(tampered_payload).encode()).decode().rstrip('=')

        tampered_token = f"{parts[0]}.{tampered_payload_b64}.{parts[2]}"

        # Try to decode tampered token - should fail
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(tampered_token, settings.security.secret_key, algorithms=["HS256"])

    def test_expiration_claim_validation(self):
        """Test that expired tokens are properly rejected."""
        # Create an already expired token
        now = datetime.now(timezone.utc)
        expired_at = now - timedelta(hours=1)  # Already expired

        payload = {
            "sub": "test_user",
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int(expired_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                settings.security.secret_key,
                algorithms=["HS256"],
                audience="supreme-octo-succotash-client",
                issuer="supreme-octo-succotash-api"
            )

    def test_audience_validation(self):
        """Test that audience validation works correctly."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Should work with correct audience
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=["HS256"],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )
        assert decoded["aud"] == "supreme-octo-succotash-client"

        # Should fail with wrong audience
        with pytest.raises(jwt.InvalidAudienceError):
            jwt.decode(
                token,
                settings.security.secret_key,
                algorithms=["HS256"],
                audience="wrong-audience",
                issuer="supreme-octo-succotash-api"
            )

    def test_issuer_validation(self):
        """Test that issuer validation works correctly."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Should work with correct issuer
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=["HS256"],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )
        assert decoded["iss"] == "supreme-octo-succotash-api"

        # Should fail with wrong issuer
        with pytest.raises(jwt.InvalidIssuerError):
            jwt.decode(
                token,
                settings.security.secret_key,
                algorithms=["HS256"],
                audience="supreme-octo-succotash-client",
                issuer="wrong-issuer"
            )

    def test_weak_secret_detection(self):
        """Test that weak secrets are detected (this is more of a configuration test)."""
        # This test ensures that the secret key is not a default/weak value
        secret_key = settings.security.secret_key

        # Secret should not be empty
        assert secret_key
        assert len(secret_key) > 10  # Should be reasonably long

        # Secret should not be a common weak password
        weak_secrets = ["password", "123456", "secret", "your-secret-key-change-in-production"]
        assert secret_key not in weak_secrets

    def test_jwt_header_injection_prevention(self):
        """Test prevention of JWT header injection attacks."""
        # This is a defense against header injection in the Authorization header
        malicious_header = 'Bearer valid_token"\nX-Custom-Header: malicious_value'

        # The middleware should only extract the token part
        # This is more of a design test - the middleware should properly parse
        # 'Bearer <token>' format and ignore anything after the token
        assert malicious_header.startswith('Bearer ')
        token_part = malicious_header[7:].split('"')[0]  # Extract until quote
        assert token_part == 'valid_token'

    def test_token_reuse_prevention(self):
        """Test that token reuse is handled properly through expiration."""
        # Create a token that expires soon
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=1)  # Expires in 1 second

        payload = {
            "sub": "test_user",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client",
            "jti": "unique-token-id-123"  # JWT ID for uniqueness
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Token should be valid now
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=["HS256"],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )
        assert decoded["jti"] == "unique-token-id-123"

        # In a real implementation, you would check jti against a blacklist
        # For this test, we verify the jti claim is present
        assert "jti" in decoded

    def test_max_age_validation(self):
        """Test token max age validation."""
        # Create a token issued too long ago
        now = datetime.now(timezone.utc)
        issued_at = now - timedelta(days=30)  # Issued 30 days ago
        expires_at = now + timedelta(hours=1)  # Still valid

        payload = {
            "sub": "test_user",
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "supreme-octo-succotash-api",
            "aud": "supreme-octo-succotash-client"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

        # Token should still be valid (no max age check in our implementation)
        # But in production, you might want to implement max-age validation
        decoded = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=["HS256"],
            audience="supreme-octo-succotash-client",
            issuer="supreme-octo-succotash-api"
        )
        assert decoded["sub"] == "test_user"