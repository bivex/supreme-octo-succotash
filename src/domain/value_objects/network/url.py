"""URL value object for handling web URLs."""

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Url:
    """Value object representing a web URL."""

    value: str

    def __post_init__(self) -> None:
        """Validate URL format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("URL must be a non-empty string")

        parsed = urlparse(self.value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("URL must have valid scheme and host")

        # Only allow HTTP/HTTPS schemes
        if parsed.scheme.lower() not in ['http', 'https']:
            raise ValueError("URL scheme must be http or https")

    @property
    def scheme(self) -> str:
        """Get URL scheme."""
        return urlparse(self.value).scheme

    @property
    def host(self) -> str:
        """Get URL host."""
        return urlparse(self.value).netloc

    @property
    def path(self) -> str:
        """Get URL path."""
        return urlparse(self.value).path

    @property
    def query(self) -> str:
        """Get URL query string."""
        return urlparse(self.value).query

    def with_query_params(self, params: dict[str, str]) -> 'Url':
        """Return URL with additional query parameters."""
        from urllib.parse import urlencode, parse_qs, urlunparse

        parsed = urlparse(self.value)
        existing_params = parse_qs(parsed.query)
        existing_params.update(params)

        new_query = urlencode(existing_params, doseq=True)
        # Create new URL tuple with updated query
        new_url_tuple = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        )
        new_url = urlunparse(new_url_tuple)

        return Url(new_url)

    def __str__(self) -> str:
        return self.value
