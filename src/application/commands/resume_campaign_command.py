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

"""Resume campaign command."""

from dataclasses import dataclass

from ...domain.value_objects import CampaignId


@dataclass
class ResumeCampaignCommand:
    """Command to resume a paused campaign."""

    campaign_id: CampaignId
