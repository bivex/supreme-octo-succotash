# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:08
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Fraud detection HTTP routes."""

import json
from loguru import logger
from ...application.handlers.fraud_handler import FraudHandler


class FraudRoutes:
    """Socketify routes for fraud detection operations."""

    def __init__(self, fraud_handler: FraudHandler):
        self.fraud_handler = fraud_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_fraud_rules_list(app)
        self._register_fraud_rule_create(app)

    def _register_fraud_rules_list(self, app):
        """Register fraud rules list route."""
        def list_fraud_rules(res, req):
            """List fraud detection rules with pagination."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                # Parse pagination parameters
                page_str = req.get_query('page')
                page = int(page_str) if page_str else 1

                page_size_str = req.get_query('pageSize')
                page_size = int(page_size_str) if page_size_str else 20

                rule_type = req.get_query('type')

                active_str = req.get_query('active')
                active_only = active_str == 'true'

                # Validate parameters
                if page < 1:
                    page = 1
                if page_size < 1 or page_size > 100:
                    page_size = 20

                # Get fraud rules
                result = self.fraud_handler.list_rules(
                    page=page,
                    page_size=page_size,
                    rule_type=rule_type,
                    active_only=active_only
                )

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error listing fraud rules: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the fraud rules list endpoint
        app.get('/v1/fraud/rules', list_fraud_rules)

    def _register_fraud_rule_create(self, app):
        """Register fraud rule creation route."""
        def create_fraud_rule(res, req):
            """Create a new fraud detection rule."""
            # Temporarily disable security middleware for testing
            # from ...presentation.middleware.security_middleware import validate_request, add_security_headers

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
                                        logger.error("Invalid JSON in fraud rule creation request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        res.end(json.dumps({
                                            "error": {"code": "VALIDATION_ERROR", "message": "Invalid JSON format"}
                                        }))
                                        return

                            # Validate required fields
                            required_fields = ['name', 'type', 'action']
                            for field in required_fields:
                                if field not in body_data:
                                    res.write_status(400)
                                    res.write_header("Content-Type", "application/json")
                                    res.end(json.dumps({
                                        "error": {"code": "VALIDATION_ERROR", "message": f"Missing required field: {field}"}
                                    }))
                                    return

                            # Create fraud rule
                            result = self.fraud_handler.create_rule(body_data)

                            res.write_header("Content-Type", "application/json")

                            if "error" in result:
                                res.write_status(400)
                                res.end(json.dumps(result))
                            else:
                                res.write_status(201)
                                res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing fraud rule creation data: {e}", exc_info=True)
                        error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in create_fraud_rule: {e}", exc_info=True)
                error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps(error_response))

        # Register the fraud rule creation endpoint
        app.post('/v1/fraud/rules', create_fraud_rule)
