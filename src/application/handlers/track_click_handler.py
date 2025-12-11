"""Track click command handler."""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

from ..commands.track_click_command import TrackClickCommand
from ...domain.entities.click import Click
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.repositories.landing_page_repository import LandingPageRepository
from ...domain.repositories.offer_repository import OfferRepository
from ...domain.repositories.pre_click_data_repository import PreClickDataRepository
from ...domain.services.click import ClickValidationService
from ...domain.value_objects import ClickId, CampaignId, Url


class TrackClickHandler:
    """Handler for tracking clicks."""

    def __init__(self,
                 click_repository: ClickRepository,
                 campaign_repository: CampaignRepository,
                 landing_page_repository: LandingPageRepository,
                 offer_repository: OfferRepository,
                 pre_click_data_repository: PreClickDataRepository,
                 click_validation_service: ClickValidationService):
        self._click_repository = click_repository
        self._campaign_repository = campaign_repository
        self._landing_page_repository = landing_page_repository
        self._offer_repository = offer_repository
        self._pre_click_data_repository = pre_click_data_repository
        self._click_validation_service = click_validation_service

    async def handle(self, command: TrackClickCommand) -> Tuple[Click, Url, bool]:
        """
        Handle track click command.

        Returns:
            Tuple of (click, redirect_url, is_valid_click)
        """
        campaign = self._find_campaign(command.campaign_id)

        if not campaign:
            return self._handle_unknown_campaign(command)

        click = await self._create_click_from_command(command) # Await the async call
        is_valid = self._validate_click_and_mark_fraud(click)

        redirect_url = self._determine_redirect_url(campaign, is_valid, command.test_mode, click.id.value, command)

        # Save click
        self._click_repository.save(click)

        # Update campaign performance if valid click
        if is_valid:
            self._update_campaign_performance(campaign)

        return click, redirect_url, is_valid

    def _find_campaign(self, campaign_id_str: str):
        """Find campaign by ID."""
        campaign_id = CampaignId.from_string(campaign_id_str)
        return self._campaign_repository.find_by_id(campaign_id)

    def _handle_unknown_campaign(self, command: TrackClickCommand) -> Tuple[Click, Url, bool]:
        """Handle clicks for unknown campaigns."""
        safe_url = Url("http://localhost:5000/mock-safe-page")
        click = self._create_click_from_command(command)
        return click, safe_url, False

    def _validate_click_and_mark_fraud(self, click: Click) -> bool:
        """Validate click for fraud and mark if fraudulent."""
        is_valid, fraud_reason, fraud_score = self._click_validation_service.validate_click(
            click, campaign_filters={}
        )

        if not is_valid:
            click.mark_as_fraudulent(fraud_reason, fraud_score)

        return is_valid

    def _determine_redirect_url(self, campaign, is_valid: bool, test_mode: bool, click_id: str, command: TrackClickCommand) -> Url:
        """Determine redirect URL based on validation, campaign settings, and specific parameters."""
        redirect_url = None

        # Priority 1: Use specific landing page if provided (overrides everything)
        if command.landing_page_id:
            try:
                landing_page = self._landing_page_repository.find_by_id(str(command.landing_page_id))
                if landing_page and landing_page.is_active:
                    redirect_url = landing_page.url
                    logger.info(f"Using specific landing page URL for lp_id {command.landing_page_id}: {landing_page.url.value}")
                    # For direct landing page links, skip fraud checks
                    is_valid = True
                else:
                    logger.warning(f"Landing page {command.landing_page_id} not found or inactive")
            except Exception as e:
                logger.warning(f"Failed to find landing page {command.landing_page_id}: {e}")

        # Priority 2: Use specific offer if provided (overrides campaign settings)
        if not redirect_url and command.campaign_offer_id:
            try:
                offer = self._offer_repository.find_by_id(str(command.campaign_offer_id))
                if offer and offer.is_active:
                    redirect_url = offer.url
                    logger.info(f"Using specific offer URL for offer_id {command.campaign_offer_id}: {offer.url.value}")
                    # For direct offer links, skip fraud checks
                    is_valid = True
                else:
                    logger.warning(f"Offer {command.campaign_offer_id} not found or inactive")
            except Exception as e:
                logger.warning(f"Failed to find offer {command.campaign_offer_id}: {e}")

        # Priority 3: Use campaign's offer page for valid clicks
        if not redirect_url and is_valid:
            if campaign.offer_page_url:
                redirect_url = campaign.offer_page_url
                logger.info("Using campaign offer page URL (valid click)")
            elif campaign.safe_page_url:
                redirect_url = campaign.safe_page_url
                logger.info("Using campaign safe page URL (valid click, no offer URL)")

        # Priority 4: Use campaign's safe page for invalid clicks
        if not redirect_url and not is_valid and campaign.safe_page_url:
            redirect_url = campaign.safe_page_url
            logger.info("Using campaign safe page URL (invalid click)")

        # Fallback
        if not redirect_url:
            redirect_url = Url("http://localhost:5000/mock-safe-page")
            logger.warning("Using fallback safe page URL")

        # Add click ID to redirect URL if in test mode
        if test_mode:
            redirect_url = redirect_url.with_query_params({'click_id': click_id})

        return redirect_url

    def _update_campaign_performance(self, campaign):
        """Update campaign performance metrics."""
        campaign.update_performance(clicks_increment=1)
        self._campaign_repository.save(campaign)

    async def _create_click_from_command(self, command: TrackClickCommand) -> Click:
        """Create Click entity from command, enriched with PreClickData."""
        click_id = ClickId.from_string(command.click_id_param)

        # Retrieve all stored tracking parameters using the click_id
        pre_click_data = await self._pre_click_data_repository.find_by_click_id(click_id)

        if not pre_click_data:
            logger.warning(f"No PreClickData found for click_id: {click_id.value}. Creating click with limited data.")
            # Fallback to creating a click with only data from the command if pre_click_data is not found
            click_data = {
                'id': click_id,
                'campaign_id': command.campaign_id,
                'ip_address': command.ip_address,
                'user_agent': command.user_agent,
                'referrer': command.referrer,
                'sub1': command.sub1,
                'sub2': command.sub2,
                'sub3': command.sub3,
                'sub4': command.sub4,
                'sub5': command.sub5,
                'click_id_param': command.click_id_param,
                'affiliate_sub': command.affiliate_sub,
                'affiliate_sub2': command.affiliate_sub2,
                'affiliate_sub3': command.affiliate_sub3,
                'affiliate_sub4': command.affiliate_sub4,
                'affiliate_sub5': command.affiliate_sub5,
                'landing_page_id': command.landing_page_id,
                'campaign_offer_id': command.campaign_offer_id,
                'traffic_source_id': command.traffic_source_id,
                'is_valid': True,
                'fraud_score': 0.0,
                'fraud_reason': None,
            }
        else:
            # Populate click_data with parameters from pre_click_data, falling back to command if not present
            tracking_params = pre_click_data.tracking_params
            click_data = {
                'id': click_id,
                'campaign_id': pre_click_data.campaign_id.value,
                'ip_address': command.ip_address,
                'user_agent': command.user_agent,
                'referrer': command.referrer,
                'sub1': tracking_params.get('sub1', command.sub1),
                'sub2': tracking_params.get('sub2', command.sub2),
                'sub3': tracking_params.get('sub3', command.sub3),
                'sub4': tracking_params.get('sub4', command.sub4),
                'sub5': tracking_params.get('sub5', command.sub5),
                'click_id_param': tracking_params.get('click_id', command.click_id_param),
                'affiliate_sub': tracking_params.get('aff_sub', command.affiliate_sub),
                'affiliate_sub2': tracking_params.get('aff_sub2', command.affiliate_sub2),
                'affiliate_sub3': tracking_params.get('aff_sub3', command.affiliate_sub3),
                'affiliate_sub4': tracking_params.get('aff_sub4', command.affiliate_sub4),
                'affiliate_sub5': tracking_params.get('aff_sub5', command.affiliate_sub5),
                'landing_page_id': int(tracking_params['lp_id']) if 'lp_id' in tracking_params else command.landing_page_id,
                'campaign_offer_id': int(tracking_params['offer_id']) if 'offer_id' in tracking_params else command.campaign_offer_id,
                'traffic_source_id': int(tracking_params['ts_id']) if 'ts_id' in tracking_params else command.traffic_source_id,
                'is_valid': True,
                'fraud_score': 0.0,
                'fraud_reason': None,
            }

            # After successfully retrieving and using pre-click data, delete it
            await self._pre_click_data_repository.delete_by_click_id(click_id)
            logger.info(f"PreClickData deleted for click_id: {click_id.value}")

        return Click(**click_data)
