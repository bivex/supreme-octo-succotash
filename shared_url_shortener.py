"""
Shared URL shortener module for both tracking and API server
"""

import base64
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs, urlparse, urlencode

# Global storage for URL shortener mappings (use Redis in production)
URL_SHORTENER_STORAGE: Dict[str, Dict[str, Any]] = {}

class URLShortener:
    """URL shortener using SHA256 hash for encoding/decoding parameters"""

    def __init__(self):
        # Use global storage
        self.storage = URL_SHORTENER_STORAGE

    def encode_params(self, params_dict: Dict[str, Any]) -> str:
        """
        Encode parameters into short identifier using SHA256 hash
        """
        # Serialize parameters to JSON
        params_json = json.dumps(params_dict, sort_keys=True)

        # Create short hash
        hash_object = hashlib.sha256(params_json.encode())
        short_hash = base64.urlsafe_b64encode(hash_object.digest())[:8].decode()

        # Store mapping
        self.storage[short_hash] = params_dict

        return short_hash

    def decode_params(self, short_hash: str) -> Optional[Dict[str, Any]]:
        """
        Decode parameters from stored identifier
        """
        return self.storage.get(short_hash)

    def shorten_url(self, original_url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Shorten URL by encoding its parameters
        """
        parsed = urlparse(original_url)
        query_params = parse_qs(parsed.query)

        # Convert lists to single values
        params_dict = {k: v[0] if len(v) == 1 else v
                      for k, v in query_params.items()}

        short_code = self.encode_params(params_dict)

        # Create short URL
        short_url = f"{parsed.scheme}://{parsed.netloc}/s/{short_code}"

        return short_url, params_dict

    def expand_url(self, short_url: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Expand short URL back to full URL
        """
        parsed = urlparse(short_url)
        short_code = parsed.path.split('/')[-1]

        params = self.decode_params(short_code)

        if params:
            query_string = urlencode(params)
            full_url = f"{parsed.scheme}://{parsed.netloc}/v1/click?{query_string}"
            return full_url, params

        return None, None

# Global URL shortener instance
url_shortener = URLShortener()
