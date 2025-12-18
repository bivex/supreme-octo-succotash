# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:00
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Encoding utilities for handling various character encodings."""

import logging

logger = logging.getLogger(__name__)


def safe_decode_string(value, encodings=('utf-8', 'windows-1251', 'iso-8859-1')) -> str:
    """
    Safely decode a string or bytes value trying multiple encodings.

    Args:
        value: String or bytes to decode
        encodings: Tuple of encodings to try in order

    Returns:
        Safely decoded string
    """
    if isinstance(value, str):
        return value

    if isinstance(value, bytes):
        for encoding in encodings:
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                continue

        # If all encodings fail, use 'replace' error handling
        logger.warning(f"Failed to decode bytes with any encoding, using replacement: {value[:50]}...")
        return value.decode('utf-8', errors='replace')

    # For other types, convert to string safely
    try:
        return str(value)
    except Exception as e:
        logger.warning(f"Failed to convert value to string: {e}")
        return repr(value)


def safe_string_for_logging(data) -> str:
    """
    Safely convert data to string for logging purposes.
    Handles dictionaries, lists, and other complex data structures.
    """
    if isinstance(data, dict):
        safe_dict = {}
        for k, v in data.items():
            safe_k = safe_decode_string(k)
            safe_v = safe_decode_string(v) if isinstance(v, (str, bytes)) else str(v)
            safe_dict[safe_k] = safe_v
        return str(safe_dict)
    elif isinstance(data, (list, tuple)):
        safe_list = []
        for item in data:
            if isinstance(item, (str, bytes)):
                safe_list.append(safe_decode_string(item))
            else:
                safe_list.append(str(item))
        return str(safe_list)
    else:
        return safe_decode_string(data)
