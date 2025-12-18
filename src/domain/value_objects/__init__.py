# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Domain value objects."""

import psycopg2.extensions

# Identifiers
from .identifiers import CampaignId, ClickId, ImpressionId


# Register adapter for CampaignId
def adapt_campaign_id(campaign_id):
    return psycopg2.extensions.adapt(campaign_id.value)


psycopg2.extensions.register_adapter(CampaignId, adapt_campaign_id)

# Financial
from .financial import Money

# Network
from .network import Url

# Status
from .status import CampaignStatus

# Analytics
from .analytics import Analytics

# Filters
from .filters import ClickFilters

__all__ = [
    'CampaignId',
    'ClickId',
    'ImpressionId',
    'Money',
    'Url',
    'CampaignStatus',
    'Analytics',
    'ClickFilters'
]
