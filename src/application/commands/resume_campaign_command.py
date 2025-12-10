"""Resume campaign command."""

from dataclasses import dataclass

from ...domain.value_objects import CampaignId


@dataclass
class ResumeCampaignCommand:
    """Command to resume a paused campaign."""

    campaign_id: CampaignId
