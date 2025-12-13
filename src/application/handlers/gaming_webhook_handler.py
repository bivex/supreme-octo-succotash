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
        transaction_id = deposit_data.get('transaction_id', 'unknown')
        user_id = deposit_data.get('user_id', 'unknown')
        amount = deposit_data.get('amount', 0)

        logger.info(f"🚀 START: Deposit webhook processing | TX:{transaction_id} | User:{user_id} | Amount:{amount}")

        # Log environment context
        import os
        import socket
        logger.info(f"📊 Context: PID={os.getpid()}, Host={socket.gethostname()}, Env={os.getenv('ENVIRONMENT', 'unknown')}")

        try:
            logger.info(f"📝 Processing deposit webhook | TX:{transaction_id} | Data keys: {list(deposit_data.keys())}")

            # Step 1: Validate deposit data
            logger.info(f"🔍 Step 1: Validating deposit data | TX:{transaction_id}")
            try:
                is_valid, error_message = self.gaming_webhook_service.validate_deposit_data(deposit_data)
                if not is_valid:
                    logger.warning(f"❌ Deposit data validation failed | TX:{transaction_id} | Error: {error_message}")
                    return {
                        "status": "error",
                        "message": error_message,
                        "step": "validation",
                        "transaction_id": transaction_id
                    }
                logger.info(f"✅ Deposit data validation passed | TX:{transaction_id}")
            except Exception as e:
                logger.error(f"❌ ERROR in validation step | TX:{transaction_id} | {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Validation error: {str(e)}",
                    "step": "validation",
                    "transaction_id": transaction_id
                }

            # Step 2: Find the original click by user identifier
            logger.info(f"🔍 Step 2: Finding click by user identifier | TX:{transaction_id} | User:{user_id}")
            try:
                click = self.gaming_webhook_service.find_click_by_user_identifier(deposit_data)
                if not click:
                    logger.warning(f"❌ No click found for deposit | TX:{transaction_id} | User:{user_id}")
                    return {
                        "status": "error",
                        "message": "Click not found for this user",
                        "step": "click_lookup",
                        "transaction_id": transaction_id
                    }
                logger.info(f"✅ Found click | TX:{transaction_id} | Click:{click.id} | Campaign:{click.campaign_id}")
            except Exception as e:
                logger.error(f"❌ ERROR in click lookup step | TX:{transaction_id} | {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Click lookup error: {str(e)}",
                    "step": "click_lookup",
                    "transaction_id": transaction_id
                }

            # Step 3: Check for duplicate deposits
            logger.info(f"🔍 Step 3: Checking for duplicate deposits | TX:{transaction_id} | Click:{click.id}")
            try:
                if self.gaming_webhook_service.is_duplicate_deposit(deposit_data, click.id):
                    logger.info(f"ℹ️ Duplicate deposit detected | TX:{transaction_id} | Click:{click.id}")
                    return {
                        "status": "duplicate",
                        "message": "Deposit already processed",
                        "step": "duplicate_check",
                        "transaction_id": transaction_id
                    }
                logger.info(f"✅ No duplicate deposit found | TX:{transaction_id}")
            except Exception as e:
                logger.error(f"❌ ERROR in duplicate check step | TX:{transaction_id} | {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Duplicate check error: {str(e)}",
                    "step": "duplicate_check",
                    "transaction_id": transaction_id
                }

            # Step 4: Create deposit conversion
            logger.info(f"🔧 Step 4: Creating deposit conversion | TX:{transaction_id} | Click:{click.id}")
            try:
                conversion = self._create_deposit_conversion(deposit_data, click)
                logger.info(f"✅ Created conversion | TX:{transaction_id} | Conv:{conversion.id} | Type:{conversion.conversion_type} | Value:{str(conversion.conversion_value)}")
            except Exception as e:
                logger.error(f"❌ ERROR in conversion creation step | TX:{transaction_id} | {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Conversion creation error: {str(e)}",
                    "step": "conversion_creation",
                    "transaction_id": transaction_id
                }

            # Step 5: Save conversion
            logger.info(f"💾 Step 5: Saving conversion to database | TX:{transaction_id} | Conv:{conversion.id}")
            try:
                self.conversion_repository.save(conversion)
                logger.info(f"✅ Saved conversion to database | TX:{transaction_id} | Conv:{conversion.id}")
            except Exception as e:
                logger.error(f"❌ ERROR in database save step | TX:{transaction_id} | Conv:{conversion.id} | {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Database save error: {str(e)}",
                    "step": "database_save",
                    "transaction_id": transaction_id
                }

            # Step 6: Check postback trigger (optional step)
            logger.info(f"🔄 Step 6: Checking postback trigger | TX:{transaction_id} | Conv:{conversion.id}")
            should_postback = False
            try:
                should_postback = self.conversion_service.should_trigger_postback(conversion)
                logger.info(f"✅ Postback trigger result | TX:{transaction_id} | Trigger:{should_postback}")
            except Exception as e:
                logger.warning(f"⚠️ WARNING in postback check step (non-critical) | TX:{transaction_id} | {e}")
                should_postback = False

            # Step 7: Prepare response
            logger.info(f"📦 Step 7: Preparing response | TX:{transaction_id}")
            try:
                response_data = {
                    "status": "success",
                    "conversion_id": conversion.id,
                    "click_id": click.id,
                    "campaign_id": click.campaign_id,
                    "deposit_amount": amount,
                    "postback_triggered": should_postback,
                    "transaction_id": transaction_id,
                    "step": "response_preparation"
                }

                logger.info(f"Response data keys: {list(response_data.keys())}")

                # Test JSON serialization before returning
                import json
                try:
                    test_json = json.dumps(response_data, default=str)
                    logger.info(f"✅ Response JSON serialization test passed | TX:{transaction_id}")
                except Exception as json_e:
                    logger.error(f"❌ JSON serialization failed | TX:{transaction_id} | Error: {json_e}")
                    logger.error(f"Response data: {response_data}")
                    # Try to identify problematic field
                    for key, value in response_data.items():
                        try:
                            json.dumps({key: value}, default=str)
                        except Exception as field_e:
                            logger.error(f"❌ Problematic field '{key}' | TX:{transaction_id} | Error: {field_e} | Value: {repr(str(value))}")
                    raise

                logger.info(f"🎉 FINISH: Deposit webhook processing successful | TX:{transaction_id} | Conv:{conversion.id}")
                return response_data

            except Exception as e:
                logger.error(f"❌ ERROR in response preparation step | TX:{transaction_id} | {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Response preparation error: {str(e)}",
                    "step": "response_preparation",
                    "transaction_id": transaction_id
                }

        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR: Unexpected error in deposit webhook processing | TX:{transaction_id} | {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "step": "unexpected_error",
                "transaction_id": transaction_id
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
        transaction_id = deposit_data.get('transaction_id', 'unknown')
        logger.info(f"🔧 Creating deposit conversion entity | TX:{transaction_id}")
        try:
            from ...domain.value_objects.financial.money import Money
            import uuid
            from datetime import datetime
            from decimal import Decimal

            # Handle monetary value
            amount = deposit_data.get('amount', 0)
            currency = deposit_data.get('currency', 'USD')
            logger.info(f"   💰 Processing monetary value | TX:{transaction_id} | Amount:{amount} {currency}")

            try:
                conversion_value = Money(amount=Decimal(str(amount)), _currency=currency)
                logger.info(f"   ✅ Money object created | TX:{transaction_id} | Value:{str(conversion_value)}")
            except Exception as e:
                logger.error(f"   ❌ ERROR creating Money object | TX:{transaction_id} | {e}")
                raise

            # Prepare metadata
            logger.info(f"   📋 Preparing metadata | TX:{transaction_id}")
            try:
                metadata = {
                    'gaming_platform': deposit_data.get('platform', 'unknown'),
                    'game_type': deposit_data.get('game_type'),
                    'deposit_method': deposit_data.get('payment_method'),
                    'is_first_deposit': deposit_data.get('is_first_deposit', True),
                    'transaction_id': transaction_id,
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
                logger.info(f"   ✅ Metadata prepared | TX:{transaction_id} | Fields:{len(metadata)}")
            except Exception as e:
                logger.error(f"   ❌ ERROR preparing metadata | TX:{transaction_id} | {e}")
                raise

            # Prepare conversion data
            logger.info(f"   🏗️ Preparing conversion data | TX:{transaction_id}")
            try:
                conversion_data = {
                    'click_id': click.id,
                    'conversion_type': 'deposit',
                    'conversion_value': conversion_value,
                    'order_id': transaction_id,
                    'campaign_id': int(click.campaign_id) if click.campaign_id and click.campaign_id.isdigit() else None,
                    'user_id': deposit_data.get('user_id'),
                    'metadata': metadata
                }
                logger.info(f"   ✅ Conversion data prepared | TX:{transaction_id} | Click:{click.id} | Type:deposit")
            except Exception as e:
                logger.error(f"   ❌ ERROR preparing conversion data | TX:{transaction_id} | {e}")
                raise

            # Create conversion entity
            logger.info(f"   🎯 Creating Conversion entity | TX:{transaction_id}")
            try:
                conversion = Conversion.create_from_request(conversion_data)
                logger.info(f"   ✅ Conversion entity created | TX:{transaction_id} | Conv:{conversion.id}")
                return conversion
            except Exception as e:
                logger.error(f"   ❌ ERROR in Conversion.create_from_request | TX:{transaction_id} | {e}")
                logger.error(f"   Failed conversion data | TX:{transaction_id} | {conversion_data}")
                raise

        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in _create_deposit_conversion | TX:{transaction_id} | {e}", exc_info=True)
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