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
