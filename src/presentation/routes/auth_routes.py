# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:12
# Last Updated: 2025-12-18T12:13:12
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Authentication routes for JWT token generation."""

import json
import time
import jwt
from datetime import datetime, timedelta, timezone
from loguru import logger

from ..config.settings import settings


class AuthRoutes:
    """Socketify routes for authentication operations."""

    def register(self, app):
        """Register authentication routes with socketify app."""
        self._register_token_endpoint(app)

    def _register_token_endpoint(self, app):
        """Register JWT token generation endpoint."""
        def generate_token(res, req):
            """Generate JWT token for authentication."""
            try:
                # Parse request body
                data_parts = []

                def on_data(res, chunk, is_last, *args):
                    try:
                        if chunk:
                            data_parts.append(chunk)

                        if is_last:
                            # Parse body
                            body_data = {}
                            if data_parts:
                                full_body = b"".join(data_parts)
                                if full_body:
                                    try:
                                        body_data = json.loads(full_body)
                                    except (ValueError, json.JSONDecodeError):
                                        logger.error("Invalid JSON in token request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        res.end(json.dumps({
                                            "error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON format"}
                                        }))
                                        return

                            # Validate request data
                            username = body_data.get('username')
                            password = body_data.get('password')

                            if not username or not password:
                                res.write_status(400)
                                res.write_header("Content-Type", "application/json")
                                res.end(json.dumps({
                                    "error": {"code": "VALIDATION_ERROR", "message": "Username and password required"}
                                }))
                                return

                            # TODO: Replace with actual user authentication logic
                            # For now, accept any username/password combination for demo
                            if username and password:
                                # Generate JWT token
                                now = datetime.now(timezone.utc)
                                expires_at = now + timedelta(hours=settings.security.jwt_expiration_hours)

                                payload = {
                                    "sub": username,  # Subject (user identifier)
                                    "iat": int(now.timestamp()),  # Issued at
                                    "exp": int(expires_at.timestamp()),  # Expiration time
                                    "iss": "supreme-octo-succotash-api",  # Issuer
                                    "aud": "supreme-octo-succotash-client"  # Audience
                                }

                                token = jwt.encode(
                                    payload,
                                    settings.security.secret_key,
                                    algorithm=settings.security.jwt_algorithm
                                )

                                response = {
                                    "access_token": token,
                                    "token_type": "Bearer",
                                    "expires_in": int((expires_at - now).total_seconds()),
                                    "expires_at": expires_at.isoformat()
                                }

                                res.write_header("Content-Type", "application/json")
                                res.end(json.dumps(response))
                            else:
                                res.write_status(401)
                                res.write_header("Content-Type", "application/json")
                                res.end(json.dumps({
                                    "error": {"code": "AUTHENTICATION_ERROR", "message": "Invalid credentials"}
                                }))

                    except Exception as e:
                        logger.error(f"Error processing token generation data: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in generate_token: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        # Register the POST endpoint for token generation
        app.post('/v1/auth/token', generate_token)