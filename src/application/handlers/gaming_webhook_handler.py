"""Gaming platform webhook handler for deposit tracking."""

import json
from typing import Dict, Any, Optional
from loguru import logger
from ...domain.repositories.conversion_repository import ConversionRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.customer_ltv_repository import CustomerLtvRepository
from ...domain.services.conversion.conversion_service import ConversionService
from ...domain.services.gaming.gaming_webhook_service import GamingWebhookService
from ...domain.entities.conversion import Conversion


class GamingWebhookHandler:
    """Handler for processing gaming platform webhooks (deposits, registrations)."""

    def __init__(
        self,
        conversion_repository: ConversionRepository,
        click_repository: ClickRepository,
        customer_ltv_repository: CustomerLtvRepository,
        conversion_service: ConversionService,
        gaming_webhook_service: GamingWebhookService
    ):
        self.conversion_repository = conversion_repository
        self.click_repository = click_repository
        self.customer_ltv_repository = customer_ltv_repository
        self.conversion_service = conversion_service
        self.gaming_webhook_service = gaming_webhook_service

    def handle_deposit(self, deposit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deposit webhook from gaming platform."""
        logger.info("🚀 START: Deposit webhook processing")
        try:
            logger.info(f"Processing deposit webhook: {deposit_data.get('transaction_id', 'unknown')}")
            logger.info(f"Deposit data: {deposit_data}")

            # Validate deposit data
            logger.info("Step 1: Validating deposit data")
            is_valid, error_message = self.gaming_webhook_service.validate_deposit_data(deposit_data)
            if not is_valid:
                logger.warning(f"Invalid deposit data: {error_message}")
                return {
                    "status": "error",
                    "message": error_message
                }
            logger.info("✅ Deposit data validation passed")

            # Find the original click by user identifier
            logger.info("Step 2: Finding click by user identifier")
            click = self.gaming_webhook_service.find_click_by_user_identifier(deposit_data)
            if not click:
                logger.warning(f"No click found for deposit: {deposit_data.get('user_id', 'unknown user')}")
                return {
                    "status": "error",
                    "message": "Click not found for this user"
                }
            logger.info(f"✅ Found click: {click.id} for campaign: {click.campaign_id}")

            # Check for duplicate deposits
            logger.info("Step 3: Checking for duplicate deposits")
            if self.gaming_webhook_service.is_duplicate_deposit(deposit_data, click.id):
                logger.info(f"Duplicate deposit detected for click {click.id}")
                return {
                    "status": "duplicate",
                    "message": "Deposit already processed"
                }
            logger.info("✅ No duplicate deposit found")

            # Create deposit conversion
            logger.info("Step 4: Creating deposit conversion")
            try:
                conversion = self._create_deposit_conversion(deposit_data, click)
                logger.info(f"Created conversion: {conversion.id}")
                logger.info(f"Conversion details: type={conversion.conversion_type}, value={conversion.conversion_value}, order_id={conversion.order_id}")
            except Exception as e:
                logger.error(f"Error creating conversion: {e}")
                raise

            # Save conversion
            logger.info("Step 5: Saving conversion to database")
            self.conversion_repository.save(conversion)
            logger.info(f"Saved conversion: {conversion.id}")
            logger.info(f"Deposit conversion saved: {conversion.id}")

            # TODO: Update LTV for the customer (disabled for debugging)
            # self._update_customer_ltv(deposit_data, conversion)

            # Trigger postback (this will be handled by the postback system)
            logger.info("Step 6: Checking postback trigger")
            try:
                should_postback = self.conversion_service.should_trigger_postback(conversion)
                logger.info(f"Postback trigger result: {should_postback}")
            except Exception as e:
                logger.error(f"Error checking postback trigger: {e}")
                should_postback = False

            # Prepare response
            logger.info("Step 7: Preparing response")
            response_data = {
                "status": "success",
                "conversion_id": conversion.id,
                "click_id": click.id,
                "campaign_id": click.campaign_id,
                "deposit_amount": deposit_data.get('amount'),
                "postback_triggered": should_postback
            }
            logger.info(f"Response data prepared: {response_data}")

            # Test JSON serialization before returning
            try:
                import json
                test_json = json.dumps(response_data, default=str)
                logger.info("✅ Response JSON serialization test passed")
            except Exception as e:
                logger.error(f"❌ Response JSON serialization failed: {e}")
                logger.error(f"Response data: {response_data}")
                raise

            logger.info("✅ FINISH: Deposit webhook processing successful")
            return response_data

        except Exception as e:
            logger.error(f"❌ ERROR: Deposit webhook processing failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def handle_registration(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user registration webhook from gaming platform."""
        try:
            logger.info(f"Processing registration webhook: {registration_data.get('user_id', 'unknown')}")

            # Validate registration data
            is_valid, error_message = self.gaming_webhook_service.validate_registration_data(registration_data)
            if not is_valid:
                logger.warning(f"Invalid registration data: {error_message}")
                return {
                    "status": "error",
                    "message": error_message
                }

            # Find the original click
            click = self.gaming_webhook_service.find_click_by_user_identifier(registration_data)
            if not click:
                logger.warning(f"No click found for registration: {registration_data.get('user_id', 'unknown user')}")
                return {
                    "status": "error",
                    "message": "Click not found for this user"
                }

            # Create registration conversion
            conversion = self._create_registration_conversion(registration_data, click)

            # Save conversion
            self.conversion_repository.save(conversion)
            logger.info(f"Registration conversion saved: {conversion.id}")

            return {
                "status": "success",
                "conversion_id": conversion.id,
                "click_id": click.id,
                "campaign_id": click.campaign_id
            }

        except Exception as e:
            logger.error(f"Error processing registration webhook: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def _create_deposit_conversion(self, deposit_data: Dict[str, Any], click) -> Conversion:
        """Create a deposit conversion entity."""
        logger.info("Creating deposit conversion entity")
        from ...domain.value_objects.financial.money import Money
        import uuid
        from datetime import datetime
        from decimal import Decimal

        # Handle monetary value
        amount = deposit_data.get('amount', 0)
        currency = deposit_data.get('currency', 'USD')
        logger.info(f"Conversion value: {amount} {currency}")

        conversion_value = Money(amount=Decimal(str(amount)), _currency=currency)
        logger.info(f"Money object created: {conversion_value}")

        now = datetime.utcnow()
        # Create conversion using the standard method
        # Create Money object directly
        conversion_value = Money(amount=Decimal(str(amount)), _currency=currency)

        # Prepare metadata
        metadata = {
            'gaming_platform': deposit_data.get('platform', 'unknown'),
            'game_type': deposit_data.get('game_type'),
            'deposit_method': deposit_data.get('payment_method'),
            'is_first_deposit': deposit_data.get('is_first_deposit', True),
            'attribution': {
                'click_timestamp': str(click.created_at),
                'campaign_id': click.campaign_id,
                'sub_parameters': {
                    'sub1': click.sub1,
                    'sub2': click.sub2,
                    'sub3': click.sub3,
                    'sub4': click.sub4,
                    'sub5': click.sub5
                }
            }
        }
        logger.info(f"Metadata prepared: {metadata}")

        conversion_data = {
            'click_id': click.id,
            'conversion_type': 'deposit',
            'conversion_value': conversion_value,
            'order_id': deposit_data.get('transaction_id'),
            'campaign_id': int(click.campaign_id) if click.campaign_id.isdigit() else None,
            'user_id': deposit_data.get('user_id'),
            'metadata': metadata
        }
        logger.info(f"Conversion data prepared: click_id={click.id}, type=deposit, order_id={deposit_data.get('transaction_id')}")

        try:
            conversion = Conversion.create_from_request(conversion_data)
            logger.info(f"Conversion entity created successfully: {conversion.id}")
            return conversion
        except Exception as e:
            logger.error(f"Failed to create conversion from request data: {e}")
            logger.error(f"Conversion data that failed: {conversion_data}")
            raise

    def _create_registration_conversion(self, registration_data: Dict[str, Any], click) -> Conversion:
        """Create a registration conversion entity."""
        import uuid
        from datetime import datetime

        now = datetime.utcnow()
        return Conversion(
            id=str(uuid.uuid4()),
            click_id=click.id,
            conversion_type='registration',
            conversion_value=None,  # Registrations don't have monetary value
            campaign_id=click.campaign_id,
            user_id=registration_data.get('user_id'),
            metadata={
                'gaming_platform': registration_data.get('platform', 'unknown'),
                'registration_method': registration_data.get('registration_method'),
                'user_country': registration_data.get('country'),
                'attribution': {
                    'click_timestamp': str(click.created_at),
                    'campaign_id': click.campaign_id
                }
            },
            timestamp=now,
            processed=False,
            created_at=now,
            updated_at=now
        )

    def _update_customer_ltv(self, deposit_data: Dict[str, Any], conversion: Conversion) -> None:
        """Update customer LTV data after deposit."""
        try:
            user_id = deposit_data.get('user_id')
            if not user_id:
                return

            # Get or create customer LTV record
            ltv_record = self.customer_ltv_repository.find_by_customer_id(user_id)
            if not ltv_record:
                # Create new LTV record
                from ...domain.entities.customer_ltv import CustomerLtv
                import uuid
                from datetime import datetime

                amount = float(conversion.conversion_value.amount) if conversion.conversion_value else 0.0
                ltv_record = CustomerLtv(
                    customer_id=user_id,
                    total_revenue=amount,
                    total_purchases=1,
                    average_order_value=amount,
                    purchase_frequency=1.0,
                    customer_lifetime_months=0,
                    predicted_clv=amount * 5,  # Simple prediction
                    actual_clv=amount,
                    segment='new_depositor',
                    first_purchase_date=datetime.utcnow().date(),
                    last_purchase_date=datetime.utcnow().date(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            else:
                # Update existing record
                ltv_record.total_revenue += conversion.conversion_value.amount if conversion.conversion_value else 0
                ltv_record.total_purchases += 1
                ltv_record.average_order_value = ltv_record.total_revenue / ltv_record.total_purchases
                ltv_record.actual_clv = ltv_record.total_revenue
                ltv_record.last_purchase_date = datetime.utcnow().date()
                ltv_record.updated_at = datetime.utcnow()

                # Update segment based on total deposits
                if ltv_record.total_revenue >= 1000:
                    ltv_record.segment = 'high_value'
                elif ltv_record.total_revenue >= 100:
                    ltv_record.segment = 'regular'
                else:
                    ltv_record.segment = 'casual'

            self.customer_ltv_repository.save(ltv_record)
            logger.info(f"LTV updated for customer {user_id}: total_revenue={ltv_record.total_revenue}")

        except Exception as e:
            logger.error(f"Error updating customer LTV: {e}", exc_info=True)