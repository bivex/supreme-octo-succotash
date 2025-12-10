"""Create landing page command."""

from dataclasses import dataclass
from typing import Optional

from ...domain.value_objects import Url


@dataclass
class CreateLandingPageCommand:
    """Command to create a new landing page."""

    campaign_id: str
    name: str
    url: Url
    page_type: str = "squeeze"
    weight: int = 100
    is_control: bool = False
