"""Domain value objects."""

# Identifiers
from .identifiers import CampaignId, ClickId, ImpressionId
import psycopg2.extensions

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
