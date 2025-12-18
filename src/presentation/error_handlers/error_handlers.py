# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:16
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Error handlers for the application."""

import json

# HTTP Status Code Constants
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_INTERNAL_SERVER_ERROR = 500


def register_error_handlers(app):
    """Register error handlers with socketify app."""
    # Socketify handles errors differently - we need to set up error handlers
    # that can be called from route handlers when exceptions occur

    # For socketify, we'll handle errors within the route handlers themselves
    # rather than using global error handlers like Flask
    pass


def handle_bad_request_error(res):
    """Handle bad request error."""
    error_response = {"error": {"code": "BAD_REQUEST", "message": "Bad request"}}
    res.write_status(HTTP_BAD_REQUEST)
    res.write_header("Content-Type", "application/json")
    res.end(json.dumps(error_response))


def handle_not_found_error(res, is_click_endpoint=False):
    """Handle not found error."""
    if is_click_endpoint:
        error_html = "<html><body><h1>Error</h1><p>Campaign not found</p></body></html>"
        res.write_status(HTTP_NOT_FOUND)
        res.write_header("Content-Type", "text/html")
        res.end(error_html)
    else:
        error_response = {"error": {"code": "NOT_FOUND", "message": "Endpoint not found"}}
        res.write_status(HTTP_NOT_FOUND)
        res.write_header("Content-Type", "application/json")
        res.end(json.dumps(error_response))


def handle_method_not_allowed_error(res):
    """Handle method not allowed error."""
    error_response = {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}}
    res.write_status(HTTP_METHOD_NOT_ALLOWED)
    res.write_header("Allow", "GET, POST, PUT, DELETE, OPTIONS")
    res.write_header("Content-Type", "application/json")
    res.end(json.dumps(error_response))


def handle_unprocessable_entity_error(res):
    """Handle unprocessable entity error."""
    error_response = {"error": {"code": "VALIDATION_ERROR", "message": "Unprocessable entity"}}
    res.write_status(HTTP_UNPROCESSABLE_ENTITY)
    res.write_header("Content-Type", "application/json")
    res.end(json.dumps(error_response))


def handle_internal_server_error(res, logger=None):
    """Handle internal server error."""
    if logger:
        logger.error("Internal server error occurred")
    error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
    res.write_status(HTTP_INTERNAL_SERVER_ERROR)
    res.write_header("Content-Type", "application/json")
    res.end(json.dumps(error_response))


def handle_unhandled_exception(res, error, logger=None):
    """Handle unhandled exception."""
    if logger:
        logger.error(f"Unhandled exception: {error}")
    error_response = {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}
    res.write_status(HTTP_INTERNAL_SERVER_ERROR)
    res.write_header("Content-Type", "application/json")
    res.end(json.dumps(error_response))
