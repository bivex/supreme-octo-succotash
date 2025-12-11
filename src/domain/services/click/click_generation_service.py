"""Click generation service for creating personalized tracking links."""

from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from loguru import logger
from datetime import datetime, timezone

from src.domain.entities.pre_click_data import PreClickData
from src.domain.repositories.pre_click_data_repository import PreClickDataRepository
from src.domain.value_objects import ClickId, CampaignId

class ClickGenerationService:
    """Service for generating personalized click tracking links."""

    def __init__(self, pre_click_data_repository: PreClickDataRepository):
        self._pre_click_data_repository = pre_click_data_repository
        self._valid_traffic_sources = {
            'facebook', 'google', 'taboola', 'outbrain', 'twitter', 'linkedin',
            'email', 'direct', 'referral', 'organic', 'paid', 'social'
        }

    async def generate_tracking_url(
        self,
        base_url: str,
        campaign_id: int,
        tracking_params: Dict[str, Any],
        landing_page_id: Optional[int] = None,
        offer_id: Optional[int] = None,
        traffic_source_id: Optional[int] = None
    ) -> str:
        """Generate a tracking URL with all necessary parameters."""
        try:
            logger.info("=== CLICK GENERATION SERVICE DEBUG ===")
            logger.info(f"Input parameters for pre-click data: base_url={base_url}, campaign_id={campaign_id}")
            logger.info(f"landing_page_id: {landing_page_id} (type: {type(landing_page_id)})")
            logger.info(f"offer_id: {offer_id} (type: {type(offer_id)})")
            logger.info(f"traffic_source_id: {traffic_source_id} (type: {type(traffic_source_id)})")
            logger.info(f"tracking_params: {tracking_params}")

            # Generate a unique click_id
            generated_click_id = ClickId.generate()

            # Collect all tracking parameters to be stored
            all_tracking_params = {
                'ts': str(int(__import__('time').time())),
            }

            if landing_page_id is not None:
                all_tracking_params['lp_id'] = str(landing_page_id)
            if offer_id is not None:
                all_tracking_params['offer_id'] = str(offer_id)
            if traffic_source_id is not None:
                all_tracking_params['ts_id'] = str(traffic_source_id)

            # Add sub-tracking parameters (1-5 levels)
            for i in range(1, 6):
                sub_key = f'sub{i}'
                if sub_key in tracking_params:
                    all_tracking_params[sub_key] = str(tracking_params[sub_key])

            # Add affiliate network parameters
            affiliate_params = ['click_id', 'aff_sub', 'aff_sub2', 'aff_sub3', 'aff_sub4', 'aff_sub5']
            for param in affiliate_params:
                if param in tracking_params:
                    all_tracking_params[param] = str(tracking_params[param])

            # Also include any other generic tracking_params that might be passed
            for key, value in tracking_params.items():
                if key not in all_tracking_params: # Avoid overwriting explicit params
                    all_tracking_params[key] = str(value)

            # Create PreClickData entity
            pre_click_data = PreClickData(
                click_id=generated_click_id,
                campaign_id=CampaignId(f"camp_{campaign_id}"), # CampaignId constructor takes 'camp_9061' format
                timestamp=datetime.now(timezone.utc),
                tracking_params=all_tracking_params,
                metadata={'generated_from': 'ClickGenerationService'}
            )

            # Save to repository
            await self._pre_click_data_repository.save(pre_click_data)
            logger.info(f"PreClickData saved for click_id: {generated_click_id.value}")

            # Construct the short URL
            # The short URL will only contain cid and the generated click_id
            parsed_base = urlparse(base_url)
            short_query_params = {
                'cid': f"camp_{campaign_id}",
                'click_id': generated_click_id.value,
            }
            short_query = urlencode(short_query_params, doseq=True)

            final_short_url = urlunparse((
                parsed_base.scheme,
                parsed_base.netloc,
                '/v1/click',
                '',
                short_query,
                ''
            ))

            logger.info(f"Generated short tracking URL for campaign {campaign_id}: {final_short_url}")
            logger.info("=== END CLICK GENERATION SERVICE DEBUG ===")
            return final_short_url

        except Exception as e:
            logger.error(f"Error generating tracking URL: {e}", exc_info=True)
            raise ValueError(f"Failed to generate tracking URL: {str(e)}")

    def validate_tracking_parameters(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate tracking parameters."""
        try:
            # Required parameters
            if 'campaign_id' not in params:
                return False, "campaign_id is required"

            if not isinstance(params['campaign_id'], int) or params['campaign_id'] <= 0:
                return False, "campaign_id must be a positive integer"

            # Optional but validated parameters
            if 'landing_page_id' in params:
                if not isinstance(params['landing_page_id'], int) or params['landing_page_id'] <= 0:
                    return False, "landing_page_id must be a positive integer"

            if 'offer_id' in params:
                if not isinstance(params['offer_id'], int) or params['offer_id'] <= 0:
                    return False, "offer_id must be a positive integer"

            # Validate URL format if provided
            if 'base_url' in params:
                base_url = params['base_url']
                if not isinstance(base_url, str) or not base_url.startswith(('http://', 'https://')):
                    return False, "base_url must be a valid HTTP/HTTPS URL"

            # Validate parameter lengths
            max_lengths = {
                'sub1': 255, 'sub2': 255, 'sub3': 255, 'sub4': 255, 'sub5': 255,
                'click_id': 255, 'aff_sub': 255, 'aff_sub2': 255, 'aff_sub3': 255,
                'aff_sub4': 255, 'aff_sub5': 255
            }

            for param, max_len in max_lengths.items():
                if param in params and len(str(params[param])) > max_len:
                    return False, f"{param} exceeds maximum length of {max_len} characters"

            return True, None

        except Exception as e:
            return False, f"Parameter validation error: {str(e)}"

    def generate_bulk_tracking_urls(
        self,
        base_url: str,
        campaign_id: int,
        variations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate multiple tracking URLs with different parameter variations."""
        results = []

        for i, variation in enumerate(variations):
            try:
                tracking_url = self.generate_tracking_url(
                    base_url=base_url,
                    campaign_id=campaign_id,
                    tracking_params=variation.get('params', {}),
                    landing_page_id=variation.get('landing_page_id'),
                    offer_id=variation.get('offer_id')
                )

                results.append({
                    'id': variation.get('id', f'variation_{i+1}'),
                    'name': variation.get('name', f'Variation {i+1}'),
                    'url': tracking_url,
                    'params': variation.get('params', {}),
                    'status': 'success'
                })

            except Exception as e:
                results.append({
                    'id': variation.get('id', f'variation_{i+1}'),
                    'name': variation.get('name', f'Variation {i+1}'),
                    'url': None,
                    'params': variation.get('params', {}),
                    'status': 'error',
                    'error': str(e)
                })

        return results

    def optimize_tracking_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize and normalize tracking parameters."""
        optimized = {}

        # Normalize campaign_id
        if 'campaign_id' in params:
            optimized['campaign_id'] = int(params['campaign_id'])

        # Normalize targeting IDs
        for key in ['landing_page_id', 'offer_id']:
            if key in params and params[key] is not None:
                optimized[key] = int(params[key])

        # Clean and normalize string parameters
        string_params = [
            'sub1', 'sub2', 'sub3', 'sub4', 'sub5',
            'click_id', 'aff_sub', 'aff_sub2', 'aff_sub3', 'aff_sub4', 'aff_sub5'
        ]

        for param in string_params:
            if param in params and params[param] is not None:
                value = str(params[param]).strip()
                if value:  # Only include non-empty values
                    optimized[param] = value

        # Add metadata
        optimized['_generated_at'] = int(__import__('time').time())
        optimized['_version'] = '1.0'

        return optimized

    def extract_tracking_data_from_url(self, url: str) -> Dict[str, Any]:
        """Extract tracking parameters from a tracking URL."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            # Flatten single-value parameters
            tracking_data = {}
            for key, values in params.items():
                if len(values) == 1:
                    tracking_data[key] = values[0]
                else:
                    tracking_data[key] = values

            return tracking_data

        except Exception as e:
            logger.error(f"Error extracting tracking data from URL: {e}")
            return {}
