# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

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
