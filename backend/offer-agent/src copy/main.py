#!/usr/bin/env python3
"""
Automated Offer Creation System - Main Orchestrator
Processes incoming email offer requests and generates offers through ERP API.
"""

import asyncio
import logging
import os
import sys
import time
import traceback
import uuid
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Add project root to path to fix imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.config.settings import get_settings
from src.config.constants import LemonsoftConstants
from src.utils.logger import setup_logging, get_audit_logger, get_logger
from src.utils.exceptions import BaseOfferAutomationError
from src.lemonsoft.api_client import LemonsoftAPIClient

# Import product matching components
from src.product_matching.ai_analyzer import AIAnalyzer
from src.product_matching.attachment_processor import AttachmentProcessor  
from src.product_matching.pdf_processor import PDFProcessor
from src.product_matching.product_matcher import ProductMatcher

# Import customer lookup logic from existing test file
from src.customer.enhanced_lookup import EnhancedCustomerLookup
from src.customer.payment_term import fetch_customer_payment_term
from src.customer.invoicing_details import fetch_customer_invoicing_details

# Import sophisticated pricing calculator
from src.pricing.calculator import PricingCalculator, LineItemPricing

# Import learning system components
from src.learning.request_logger import OfferRequestLogger

# Import product matching components
from src.product_matching.matcher_class import ProductMatch

from src.email_processing.gmail_service_account_processor import GmailServiceAccountProcessor
from src.notifications.gmail_service_account_sender import GmailServiceAccountSender
from src.email_processing.LLM_services.email_classifier import EmailClassifier, EmailAction

def _parse_quantity_from_string(quantity_str: str) -> int:
    """
    Extract numeric quantity from a string that might contain units.
    
    Examples:
        "25" -> 25
        "100 metriä" -> 100
        "2 kpl" -> 2
        "15.5" -> 15 (rounded down)
    
    Args:
        quantity_str: String containing quantity and possibly units
        
    Returns:
        int: Extracted quantity, defaulting to 1 if parsing fails
    """
    if isinstance(quantity_str, int):
        return quantity_str
    
    if isinstance(quantity_str, float):
        return int(quantity_str)
    
    if not isinstance(quantity_str, str):
        return 1
    
    # Extract first number from the string using regex
    match = re.search(r'(\d+(?:\.\d+)?)', quantity_str.strip())
    if match:
        try:
            return int(float(match.group(1)))
        except (ValueError, TypeError):
            pass
    
    # Fallback to 1 if no number found
    return 1

