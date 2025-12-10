"""
Shared URL shortener module for both tracking and API server
"""

import json
import hashlib
import base64
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs, urlparse, urlencode


class URLShortener:
    """URL shortener with in-memory storage for tracking parameters."""

    def __init__(self):
        """Initialize URL shortener with in-memory storage."""
        self.storage: Dict[str, Dict[str, Any]] = {}

    def encode_params(self, params_dict: Dict[str, Any]) -> str:
        """
        Encode parameters into a short identifier.

        Args:
            params_dict: Dictionary of parameters to encode

        Returns:
            Short hash identifier
        """
        # Sort keys for consistent hashing
        params_json = json.dumps(params_dict, sort_keys=True, separators=(',', ':'))

        # Create hash using SHA256 for uniqueness
        hash_object = hashlib.sha256(params_json.encode('utf-8'))
        # Use more characters to reduce collision probability
        short_hash = base64.urlsafe_b64encode(hash_object.digest())[:12].decode('ascii')

        # Store the mapping in memory
        self.storage[short_hash] = params_dict.copy()

        return short_hash

    def decode_params(self, short_hash: str) -> Optional[Dict[str, Any]]:
        """
        Decode parameters from short identifier.

        Args:
            short_hash: Short hash identifier

        Returns:
            Original parameters dictionary or None if not found
        """
        return self.storage.get(short_hash)

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
