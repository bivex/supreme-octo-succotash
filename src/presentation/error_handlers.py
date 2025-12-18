# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:02
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Error handlers for the application."""

# HTTP Status Code Constants
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_INTERNAL_SERVER_ERROR = 500


def register_error_handlers(app):
    """Register error handlers with Flask app."""

    @app.errorhandler(HTTP_BAD_REQUEST)
    def bad_request_error(error):
        return {"error": {"code": "BAD_REQUEST", "message": "Bad request"}}, HTTP_BAD_REQUEST

    @app.errorhandler(HTTP_NOT_FOUND)
    def not_found_error(error):
        return {"error": {"code": "NOT_FOUND", "message": "Endpoint not found"}}, HTTP_NOT_FOUND

    @app.errorhandler(HTTP_METHOD_NOT_ALLOWED)
    def method_not_allowed_error(error):
        return {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}}, HTTP_METHOD_NOT_ALLOWED

    @app.errorhandler(HTTP_UNPROCESSABLE_ENTITY)
    def unprocessable_entity_error(error):
        return {"error": {"code": "VALIDATION_ERROR", "message": "Unprocessable entity"}}, HTTP_UNPROCESSABLE_ENTITY

    @app.errorhandler(HTTP_INTERNAL_SERVER_ERROR)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return {
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}, HTTP_INTERNAL_SERVER_ERROR

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        return {
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}}, HTTP_INTERNAL_SERVER_ERROR
