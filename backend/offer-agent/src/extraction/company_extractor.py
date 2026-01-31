"""
Company Information Extractor

Extracts company name, delivery contact, and customer reference from emails using AI.
This module is completely ERP-independent - it only handles text extraction.
"""
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from google import genai
from google.genai import types
import os
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()


class CompanyExtractor:
    """
    Extracts company information from emails using AI (Gemini).

    This is a pure extraction service with NO ERP dependencies.
    It handles:
    - Company name extraction
    - Delivery contact extraction
    - Customer reference extraction
    - Retry logic for failed extractions
    """

    def __init__(self):
        """
        Initialize the company extractor.

        Args:
            ai_analyzer: Optional AI analyzer instance (for Gemini access)
        """
        self.logger = get_logger(__name__)
        self.gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    def parse_email_sender(self, sender: str) -> tuple[str, str]:
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

    async def extract_company_information(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract company name, delivery contact, and customer reference from email.

        This is the main entry point for company information extraction.

        Args:
            email_data: Dict containing 'body', 'sender', 'subject', 'attachments'

        Returns:
            Dict with:
                - company_name: Extracted company name
                - customer_number: Customer number (if found)
                - delivery_contact: Delivery contact person
                - customer_reference: Customer reference/project
                - confidence scores
                - source information
        """
        body = email_data.get('body', '')
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        attachments = email_data.get('attachments', [])

        # Parse sender to get clean email address and display name
        sender_email, sender_name = self.parse_email_sender(sender)
        self.logger.debug(f"Parsed sender: email={sender_email}, name={sender_name}")

        self.logger.info("Extracting company information and delivery contact from email")
        self.logger.debug(f"📧 Email details for analysis:")
        self.logger.debug(f"   Sender: {sender}")
        self.logger.debug(f"   Subject: {subject}")
        self.logger.debug(f"   Body length: {len(body)} characters")
        self.logger.debug(f"   Attachments: {len(attachments)} files")

        if attachments:
            for i, att in enumerate(attachments):
                self.logger.debug(
                    f"     Attachment {i}: {att.get('filename', 'unnamed')} "
                    f"({att.get('size', 0)} bytes, {att.get('mime_type', 'unknown')})"
                )

        if len(body) > 100:
            preview = body[:500].replace('\n', ' ').replace('\r', ' ')
            self.logger.debug(f"   Body preview: {preview}...")
        else:
            self.logger.debug(f"   Full body: {body}")



        # Use AI to extract all information in one call
        combined_info = await self._extract_with_ai(
            body, sender_email, sender_name, subject
        )

        self.logger.info(f"Extracted company: {combined_info.get('company_name', 'Not found')}")
        self.logger.info(f"Extracted delivery contact: {combined_info.get('delivery_contact', 'Not found')}")
        self.logger.info(f"Extracted customer reference: {combined_info.get('customer_reference', 'Not found')}")

        return combined_info

    async def retry_company_extraction(
        self,
        body: str,
        sender_email: str,
        subject: str,
        failed_company_name: str
    ) -> Dict[str, Any]:
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
                import google.genai as genai
                model = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
                response = model.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=500,
                    )
                )
                return response.text

            response = self._retry_llm_request(make_request)

            if response and response.text:
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

    async def _extract_with_ai(
        self,
        body: str,
        sender_email: str,
        sender_name: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Use AI to extract company name, delivery contact, and customer reference.

        Args:
            body: Email body text
            sender_email: Sender email address (clean, without display name)
            sender_name: Sender display name (the sales person who forwarded the email)
            subject: Email subject

        Returns:
            Dict with extracted information and confidence scores
        """
        try:
            from google.genai import types
            from config.constants import get_our_companies
            company_names = get_our_companies()
            company_names_str = ', '.join(company_names)

            prompt = f"""Extract company name, delivery contact person, and customer reference from this email content.

SALES PERSON WHO FORWARDED THIS EMAIL:
Name: {sender_name}
Email: {sender_email}

EMAIL SUBJECT: {subject}

EMAIL CONTENT:
{body}

CRITICAL RULES - NEVER VIOLATE THESE:
- NEVER return {company_names_str} or any variation as the customer company
- These are OUR OWN companies who CREATE offers, not customers who receive them
- {company_names_str} is THE COMPANY RUNNING THIS SYSTEM - it can NEVER be the customer
- If the email is FROM someone @{company_names_str}.fi, they are asking for an offer for THEIR customer, not for {company_names_str}
- If you only see these company names, look harder for the actual customer company name
- The customer is the company RECEIVING the offer, not sending this email

INSTRUCTIONS:
1. COMPANY NAME: Look for the CUSTOMER's company name (the one receiving the offer)
   - Often locates in the email signature, greeting, or content (f.ex. "Ystävällisin terveisin, / Jarkko Suominen/ Yritys Oy" in the end of the customer's email)
   - This is NOT {company_names_str} (these are our companies)
   - This is NOT Gmail, Outlook, or other email providers
   - Look in email body for mentions like "asiakkaalle" (to customer), "tilaaja" (orderer), or company names in forwarded content
   - Check if the salesperson mentions who the offer is for

2. CUSTOMER NUMBER: This is rare, but sometimes the sales person (works at {company_names_str}) who is forwarding this message, has included customer number. If this is mentioned clearly, include it in the response.

3. DELIVERY CONTACT - EXTREMELY IMPORTANT:
   - NEVER EVER return "{sender_name}" as the delivery contact - THIS IS THE SALES PERSON, NOT THE CUSTOMER
   - NEVER use the email address "{sender_email}" to extract a name
   - Look for customer's contact person names ONLY in:
     * Email signatures FROM THE CUSTOMER (not from the sales person)
     * Customer's quoted/forwarded messages
     * Explicit mentions like "contact person: John Doe" or "yhteyshenkilö: Matti Virtanen"
   - Do NOT use names of people who work at {company_names_str}
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

IMPORTANT: If the extracted company name is {company_names_str} or similar, these are NOT customers - look for the actual customer company name or use "null" instead.

If no clear contact name found, use "Not available". If no specific reference found, generate a short one like "VESIMITTARIT" based on company/subject.

If no clear customer number found, use "null"."""

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
                self.gemini_client.models.generate_content,
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
                return self._fallback_extraction(sender_email)

            # Parse JSON response
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()

            result = json.loads(json_text)

            # Validate and clean up the results - handle None values
            company_name = (result.get('company_name') or '').strip()
            delivery_contact = (result.get('delivery_contact') or '').strip()
            customer_reference = (result.get('customer_reference') or '').strip()
            customer_number = (result.get('customer_number') or '').strip()

            # CRITICAL: Check if AI incorrectly identified our own company as customer
            our_companies = get_our_companies()
            # More robust check - also check exact matches and variations
            company_lower = company_name.lower().replace('-', '').replace(' ', '').replace('_', '')
            if any(own_company.replace('-', '').replace(' ', '').replace('_', '') in company_lower
                   for own_company in our_companies):
                self.logger.warning(
                    f"AI incorrectly identified our own company '{company_name}' as customer - "
                    f"resetting to Unknown Customer"
                )
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
            return self._fallback_extraction(sender_email)

    def _fallback_extraction(self, sender_email: str) -> Dict[str, Any]:
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
            'customer_number': 'null',
            'delivery_contact': delivery_contact,  # Always default, never sender
            'customer_reference': customer_reference,
            'company_confidence': 0.5,
            'contact_confidence': 0.5,
            'reference_confidence': 0.5,
            'company_source': 'domain_fallback',
            'contact_source': 'default_fallback',
            'reference_source': 'fallback_generated',
            'email_domain': sender_email.split('@')[1] if '@' in sender_email else '',
            'source': 'fallback_extraction'
        }

    def _retry_llm_request(self, request_func, *args, **kwargs):
        """
        Wrapper to retry LLM requests with appropriate wait times based on error type.

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
