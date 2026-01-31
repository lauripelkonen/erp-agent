"""
Offer Creation Orchestrator

Clean, ERP-agnostic orchestrator that replaces the 2,359-line main.py.
Uses the adapter layer to work with any ERP system.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import csv
import os
import re
from pathlib import Path

from src.core.workflow import (
    WorkflowContext,
    WorkflowResult,
    WorkflowStep,
    WorkflowDefinition
)
from src.erp.factory import ERPFactory
from src.erp.base.customer_repository import CustomerRepository
from src.erp.base.person_repository import PersonRepository
from src.erp.base.offer_repository import OfferRepository
from src.erp.base.product_repository import ProductRepository
from src.erp.base.pricing_service import PricingService
from src.extraction.company_extractor import CompanyExtractor
from src.domain.offer import Offer, OfferLine
from src.domain.customer import Customer
from src.domain.person import Person
from src.product_matching.ai_analyzer import AIAnalyzer
from src.product_matching.attachment_processor import AttachmentProcessor
from src.product_matching.pdf_processor import PDFProcessor
from src.product_matching.product_matcher import ProductMatcher
from src.product_matching.matcher_class import ProductMatch
from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError, ValidationError


class OfferOrchestrator:
    """
    Orchestrates the offer creation workflow.

    This replaces the monolithic OfferAutomation class with a clean,
    ERP-agnostic implementation using the adapter pattern.
    """

    def __init__(self, erp_type: Optional[str] = None):
        """
        Initialize the orchestrator.

        Args:
            erp_type: ERP system type (defaults to environment variable)
        """
        self.logger = get_logger(__name__)

     # Determine ERP type from parameter or environment

        if erp_type is None:

            erp_type = os.getenv('ERP_TYPE', 'lemonsoft')

 

        self.erp_type = erp_type.lower()

 

        # Create ERP factory and repositories only if not using CSV mode


        from src.erp.factory import ERPFactory

 

        self.factory = ERPFactory(erp_type)

        self.customer_repo = self.factory.create_customer_repository()

        self.person_repo = self.factory.create_person_repository()

        self.offer_repo = self.factory.create_offer_repository()

        self.product_repo = self.factory.create_product_repository()

        self.pricing_service = self.factory.create_pricing_service()

        self.logger.info(f"Orchestrator initialized for ERP: {self.factory.erp_name}")


        # Create extraction and matching services

        self.company_extractor = CompanyExtractor()

        self.ai_analyzer: Optional[AIAnalyzer] = None

        self.attachment_processor: Optional[AttachmentProcessor] = None

        self.pdf_processor: Optional[PDFProcessor] = None

        self.product_matcher: Optional[ProductMatcher] = None

 

        # Initialize AI components if available

        try:

            self.ai_analyzer = AIAnalyzer()

            self.attachment_processor = AttachmentProcessor()

            self.pdf_processor = PDFProcessor()

            self.product_matcher = ProductMatcher(product_repository=self.product_repo)

            self.logger.info("AI components initialized")

        except Exception as e:

            self.logger.warning(f"AI components not available: {e}")

    async def process_offer_request(self, email_data: Dict[str, Any]) -> WorkflowResult:
        """
        Process an offer request from an email.

        This is the main entry point that executes the complete workflow.

        Args:
            email_data: Email data with sender, subject, body, attachments

        Returns:
            WorkflowResult with success status and offer details
        """
        context = WorkflowContext(email_data=email_data)

        try:
            self.logger.info("=" * 80)
            self.logger.info("Starting offer creation workflow")
            self.logger.info("=" * 80)

            # Execute workflow steps
            await self._parse_email(context)
            await self._extract_company(context)
            await self._find_customer(context)
            await self._find_salesperson(context)
            await self._extract_products(context)
            await self._match_products(context)
            await self._calculate_pricing(context)
            await self._build_offer(context)
            await self._create_offer(context)
            await self._verify_offer(context)

            # Mark as complete
            context.current_step = WorkflowStep.COMPLETE

            # Build result
            result = WorkflowResult(
                success=True,
                offer_number=context.offer_number,
                customer_name=context.company_name,
                total_amount=context.pricing_result.get('total_amount', 0.0) if context.pricing_result else 0.0,
                warnings=context.warnings,
                context=context
            )

            self.logger.info("=" * 80)
            self.logger.info(f"✅ Workflow completed successfully: Offer {context.offer_number}")
            self.logger.info("=" * 80)

            return result

        except Exception as e:
            self.logger.error(f"Workflow failed at step {context.current_step.value}: {e}", exc_info=True)
            context.add_error(str(e))

            return WorkflowResult(
                success=False,
                errors=context.errors,
                warnings=context.warnings,
                context=context
            )

    async def process_offer_request_for_review(self, email_data: Dict[str, Any]) -> WorkflowResult:
        """
        Process an offer request but stop before ERP creation.

        This method runs workflow steps 1-8 (parse through build_offer) and
        returns a WorkflowResult ready for human review. The offer is NOT
        created in the ERP system - that happens via send_offer_to_erp().

        Used by the REST API to prepare offers for frontend review before
        sending to ERP.

        Args:
            email_data: Email data with sender, subject, body, attachments

        Returns:
            WorkflowResult with offer details ready for review
        """
        context = WorkflowContext(email_data=email_data)

        try:
            self.logger.info("=" * 80)
            self.logger.info("Starting offer creation workflow (FOR REVIEW)")
            self.logger.info("=" * 80)

            # Execute workflow steps 1-8 (stops before CREATE_OFFER)
            await self._parse_email(context)
            await self._extract_company(context)
            await self._find_customer(context)
            await self._find_salesperson(context)
            await self._extract_products(context)
            await self._match_products(context)
            await self._calculate_pricing(context)
            await self._build_offer(context)

            # Generate a temporary offer number for tracking
            import random
            temp_offer_number = f"PENDING-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
            context.offer_number = temp_offer_number

            # Mark as ready for review (not complete yet)
            context.current_step = WorkflowStep.BUILD_OFFER

            # Build result
            result = WorkflowResult(
                success=True,
                offer_number=temp_offer_number,
                customer_name=context.company_name,
                total_amount=context.pricing_result.get('total_amount', 0.0) if context.pricing_result else 0.0,
                warnings=context.warnings,
                context=context
            )

            self.logger.info("=" * 80)
            self.logger.info(f"✅ Offer ready for review: {temp_offer_number}")
            self.logger.info(f"   Customer: {context.company_name}")
            self.logger.info(f"   Lines: {len(context.offer.lines) if context.offer else 0}")
            self.logger.info("=" * 80)

            return result

        except Exception as e:
            self.logger.error(f"Workflow failed at step {context.current_step.value}: {e}", exc_info=True)
            context.add_error(str(e))

            return WorkflowResult(
                success=False,
                errors=context.errors,
                warnings=context.warnings,
                context=context
            )

    async def send_offer_to_erp(self, context: WorkflowContext) -> WorkflowResult:
        """
        Send a reviewed offer to the ERP system.

        This completes the workflow by executing the CREATE_OFFER and
        VERIFY_OFFER steps.

        Args:
            context: WorkflowContext with offer data from process_offer_request_for_review

        Returns:
            WorkflowResult with ERP offer number
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("Sending reviewed offer to ERP")
            self.logger.info("=" * 80)

            # Execute remaining workflow steps
            await self._create_offer(context)
            await self._verify_offer(context)

            # Mark as complete
            context.current_step = WorkflowStep.COMPLETE

            result = WorkflowResult(
                success=True,
                offer_number=context.offer_number,
                customer_name=context.company_name,
                total_amount=context.pricing_result.get('total_amount', 0.0) if context.pricing_result else 0.0,
                warnings=context.warnings,
                context=context
            )

            self.logger.info(f"✅ Offer sent to ERP: {context.offer_number}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to send offer to ERP: {e}", exc_info=True)
            context.add_error(str(e))

            return WorkflowResult(
                success=False,
                errors=context.errors,
                warnings=context.warnings,
                context=context
            )

    # ==================== WORKFLOW STEPS ====================

    async def _parse_email(self, context: WorkflowContext) -> None:
        """Step 1: Parse email data."""
        context.current_step = WorkflowStep.PARSE_EMAIL
        self.logger.info("Step 1: Parsing email")

        email_data = context.email_data
        context.sender_email = email_data.get('sender', '')
        context.email_subject = email_data.get('subject', '')
        context.email_body = email_data.get('body', '')

        # Extract sender name if available
        if '<' in context.sender_email:
            parts = context.sender_email.split('<')
            context.sender_name = parts[0].strip().strip('"')
            context.sender_email = parts[1].rstrip('>')
        else:
            context.sender_name = context.sender_email.split('@')[0]

        self.logger.info(f"Sender: {context.sender_name} <{context.sender_email}>")
        self.logger.info(f"Subject: {context.email_subject}")

    async def _extract_company(self, context: WorkflowContext) -> None:
        """Step 2: Extract company information using AI."""
        context.current_step = WorkflowStep.EXTRACT_COMPANY
        self.logger.info("Step 2: Extracting company information")

        extraction_result = await self.company_extractor.extract_company_information(
            context.email_data
        )

        context.company_name = extraction_result.get('company_name')
        context.customer_number = extraction_result.get('customer_number')
        context.delivery_contact = extraction_result.get('delivery_contact')
        context.customer_reference = extraction_result.get('customer_reference')
        context.extraction_confidence = extraction_result.get('confidence', 0.0)

        if not context.company_name:
            raise ValidationError("Could not extract company name from email")

        self.logger.info(f"Company: {context.company_name}")
        self.logger.info(f"Contact: {context.delivery_contact}")
        self.logger.info(f"Reference: {context.customer_reference}")

    async def _find_customer(self, context: WorkflowContext) -> None:
        """Step 3: Find customer in CSV."""
        context.current_step = WorkflowStep.FIND_CUSTOMER
        self.logger.info("Step 3: Finding customer in CSV")

        # Read customers from CSV
        customers = self._read_csv('customers.csv')
        if self.erp_type == 'csv':
            print("------------------FINDINGG CSV CUSTOMERS------------------")

            customer_data = None

            # Try lookup by customer number first if available
            if context.customer_number:
                for row in customers:
                    if row.get('customer_number') == str(context.customer_number):
                        customer_data = row
                        break

            # Fall back to name search (case-insensitive partial match)
            if not customer_data and context.company_name:
                search_name = context.company_name.lower()
                for row in customers:
                    if search_name in row.get('name', '').lower():
                        customer_data = row
                        break
                try:
                    from src.customer.enhanced_lookup import EnhancedCustomerLookup
                    enhanced_customer_lookup = EnhancedCustomerLookup()
                    y_tunnus = await enhanced_customer_lookup._search_ytunnus_with_google(context.company_name)
                    if y_tunnus:
                        customer_data = {
                            'customer_number': y_tunnus
                            }
                except Exception as e:
                    self.logger.error(f"Error searching Y-tunnus with Google: {e}")

            if not customer_data and self.erp_type.lower() == 'csv':
                # Create fallback customer when not found
                self.logger.warning(f"Customer not found in CSV: {context.company_name} - using fallback customer")
                context.customer = Customer(
                    id='UNKNOWN',
                    customer_number='UNKNOWN',
                    name=f'{context.company_name} - No data available',
                    credit_allowed=False,
                    responsible_person_number=''
                )
                context.add_warning(f"Customer not found in CSV: {context.company_name}. Using fallback customer with default pricing.")

                # Store default metadata for fallback customer
                context.metadata['payment_terms'] = {'days': 30}  # Default
                context.metadata['invoicing_details'] = {
                    'street': '',
                    'postal_code': '',
                    'city': '',
                    'country': ''
                }

                self.logger.info(f"⚠️ Using fallback customer: {context.customer.name}")
            else:
                # Create Customer object from CSV data
                context.customer = Customer(
                    id=customer_data.get('customer_number', ''),
                    customer_number=customer_data.get('customer_number', ''),
                    name=context.company_name if context.company_name else customer_data.get('name', ''),
                    credit_allowed=customer_data.get('credit_allowed', 'FALSE').upper() == 'TRUE',
                    responsible_person_number=customer_data.get('responsible_person_number', '')
                )

                self.logger.info(f"✅ Found customer: {context.customer.name} ({context.customer.customer_number})")
                self.logger.info(f"Credit allowed: {context.customer.credit_allowed}")

                # Store additional customer details in metadata
                context.metadata['payment_terms'] = {'days': 30}  # Default
                context.metadata['invoicing_details'] = {
                    'street': customer_data.get('street', ''),
                    'postal_code': customer_data.get('postal_code', ''),
                    'city': customer_data.get('city', ''),
                    'country': customer_data.get('country', '')
                }
        else:
            """Step 3: Find customer in ERP."""
            context.current_step = WorkflowStep.FIND_CUSTOMER
            self.logger.info("Step 3: Finding customer in ERP")

            # Try lookup by customer number first if available
            if context.customer_number:
                context.customer = await self.customer_repo.find_by_number(
                    context.customer_number
                )

            # Fall back to name search
            if not context.customer:
                context.customer = await self.customer_repo.find_by_name(
                    context.company_name
                )

            if not context.customer:
                raise ValidationError(
                    f"Customer not found in ERP: {context.company_name}"
                )

            self.logger.info(f"✅ Found customer: {context.customer.name} ({context.customer.customer_number})")
            self.logger.info(f"Credit allowed: {context.customer.credit_allowed}")

            # Get additional customer details and store in metadata
            payment_terms = await self.customer_repo.get_payment_terms(
                context.customer.id
            )
            invoicing_details = await self.customer_repo.get_invoicing_details(
                context.customer.id
            )

            context.metadata['payment_terms'] = payment_terms
            context.metadata['invoicing_details'] = invoicing_details

    async def _find_salesperson(self, context: WorkflowContext) -> None:
        """Step 4: Find responsible salesperson in CSV."""
        context.current_step = WorkflowStep.FIND_SALESPERSON
        self.logger.info("Step 4: Finding salesperson in CSV")

        # Read persons from CSV
        persons = self._read_csv('persons.csv')

        person_data = None

        # Try to find by email first
        if context.sender_email:
            for row in persons:
                if row.get('email', '').lower() == context.sender_email.lower():
                    person_data = row
                    break

        # Fall back to customer's responsible person
        if not person_data and context.customer and context.customer.responsible_person_number:
            for row in persons:
                if row.get('number') == str(context.customer.responsible_person_number):
                    person_data = row
                    break

        if person_data:
            # Create Person object from CSV data
            context.salesperson = Person(
                id=person_data.get('number', ''),
                number=person_data.get('number', ''),
                name=person_data.get('name', ''),
                email=person_data.get('email', ''),
                phone=person_data.get('phone', '')
            )
            self.logger.info(f"✅ Salesperson: {context.salesperson.name} ({context.salesperson.number})")
        else:
            context.add_warning("No salesperson found - offer will use default")

    async def _extract_products(self, context: WorkflowContext) -> None:
        """Step 5: Extract products from email."""
        context.current_step = WorkflowStep.EXTRACT_PRODUCTS
        self.logger.info("Step 5: Extracting products from email")

        if not self.ai_analyzer:
            context.add_warning("AI analyzer not available - using manual processing")
            context.extracted_products = []
            return

        # Reset AI analyzer state for this new email to prevent
        # products from previous emails affecting current extraction
        self.ai_analyzer.reset_state()

        # Process attachments
        excel_data, pdf_data = await self._process_email_attachments(context.email_data)

        # Extract products using AI
        filtered_emails = [context.email_data]
        
        # Log attachment info being passed to AI analyzer for debugging
        attachments = context.email_data.get('attachments', [])
        self.logger.info(f"📎 Passing {len(attachments)} attachments to AI analyzer for image processing")
        for i, att in enumerate(attachments):
            filename = att.get('filename', 'unknown')
            mime_type = att.get('mime_type', 'unknown')
            has_data = 'data' in att and att.get('data') is not None
            data_size = len(att.get('data', b'')) if has_data else 0
            source = att.get('source', 'unknown')
            self.logger.info(f"   Attachment {i+1}: {filename} (mime: {mime_type}, source: {source}, size: {data_size} bytes)")
        
        matched_products = []
        unclear_terms = []

        def on_match_found(match_dict):
            matched_products.append(match_dict)

        def on_unclear_term_found(unclear_dict):
            unclear_terms.append(unclear_dict)

        try:
            await self.ai_analyzer.identify_unclear_terms(
                filtered_emails,
                excel_data,
                pdf_data,
                on_unclear_term_found=on_unclear_term_found,
                on_match_found=on_match_found
            )
        except Exception as e:
            self.logger.error(f"Product extraction failed: {e}")
            context.add_warning(f"Product extraction error: {e}")

        context.extracted_products = matched_products + unclear_terms
        self.logger.info(f"Extracted {len(context.extracted_products)} product items")

    async def _match_products(self, context: WorkflowContext) -> None:
        """Step 6: Match extracted products to CSV catalog."""
        context.current_step = WorkflowStep.MATCH_PRODUCTS
        self.logger.info("Step 6: Matching products to CSV catalog")

        if not context.extracted_products:
            raise ValidationError("No products found in email")

        # Read products from CSV
        products_csv = self._read_csv('products.csv')

        # Convert extracted products to ProductMatch objects
        context.matched_products = []

        for item in context.extracted_products:
            try:
                # Try to find product in CSV by product code
                product_code = item.get('matched_product_code', item.get('product_code', ''))
                product_name = item.get('matched_product_name', item.get('product_name', ''))

                csv_product = None
                if product_code:
                    # Search by product code (Tuotekoodi)
                    for row in products_csv:
                        if row.get('Tuotekoodi', '') == product_code:
                            csv_product = row
                            break

                # If not found by code, try partial name match
                if not csv_product and product_name:
                    search_name = product_name.lower()
                    for row in products_csv:
                        if search_name in row.get('Tuotenimi', '').lower():
                            csv_product = row
                            break

                # Use CSV data if found, otherwise use extracted data
                if csv_product:
                    final_code = csv_product.get('Tuotekoodi', product_code)
                    final_name = csv_product.get('Tuotenimi', product_name)
                    final_group = csv_product.get('Tuoteryhmä', '')
                    final_quality = csv_product.get('Laatu', '')
                    final_specification = csv_product.get('Määrittely', '')
                else:
                    final_code = product_code
                    final_name = product_name
                    final_group = item.get('product_group', '')
                    final_quality = ''
                    final_specification = ''
                    context.add_warning(f"Product not found in CSV, using extracted data: {product_name}")

                # Parse quantity - handle strings like "1 kpl", "25 m", etc.
                quantity_raw = item.get('quantity', 1.0)
                try:
                    if isinstance(quantity_raw, (int, float)):
                        quantity = float(quantity_raw)
                    else:
                        # Extract numeric part from string like "1 kpl", "25.5 m"
                        quantity_str = str(quantity_raw).strip()
                        # Match numbers (including decimals) at the start
                        match = re.match(r'^[\d.,]+', quantity_str)
                        if match:
                            # Handle both . and , as decimal separators
                            quantity = float(match.group().replace(',', '.'))
                        else:
                            quantity = 1.0
                except (ValueError, TypeError):
                    quantity = 1.0

                # Parse price safely
                price_raw = item.get('matched_price', item.get('price', 0.0))
                try:
                    price = float(price_raw) if price_raw else 0.0
                except (ValueError, TypeError):
                    price = 0.0

                # Parse confidence score safely
                confidence_raw = item.get('confidence_score', 0.0)
                try:
                    confidence = float(confidence_raw) if confidence_raw else 0.0
                except (ValueError, TypeError):
                    confidence = 0.0

                # Create ProductMatch from extraction result
                # Add quality and specification to match_details
                enhanced_match_details = item.copy()
                enhanced_match_details['quality'] = final_quality
                enhanced_match_details['specification'] = final_specification

                product_match = ProductMatch(
                    product_code=final_code,
                    product_name=final_name,
                    description=item.get('description', ''),
                    unit=item.get('unit', 'KPL'),
                    price=price,
                    product_group=final_group,
                    confidence_score=confidence,
                    match_method='csv_lookup' if csv_product else 'ai_extraction',
                    quantity_requested=quantity,
                    match_details=enhanced_match_details
                )
                context.matched_products.append(product_match)

            except Exception as e:
                self.logger.error(f"Error converting product match: {e}")
                context.add_warning(f"Skipped invalid product: {item.get('product_name', 'unknown')}")

        if not context.matched_products:
            raise ValidationError("No valid products could be matched")

        self.logger.info(f"✅ Matched {len(context.matched_products)} products")

    async def _calculate_pricing(self, context: WorkflowContext) -> None:
        """Step 7: Calculate pricing with discounts."""
        context.current_step = WorkflowStep.CALCULATE_PRICING
        self.logger.info("Step 7: Calculating pricing")

        if not context.customer or not context.matched_products:
            raise ValidationError("Missing customer or products for pricing calculation")

        # Use CSV mode simple pricing or ERP pricing service

        if self.erp_type == 'csv':

            # Simple pricing calculation for CSV mode

            product_lines = []

            net_total = 0.0

            vat_amount = 0.0

 

            for product in context.matched_products:

                unit_price = product.price

                quantity = product.quantity_requested

                line_total = unit_price * quantity

                vat_rate = 25.5  # Default VAT rate

                line_vat = line_total * (vat_rate / 100)

 

                product_lines.append({

                    'product_code': product.product_code,

                    'product_name': product.product_name,

                    'quantity': quantity,

                    'unit_price': unit_price,

                    'net_price': unit_price,

                    'line_total': line_total,

                    'discount_percent': 0.0,

                    'vat_rate': vat_rate,

                    'vat_amount': line_vat,

                })

 

                net_total += line_total

                vat_amount += line_vat

 

            context.pricing_result = {

                'net_total': net_total,

                'vat_amount': vat_amount,

                'total_amount': net_total + vat_amount,

                'product_lines': product_lines,

            }

 

            self.logger.info(f"✅ Pricing calculated (CSV mode): €{net_total + vat_amount:.2f} "

                            f"({len(product_lines)} lines)")

        else:

            # Calculate pricing using the pricing service

            pricing_result = await self.pricing_service.calculate_pricing(

                customer_id=context.customer.customer_number,

                matched_products=context.matched_products

            )

 

            context.pricing_result = {

                'net_total': pricing_result.net_total,

                'vat_amount': pricing_result.vat_amount,

                'total_amount': pricing_result.total_amount,

                'product_lines': pricing_result.product_lines,

            }

 

            self.logger.info(f"✅ Pricing calculated: €{pricing_result.total_amount:.2f} "

                            f"({len(pricing_result.product_lines)} lines)")

    async def _build_offer(self, context: WorkflowContext) -> None:
        """Step 8: Build offer object."""
        context.current_step = WorkflowStep.BUILD_OFFER
        self.logger.info("Step 8: Building offer object")

        if not context.customer or not context.pricing_result:
            raise ValidationError("Missing customer or pricing data for offer creation")

        # Create offer object
        offer = Offer(
            customer_id=context.customer.customer_number,
            customer_name=context.customer.name,
            offer_date=datetime.now(),
            valid_until=datetime.now() + timedelta(days=30),
            delivery_contact=context.delivery_contact or '',
            customer_reference=context.customer_reference or '',
        )

        # Add metadata for ERP-specific fields
        offer.erp_metadata = {
            'customer_internal_id': context.customer.id,
            'credit_allowed': context.customer.credit_allowed,
            'responsible_person_number': context.salesperson.number if context.salesperson else None,
            'invoicing_details': context.metadata.get('invoicing_details', {}),
            'payment_terms': context.metadata.get('payment_terms', {}),
        }

        # Add product lines from pricing result
        for line_data in context.pricing_result['product_lines']:
            offer_line = OfferLine(
                product_code=line_data.get('product_code', ''),
                product_name=line_data.get('product_name', ''),
                quantity=line_data.get('quantity', 0.0),
                unit_price=line_data.get('unit_price', 0.0),
                net_price=line_data.get('net_price', 0.0),
                line_total=line_data.get('line_total', 0.0),
                discount_percent=line_data.get('discount_percent', 0.0),
                vat_rate=line_data.get('vat_rate', 25.5),
                vat_amount=line_data.get('vat_amount', 0.0),
                ai_confidence=line_data.get('ai_confidence', 0),
            )
            offer.add_line(offer_line)

        context.offer = offer
        self.logger.info(f"✅ Offer built with {len(offer.lines)} lines")

    async def _create_offer(self, context: WorkflowContext) -> None:
        """Step 9: Create offer in ERP or generate mock number for CSV."""
        context.current_step = WorkflowStep.CREATE_OFFER
        self.logger.info("Step 9: Creating offer")

        if not context.offer:
            raise ValidationError("No offer object to create")

        if self.erp_type == 'csv':
            # Generate a mock offer number for CSV mode
            import random
            offer_number = f"CSV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            context.offer_number = offer_number
            self.logger.info(f"✅ Offer generated (CSV mode): {offer_number}")
        else:
            # Create offer using repository
            offer_number = await self.offer_repo.create(context.offer)
            context.offer_number = offer_number
            self.logger.info(f"✅ Offer created in ERP: {offer_number}")

        if not context.offer:

            raise ValidationError("No offer object to create")


    async def _verify_offer(self, context: WorkflowContext) -> None:
        """Step 10: Verify offer was created correctly."""
        context.current_step = WorkflowStep.VERIFY_OFFER
        self.logger.info("Step 10: Verifying offer")

        if not context.offer_number:
            raise ValidationError("No offer number to verify")

        if self.erp_type == 'csv':

            # Skip verification in CSV mode

            context.verification_result = {'verified': True, 'mode': 'csv'}
            self.logger.info(f"✅ Offer verified (CSV mode - skipped ERP verification)")

        else:
            # Verify using repository
            verification = await self.offer_repo.verify(context.offer_number)
            context.verification_result = verification
            if not verification.get('verified', False):

                error_msg = verification.get('error', 'Unknown verification error')

                context.add_warning(f"Offer verification failed: {error_msg}")

                self.logger.warning(f"⚠️ Offer verification failed: {error_msg}")

            else:

                self.logger.info(f"✅ Offer verified successfully")

    # ==================== HELPER METHODS ====================

    def _get_csv_path(self, filename: str) -> Path:
        """Get path to CSV data file."""
        return Path(__file__).parent.parent / 'erp' / 'csv' / 'data' / filename

    def _read_csv(self, filename: str) -> List[Dict[str, str]]:
        """Read CSV file and return list of dictionaries."""
        csv_path = self._get_csv_path(filename)
        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return []

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                return list(reader)
        except Exception as e:
            self.logger.error(f"Error reading CSV file {filename}: {e}")
            return []

    async def _process_email_attachments(
        self, email_data: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process email attachments for product data.
        
        Includes fallback to image-based extraction for PDFs that fail 
        text extraction (both Mistral OCR and standard extraction).
        """
        attachments = email_data.get('attachments', [])

        if not attachments:
            return [], []

        self.logger.info(f"Processing {len(attachments)} email attachments")

        # Convert to format expected by processors
        converted_email = self._convert_gmail_to_legacy_format(email_data)
        email_list = [converted_email]

        # Process Excel attachments
        excel_data = []
        if self.attachment_processor:
            try:
                excel_data = self.attachment_processor.extract_excel_content(email_list)
            except Exception as e:
                self.logger.error(f"Excel attachment processing failed: {e}")

        # Process PDF attachments
        pdf_data = []
        if self.pdf_processor:
            try:
                pdf_data = self.pdf_processor.extract_pdf_content(email_list)
            except Exception as e:
                self.logger.error(f"PDF attachment processing failed: {e}")

        # ============================================================
        # FALLBACK: Convert failed PDFs to images for vision-based OCR
        # ============================================================
        # Check which PDFs failed to extract text and use image analyzer as fallback
        pdf_attachments = [att for att in attachments if att.get('filename', '').lower().endswith('.pdf')]
        
        if pdf_attachments and self.pdf_processor:
            # Determine which PDFs were successfully processed
            successfully_processed_pdfs = set()
            for pdf_result in pdf_data:
                for pdf_content in pdf_result.get('pdf_contents', []):
                    successfully_processed_pdfs.add(pdf_content.get('filename', '').lower())
            
            # Find PDFs that failed extraction
            failed_pdfs = []
            for pdf_att in pdf_attachments:
                pdf_filename = pdf_att.get('filename', '')
                if pdf_filename.lower() not in successfully_processed_pdfs:
                    failed_pdfs.append(pdf_att)
            
            if failed_pdfs:
                self.logger.info(f"🖼️ {len(failed_pdfs)} PDF(s) failed text extraction - using image fallback")
                
                # Convert failed PDFs to images and add to email attachments
                # These will be picked up by the image analyzer later
                for pdf_att in failed_pdfs:
                    try:
                        pdf_filename = pdf_att.get('filename', 'unknown.pdf')
                        self.logger.info(f"📄 Converting failed PDF to images: {pdf_filename}")
                        
                        # Convert first 2 pages of PDF to images
                        pdf_images = self.pdf_processor.convert_pdf_to_images(pdf_att, max_pages=2)
                        
                        if pdf_images:
                            # Add converted images to the email's attachments
                            # They will be processed by image_analyzer in identify_unclear_terms
                            email_data['attachments'].extend(pdf_images)
                            self.logger.info(f"✅ Added {len(pdf_images)} images from {pdf_filename} for vision-based OCR")
                        else:
                            self.logger.warning(f"❌ Could not convert {pdf_filename} to images")
                            
                    except Exception as e:
                        self.logger.error(f"Error converting PDF {pdf_att.get('filename', 'unknown')} to images: {e}")

        self.logger.info(f"Processed attachments: {len(excel_data)} Excel, {len(pdf_data)} PDF")

        return excel_data, pdf_data

    def _convert_gmail_to_legacy_format(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Gmail OAuth format to legacy attachment processor format."""

        class AttachmentObject:
            def __init__(self, data: bytes):
                self.data = data

            @property
            def content_stream(self):
                return self

            def to_array(self):
                return self.data

        # Convert attachments
        converted_attachments = []
        for attachment in email_data.get('attachments', []):
            attachment_data = attachment.get('data', b'')
            converted_attachment = {
                'filename': attachment.get('filename', 'attachment'),
                'attachment_object': AttachmentObject(attachment_data)
            }
            converted_attachments.append(converted_attachment)

        return {
            'subject': email_data.get('subject', ''),
            'date': email_data.get('date', ''),
            'sender': email_data.get('sender', ''),
            'body': email_data.get('body', ''),
            'attachments': converted_attachments
        }
