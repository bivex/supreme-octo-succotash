"""
Shared URL shortener module for both tracking and API server
"""

import json
import base64
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs, urlparse, urlencode

# Base58 alphabet (Bitcoin style, excludes 0, O, I, l for readability)
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def base58_encode(data: bytes) -> str:
    """Encode bytes to base58 string."""
    if not data:
        return ''

    # Convert to integer
    n = int.from_bytes(data, 'big')

    result = []
    while n > 0:
        n, remainder = divmod(n, 58)
        result.append(BASE58_ALPHABET[remainder])

    # Handle leading zeros
    for byte in data:
        if byte == 0:
            result.append(BASE58_ALPHABET[0])
        else:
            break

    return ''.join(result[::-1])

def base58_decode(s: str) -> bytes:
    """Decode base58 string to bytes."""
    if not s:
        return b''

    n = 0
    for char in s:
        n = n * 58 + BASE58_ALPHABET.index(char)

    # Convert to bytes
    h = hex(n)[2:]
    if len(h) % 2:
        h = '0' + h
    return bytes.fromhex(h)


class URLShortener:
    """URL shortener with self-contained encoding for tracking parameters."""

    def __init__(self):
        """Initialize URL shortener with self-contained encoding."""
        pass

    def encode_params(self, params_dict: Dict[str, Any]) -> str:
        """
        Encode parameters into a very short identifier (max 10 chars).

        Args:
            params_dict: Dictionary of parameters to encode

        Returns:
            Short encoded identifier
        """
        # Create compact binary format for common tracking parameters
        import struct

        try:
            # Extract common parameters with defaults
            cid_str = str(params_dict.get('cid', '0'))
            cid = int(cid_str) if cid_str.isdigit() else hash(cid_str) % 1000000

            sub1 = params_dict.get('sub1', '')
            sub2 = params_dict.get('sub2', '')
            sub3 = params_dict.get('sub3', '')
            sub4 = params_dict.get('sub4', '')
            sub5 = params_dict.get('sub5', '')

            # Create compact binary representation
            # Format: cid(4 bytes) + len(sub1)(1) + sub1 + len(sub2)(1) + sub2 + ...
            data = struct.pack('>I', cid & 0xFFFFFFFF)  # 4 bytes for cid

            for sub in [sub1, sub2, sub3, sub4, sub5]:
                sub_bytes = sub.encode('utf-8')[:31]  # Max 31 chars per sub
                data += bytes([len(sub_bytes)]) + sub_bytes

            # Fill remaining space to make it predictable
            while len(data) < 16:
                data += b'\x00'

            # Encode with base62 for maximum compactness
            encoded = self._base62_encode(data)

            # Ensure max 10 characters
            return encoded[:10]

        except Exception:
            # Fallback to simple hash if binary encoding fails
            query_string = urlencode(params_dict, doseq=True)
            return base58_encode(query_string.encode('utf-8'))[:10]

    def _base62_encode(self, data: bytes) -> str:
        """Encode bytes to base62 string."""
        if not data:
            return '0'

        BASE62 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        result = []

        # Convert bytes to integer
        n = int.from_bytes(data, 'big')

        if n == 0:
            return '0'

        while n > 0:
            result.append(BASE62[n % 62])
            n //= 62

        return ''.join(result[::-1])

    def decode_params(self, short_code: str) -> Optional[Dict[str, Any]]:
        """
        Decode parameters from short identifier.

        Args:
            short_code: Short encoded identifier

        Returns:
            Original parameters dictionary or None if invalid
        """
        try:
            # Decode base58 back to query string
            decoded_bytes = base58_decode(short_code)
            decoded_query = decoded_bytes.decode('utf-8')

            # Parse query string back to dict
            params_dict = parse_qs(decoded_query, keep_blank_values=True)

            # Convert single values from lists
            result = {}
            for k, v in params_dict.items():
                if len(v) == 1:
                    result[k] = v[0]
                else:
                    result[k] = v

            return result

        except (ValueError, UnicodeDecodeError, IndexError):
            # If decoding fails, this might be an old SHA256 hash or corrupted data
            print(f"Warning: Unable to decode short code '{short_code}' - may be from old format or corrupted")
            return None

    def shorten_url(self, original_url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Shorten a URL by encoding its query parameters.

        Args:
            original_url: Original URL to shorten

        Returns:
            Tuple of (short_url, params_dict)
        """
        try:
            parsed = urlparse(original_url)
            query_params = parse_qs(parsed.query)

            # Convert lists to single values, keep lists for multi-value params
            params_dict = {}
            for k, v in query_params.items():
                if len(v) == 1:
                    params_dict[k] = v[0]
                else:
                    params_dict[k] = v

            short_code = self.encode_params(params_dict)

            # Create short URL
            short_url = f"{parsed.scheme}://{parsed.netloc}/s/{short_code}"

            return short_url, params_dict

        except Exception as e:
            raise ValueError(f"Failed to shorten URL: {e}")

    def expand_url(self, short_url: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Expand a short URL back to original URL with parameters.

        Args:
            short_url: Short URL to expand

        Returns:
            Tuple of (full_url, params_dict) or (None, None) if not found
        """
        try:
            parsed = urlparse(short_url)
            path_parts = parsed.path.strip('/').split('/')

            if len(path_parts) < 2 or path_parts[-2] != 's':
                return None, None

            short_code = path_parts[-1]

            if not short_code:
                return None, None

            params = self.decode_params(short_code)

            if params is None:
                return None, None

            # Reconstruct the original URL
            query_string = urlencode(params, doseq=True)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            full_url = f"{base_url}/v1/click?{query_string}"

            return full_url, params

        except Exception as e:
            print(f"Warning: Failed to expand URL: {e}")
            return None, None



# Global instance for use across the application
url_shortener = URLShortener()