class OfferAutomationOrchestrator:
    """
    Main orchestrator for the complete offer automation workflow.
    
    Workflow:
    1. Receive email notification
    2. Parse email content and attachments
    3. Extract company name using AI
    4. Identify customer using enhanced lookup
    5. Match products with pricing using existing logic
    6. Create offer in Lemonsoft
    7. Send notifications
    """
    
    def _retry_llm_request(self, request_func, *args, **kwargs):
        """Wrapper to retry LLM requests with appropriate wait times based on error type.
        
        - 503 errors: immediate retry (up to 3 times)
        - Rate limit errors (429): wait 10 seconds before retry
        - Other errors: exponential backoff
        """
        max_retries = 5
        base_wait = 1  # Base wait time in seconds
        
        for attempt in range(max_retries):
            try:
                # Call the wrapped function
                return request_func(*args, **kwargs)
                
            except Exception as e:
                error_str = str(e).lower()
                self.logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Check if it's the last attempt
                if attempt == max_retries - 1:
                    self.logger.error(f"LLM request failed after {max_retries} attempts")
                    raise
                
                # Determine wait time based on error type
                wait_time = base_wait
                
                if "503" in error_str or "service unavailable" in error_str:
                    # 503 errors: immediate retry (very short wait)
                    wait_time = 1
                    self.logger.info(f"503 error detected, retrying immediately (wait {wait_time}s)")
                    
                elif "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                    # Rate limit errors: wait 10 seconds
                    wait_time = 10
                    self.logger.info(f"Rate limit error detected, waiting {wait_time} seconds before retry")
                    
                elif "500" in error_str or "internal" in error_str:
                    # Internal server errors: exponential backoff
                    wait_time = base_wait * (2 ** attempt)
                    self.logger.info(f"Server error detected, waiting {wait_time} seconds (exponential backoff)")
                    
                else:
                    # Other errors: exponential backoff
                    wait_time = base_wait * (2 ** attempt)
                    self.logger.info(f"Unknown error, waiting {wait_time} seconds (exponential backoff)")
                
                # Wait before retrying
                time.sleep(wait_time)
        
        # This should never be reached due to the raise in the last attempt
        raise Exception(f"Failed to complete LLM request after {max_retries} attempts")
    
    def __init__(self):
        """Initialize the offer automation orchestrator."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Initialize core components
        self.lemonsoft_client = LemonsoftAPIClient()
        self.customer_lookup = EnhancedCustomerLookup()
        self.pricing_calculator = PricingCalculator()
        self.request_logger = OfferRequestLogger()
        
        # Initialize email processing components (Service Account)
        self.gmail_processor = GmailServiceAccountProcessor()
        self.gmail_sender = GmailServiceAccountSender()
        
        # Initialize OAuth2 components on startup
        self._init_oauth_components()
        
        # Initialize email processing components (from /emails directory)
        self.ai_analyzer = None
        self.attachment_processor = None 
        self.pdf_processor = None
        self.product_matcher = None
        self.email_classifier = None
        
        try:
            self.logger.info("Initializing email processing components...")
            self.ai_analyzer = AIAnalyzer()
            self.logger.info("AIAnalyzer initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AIAnalyzer: {e}")
            
        try:
            self.attachment_processor = AttachmentProcessor()
            self.logger.info("AttachmentProcessor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AttachmentProcessor: {e}")
            
        try:
            self.pdf_processor = PDFProcessor()
            self.logger.info("PDFProcessor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize PDFProcessor: {e}")
            
        try:
            self.product_matcher = ProductMatcher()
            self.logger.info("ProductMatcher initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize ProductMatcher: {e}")
            self.logger.error(f"ProductMatcher error details: {type(e).__name__}: {str(e)}")
            
        try:
            # Initialize EmailClassifier with existing AI analyzer's Gemini client
            if self.ai_analyzer and hasattr(self.ai_analyzer, 'gemini_client'):
                self.email_classifier = EmailClassifier(gemini_client=self.ai_analyzer.gemini_client)
            else:
                self.email_classifier = EmailClassifier()
            self.logger.info("EmailClassifier initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize EmailClassifier: {e}")
            
        # Count successfully initialized components
        components_initialized = sum([
            self.ai_analyzer is not None,
            self.attachment_processor is not None,
            self.pdf_processor is not None,
            self.product_matcher is not None,
            self.email_classifier is not None
        ])
        
        self.logger.info(f"Email processing components: {components_initialized}/5 initialized successfully")
    
    async def initialize(self):
        """
        Async initialization method for components that require it.
        Called after constructor to complete setup.
        """
        initialization_results = {
            'gmail_processor': False,
            'gmail_sender': False,
            'pricing_calculator': False,
            'lemonsoft_api': False
        }
        
        self.logger.info("Performing async initialization...")
        
        # Initialize OAuth2 components
        try:
            if hasattr(self.gmail_processor, 'initialize'):
                await self.gmail_processor.initialize()
                initialization_results['gmail_processor'] = True
                self.logger.info("✅ Gmail processor initialized")
        except Exception as e:
            self.logger.error(f"❌ Gmail processor initialization failed: {e}")
        
        try:
            if hasattr(self.gmail_sender, 'initialize'):
                await self.gmail_sender.initialize()
                initialization_results['gmail_sender'] = True
                self.logger.info("✅ Gmail sender initialized")
        except Exception as e:
            self.logger.error(f"❌ Gmail sender initialization failed: {e}")
        
        # Initialize pricing calculator (may fail if Lemonsoft API unavailable)
        try:
            if hasattr(self.pricing_calculator, 'initialize'):
                await self.pricing_calculator.initialize()
                initialization_results['pricing_calculator'] = True
                initialization_results['lemonsoft_api'] = True
                self.logger.info("✅ Pricing calculator initialized")
                self.logger.info("✅ Lemonsoft API connection established")
        except Exception as e:
            self.logger.warning(f"⚠️ Pricing calculator initialization failed: {e}")
            self.logger.warning("⚠️ Service will start without Lemonsoft API - offers cannot be created until connection is restored")
            self.logger.info("💡 The service will continue to accept requests and can perform partial processing")
        
        # Log initialization summary
        successful_components = sum(initialization_results.values())
        total_components = len(initialization_results)
        
        self.logger.info(f"📊 Initialization summary: {successful_components}/{total_components} components initialized")
        
        for component, status in initialization_results.items():
            status_icon = "✅" if status else "❌"
            self.logger.info(f"   {status_icon} {component}: {'OK' if status else 'FAILED'}")
        
        if successful_components >= 2:  # Need at least Gmail components to function
            self.logger.info("✅ Minimum components initialized - service ready")
        else:
            self.logger.warning("⚠️ Critical components failed - service functionality limited")
        
        # Store initialization status for health checks
        self._initialization_status = initialization_results
        
    async def process_email_offer_request(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a complete email offer request from start to finish.
        
        Args:
            email_data: Email data with content, attachments, etc.
        
        Returns:
            Dict with processing results and offer details
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(f"🚀 Starting offer request processing - ID: {request_id}, Subject: {email_data.get('subject', '')}, Sender: {email_data.get('sender', '')}")
        
        try:
            # Step 1: Parse email content and extract company name + delivery contact + customer reference
            company_info = await self._extract_company_information(email_data)
            delivery_contact = company_info.get('delivery_contact', 'Not available')
            customer_reference = company_info.get('customer_reference', f"AUTO{datetime.now().strftime('%m%d')}")
            
            # Step 2: Lookup customer in Lemonsoft (with retry mechanism)
            customer_info = await self._lookup_customer(company_info, email_data)
            
            # Step 2.5: Lookup salesperson by email (SMARTER METHOD - use email sender)
            sender_email, sender_name = self._parse_email_sender(email_data.get('sender', ''))
            salesperson_info = await self._lookup_salesperson_by_email(sender_email)
            
            if salesperson_info:
                self.logger.info(f"✅ Using salesperson from email sender: {salesperson_info.get('name')} (number: {salesperson_info.get('number')})")
                # Override customer's person_responsible_number with the email sender's number
                customer_info['person_responsible_number'] = salesperson_info.get('number')
                customer_info['person_responsible_name'] = salesperson_info.get('name')
                customer_info['person_responsible_source'] = 'email_sender_lookup'
            else:
                self.logger.info(f"ℹ️ No salesperson found for email {sender_email}, using customer's assigned person (fallback)")
                customer_info['person_responsible_source'] = 'customer_default'
            
            # Step 3: Process attachments for product data
            excel_data, pdf_data = await self._process_email_attachments(email_data)
            
            # Step 4: Extract and match products using AI
            matched_products = await self._extract_and_match_products(email_data, excel_data, pdf_data)
            
            # Step 5: Create offer in Lemonsoft (if API available)
            if getattr(self, '_initialization_status', {}).get('lemonsoft_api', False):
                offer_details, offer_pricing = await self._create_lemonsoft_offer(customer_info, matched_products, email_data, delivery_contact, customer_reference)
            else:
                self.logger.warning("⚠️ Lemonsoft API not available - cannot create offer")
                # Create mock offer details for notification
                offer_details = {
                    'offer_number': 'PENDING_API_CONNECTION',
                    'customer_id': customer_info.get('id'),
                    'products_count': len(matched_products),
                    'status': 'pending_api_connection',
                    'created_at': datetime.now().isoformat(),
                    'error': 'Lemonsoft API not available during service startup'
                }
                # Create mock pricing from products
                from src.pricing.calculator import OfferPricing, LineItemPricing
                line_items = []
                for i, product in enumerate(matched_products):
                    line_item = LineItemPricing(
                        product_code=product.product_code,
                        quantity=product.quantity_requested,
                        list_price=getattr(product, 'price', 0.0),
                        unit_price=getattr(product, 'price', 0.0),
                        net_price=getattr(product, 'price', 0.0),
                        discount_percent=0.0,
                        discount_amount=0.0,
                        line_total=getattr(product, 'price', 0.0) * product.quantity_requested,
                        vat_rate=25.5,
                        vat_amount=getattr(product, 'price', 0.0) * product.quantity_requested * 0.255,
                        applied_rules=[]
                    )
                    line_items.append(line_item)
                
                total_net = sum(item.line_total for item in line_items)
                total_vat = sum(item.vat_amount for item in line_items)
                
                offer_pricing = OfferPricing(
                    line_items=line_items,
                    net_total=total_net,
                    vat_amount=total_vat,
                    total_amount=total_net + total_vat,
                    total_discount_percent=0.0,
                    currency='EUR'
                )
            
            # Step 6: Send notifications
            await self._send_offer_notifications(offer_details, email_data, customer_info, matched_products, offer_pricing)
            
            # Audit log successful completion
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.audit_logger.info(f"Offer request completed successfully - ID: {request_id}, Customer: {customer_info.get('id')}, Offer: {offer_details.get('offer_number')}, Products: {len(matched_products)}, Time: {processing_time:.2f}s")
            
            return {
                'success': True,
                'request_id': request_id,
                'customer_info': customer_info,
                'offer_details': offer_details,
                'products_matched': len(matched_products),
                'processing_time_seconds': processing_time
            }
            
        except BaseOfferAutomationError as e:
            # Check if this is an insufficient rows error
            if hasattr(e, 'context') and e.context and e.context.get('insufficient_rows'):
                self.logger.error(f"Insufficient rows error for request {request_id}: {e}")
                
                # Send error notification email instead of success notification
                try:
                    await self._send_error_notification(
                        error_details={
                            'error_type': 'InsufficientRowsError',
                            'error_message': str(e),
                            'context': e.context,
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        email_data=email_data,
                        customer_info=customer_info if 'customer_info' in locals() else None
                    )
                except Exception as email_error:
                    self.logger.error(f"Failed to send error notification email: {email_error}")
                
                # Audit log the insufficient rows error
                self.audit_logger.log_error(request_id, 'InsufficientRowsError', str(e), {
                    'insufficient_rows': True,
                    'error_details': e.context.get('error_details', {}),
                    'traceback': traceback.format_exc()
                })
                
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': str(e),
                    'error_type': 'InsufficientRowsError',
                    'error_notification_sent': True
                }
            else:
                # Regular BaseOfferAutomationError handling
                self.audit_logger.log_error(request_id, type(e).__name__, str(e), {
                    'traceback': traceback.format_exc()
                })
                
                self.logger.error(f"Failed to process offer request {request_id}: {e}", exc_info=True)
                
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                
        except Exception as e:
            # Audit log error
            self.audit_logger.log_error(request_id, type(e).__name__, str(e), {
                'traceback': traceback.format_exc()
            })
            
            self.logger.error(f"Failed to process offer request {request_id}: {e}", exc_info=True)
            
            return {
                'success': False,
                'request_id': request_id,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _parse_email_sender(self, sender: str) -> tuple[str, str]:
        """
        Parse email sender to extract clean email address and display name.
        
        Args:
            sender: Raw sender string (e.g., "John Doe" <john.doe@example.com> or john.doe@example.com)
            
        Returns:
            tuple: (email_address, display_name)
        """
        import email.utils
        
        # Use email.utils.parseaddr to properly parse the sender
        display_name, email_address = email.utils.parseaddr(sender)
        
        # Clean up display name (remove quotes and extra whitespace)
        display_name = display_name.strip(' "\'')
        email_address = email_address.strip(' <>')
        
        return email_address, display_name
    
    async def _extract_company_information(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract company name and delivery contact from email using AI in a single call."""
        body = email_data.get('body', '')
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        attachments = email_data.get('attachments', [])
        
        # Parse sender to get clean email address and display name
        sender_email, sender_name = self._parse_email_sender(sender)
        self.logger.debug(f"Parsed sender: email={sender_email}, name={sender_name}")
        
        self.logger.info("Extracting company information and delivery contact from email")
        self.logger.debug(f"📧 Email details for analysis:")
        self.logger.debug(f"   Sender: {sender}")
        self.logger.debug(f"   Subject: {subject}")
        self.logger.debug(f"   Body length: {len(body)} characters")
        self.logger.debug(f"   Attachments: {len(attachments)} files")
        
        if attachments:
            for i, att in enumerate(attachments):
                self.logger.debug(f"     Attachment {i}: {att.get('filename', 'unnamed')} ({att.get('size', 0)} bytes, {att.get('mime_type', 'unknown')})")
        
        if len(body) > 100:
            preview = body[:500].replace('\n', ' ').replace('\r', ' ')
            self.logger.debug(f"   Body preview: {preview}...")
        else:
            self.logger.debug(f"   Full body: {body}")
        
        if self.ai_analyzer is None:
            self.logger.warning("AI Analyzer not available, using fallback extraction")
            # Fallback: extract company from email domain - NEVER use sender as delivery contact
            company_name = 'null'
            delivery_contact = 'Not available'  # Default to customer service
            
            if '@' in sender_email:
                domain = sender_email.split('@')[1]
                company_name = domain.split('.')[0].replace('-', ' ').title()

                if company_name.lower() in ['gmail', 'outlook', 'yahoo', 'hotmail']:
                    company_name = 'null'
            
            return {
                'company_name': company_name,
                'delivery_contact': delivery_contact,  # Always default, never sender
                'confidence': 0.5,
                'source': 'email_domain_fallback'
            }
        
        # Use AI to extract both company and delivery contact in one call
        # Pass the parsed sender_email and sender_name separately for better context
        combined_info = await self._extract_company_and_contact_with_ai(
            body, sender_email, sender_name, subject
        )
        
        self.logger.info(f"Extracted company: {combined_info.get('company_name', 'Not found')}")
        self.logger.info(f"Extracted delivery contact: {combined_info.get('delivery_contact', 'Not found')}")
        self.logger.info(f"Extracted customer reference: {combined_info.get('customer_reference', 'Not found')}")
        
        return combined_info
    
    async def _retry_company_extraction_with_ai(self, body: str, sender_email: str, subject: str,
                                               failed_company_name: str) -> Dict[str, Any]:
        """
        Retry extracting company name with LLM after initial extraction failed.
        Provides context about the failed attempt to help find the correct company.

        Args:
            body: Email body text
            sender_email: Sender email address (clean, without display name)
            subject: Email subject
            failed_company_name: The company name that was not found in database

        Returns:
            Dict with retry_company_name and should_retry flag
        """
        try:
            from google.genai import types

            prompt = f"""You previously extracted '{failed_company_name}' as the customer company name, but this was NOT found in our database.

PLEASE TRY AGAIN to find the REAL customer company name from this email.

EMAIL FROM: {sender_email}
SUBJECT: {subject}

EMAIL CONTENT:
{body}

IMPORTANT CONTEXT:
- The company name '{failed_company_name}' does NOT exist in our database
- You must find a DIFFERENT company name if possible
- Look carefully in:
  * Email signatures (especially at the end of the email)
  * Company domains in email addresses
  * References to "asiakkaalle" (to customer) or "tilaaja" (orderer)
  * Any other company names mentioned that are NOT Metec, LVI-WaBeK, ClimaPri, or Wcom Group
  * Sometimes the real company name is abbreviated or written differently

CRITICAL RULES:
- NEVER return "Metec", "LVI-WaBeK", "ClimaPri", "Wcom Group" - these are OUR companies
- Must return a DIFFERENT name than '{failed_company_name}'
- If you cannot find any other valid company name, set should_retry to false

RESPONSE FORMAT (JSON only):
{{
  "should_retry": true/false,
  "retry_company_name": "Different Company Name Oy",
  "confidence": 0.0-1.0,
  "reason": "Brief explanation of why this might be the correct company"
}}

Only return JSON, no other text."""

            # Use retry wrapper for LLM request
            def make_request():
                import google.generativeai as genai
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(
                    prompt,
                    generation_config=types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=500,
                        response_mime_type="application/json"
                    )
                )
                return response

            response = self._retry_llm_request(make_request)

            if response and response.text:
                import json
                retry_info = json.loads(response.text)

                self.logger.info(f"Company extraction retry result: {retry_info}")

                return {
                    'should_retry': retry_info.get('should_retry', False),
                    'company_name': retry_info.get('retry_company_name', ''),
                    'confidence': retry_info.get('confidence', 0.0),
                    'reason': retry_info.get('reason', ''),
                    'source': 'ai_extraction_retry'
                }

        except Exception as e:
            self.logger.error(f"Failed to retry company extraction with AI: {e}")

        return {
            'should_retry': False,
            'company_name': '',
            'confidence': 0.0,
            'source': 'ai_extraction_retry_failed'
        }

    async def _extract_company_and_contact_with_ai(self, body: str, sender_email: str, sender_name: str, subject: str) -> Dict[str, Any]:
        """
        Use AI to extract both company name and delivery contact from email in a single call.

        Args:
            body: Email body text
            sender_email: Sender email address (clean, without display name)
            sender_name: Sender display name (the sales person who forwarded the email)
            subject: Email subject

        Returns:
            Dict with company_name, delivery_contact, and metadata
        """
        try:
            from google.genai import types
            
            prompt = f"""Extract company name, delivery contact person, and customer reference from this email content.

SALES PERSON WHO FORWARDED THIS EMAIL:
Name: {sender_name}
Email: {sender_email}

EMAIL SUBJECT: {subject}

EMAIL CONTENT:
{body}

CRITICAL RULES - NEVER VIOLATE THESE:
- NEVER return "LVI-WaBeK", "LVI WaBeK", "LVI-WABEK", "Lvi Wabek" or ANY variation as the customer company
- NEVER return "Metec", "Wcom Group", "Wcom-Group", "ClimaPri" or any variation as the customer company
- These are OUR OWN companies who CREATE offers, not customers who receive them
- LVI-WaBeK is THE COMPANY RUNNING THIS SYSTEM - it can NEVER be the customer
- If the email is FROM someone @lvi-wabek.fi, they are asking for an offer for THEIR customer, not for LVI-WaBeK
- If you only see these company names, look harder for the actual customer company name
- The customer is the company RECEIVING the offer, not sending this email

INSTRUCTIONS:
1. COMPANY NAME: Look for the CUSTOMER's company name (the one receiving the offer)
   - Often locates in the email signature, greeting, or content (f.ex. "Ystävällisin terveisin, / Jarkko Suominen/ Yritys Oy" in the end of the customer's email)
   - This is NOT Metec, ClimaPri, LVI-WaBeK, or Wcom Group (these are our companies)
   - This is NOT Gmail, Outlook, or other email providers
   - Look in email body for mentions like "asiakkaalle" (to customer), "tilaaja" (orderer), or company names in forwarded content
   - Check if the salesperson mentions who the offer is for

2. CUSTOMER NUMBER: This is rare, but sometimes the sales person (works at LVI-WaBeK or Metec) who is forwarding this message, has included customer number. If this is mentioned clearly, include it in the response.

3. DELIVERY CONTACT - EXTREMELY IMPORTANT:
   - NEVER EVER return "{sender_name}" as the delivery contact - THIS IS THE SALES PERSON, NOT THE CUSTOMER
   - NEVER use the email address "{sender_email}" to extract a name
   - Look for customer's contact person names ONLY in:
     * Email signatures FROM THE CUSTOMER (not from the sales person)
     * Customer's quoted/forwarded messages
     * Explicit mentions like "contact person: John Doe" or "yhteyshenkilö: Matti Virtanen"
   - Do NOT use names of people who work at Metec, ClimaPri, LVI-WaBeK, or Wcom Group
   - If you CANNOT find a clear customer contact person, return "Not available" - DO NOT GUESS
   - It's BETTER to return "Not available" than to incorrectly use the sales person's name

4. CUSTOMER REFERENCE: Look for project names, project numbers, or specific references the customer mentions for their project
5. Return only the full name (first and last name) of the person who should be contacted for delivery
6. Prefer names mentioned as contact person, sender, or in signature FROM THE CUSTOMER company
7. For company name, consider Finnish business suffixes (Oy, Ab, Ltd, etc.)
8. For customer reference: If no specific project reference found, generate a short descriptive reference (max 14 chars) based on email subject or content

RESPONSE FORMAT (JSON only):
{{
  "company_name": "Customer Company Oy",
  "customer_number": "218772",
  "delivery_contact": "John Doe",
  "customer_reference": "PROJ2024-01",
  "company_confidence": 0.85,
  "contact_confidence": 0.80,
  "reference_confidence": 0.75,
  "company_source": "email_signature",
  "contact_source": "email_signature",
  "reference_source": "email_subject",
  "email_domain": "company.fi"
}}

If company name not clearly found, extract from email domain. If extracting name from domain, notice that in finnish some letters are ä or ö instead if a and o. 

IMPORTANT: If the extracted company name is "Metec", "ClimaPri", "LVI-WaBeK", "Wcom Group" or similar, these are NOT customers - look for the actual customer company name or use "null" instead.

If no clear contact name found, use "Not available". If no specific reference found, generate a short one like "VESIMITTARIT" based on company/subject.

If no clear customer number found, use "null".
"""

            # Get the gemini model from the AIAnalyzer's config
            try:
                from product_matching.config import Config
                gemini_model = Config.GEMINI_MODEL
            except ImportError:
                gemini_model = "gemini-2.5-flash"  # fallback

            config = types.GenerateContentConfig(
                temperature=0.1,
                candidate_count=1,
            )

            response = self._retry_llm_request(
                self.ai_analyzer.gemini_client.models.generate_content,
                model=gemini_model,
                contents=prompt,
                config=config,
            )

            # Extract response text using the same method as AIAnalyzer
            response_text = None
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            part = candidate.content.parts[0]
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text.strip()
                except Exception as e:
                    self.logger.warning(f"Error extracting text from candidates: {e}")

            if not response_text:
                self.logger.warning("No response from AI for combined extraction")
                return self._fallback_combined_extraction(sender_email)
            
            # Parse JSON response
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            import json
            result = json.loads(json_text)
            
            # Validate and clean up the results - handle None values
            company_name = (result.get('company_name') or '').strip()
            delivery_contact = (result.get('delivery_contact') or '').strip()
            customer_reference = (result.get('customer_reference') or '').strip()
            customer_number = (result.get('customer_number') or '').strip()
            
            # CRITICAL: Check if AI incorrectly identified our own company as customer
            our_companies = ['metec', 'lvi-wabek', 'lvi wabek', 'wcom group', 'wcom-group', 'lviwabek', 'wcom', 'climapri', 'clima-pri']
            # More robust check - also check exact matches and variations
            company_lower = company_name.lower().replace('-', '').replace(' ', '').replace('_', '')
            if any(own_company.replace('-', '').replace(' ', '').replace('_', '') in company_lower for own_company in our_companies):
                self.logger.warning(f"AI incorrectly identified our own company '{company_name}' as customer - resetting to Unknown Customer")
                company_name = 'Unknown Customer'
                # Also reset confidence since we know this is wrong
                result['company_confidence'] = 0.1
                result['company_source'] = 'fallback_own_company_filtered'
            
            if not company_name:
                # Fallback to domain extraction from sender_email
                if '@' in sender_email:
                    domain = sender_email.split('@')[1]
                    company_name = domain.split('.')[0].replace('-', ' ').title()
                else:
                    company_name = 'Unknown Company'
            
            # CRITICAL: Never use sender as delivery contact - sender is the sales person, not the customer
            # If AI didn't find a delivery contact, it's better to use default than to use sales person's name
            if not delivery_contact:
                delivery_contact = 'Not available'
            
            # Additional validation: Check if delivery contact matches sender name (sales person)
            # This provides extra protection against AI mistakes
            if delivery_contact and sender_name:
                # Normalize both names for comparison (lowercase, remove extra spaces)
                contact_normalized = delivery_contact.lower().strip()
                sender_normalized = sender_name.lower().strip()
                
                # Check for exact match or if one contains the other
                if contact_normalized == sender_normalized or \
                   (len(contact_normalized) > 5 and contact_normalized in sender_normalized) or \
                   (len(sender_normalized) > 5 and sender_normalized in contact_normalized):
                    self.logger.warning(
                        f"AI extracted delivery contact '{delivery_contact}' matches sender name '{sender_name}' - "
                        f"resetting to default 'Not available'"
                    )
                    delivery_contact = 'Not available'
            
            if not customer_reference:
                # Generate fallback reference from subject or company
                if subject and len(subject) > 0:
                    # Create reference from subject (first 10 chars + year)
                    subject_clean = ''.join(c for c in subject[:10] if c.isalnum())
                    customer_reference = f"{subject_clean}{datetime.now().year}"[:14]
                else:
                    # Create reference from company name + year
                    company_clean = ''.join(c for c in company_name[:8] if c.isalnum())
                    customer_reference = f"{company_clean}{datetime.now().year}"[:14]
            
            # Ensure reference doesn't exceed 14 characters
            customer_reference = customer_reference[:14]
            
            return {
                'company_name': company_name,
                'customer_number': customer_number,
                'delivery_contact': delivery_contact,
                'customer_reference': customer_reference,
                'company_confidence': result.get('company_confidence', 0.8),
                'contact_confidence': result.get('contact_confidence', 0.8),
                'reference_confidence': result.get('reference_confidence', 0.8),
                'company_source': result.get('company_source', 'ai_extraction'),
                'contact_source': result.get('contact_source', 'ai_extraction'),
                'reference_source': result.get('reference_source', 'ai_extraction'),
                'email_domain': result.get('email_domain', sender_email.split('@')[1] if '@' in sender_email else ''),
                'source': 'ai_combined_extraction'
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI combined extraction: {e}")
            return self._fallback_combined_extraction(sender_email)
    
    def _fallback_combined_extraction(self, sender_email: str) -> Dict[str, Any]:
        """
        Fallback extraction when AI fails.
        
        Args:
            sender_email: Clean email address (not display name format)
            
        Returns:
            Dict with extracted information
        """
        company_name = 'Unknown Company'
        delivery_contact = 'Not available'  # NEVER use sender as delivery contact
        customer_reference = f"AUTO{datetime.now().strftime('%m%d')}"  # AUTO + month/day
        
        if '@' in sender_email:
            domain = sender_email.split('@')[1]
            company_name = domain.split('.')[0].replace('-', ' ').title()
            # Generate reference from domain
            domain_clean = ''.join(c for c in domain.split('.')[0][:8] if c.isalnum())
            customer_reference = f"{domain_clean}{datetime.now().year}"[:14]
        
        return {
            'company_name': company_name,
            'delivery_contact': delivery_contact,  # Always default, never sender
            'customer_reference': customer_reference,
            'company_confidence': 0.5,
            'contact_confidence': 0.5,
            'reference_confidence': 0.5,
            'company_source': 'domain_fallback',
            'contact_source': 'default_fallback',  # Changed from 'sender_fallback'
            'reference_source': 'fallback_generated',
            'email_domain': sender_email.split('@')[1] if '@' in sender_email else '',
            'source': 'fallback_extraction'
        }
    
    async def _lookup_salesperson_by_email(self, email_address: str) -> Optional[Dict[str, Any]]:
        """
        Lookup salesperson by email address using Lemonsoft persons API.
        
        Args:
            email_address: Email address to search for
            
        Returns:
            Dict with person data including 'number' field, or None if not found
        """
        try:
            self.logger.info(f"🔍 Looking up salesperson by email: {email_address}")
            email_address = email_address.split('@')[0]
            
            async with self.lemonsoft_client as client:
                await client.ensure_ready()
                
                # Search for person using filter.search parameter
                params = {'filter.search': email_address}
                response = await client.get('/api/persons', params=params)
                
                if response.status_code != 200:
                    self.logger.warning(f"Person search API returned status {response.status_code}")
                    return None
                
                data = response.json()
                
                # Debug: Log the raw response to understand the format
                self.logger.info(f"🔍 DEBUG - /api/persons raw response type: {type(data)}")
                if data is None:
                    self.logger.warning("⚠️ API returned None for persons search")
                    return None
                
                # Handle response format - could be list or dict
                persons = []
                if isinstance(data, list):
                    persons = data
                elif isinstance(data, dict):
                    self.logger.info(f"🔍 DEBUG - Response dict keys: {list(data.keys())}")
                    
                    # Check for errors in response
                    if data.get('has_errors'):
                        errors = data.get('errors', [])
                        self.logger.warning(f"⚠️ API returned errors: {errors}")
                    
                    # Get results and log what we found
                    results = data.get('results')
                    
                    if results is None:
                        # Try alternative keys
                        results = data.get('data', data.get('persons', []))
                        self.logger.info(f"🔍 DEBUG - Tried alternative keys, got: {results}")
                    
                    persons = results if results is not None else []
                else:
                    self.logger.warning(f"⚠️ Unexpected response type: {type(data)}")
                    return None
                
                # Ensure persons is a list
                if not isinstance(persons, list):
                    self.logger.warning(f"⚠️ Persons is not a list (type: {type(persons)}), converting to list")
                    persons = [] if persons is None else [persons]
                
                self.logger.info(f"Found {len(persons)} person(s) matching email search")
                

                
                # Find exact email match
                for person in persons:
                    person_email = person.get('email', '').lower().strip()
                    if person_email == email_address.lower().strip():
                        person_number = person.get('number')
                        person_name = person.get('name', 'Unknown')
                        self.logger.info(f"✅ Found exact match: {person_name} (number: {person_number}, email: {person_email})")
                        return {
                            'number': person_number,
                            'name': person_name,
                            'email': person_email,
                            'source': 'email_lookup'
                        }
                
                # If no exact match but we have results, use the first one
                if persons:
                    person = persons[0]
                    person_number = person.get('number')
                    person_name = person.get('name', 'Unknown')
                    person_email = person.get('email', '')
                    self.logger.info(f"⚠️ No exact match, using first result: {person_name} (number: {person_number}, email: {person_email})")
                    return {
                        'number': person_number,
                        'name': person_name,
                        'email': person_email,
                        'source': 'email_lookup_partial'
                    }
                
                self.logger.warning(f"No person found with email: {email_address}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error looking up salesperson by email: {e}", exc_info=True)
            return None
    
    async def _lookup_customer(self, company_info: Dict[str, Any], email_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Lookup customer in Lemonsoft using enhanced search with retry mechanism."""
        company_name = company_info.get('company_name', '')
        customer_number = company_info.get('customer_number', '')

        if not company_name:
            raise BaseOfferAutomationError("No company name found in email")

        self.logger.info(f"Looking up customer: {company_name}")

        # Use enhanced customer lookup with multiple strategies
        customer_result = await self.customer_lookup.find_customer(company_name, customer_number)

        if not customer_result.get('success'):
            self.logger.warning(f"Initial customer lookup failed for: {company_name}")

            # Try to extract a different company name with AI
            if email_data:
                body = email_data.get('body', '')
                sender = email_data.get('sender', '')
                subject = email_data.get('subject', '')
                
                # Parse sender to get clean email
                sender_email, sender_name = self._parse_email_sender(sender)

                self.logger.info("Attempting to re-extract company name with AI...")
                retry_info = await self._retry_company_extraction_with_ai(body, sender_email, subject, company_name)

                if retry_info.get('should_retry') and retry_info.get('company_name'):
                    retry_company_name = retry_info.get('company_name')
                    self.logger.info(f"Retrying customer lookup with: {retry_company_name} (reason: {retry_info.get('reason')})")

                    # Try lookup with the new company name
                    retry_result = await self.customer_lookup.find_customer(retry_company_name, customer_number)

                    if retry_result.get('success'):
                        customer_info = retry_result['customer_data']
                        self.logger.info(f"Found customer on retry: {customer_info.get('name')} (ID: {customer_info.get('id')})")
                        return customer_info
                    else:
                        self.logger.warning(f"Retry lookup also failed for: {retry_company_name}")
                        # Send notification email to sales person
                        await self._send_no_customer_found_notification(email_data, [company_name, retry_company_name])
                else:
                    self.logger.info("AI decided not to retry with a different company name")
                    # Send notification email to sales person
                    await self._send_no_customer_found_notification(email_data, [company_name])

            raise BaseOfferAutomationError(f"Customer not found after retry: {company_name}")

        customer_info = customer_result['customer_data']
        self.logger.info(f"Found customer: {customer_info.get('name')} (ID: {customer_info.get('id')})")

        return customer_info

    async def _send_no_customer_found_notification(self, email_data: Dict[str, Any],
                                                  attempted_names: List[str]) -> bool:
        """
        Send notification email to sales person when no customer is found.

        Args:
            email_data: Original email data
            attempted_names: List of company names that were attempted

        Returns:
            bool: True if notification sent successfully
        """
        try:
            sender_email = email_data.get('sender', '')
            subject = email_data.get('subject', 'No Subject')

            # Send notification to the original sender (sales person)
            notification_sent = await self.gmail_sender.send_no_customer_found_notification(
                recipient_email=sender_email,
                original_subject=subject,
                attempted_names=attempted_names,
                email_data=email_data
            )

            if notification_sent:
                self.logger.info(f"No customer found notification sent to: {sender_email}")
            else:
                self.logger.error(f"Failed to send no customer found notification to: {sender_email}")

            return notification_sent

        except Exception as e:
            self.logger.error(f"Error sending no customer found notification: {e}")
            return False
    
    async def _process_email_attachments(self, email_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process email attachments for product data."""
        attachments = email_data.get('attachments', [])
        
        if not attachments:
            return [], []
        
        self.logger.info(f"Processing {len(attachments)} email attachments")
        
        # Convert Gmail OAuth format to legacy attachment processor format
        converted_email = self._convert_gmail_to_legacy_format(email_data)
        email_list = [converted_email]  # Wrap in list as expected by processor
        
        # Process Excel attachments if processor is available
        excel_data = []
        if self.attachment_processor:
            try:
                excel_data = self.attachment_processor.extract_excel_content(email_list)
            except Exception as e:
                self.logger.error(f"Excel attachment processing failed: {e}")
        
        # Process PDF attachments if processor is available
        pdf_data = []
        if self.pdf_processor:
            try:
                pdf_data = self.pdf_processor.extract_pdf_content(email_list)
            except Exception as e:
                self.logger.error(f"PDF attachment processing failed: {e}")
        
        self.logger.info(f"Processed attachments: {len(excel_data)} Excel, {len(pdf_data)} PDF")
        
        return excel_data, pdf_data
    
    def _convert_gmail_to_legacy_format(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Gmail OAuth format to legacy attachment processor format."""
        
        # Create a simple attachment object that mimics Aspose.Email format
        class AttachmentObject:
            def __init__(self, data: bytes):
                self.data = data
                
            @property
            def content_stream(self):
                return self
                
            def to_array(self):
                return self.data
        
        # Convert attachments to expected format
        converted_attachments = []
        for attachment in email_data.get('attachments', []):
            attachment_data = attachment.get('data', b'')
            self.logger.info(f"🔍 Gmail attachment: {attachment.get('filename', 'unnamed')}, data size: {len(attachment_data)} bytes")
            self.logger.debug(f"🔍 Gmail attachment keys: {list(attachment.keys())}")
            
            converted_attachment = {
                'filename': attachment.get('filename', 'attachment'),
                'attachment_object': AttachmentObject(attachment_data)
            }
            converted_attachments.append(converted_attachment)
        
        # Create converted email data
        converted_email = {
            'subject': email_data.get('subject', ''),
            'date': email_data.get('date', ''),
            'sender': email_data.get('sender', ''),
            'body': email_data.get('body', ''),
            'attachments': converted_attachments
        }
        
        self.logger.debug(f"🔄 Converted {len(converted_attachments)} Gmail attachments to legacy format")
        
        return converted_email
    
    async def _extract_and_match_products(self, email_data: Dict[str, Any], excel_data: List[Dict], pdf_data: List[Dict]) -> List[ProductMatch]:
        """Extract products from email and match them using existing logic, then convert to ProductMatch objects."""
        self.logger.info("Extracting and matching products")
        
        if self.ai_analyzer is None:
            self.logger.warning("AI Analyzer not available, creating fallback product matches")
            # Create a simple fallback product
            fallback_product = ProductMatch(
                product_code='9000',
                product_name='Manual Processing Required',
                description='AI components not available - manual review needed',
                unit='KPL',
                price=0.0,
                product_group='',
                confidence_score=0.1,
                match_method='fallback_no_ai',
                quantity_requested=1,
                match_details={'reason': 'AI analyzer not initialized'}
            )
            return [fallback_product]
        
        # Convert to format expected by AI analyzer
        filtered_emails = [email_data]
        
        # Use the enhanced AI analyzer with product matching
        matched_products = []
        unclear_terms = []
        
        def on_match_found(match_dict):
            """Callback for when a product is matched."""
            matched_products.append(match_dict)
            self.logger.info(f"Matched product: {match_dict.get('matched_product_name', 'Unknown')}")
        
        def on_unclear_term_found(unclear_dict):
            """Callback for unclear terms - we'll try to match these too."""
            unclear_terms.append(unclear_dict)
            self.logger.info(f"Unclear term found: {unclear_dict.get('unclear_term', 'Unknown')}")
        
        try:
            # Analyze email content for products
            await self.ai_analyzer.identify_unclear_terms(
                filtered_emails,
                excel_data,
                pdf_data,
                on_unclear_term_found=on_unclear_term_found,
                on_match_found=on_match_found
            )
        except Exception as e:
            self.logger.error(f"Error in AI product analysis: {e}")
            # Return fallback product on error
            fallback_product = ProductMatch(
                product_code='9000',
                product_name='Product Analysis Failed',
                description=f'Error in AI analysis: {str(e)}',
                unit='KPL',
                price=0.0,
                product_group='',
                confidence_score=0.1,
                match_method='fallback_error',
                quantity_requested=1,
                match_details={'error': str(e)}
            )
            return [fallback_product]
        
        # Convert to ProductMatch objects for pricing calculator
        product_matches = []
        
        # Convert matched products
        for match_dict in matched_products:
            # Get AI confidence - check both 'ai_confidence' and 'confidence' fields
            ai_confidence = match_dict.get('ai_confidence', match_dict.get('confidence', 80))
            # Convert to 0-1 scale if it's a percentage
            confidence_score = ai_confidence / 100.0 if ai_confidence > 1 else ai_confidence
            
            product_match = ProductMatch(
                product_code=match_dict.get('matched_product_code', match_dict.get('product_code', 'UNKNOWN')),
                product_name=match_dict.get('matched_product_name', match_dict.get('product_name', '')),
                description=match_dict.get('matched_product_description', ''),
                unit=match_dict.get('unit', 'KPL'),
                price=float(match_dict.get('matched_product_price', match_dict.get('unit_price', 0.0))),
                product_group=match_dict.get('product_group', ''),
                confidence_score=confidence_score,
                match_method="ai_analyzer",
                quantity_requested=_parse_quantity_from_string(match_dict.get('quantity', 1)),
                match_details=match_dict  # This preserves ai_confidence and ai_reasoning
            )
            product_matches.append(product_match)
        
        # Convert unclear terms to ProductMatch objects with code 9000
        for unclear_term in unclear_terms:
            unclear_match = ProductMatch(
                product_code='9000',  # Code for unidentifiable products per PRD
                product_name=unclear_term.get('unclear_term', ''),
                description=unclear_term.get('explanation', ''),
                unit='KPL',
                price=0.0,  # Will be filled manually
                product_group='',
                confidence_score=0.1,  # Low confidence for unclear terms
                match_method="unclear_term",
                quantity_requested=_parse_quantity_from_string(unclear_term.get('quantity', 1)),
                match_details=unclear_term
            )
            product_matches.append(unclear_match)
        
        self.logger.info(f"Total products to add to offer: {len(product_matches)}")
        
        return product_matches
    
    async def _create_lemonsoft_offer(self, customer_info: Dict, products: List[ProductMatch], email_data: Dict, delivery_contact: str, customer_reference: str = "") -> Tuple[Dict, Any]:
        """Create offer in Lemonsoft with customer and products using sophisticated pricing."""
        self.logger.info(f"Creating Lemonsoft offer for customer ID: {customer_info.get('id')}")
        
        # Initialize pricing calculator
        await self.pricing_calculator.initialize()

        # Calculate sophisticated pricing for all products
        self.logger.info("Calculating sophisticated pricing for products")
        offer_pricing = await self.pricing_calculator.calculate_offer_pricing(
            product_matches=products,
            customer_id=str(customer_info.get('number')),
            pricing_context={
                'email_subject': email_data.get('subject', ''),
                'currency': 'EUR'
            }
        )
        
        self.logger.info(
            f"Pricing calculated: €{offer_pricing.total_amount:.2f} "
            f"(Net: €{offer_pricing.net_total:.2f}, VAT: €{offer_pricing.vat_amount:.2f})"
        )
        
        # Create minimal offer using type 6 as per PRD (POST doesn't allow data)
        minimal_offer_data = {
            "customer_id": customer_info.get('id')
        }

        # Create the offer
        async with self.lemonsoft_client as client:
            # Ensure token/session is valid before any API call
            await client.ensure_ready()

            # Fetch payment term and invoicing details for the customer
            customer_number = customer_info.get('number')
            payment_term = await fetch_customer_payment_term(client, customer_number)

            # Use fetched payment term or default to 14
            if payment_term is None:
                self.logger.warning(f"Could not fetch payment term for customer {customer_number}, using default 2 which equals net 14 days")
                payment_term = 2
            else:
                self.logger.info(f"Using payment term {payment_term} for customer {customer_number}")

            # Fetch invoicing details for offer_customer fields
            invoicing_details = await fetch_customer_invoicing_details(client, customer_number)
            self.logger.info(f"Fetched invoicing details for customer {customer_number}")
            # Step 1: Create minimal offer
            await client.ensure_ready()
            offer_response = await client.post('/api/offers/6', json=minimal_offer_data)
            
            if offer_response.status_code not in [200, 201]:
                raise BaseOfferAutomationError(f"Failed to create offer: {offer_response.status_code}")
            
            offer_result = offer_response.json()
            offer_number = offer_result.get('offer_number') or offer_result.get('number')
            offer_id = offer_result.get('offer_id') or offer_result.get('id')
            
            self.logger.info(f"Created minimal offer: {offer_number} (ID: {offer_id})")
            
            # Step 2: Get the created offer to update it
            await client.ensure_ready()
            get_response = await client.get(f'/api/offers/{offer_number}')
            if get_response.status_code != 200:
                raise BaseOfferAutomationError(f"Failed to retrieve created offer: {get_response.status_code}")
            
            complete_offer = get_response.json()
            
            # Step 3: Prepare complete offer data with all fields (delivery_contact and customer_reference already extracted)
            # Check if customer denies credit to set appropriate delivery method
            deny_credit = customer_info.get('deny_credit', False)
            delivery_method = 33 if deny_credit else 6
            
            if deny_credit:
                self.logger.info(f"Customer {customer_info.get('name')} denies credit - using delivery method 33")
            else:
                self.logger.info(f"Customer {customer_info.get('name')} allows credit - using delivery method 6")
            
            # Debug salesperson field
            person_responsible = customer_info.get('person_responsible_number')
            person_responsible_name = customer_info.get('person_responsible_name', 'Unknown')
            person_responsible_source = customer_info.get('person_responsible_source', 'unknown')
            
            self.logger.info(f"🔍 DEBUG - Salesperson Info:")
            self.logger.info(f"   Number: {person_responsible} (type: {type(person_responsible)})")
            self.logger.info(f"   Name: {person_responsible_name}")
            self.logger.info(f"   Source: {person_responsible_source}")
            
            if person_responsible:
                if person_responsible_source == 'email_sender_lookup':
                    self.logger.info(f"✅ Will use salesperson from EMAIL SENDER: {person_responsible_name} (number: {person_responsible})")
                elif person_responsible_source == 'customer_default':
                    self.logger.info(f"✅ Will use salesperson from CUSTOMER DEFAULT: (number: {person_responsible})")
                else:
                    self.logger.info(f"✅ Will use salesperson: (number: {person_responsible})")
                self.logger.info(f"   Fields to be set: person_invoice_res_person={person_responsible}, person_seller_number={person_responsible}")
            else:
                self.logger.warning(f"⚠️ No person_responsible_number found - salesperson fields will NOT be added to offer")
            
            complete_offer.update({
                "offer_date": datetime.now().isoformat(),
                "offer_valid_date": (datetime.now().replace(day=min(datetime.now().day + 30, 28))).isoformat(),
                "offer_our_reference": f"AUTO-{datetime.now().strftime('%Y%m%d%H%M')}",
                "offer_customer_reference": customer_reference,
                "offer_note": f"Automated offer from email",
                "offer_delivery_term": "",
                "offer_type": 6,
                "company_location_id": 1,
                "language_code": "FIN",
                "payment_term": payment_term,
                "delivery_method": delivery_method,
                "offer_delivery_code": "",
                "offer_delivery_term": 1,
                "Sales_phase_collection": 1,
                "Offer_current_sales_phase": 1,
                # Only set person fields if they have valid values
                **({"person_invoice_res_person": customer_info.get('person_responsible_number')} if customer_info.get('person_responsible_number') else {}),
                **({"person_seller_number": customer_info.get('person_responsible_number')} if customer_info.get('person_responsible_number') else {}),
                # Customer details - use fetched invoicing details
                "offer_customer_number": invoicing_details.get('offer_customer_number', customer_info.get('number')),
                "offer_customer_name1": invoicing_details.get('offer_customer_name1', customer_info.get('name', '')),
                "offer_customer_name2": invoicing_details.get('offer_customer_name2', ''),
                "offer_customer_address1": invoicing_details.get('offer_customer_address1', customer_info.get('street', '')),
                "offer_customer_address2": invoicing_details.get('offer_customer_address2', ''),
                "offer_customer_address3": invoicing_details.get('offer_customer_address3', f"{customer_info.get('postal_code', '')} {customer_info.get('city', '')}".strip()),
                "offer_customer_contact": customer_info.get('ceo_contact', ''),
                # Delivery customer details
                "delivery_customer_number": str(customer_info.get('number', '')),
                "delivery_customer_name1": customer_info.get('name', ''),
                "delivery_customer_address1": customer_info.get('street', ''),
                "delivery_customer_address2": "",
                "delivery_customer_address3": f"{customer_info.get('postal_code', '')} {customer_info.get('city', '')}".strip(),
                "offer_customer_country": "FINLAND",
                "delivery_customer_contact": delivery_contact,
            })
            
            # Step 4: Update the offer with complete data
            await client.ensure_ready()
            
            # Debug: Log what we're sending to the API
            self.logger.info(f"🔍 DEBUG - Sending offer update with fields:")
            if 'person_invoice_res_person' in complete_offer:
                self.logger.info(f"   ✅ person_invoice_res_person: {complete_offer['person_invoice_res_person']}")
            else:
                self.logger.warning(f"   ❌ person_invoice_res_person: NOT IN REQUEST")
            if 'person_seller_number' in complete_offer:
                self.logger.info(f"   ✅ person_seller_number: {complete_offer['person_seller_number']}")
            else:
                self.logger.warning(f"   ❌ person_seller_number: NOT IN REQUEST")
            
            update_response = await client.put('/api/offers', json=complete_offer)
            if update_response.status_code not in [200, 201, 204]:
                self.logger.warning(f"Failed to update offer with complete data: {update_response.status_code}")
                # Log the error but continue
                try:
                    error_data = update_response.json()
                    self.logger.warning(f"Update error response: {error_data}")
                except:
                    self.logger.warning(f"Update error response text: {update_response.text}")
            else:
                self.logger.info(f"✅ Updated offer {offer_number} with complete data including payment terms")
                if customer_info.get('ceo_contact'):
                    self.logger.info(f"CEO contact: {customer_info.get('ceo_contact')}")
                if delivery_contact:
                    self.logger.info(f"Delivery contact: {delivery_contact}")
                
                # Debug: Verify what came back from the API
                try:
                    await client.ensure_ready()
                    verify_response = await client.get(f'/api/offers/{offer_number}')
                    if verify_response.status_code == 200:
                        updated_offer_data = verify_response.json()
                        self.logger.info(f"🔍 DEBUG - Verifying updated offer from API:")
                        if 'person_invoice_res_person' in updated_offer_data:
                            self.logger.info(f"   ✅ person_invoice_res_person in API response: {updated_offer_data['person_invoice_res_person']}")
                        else:
                            self.logger.warning(f"   ❌ person_invoice_res_person: NOT IN API RESPONSE")
                        if 'person_seller_number' in updated_offer_data:
                            self.logger.info(f"   ✅ person_seller_number in API response: {updated_offer_data['person_seller_number']}")
                        else:
                            self.logger.warning(f"   ❌ person_seller_number: NOT IN API RESPONSE")
                except Exception as verify_error:
                    self.logger.warning(f"Could not verify updated offer: {verify_error}")
            
            # Step 5: Add product rows to the offer with sophisticated pricing
            # First, check if the offer already has rows to avoid duplicates
            successful_row_additions = 0
            row_addition_errors = []
            
            await client.ensure_ready()
            get_response_check = await client.get(f'/api/offers/{offer_number}')
            if get_response_check.status_code == 200:
                current_offer = get_response_check.json()
                existing_rows = current_offer.get('offer_rows', [])
                if existing_rows:
                    self.logger.warning(f"Offer {offer_number} already has {len(existing_rows)} rows - counting existing rows")
                    successful_row_additions = len(existing_rows)
                else:
                    # Safe to add rows
                    for i, line_item in enumerate(offer_pricing.line_items, 1):
                        try:
                            success = await self._add_product_row_to_offer(client, offer_number, i, line_item)
                            if success:
                                successful_row_additions += 1
                        except Exception as e:
                            error_msg = f"Failed to add row {i} (product {line_item.product_code}): {str(e)}"
                            row_addition_errors.append(error_msg)
                            self.logger.error(error_msg)
            else:
                # Fallback: try to add rows anyway
                for i, line_item in enumerate(offer_pricing.line_items, 1):
                    try:
                        await client.ensure_ready()
                        success = await self._add_product_row_to_offer(client, offer_number, i, line_item)
                        await client.ensure_ready()
                        success = await self._add_product_row_to_offer(client, offer_number, i, line_item)
                        if success:
                            successful_row_additions += 1
                    except Exception as e:
                        error_msg = f"Failed to add row {i} (product {line_item.product_code}): {str(e)}"
                        row_addition_errors.append(error_msg)
                        self.logger.error(error_msg)
            
            self.logger.info(f"Row addition summary: {successful_row_additions} successful, {len(row_addition_errors)} failed")
            
            # Check if we have enough valid rows (at least 1 meaningful row)
            if successful_row_additions < 1:
                # Not enough valid rows - delete the offer and raise an error with details
                self.logger.error(f"Offer {offer_number} has insufficient rows ({successful_row_additions}), deleting offer")
                
                try:
                    # Try to delete the empty offer
                    await client.ensure_ready()
                    await client._make_request('DELETE', f'/api/offers/{offer_number}')
                    self.logger.info(f"Deleted empty offer {offer_number}")
                except Exception as delete_e:
                    self.logger.warning(f"Could not delete empty offer {offer_number}: {delete_e}")
                
                # Compile error details
                error_details = {
                    'successful_rows': successful_row_additions,
                    'total_products_attempted': len(offer_pricing.line_items),
                    'row_errors': row_addition_errors,
                    'offer_number': offer_number
                }
                
                raise BaseOfferAutomationError(
                    f"Offer creation failed: Only {successful_row_additions} out of {len(offer_pricing.line_items)} products could be added to the offer",
                    context={'insufficient_rows': True, 'error_details': error_details}
                )
            
            # Step 6: Verify the created offer
            verified_offer = await self._verify_created_offer(offer_number, offer_pricing)
            
            # Step 7: Save offer context to S3 for learning system
            try:
                await self.request_logger.save_offer_context(
                    offer_number=offer_number,
                    email_data=email_data,
                    matched_products=products,
                    customer_info=customer_info,
                    offer_pricing=offer_pricing
                )
            except Exception as e:
                # Don't fail the whole process if S3 logging fails
                self.logger.warning(f"Failed to save offer context to S3: {e}")
            
            return {
                'offer_number': offer_number,
                'customer_id': customer_info.get('id'),
                'products_count': len(offer_pricing.line_items),
                'net_total': offer_pricing.net_total,
                'vat_amount': offer_pricing.vat_amount,
                'total_amount': offer_pricing.total_amount,
                'total_discount_percent': offer_pricing.total_discount_percent,
                'created_at': datetime.now().isoformat(),
                'verification': verified_offer
            }, offer_pricing
    
    async def _add_product_row_to_offer(self, client, offer_number: str, position: int, line_item: LineItemPricing) -> bool:
        """Add a single product row to the offer using sophisticated pricing calculations.
        
        Returns:
            bool: True if row was successfully added, False otherwise
        """
        
        # Extract all pricing information from the LineItemPricing object
        product_code = line_item.product_code
        product_name = line_item.product_name if hasattr(line_item, 'product_name') else ''
        quantity = line_item.quantity
        unit_price = line_item.unit_price
        net_price = line_item.net_price
        discount_percent = line_item.discount_percent
        discount_amount = line_item.discount_amount
        line_total = line_item.line_total
        vat_rate = line_item.vat_rate
        vat_amount = line_item.vat_amount
        unit = line_item.unit
        extra_name = line_item.extra_name
        
        # Log the sophisticated pricing being applied
        applied_rules = ', '.join(line_item.applied_rules) if line_item.applied_rules else 'List price'
        self.logger.info(
            f"Adding product {product_code} with sophisticated pricing: "
            f"OVH: €{unit_price:.2f}, "
            f"Net (product_exp_price): €{net_price:.2f}, "
            f"Discount: {discount_percent:.1f}%, "
            f"Applied rules: {applied_rules}"
        )
        
        row_data = {
            "number": position,
            "position": str(position),
            "product_code": product_code,
            "product_name": product_name,
            "product_extra_name": extra_name,
            "quantity": f"{quantity:.4f}",
            "unit": unit,
            "unit_price": unit_price,  # OVH list price
            "unit_net_price": f"{net_price:.2f}",  # product_exp_price from database
            "discount": f"{discount_percent:.2f}",  # Customer discount percentage
            "total": f"{line_total + vat_amount:.2f}",  # Total including VAT
            "tax_rate": f"{vat_rate:.2f}",
            "tax_amount": f"{vat_amount:.2f}",
            "net_price": f"{net_price:.2f}",  # Net total before VAT (unit_price discounted × quantity)
            "type": 0,
            "account": LemonsoftConstants.DEFAULT_ACCOUNT,
            "cost_center": LemonsoftConstants.DEFAULT_COST_CENTER,
            "product_stock": LemonsoftConstants.DEFAULT_PRODUCT_STOCK
        }
        
        try:
            response_data = await client._make_request('POST', f'/api/offers/{offer_number}/offerrows', data=row_data)
            
            self.logger.info(
                f"Added product row: {product_name} x {quantity} "
                f"@ EUR{unit_price:.2f} (discount: {discount_percent:.1f}%) "
                f"= EUR{line_total:.2f} + VAT EUR{vat_amount:.2f}"
            )
            
        except Exception as e:
            error_str = str(e).lower()
            if "duplicate key" in error_str and "index2" in error_str:
                # This is a duplicate position error - likely a race condition
                self.logger.warning(f"Duplicate position {position} for offer {offer_number} - this may be due to concurrent processing")
                # Try with a different position number
                for retry_position in range(position + 10, position + 50):  # Try positions 11-50 higher
                    try:
                        retry_row_data = row_data.copy()
                        retry_row_data["number"] = retry_position
                        retry_row_data["position"] = str(retry_position)
                        
                        self.logger.info(f"Retrying with position {retry_position} for product {product_code}")
                        response_data = await client._make_request('POST', f'/api/offers/{offer_number}/offerrows', data=retry_row_data)
                        
                        self.logger.info(
                            f"Added product row (position {retry_position}): {product_name} x {quantity} "
                            f"@ EUR{unit_price:.2f} (discount: {discount_percent:.1f}%) "
                            f"= EUR{line_total:.2f} + VAT EUR{vat_amount:.2f}"
                        )
                        return True  # Success with retry position
                        
                    except Exception as retry_e:
                        if "duplicate key" not in str(retry_e).lower():
                            # Different error, stop retrying
                            break
                        continue
                
                # If all retries failed, log warning but don't fail the whole process
                self.logger.warning(f"Could not add product row for {product_code} due to position conflicts - continuing with other products")
                return False
            else:
                # Non-duplicate error, re-raise
                self.logger.error(f"Failed to add product row: {e}")
                raise BaseOfferAutomationError(f"Failed to add product row for {product_code}: {e}")
        
        return True  # Success on first try
    
    
    def _init_oauth_components(self):
        """Initialize OAuth2 components asynchronously."""
        # OAuth2 components will be initialized when first used
        # This avoids blocking the constructor but ensures they're ready
        pass
    
    async def _send_offer_notifications(self, offer_details: Dict, email_data: Dict, customer_info: Dict, matched_products: List[ProductMatch], offer_pricing):
        """Send offer confirmation email to the salesperson who forwarded the request (not the customer)."""
        self.logger.info(f"Sending offer confirmation to salesperson for offer: {offer_details.get('offer_number')}")
        
        try:
            # Initialize OAuth2 components if not already done
            if not hasattr(self.gmail_sender, 'service') or not self.gmail_sender.service:
                await self.gmail_sender.initialize()
            
            # Extract recipient email (original sender - the salesperson)
            recipient_email = email_data.get('sender', '')
            if not recipient_email:
                self.logger.warning("No sender email found, cannot send confirmation")
                return
            
            self.logger.info(f"Sending offer confirmation to salesperson: {recipient_email}")
            
            # Prepare product match data for email
            product_matches = []
            for i, product in enumerate(matched_products):
                line_item = offer_pricing.line_items[i] if i < len(offer_pricing.line_items) else None
                
                # Determine match method based on product code and match data
                match_method = 'direct'
                if hasattr(product, 'match_method'):
                    match_method = product.match_method
                elif product.product_code == '9000':
                    match_method = 'fallback'
                
                # Get discount method from applied rules
                discount_method = 'Listahinta'
                if line_item and line_item.applied_rules:
                    discount_method = ', '.join(line_item.applied_rules)
                
                # Extract AI confidence and reasoning from match_details
                ai_confidence = 75  # Default
                ai_reasoning = 'Ei saatavilla'
                
                if hasattr(product, 'match_details') and product.match_details:
                    ai_confidence = product.match_details.get('ai_confidence', 75)
                    ai_reasoning = product.match_details.get('ai_reasoning', 'Ei saatavilla')
                    # Also preserve original customer term
                    original_customer_term = product.match_details.get('original_customer_term', product.product_name)
                elif hasattr(product, 'confidence_score'):
                    # Convert confidence_score (0-1) to percentage if needed
                    ai_confidence = int(product.confidence_score * 100) if product.confidence_score <= 1 else product.confidence_score
                    original_customer_term = product.product_name
                else:
                    original_customer_term = product.product_name
                
                product_match_data = {
                    'product_code': product.product_code,
                    'product_name': getattr(product, 'product_name', 'Unknown Product'),
                    'quantity': product.quantity_requested,
                    'match_method': match_method,
                    'discount_method': discount_method,
                    'discount_percent': line_item.discount_percent if line_item else 0,
                    'line_total': line_item.line_total if line_item else 0,
                    'ai_confidence': ai_confidence,
                    'ai_reasoning': ai_reasoning,
                    'original_customer_term': original_customer_term
                }
                product_matches.append(product_match_data)
            
            # Prepare pricing details with line items
            pricing_details = {
                'net_total': offer_pricing.net_total,
                'vat_amount': offer_pricing.vat_amount,
                'total_amount': offer_pricing.total_amount,
                'total_discount_percent': offer_pricing.total_discount_percent,
                'line_items': []
            }
            
            # Add credit denial warning if applicable
            credit_warning = None
            if customer_info.get('deny_credit', False):
                credit_warning = "⚠️ ASIAKAS ON LUOTTOKIELLOSSA - Käytä toimitusehtoa 33 (ennakkomaksu)"
                self.logger.warning(f"Credit denial warning added for customer {customer_info.get('name')}: {credit_warning}")
            
            # Add line item details for discount analysis
            for line_item in offer_pricing.line_items:
                pricing_details['line_items'].append({
                    'applied_rules': line_item.applied_rules or ['Listahinta'],
                    'discount_percent': line_item.discount_percent,
                    'line_total': line_item.line_total,
                    'unit_price': line_item.unit_price
                })
            
            # Send confirmation email to salesperson (who can review before sending to customer)
            email_sent = await self.gmail_sender.send_offer_confirmation(
                recipient_email=recipient_email,
                offer_details=offer_details,
                customer_details=customer_info,
                product_matches=product_matches,
                pricing_details=pricing_details,
                verification_results=offer_details.get('verification', {}),
                original_email_data=email_data,
                credit_warning=credit_warning
            )
            
            if email_sent:
                self.logger.info(f"✅ Offer confirmation sent to salesperson: {recipient_email}")
                self.logger.info("   Salesperson can now review the offer before sending to customer")
                self.audit_logger.info(f"Offer confirmation email sent - Offer: {offer_details.get('offer_number')}, To: {recipient_email}, Customer: {customer_info.get('id')}, Products: {len(product_matches)}")
            else:
                self.logger.warning(f"Failed to send confirmation email to {recipient_email}")
            
        except Exception as e:
            self.logger.error(f"Error sending offer confirmation: {e}", exc_info=True)
            # Don't fail the whole process if email fails
            pass
    
    async def _send_error_notification(self, error_details: Dict, email_data: Dict, customer_info: Dict = None):
        """Send error notification email when offer creation fails."""
        self.logger.info(f"Sending error notification for failed offer creation")
        
        try:
            # Initialize OAuth2 components if not already done
            if not hasattr(self.gmail_sender, 'service') or not self.gmail_sender.service:
                await self.gmail_sender.initialize()
            
            # Extract recipient email (original sender - the salesperson)
            recipient_email = email_data.get('sender', '')
            if not recipient_email:
                self.logger.warning("No sender email found, cannot send error notification")
                return
            
            self.logger.info(f"Sending error notification to salesperson: {recipient_email}")
            
            # Send error notification email to salesperson
            email_sent = await self.gmail_sender.send_offer_error_notification(
                recipient_email=recipient_email,
                error_details=error_details,
                customer_details=customer_info,
                original_email_data=email_data
            )
            
            if email_sent:
                self.logger.info(f"✅ Error notification sent to salesperson: {recipient_email}")
                self.audit_logger.info(f"Error notification email sent - To: {recipient_email}, Customer: {customer_info.get('name') if customer_info else 'Unknown'}, Error: {error_details.get('error_type', 'Unknown')}")
            else:
                self.logger.warning(f"Failed to send error notification email to {recipient_email}")
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}", exc_info=True)
            # Don't fail the whole process if email fails
            pass
    
    async def process_incoming_email_requests(self, max_emails: int = 5) -> List[Dict[str, Any]]:
        """
        Check for new email requests and process them.
        
        Args:
            max_emails: Maximum number of emails to process
            
        Returns:
            List of processing results
        """
        import sys
        
        # Define allowed sender domains
        ALLOWED_DOMAINS = ['metec.fi', 'lvi-wabek.fi', 'wcom-group.fi', 'climapri.com', 'climapri.fi']
        
        sys.stdout.flush()
        
        try:
            # Initialize OAuth2 processor if needed
            if not hasattr(self.gmail_processor, 'gmail_service') or not self.gmail_processor.gmail_service:
                self.logger.info("📧 Initializing Gmail OAuth processor...")
                sys.stdout.flush()
                await self.gmail_processor.initialize()
            
            # Get unread emails
            sys.stdout.flush()
            
            emails = await self.gmail_processor.get_recent_emails(
                query="is:unread", 
                max_results=max_emails
            )
            
            if not emails:
                sys.stdout.flush()
                return []
            
            sys.stdout.flush()
            
            # Log details about each email
            for i, email in enumerate(emails):
                sender = email.get('sender', 'Unknown')
                subject = email.get('subject', 'No Subject')
                self.logger.info(f"  Email {i+1}: From {sender}, Subject: {subject[:50]}...")
                sys.stdout.flush()
            
            results = []
            for i, email in enumerate(emails):
                email_subject = email.get('subject', 'No Subject')[:50]
                email_sender = email.get('sender', 'Unknown')
                
                # Extract domain from sender email
                sender_domain = ''
                if '@' in email_sender:
                    # Handle format like "Name <email@domain.com>"
                    if '<' in email_sender and '>' in email_sender:
                        email_part = email_sender[email_sender.index('<')+1:email_sender.index('>')]
                        sender_domain = email_part.split('@')[1].lower() if '@' in email_part else ''
                    else:
                        sender_domain = email_sender.split('@')[1].lower()
                
                # Check if sender is from allowed domain
                is_allowed_domain = any(sender_domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)
                
                if not is_allowed_domain:
                    self.logger.info(f"⏭️ Skipping email {i+1}/{len(emails)} from {email_sender} - not from allowed domain")
                    self.logger.info(f"   Sender domain '{sender_domain}' not in allowed list: {ALLOWED_DOMAINS}")
                    # Mark as read to avoid processing again
                    await self.gmail_processor.mark_email_as_read(email.get('message_id'))
                    results.append({
                        'success': False,
                        'error': 'Sender not from allowed domain',
                        'sender_domain': sender_domain,
                        'skipped': True
                    })
                    continue
                
                self.logger.info(f"🔄 Processing email {i+1}/{len(emails)}: {email_subject}... from {email_sender}")
                sys.stdout.flush()
                
                # Classify email to determine appropriate action
                classification_result = None
                if self.email_classifier:
                    try:
                        self.logger.info(f"📋 Classifying email {i+1} to determine action...")
                        classification_result = await self.email_classifier.classify_email(email)
                        action = classification_result['action']
                        confidence = classification_result['confidence']
                        reasoning = classification_result['reasoning']
                        
                        self.logger.info(f"📋 Email classification: {action.value} (confidence: {confidence:.2f})")
                        self.logger.debug(f"📋 Classification reasoning: {reasoning}")
                        
                    except Exception as e:
                        self.logger.error(f"Email classification failed: {e}")
                        # Default to offer automation on classification failure
                        classification_result = {
                            'action': EmailAction.START_OFFER_AUTOMATION,
                            'confidence': 0.5,
                            'reasoning': f'Classification failed ({str(e)}), defaulting to offer automation',
                            'suggested_reply': None
                        }
                        action = EmailAction.START_OFFER_AUTOMATION
                else:
                    # No classifier available, default to offer automation
                    action = EmailAction.START_OFFER_AUTOMATION
                    classification_result = {
                        'action': action,
                        'confidence': 1.0,
                        'reasoning': 'EmailClassifier not available, defaulting to offer automation',
                        'suggested_reply': None
                    }
                
                # Process based on classification
                result = None
                
                if action == EmailAction.START_OFFER_AUTOMATION:
                    # Send "starting process" confirmation first
                    try:
                        self.logger.info(f"📧 Sending AI-generated process starting confirmation to {email_sender}...")
                        await self.gmail_sender.send_process_starting_confirmation(email_sender, email, classification_result)
                        self.logger.info(f"✅ AI-generated process starting confirmation sent to {email_sender}")
                    except Exception as e:
                        self.logger.warning(f"Failed to send starting confirmation: {e}")
                    
                    # Process the email through the offer automation
                    self.logger.info(f"🚀 Starting offer automation for email {i+1}...")
                    result = await self.process_email_offer_request(email)
                    result['classification'] = classification_result
                    
                elif action == EmailAction.SEND_REPLY_ONLY:
                    # Send contextual reply without offer processing
                    suggested_reply = classification_result.get('suggested_reply', 'Thank you for your email.')
                    try:
                        self.logger.info(f"📧 Sending contextual reply to {email_sender}...")
                        await self.gmail_sender.send_classification_reply(email_sender, suggested_reply, email)
                        result = {
                            'success': True,
                            'action': 'reply_sent',
                            'classification': classification_result,
                            'reply_sent': True
                        }
                        self.logger.info(f"✅ Contextual reply sent to {email_sender}")
                    except Exception as e:
                        self.logger.error(f"Failed to send contextual reply: {e}")
                        result = {
                            'success': False,
                            'error': f'Failed to send reply: {str(e)}',
                            'classification': classification_result,
                            'reply_sent': False
                        }
                
                elif action == EmailAction.DO_NOTHING:
                    # Just log and mark as processed
                    self.logger.info(f"⏭️ Email {i+1} classified as 'do nothing' - skipping processing")
                    result = {
                        'success': True,
                        'action': 'do_nothing',
                        'classification': classification_result,
                        'skipped': True
                    }
                
                results.append(result)
                
                # Always mark email as read regardless of processing result to prevent infinite loops
                try:
                    await self.gmail_processor.mark_email_as_read(email.get('message_id'))
                    if result.get('success'):
                        self.logger.info(f"✅ Email {i+1} processed successfully and marked as read: {email.get('message_id')}")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        self.logger.warning(f"❌ Email {i+1} processing failed but marked as read to prevent infinite loops: {email.get('message_id')}")
                        self.logger.warning(f"   Error: {error_msg}")
                    sys.stdout.flush()
                except Exception as mark_read_error:
                    self.logger.error(f"Failed to mark email {i+1} as read: {mark_read_error}")
                    sys.stdout.flush()
            
            success_count = sum(1 for r in results if r.get('success'))
            self.logger.info(f"📊 Email processing summary: {success_count}/{len(results)} successful")
            sys.stdout.flush()
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error processing incoming emails: {e}", exc_info=True)
            sys.stdout.flush()
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {},
            'initialization_status': getattr(self, '_initialization_status', {})
        }
        
        # Use cached initialization status if available
        if hasattr(self, '_initialization_status'):
            for component, status in self._initialization_status.items():
                health_status['components'][component] = 'healthy' if status else 'failed_during_init'
        
        # Try to check Lemonsoft API connectivity if it was initialized
        if getattr(self, '_initialization_status', {}).get('lemonsoft_api', False):
            try:
                async with self.lemonsoft_client as client:
                    await client.get('/api/health')
                    health_status['components']['lemonsoft_api_live'] = 'healthy'
            except Exception as e:
                health_status['components']['lemonsoft_api_live'] = f'unhealthy: {str(e)}'
                health_status['status'] = 'degraded'
        else:
            health_status['components']['lemonsoft_api_live'] = 'not_initialized'
        
        # Check Gmail OAuth processor
        try:
            if not hasattr(self.gmail_processor, 'gmail_service') or not self.gmail_processor.gmail_service:
                await self.gmail_processor.initialize()
            gmail_health = await self.gmail_processor.health_check()
            health_status['components']['gmail_oauth_processor'] = gmail_health['status']
            if gmail_health['status'] == 'healthy':
                health_status['components']['gmail_email'] = gmail_health.get('email_address', 'unknown')
        except Exception as e:
            health_status['components']['gmail_oauth_processor'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check Gmail OAuth sender
        try:
            if not hasattr(self.gmail_sender, 'service') or not self.gmail_sender.service:
                await self.gmail_sender.initialize()
            health_status['components']['gmail_oauth_sender'] = 'healthy'
        except Exception as e:
            health_status['components']['gmail_oauth_sender'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check AI analyzer
        try:
            if self.ai_analyzer and hasattr(self.ai_analyzer, 'health_check'):
                await self.ai_analyzer.health_check()
            health_status['components']['ai_analyzer'] = 'healthy' if self.ai_analyzer else 'not_initialized'
        except Exception as e:
            health_status['components']['ai_analyzer'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check pricing calculator
        try:
            pricing_health = await self.pricing_calculator.health_check()
            health_status['components']['pricing_calculator'] = pricing_health['status']
        except Exception as e:
            health_status['components']['pricing_calculator'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        return health_status
    
    async def close(self):
        """Close the orchestrator and cleanup resources."""
        try:
            if self.pricing_calculator:
                await self.pricing_calculator.close()
            
            if self.lemonsoft_client:
                await self.lemonsoft_client.close()
                
            self.logger.info("Orchestrator closed successfully")
        except Exception as e:
            self.logger.error(f"Error during orchestrator cleanup: {e}")
    
    async def _verify_created_offer(self, offer_number: str, expected_pricing: Any) -> Dict[str, Any]:
        """
        Verify the created offer by fetching it from Lemonsoft and comparing with expected values.
        
        Args:
            offer_number: The offer number to verify
            expected_pricing: The OfferPricing object with expected values
            
        Returns:
            Dict with verification results
        """
        self.logger.info(f"Verifying created offer: {offer_number}")
        
        try:
            async with self.lemonsoft_client as client:
                # Fetch the offer from Lemonsoft
                offer_data = await client._make_request('GET', f'/api/offers/{offer_number}')
                
                verification_result = {
                    'success': True,
                    'offer_found': True,
                    'offer_number': offer_number,
                    'lemonsoft_data': {},
                    'pricing_verification': {},
                    'product_verification': {},
                    'issues': []
                }
                
                # Extract key offer information
                verification_result['lemonsoft_data'] = {
                    'offer_id': offer_data.get('offer_id'),
                    'offer_number': offer_data.get('offer_number'),
                    'customer_number': offer_data.get('offer_customer_number'),
                    'customer_name': offer_data.get('offer_customer_name1'),
                    'total_without_tax': offer_data.get('tot_without_tax'),
                    'total_amount': offer_data.get('offer_totalsum'),
                    'profit_percent': offer_data.get('profit_percent'),
                    'currency': offer_data.get('currency_code'),
                    'rows_count': len(offer_data.get('offer_rows', []))
                }
                
                # Verify pricing
                lemonsoft_net_total = offer_data.get('tot_without_tax', 0)
                lemonsoft_total = offer_data.get('offer_totalsum', 0)
                expected_net_total = expected_pricing.net_total
                expected_total = expected_pricing.total_amount
                
                # Allow for small rounding differences (0.01€)
                net_diff = abs(lemonsoft_net_total - expected_net_total)
                total_diff = abs(lemonsoft_total - expected_total)
                
                verification_result['pricing_verification'] = {
                    'net_total_match': net_diff <= 0.01,
                    'total_amount_match': total_diff <= 0.01,
                    'lemonsoft_net_total': lemonsoft_net_total,
                    'expected_net_total': expected_net_total,
                    'net_difference': net_diff,
                    'lemonsoft_total': lemonsoft_total,
                    'expected_total': expected_total,
                    'total_difference': total_diff
                }
                
                if net_diff > 0.01:
                    verification_result['issues'].append(f"Net total mismatch: Expected €{expected_net_total:.2f}, got €{lemonsoft_net_total:.2f}")
                
                if total_diff > 0.01:
                    verification_result['issues'].append(f"Total amount mismatch: Expected €{expected_total:.2f}, got €{lemonsoft_total:.2f}")
                
                # Verify product rows
                offer_rows = offer_data.get('offer_rows', [])
                expected_rows = len(expected_pricing.line_items)
                actual_rows = len(offer_rows)
                
                verification_result['product_verification'] = {
                    'row_count_match': expected_rows == actual_rows,
                    'expected_rows': expected_rows,
                    'actual_rows': actual_rows,
                    'products': []
                }
                
                if expected_rows != actual_rows:
                    verification_result['issues'].append(f"Row count mismatch: Expected {expected_rows} rows, got {actual_rows} rows")
                
                # Verify individual product rows
                for i, row in enumerate(offer_rows):
                    if i < len(expected_pricing.line_items):
                        expected_line = expected_pricing.line_items[i]
                        
                        row_verification = {
                            'position': row.get('position'),
                            'product_code': row.get('product_code'),
                            'product_name': row.get('product_name'),
                            'quantity': row.get('quantity'),
                            'unit_price': row.get('unit_price'),
                            'discount': row.get('discount'),
                            'net_price': row.get('net_price'),
                            'total': row.get('total'),
                            'tax_amount': row.get('tax_amount'),
                            'expected_product_code': expected_line.product_code,
                            'expected_quantity': expected_line.quantity,
                            'expected_discount': expected_line.discount_percent,
                            'product_code_match': row.get('product_code') == expected_line.product_code,
                            'quantity_match': abs(row.get('quantity', 0) - expected_line.quantity) <= 0.01,
                            'discount_match': abs(row.get('discount', 0) - expected_line.discount_percent) <= 0.1
                        }
                        
                        verification_result['product_verification']['products'].append(row_verification)
                        
                        if not row_verification['product_code_match']:
                            verification_result['issues'].append(f"Row {i+1}: Product code mismatch")
                        
                        if not row_verification['quantity_match']:
                            verification_result['issues'].append(f"Row {i+1}: Quantity mismatch")
                        
                        if not row_verification['discount_match']:
                            verification_result['issues'].append(f"Row {i+1}: Discount mismatch")
                
                # Overall verification status
                if verification_result['issues']:
                    verification_result['success'] = False
                    self.logger.warning(f"Offer verification found issues: {verification_result['issues']}")
                else:
                    self.logger.info(f"Offer {offer_number} verification successful - all values match")
                
                return verification_result
                
        except Exception as e:
            self.logger.error(f"Error verifying offer {offer_number}: {e}", exc_info=True)
            return {
                'success': False,
                'offer_found': False,
                'error': str(e),
                'issues': [f"Failed to verify offer: {str(e)}"]
            }


async def test_main():
    """Test function that processes offer requests from test.md file instead of email."""
    logger = None
    orchestrator = None
    
    try:
        # Initialize logging first
        setup_logging()
        logger = get_logger(__name__)
        
        logger.info("Starting Offer Automation Test System...")
        orchestrator = OfferAutomationOrchestrator()
        
        # Initialize async components
        await orchestrator.initialize()
        
        # Perform health check
        health_status = await orchestrator.health_check()
        logger.info(f"System health check: {health_status['status']}")
        
        logger.info("Test system started successfully")
        logger.info("Ready to process test offer from test.md file...")
        
        # Read test data from test.md file
        test_file_path = Path(__file__).parent.parent / "test.md"
        
        if not test_file_path.exists():
            logger.error(f"Test file not found: {test_file_path}")
            logger.info("Please create a test.md file in the project root with your test offer content")
            return
        
        logger.info(f"Reading test data from: {test_file_path}")
        with open(test_file_path, 'r', encoding='utf-8') as f:
            test_content = f.read()
        
        if not test_content.strip():
            logger.error("Test file is empty")
            return
        
        logger.info(f"Loaded test content ({len(test_content)} characters)")
        
        # Create mock email data from test.md content
        test_email_data = {
            'subject': 'Test Offer Request',
            'sender': 'lauri.pelkonen@lvi-wabek.fi',  # Use allowed domain
            'body': test_content,
            'date': datetime.now().isoformat(),
            'message_id': 'test_message_002',
            'attachments': []  # No attachments in test mode
        }
        
        logger.info("Processing test offer request...")
        
        # Process the test email through the offer automation
        result = await orchestrator.process_email_offer_request(test_email_data)
        
        if result.get('success'):
            logger.info("✅ Test offer processing completed successfully!")
            logger.info(f"   Customer: {result.get('customer_info', {}).get('name', 'Unknown')}")
            logger.info(f"   Offer: {result.get('offer_details', {}).get('offer_number', 'Unknown')}")
            logger.info(f"   Products matched: {result.get('products_matched', 0)}")
            logger.info(f"   Processing time: {result.get('processing_time_seconds', 0):.2f}s")
        else:
            logger.error("❌ Test offer processing failed!")
            logger.error(f"   Error: {result.get('error', 'Unknown error')}")
            logger.error(f"   Error type: {result.get('error_type', 'Unknown')}")
        
        return result
        
    except Exception as e:
        if logger:
            logger.error(f"Fatal error in test_main: {str(e)}", exc_info=True)
        else:
            logging.error(f"Fatal error in test_main: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}
    finally:
        # Ensure proper cleanup
        if orchestrator:
            try:
                await orchestrator.close()
            except Exception as e:
                if logger:
                    logger.error(f"Error during cleanup: {e}")
                else:
                    print(f"Error during cleanup: {e}")


async def main():
    """Main entry point for the application."""
    logger = None
    orchestrator = None
    
    try:
        # Initialize logging first
        setup_logging()
        logger = get_logger(__name__)
        
        logger.info("Starting Offer Automation System...")
        orchestrator = OfferAutomationOrchestrator()
        
        # Initialize async components (CRITICAL - this was missing!)
        await orchestrator.initialize()
        
        # Perform health check
        health_status = await orchestrator.health_check()
        logger.info(f"System health check: {health_status['status']}")
        
        logger.info("Offer Automation System started successfully")
        logger.info("Ready to process email offer requests with sophisticated pricing...")
        logger.info("Using OAuth2 Gmail integration for personal Gmail account")
        
        # This main loop is only used when running main.py directly
        # In container mode, the pub/sub loop in enhanced_webhook.py handles email processing
        logger.info("🔄 Starting periodic email check loop (this runs when main.py is executed directly)")
        logger.info("💡 In container mode, the pub/sub loop in enhanced_webhook.py handles email processing automatically")
        
        # Process incoming emails periodically
        loop_count = 0
        while True:
            try:
                loop_count += 1
                
                # Check for new emails every 30 seconds
                await asyncio.sleep(30)
                
                
                # Process any new email requests
                results = await orchestrator.process_incoming_email_requests(max_emails=3)
                
                if results:
                    successful = sum(1 for r in results if r.get('success'))
                    logger.info(f"📊 Processed {len(results)} emails: {successful} successful, {len(results) - successful} failed")

                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main processing loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer after errors
            
    except KeyboardInterrupt:
        if logger:
            logger.info("Shutting down Offer Automation System...")
        else:
            print("Shutting down Offer Automation System...")
    except Exception as e:
        if logger:
            logger.error(f"Fatal error in main: {str(e)}", exc_info=True)
        else:
            logging.error(f"Fatal error in main: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Ensure proper cleanup
        if orchestrator:
            try:
                await orchestrator.close()
            except Exception as e:
                if logger:
                    logger.error(f"Error during cleanup: {e}")
                else:
                    print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(test_main())