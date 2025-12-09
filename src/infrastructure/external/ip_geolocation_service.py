"""IP geolocation service interface and implementation."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ipaddress import IPv4Address, IPv6Address


class IpGeolocationService(ABC):
    """Abstract service for IP geolocation."""

    @abstractmethod
    def get_location(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Get location information for an IP address.

        Returns dict with keys: country, region, city, etc.
        """
        pass


class MockIpGeolocationService(IpGeolocationService):
    """Mock implementation of IP geolocation service."""

    def __init__(self):
        # Mock location data
        self._mock_locations = {
            "192.168.1.100": {"country": "US", "region": "CA", "city": "San Francisco"},
            "10.0.0.50": {"country": "US", "region": "NY", "city": "New York"},
            "127.0.0.1": {"country": "LOCAL", "region": "LOCAL", "city": "Localhost"},
        }

    def get_location(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get mock location for IP address."""
        try:
            # Validate IP format
            IPv4Address(ip_address)
        except ValueError:
            try:
                IPv6Address(ip_address)
            except ValueError:
                # Invalid IP format, return None
                return None

        # Return mock data or default
        return self._mock_locations.get(ip_address, {"country": "US", "region": "CA", "city": "Unknown"})
