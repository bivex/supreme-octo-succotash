# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:30
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..value_objects import ClickId, CampaignId


@dataclass
class PreClickData:
    """Entity to store all tracking parameters before a click is processed."""

    click_id: ClickId
    campaign_id: CampaignId
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # All other tracking parameters will be stored as a dictionary
    tracking_params: Dict[str, Optional[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.click_id, ClickId):
            self.click_id = ClickId(self.click_id)
        if not isinstance(self.campaign_id, CampaignId):
            self.campaign_id = CampaignId(self.campaign_id)
