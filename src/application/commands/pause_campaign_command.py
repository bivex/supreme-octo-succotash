"""Pause campaign command."""

from dataclasses import dataclass

from ...domain.value_objects import CampaignId


@dataclass
class PauseCampaignCommand:
    """Command to pause a campaign."""

    campaign_id: CampaignId
