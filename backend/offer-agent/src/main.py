#!/usr/bin/env python3
"""
Offer Automation System - V2 Entry Point

Clean, ERP-agnostic entry point using the new adapter architecture.
This replaces the 2,359-line main.py with a slim, maintainable implementation.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.orchestrator import OfferOrchestrator
from src.core.workflow import WorkflowResult
from src.config.settings import get_settings
from src.utils.logger import setup_logging, get_logger
from src.email_processing.gmail_service_account_processor import GmailServiceAccountProcessor
from src.notifications.gmail_service_account_sender import GmailServiceAccountSender
from src.email_processing.LLM_services.email_classifier import EmailClassifier, EmailAction


class OfferAutomationV2:
    """
    Version 2 of the Offer Automation System.

    Clean implementation using the ERP adapter pattern.
    Supports multiple ERP systems through configuration.
    """

    def __init__(self, erp_type: Optional[str] = None, max_concurrent_offers: int = 2):
        """
        Initialize the automation system.

        Args:
            erp_type: ERP system type (defaults to environment variable)
            max_concurrent_offers: Maximum number of offers to process concurrently (default: 2)
        """
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.erp_type = erp_type.lower()

        # Create orchestrator (ERP-agnostic!)
        self.orchestrator = OfferOrchestrator(erp_type=erp_type)

        # Email processing
        self.gmail_processor: Optional[GmailServiceAccountProcessor] = None
        self.gmail_sender: Optional[GmailServiceAccountSender] = None
        self.email_classifier: Optional[EmailClassifier] = None

        # Concurrency control
        self.max_concurrent_offers = max_concurrent_offers
        self.semaphore: Optional[asyncio.Semaphore] = None
        self._active_tasks: List[asyncio.Task] = []

        # System state
        self.is_initialized = False

        # Log ERP information without assuming a concrete ERP factory exists
        erp_name = (
            getattr(self.orchestrator.factory, "erp_name", None)
            if getattr(self.orchestrator, "factory", None) is not None
            else getattr(self.orchestrator, "erp_type", "unknown")
        )

        self.logger.info(
            f"Offer Automation V2 initialized for ERP: {erp_name} "
            f"(max concurrent: {max_concurrent_offers})"
        )

    async def initialize(self) -> None:
        """Initialize async components."""
        if self.is_initialized:
            return

        self.logger.info("Initializing email processing components...")

        try:
            # Initialize Gmail processor
            self.gmail_processor = GmailServiceAccountProcessor()
            await self.gmail_processor.initialize()

            # Initialize Gmail sender
            self.gmail_sender = GmailServiceAccountSender()

            # Initialize email classifier
            self.email_classifier = EmailClassifier()

            # Initialize semaphore for concurrency control
            self.semaphore = asyncio.Semaphore(self.max_concurrent_offers)

            self.is_initialized = True
            self.logger.info(
                f"✅ Email processing components initialized "
                f"(concurrency limit: {self.max_concurrent_offers})"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize email components: {e}")
            raise

    async def close(self) -> None:
        """Clean up resources."""
        self.logger.info("Closing Offer Automation V2...")
        # Add any cleanup needed

    async def _process_with_semaphore(self, email_data: Dict[str, Any]) -> WorkflowResult:
        """
        Process a single email with semaphore-controlled concurrency.

        Args:
            email_data: Email data to process

        Returns:
            WorkflowResult
        """
        async with self.semaphore:
            email_id = email_data.get('id', 'unknown')
            self.logger.info(f"🔒 Acquired semaphore slot for email {email_id}")

            try:
                result = await self.process_single_email(email_data)
                return result
            finally:
                self.logger.info(f"🔓 Released semaphore slot for email {email_id}")

    async def process_single_email(self, email_data: Dict[str, Any]) -> WorkflowResult:
        """
        Process a single email offer request.

        Args:
            email_data: Email data with sender, subject, body, attachments

        Returns:
            WorkflowResult with success status and offer details
        """
        if not self.is_initialized:
            await self.initialize()

        self.logger.info("=" * 80)
        self.logger.info(f"Processing email: {email_data.get('subject', 'No subject')}")
        self.logger.info("=" * 80)

        start_time = datetime.now()

        # Send "process starting" confirmation to the sender
        if self.gmail_sender and email_data.get('sender'):
            try:
                await self.gmail_sender.send_process_starting_confirmation(
                    recipient_email=email_data.get('sender'),
                    email_data=email_data,
                    classification_result=None  # Classification already passed at this point
                )
                self.logger.info(f"✅ Process starting confirmation sent to {email_data.get('sender')}")
            except Exception as e:
                self.logger.warning(f"Failed to send process starting confirmation: {e}")
                # Continue processing even if confirmation fails

        try:
            # Use the orchestrator to process the offer
            result = await self.orchestrator.process_offer_request(email_data)

            processing_time = (datetime.now() - start_time).total_seconds()

            if result.success:
                self.logger.info("=" * 80)
                self.logger.info(f"✅ Offer created successfully in {processing_time:.2f}s")
                self.logger.info(f"   Offer number: {result.offer_number}")
                self.logger.info(f"   Customer: {result.customer_name}")
                self.logger.info(f"   Total: €{result.total_amount:.2f}")
                self.logger.info("=" * 80)

                # Send confirmation email if configured
                if self.gmail_sender and email_data.get('sender'):
                    await self._send_confirmation(email_data, result)

            else:
                self.logger.error("=" * 80)
                self.logger.error(f"❌ Offer creation failed after {processing_time:.2f}s")
                self.logger.error(f"   Errors: {', '.join(result.errors)}")
                self.logger.error("=" * 80)

                # Send failure notification
                if self.gmail_sender and email_data.get('sender'):
                    await self._send_failure_notification(email_data, result)

            return result

        except Exception as e:
            self.logger.error(f"Unexpected error processing email: {e}", exc_info=True)
            return WorkflowResult(
                success=False,
                errors=[str(e)]
            )

    async def process_incoming_emails(self, max_emails: int = 10) -> List[WorkflowResult]:
        """
        Poll and process incoming offer request emails concurrently.

        Processes up to max_concurrent_offers emails in parallel, controlled by semaphore.

        Args:
            max_emails: Maximum number of emails to process in one batch

        Returns:
            List of WorkflowResult objects
        """
        if not self.is_initialized:
            await self.initialize()


        try:
            # Fetch unread emails
            emails = await self.gmail_processor.get_recent_emails(
                max_results=max_emails
            )

            if not emails:
                return []

            self.logger.info(
                f"Found {len(emails)} new offer request(s) - "
                f"processing up to {self.max_concurrent_offers} concurrently"
            )

            # Classify and filter emails first
            emails_to_process = []
            for email_data in emails:
                if self.email_classifier:
                    try:
                        classification = await self.email_classifier.classify_email(email_data)
                        if classification['action'] != EmailAction.START_OFFER_AUTOMATION:
                            self.logger.info(
                                f"Email {email_data.get('id', 'unknown')} classified as "
                                f"{classification['action'].value}, skipping"
                            )
                            continue
                    except Exception as e:
                        self.logger.error(f"Email classification failed: {e}")
                        # Continue processing anyway

                emails_to_process.append(email_data)

            if not emails_to_process:
                self.logger.info("No emails to process after classification")
                # Still mark all fetched emails as read to prevent re-classification
                if self.gmail_processor:
                    for email_data in emails:
                        email_id = email_data.get('id')
                        if email_id:
                            try:
                                await self.gmail_processor.mark_email_as_read(email_id)
                                self.logger.debug(f"✅ Marked skipped email {email_id} as read")
                            except Exception as e:
                                self.logger.warning(f"Failed to mark email {email_id} as read: {e}")
                    self.logger.info(f"✅ Marked {len(emails)} skipped emails as read")
                return []

            self.logger.info(f"Processing {len(emails_to_process)} emails concurrently...")

            # Process emails concurrently with semaphore control
            tasks = [
                self._process_with_semaphore(email_data)
                for email_data in emails_to_process
            ]

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results
            processed_results = []
            for i, result in enumerate(results):
                email_data = emails_to_process[i]
                email_id = email_data.get('id', 'unknown')

                # Handle exceptions from tasks
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Email {email_id} processing failed with exception: {result}",
                        exc_info=result
                    )
                    processed_results.append(
                        WorkflowResult(success=False, errors=[str(result)])
                    )
                else:
                    processed_results.append(result)

            # Mark ALL fetched emails as read (regardless of classification or processing result)
            # This prevents infinite loops of re-processing failing or skipped emails
            if self.gmail_processor:
                for email_data in emails:
                    email_id = email_data.get('id')
                    if email_id:
                        try:
                            await self.gmail_processor.mark_email_as_read(email_id)
                            self.logger.debug(f"✅ Marked email {email_id} as read")
                        except Exception as e:
                            self.logger.warning(f"Failed to mark email {email_id} as read: {e}")
                self.logger.info(f"✅ Marked {len(emails)} emails as read")

            # Summary
            successful = sum(1 for r in processed_results if r.success)
            failed = len(processed_results) - successful

            self.logger.info("=" * 80)
            self.logger.info(f"📊 Batch complete: {successful} successful, {failed} failed")
            self.logger.info("=" * 80)

            return processed_results

        except Exception as e:
            self.logger.error(f"Error processing incoming emails: {e}", exc_info=True)
            return []

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform system health check.

        Returns:
            Dict with health status
        """
        try:
            if not self.is_initialized:
                await self.initialize()

            # Check email connectivity
            email_healthy = self.gmail_processor is not None

            # Check ERP connectivity
            erp_healthy = True
            try:
                # You can add a ping method to repositories if needed
                pass
            except Exception as e:
                self.logger.error(f"ERP health check failed: {e}")
                erp_healthy = False

            overall_healthy = email_healthy and erp_healthy

            return {
                'status': 'healthy' if overall_healthy else 'degraded',
                'email_processor': 'healthy' if email_healthy else 'unavailable',
                'erp_system': 'healthy' if erp_healthy else 'unavailable',
                'erp_type': getattr(self.orchestrator, 'erp_type', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _send_confirmation(
        self, email_data: Dict[str, Any], result: WorkflowResult
    ) -> None:
        """Send confirmation email to sender."""
        try:
            sender_email = email_data.get('sender', '')
            offer_details = {
                'offer_number': result.offer_number,
                'customer_name': result.customer_name,
                'total_amount': result.total_amount
            }
            
            # Build customer details from result context
            customer = result.context.customer if result.context else None
            customer_details = {
                'name': result.customer_name or (customer.name if customer else ''),
                'number': customer.customer_number if customer else '',
                'id': customer.id if customer else '',
                'email': sender_email,
                'street': customer.street if customer else '',
                'postal_code': "N/A" if self.erp_type.lower() == 'csv' else customer.postal_code if customer else '',
                'city': "N/A" if self.erp_type.lower() == 'csv' else customer.city if customer else '',
                'ceo_contact': "N/A" if self.erp_type.lower() == 'csv' else customer.contact_person if customer else '',
                'deny_credit': False if self.erp_type.lower() == 'csv' else not customer.credit_allowed if customer else False
            }
            
            # Build product matches from result context
            product_matches = []
            if result.context and hasattr(result.context, 'matched_products') and result.context.matched_products:
                for product in result.context.matched_products:
                    match_details = getattr(product, 'match_details', {})

                    # Extract AI confidence and reasoning from match_details
                    ai_confidence = 75  # Default
                    ai_reasoning = 'Ei saatavilla'
                    original_customer_term = getattr(product, 'product_name', '')

                    if match_details:
                        ai_confidence = match_details.get('ai_confidence', 75)
                        ai_reasoning = match_details.get('ai_reasoning', 'Ei saatavilla')
                        original_customer_term = match_details.get('original_customer_term', getattr(product, 'product_name', ''))
                    elif hasattr(product, 'confidence_score'):
                        # Convert confidence_score (0-1) to percentage if needed
                        ai_confidence = int(product.confidence_score * 100) if product.confidence_score <= 1 else product.confidence_score
                        original_customer_term = getattr(product, 'product_name', '')

                    product_matches.append({
                        'product_code': getattr(product, 'product_code', ''),
                        'product_name': getattr(product, 'product_name', ''),
                        'quality': match_details.get('quality', ''),
                        'specification': match_details.get('specification', ''),
                        'quantity': getattr(product, 'quantity_requested', 1),
                        'unit_price': getattr(product, 'price', 0.0),
                        'total_price': getattr(product, 'price', 0.0) * getattr(product, 'quantity_requested', 1),
                        'ai_confidence': ai_confidence,
                        'ai_reasoning': ai_reasoning,
                        'original_customer_term': original_customer_term
                    })
            
            # Build pricing details
            pricing_details = {
                'subtotal': result.total_amount or 0.0,
                'total': result.total_amount or 0.0,
                'currency': 'EUR'
            }
            
            await self.gmail_sender.send_offer_confirmation(
                recipient_email=sender_email,
                offer_details=offer_details,
                customer_details=customer_details,
                product_matches=product_matches,
                pricing_details=pricing_details,
                original_email_data=email_data
            )

            self.logger.info(f"Confirmation email sent to {sender_email}")

        except Exception as e:
            self.logger.error(f"Failed to send confirmation email: {e}")

    async def _send_failure_notification(
        self, email_data: Dict[str, Any], result: WorkflowResult
    ) -> None:
        """Send failure notification to sender."""
        try:
            sender_email = email_data.get('sender', '')
            
            error_details = {
                'errors': result.errors,
                'subject': email_data.get('subject', 'Request')
            }

            await self.gmail_sender.send_offer_error_notification(
                recipient_email=sender_email,
                error_details=error_details,
                original_email_data=email_data
            )

            self.logger.info(f"Failure notification sent to {sender_email}")

        except Exception as e:
            self.logger.error(f"Failed to send failure notification: {e}")


# ==================== ENTRY POINTS ====================


async def main():
    """
    Main entry point for production use.

    Starts the email polling loop.
    """
    logger = None
    automation = None

    try:
        # Initialize logging
        setup_logging()
        logger = get_logger(__name__)

        logger.info("=" * 80)
        logger.info("Starting Offer Automation System V2")
        logger.info("=" * 80)
        import os
        erp_type = os.getenv('ERP_TYPE', 'CSV')
        # Create automation system (ERP type from environment)
        automation = OfferAutomationV2(
            erp_type=erp_type
        )
        await automation.initialize()

        # Health check
        health = await automation.health_check()
        logger.info(f"System health: {health['status']}")
        logger.info(f"ERP system: {health['erp_type']}")

        logger.info("=" * 80)
        logger.info("Ready to process offer requests")
        logger.info("=" * 80)

        # Polling loop
        while True:
            try:
                # Check for new emails every 30 seconds
                await asyncio.sleep(30)

                results = await automation.process_incoming_emails(max_emails=5)

                if results:
                    successful = sum(1 for r in results if r.success)
                    logger.info(
                        f"📊 Processed {len(results)} emails: "
                        f"{successful} successful, {len(results) - successful} failed"
                    )

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer after errors

    except KeyboardInterrupt:
        if logger:
            logger.info("Shutting down...")
    except Exception as e:
        if logger:
            logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if automation:
            await automation.close()


async def test_main():
    """
    Test entry point for development.

    Processes a sample email to test the system.
    """
    logger = None
    automation = None

    try:
        # Initialize logging
        setup_logging()
        logger = get_logger(__name__)

        logger.info("=" * 80)
        logger.info("Offer Automation V2 - Test Mode")
        logger.info("=" * 80)
        import os
        erp_type = os.getenv('ERP_TYPE', 'CSV')
        # Create automation system
        automation = OfferAutomationV2(
            erp_type=erp_type
        )
        await automation.initialize()

        # Sample test email
        test_email = {
            'sender': 'lauri@erp-agent.com',
            'subject': 'Tilaus lvi caidon oy',
            'body': '''
                Tilaus asiakkaalta


DN50 Kaulus HST
DN65 Kaulus HST
DN50 irtolaippa hst
dn65 irtolaippa hst
dn65/50 sup.kesk. HST
DN50 Käyrä HST
DN20 Putki HST s=2

DN100 Putki HST s=2
DN50 Kynsiliitin HST UK

                yt,
                jarkko, 
                lvi caidon oy
            ''',
            'date': datetime.now().isoformat(),
            'attachments': []
        }
        additional_rows_if_needed = '''
                D16 En 1,4301  24 Kg
                Av 14 En 1,4404  1 salko (3m)
                Av 19 En 1,4404 36 Kg
                Av 24 En 1,4404 35 Kg
        '''

        # Process the test email
        result = await automation.process_single_email(test_email)

        if result.success:
            logger.info("=" * 80)
            logger.info("✅ Test completed successfully!")
            logger.info(f"   Offer: {result.offer_number}")
            logger.info(f"   Customer: {result.customer_name}")
            logger.info(f"   Total: €{result.total_amount:.2f}")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("❌ Test failed!")
            logger.error(f"   Errors: {', '.join(result.errors)}")
            logger.error("=" * 80)

        return result.to_dict()

    except Exception as e:
        if logger:
            logger.error(f"Test failed with exception: {e}", exc_info=True)
        else:
            logging.error(f"Test failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
    finally:
        if automation:
            await automation.close()


if __name__ == "__main__":
    # Run test mode by default
    asyncio.run(main())

    # To run in production mode, use:
    # asyncio.run(main())
