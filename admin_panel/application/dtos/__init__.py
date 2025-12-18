# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Application Layer DTOs - Data Transfer Objects."""

from .offer_dto import OfferDTO, CreateOfferDTO, UpdateOfferDTO
from .landing_page_dto import LandingPageDTO, CreateLandingPageDTO, UpdateLandingPageDTO
from .campaign_dto import CampaignDTO, CreateCampaignRequest

__all__ = [
    'OfferDTO',
    'CreateOfferDTO',
    'UpdateOfferDTO',
    'LandingPageDTO',
    'CreateLandingPageDTO',
    'UpdateLandingPageDTO',
    'CampaignDTO',
    'CreateCampaignRequest'
]