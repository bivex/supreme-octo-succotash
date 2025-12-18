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

from .error_handlers import (
    register_error_handlers,
    handle_internal_server_error,
    handle_bad_request_error,
    handle_not_found_error,
    handle_method_not_allowed_error,
    handle_unprocessable_entity_error,
    handle_unhandled_exception
)

__all__ = [
    'register_error_handlers',
    'handle_internal_server_error',
    'handle_bad_request_error',
    'handle_not_found_error',
    'handle_method_not_allowed_error',
    'handle_unprocessable_entity_error',
    'handle_unhandled_exception'
]
