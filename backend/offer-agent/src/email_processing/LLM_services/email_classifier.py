"""
Email Classification System for Offer Automation
Analyzes incoming emails to determine if they should trigger offer automation or require different handling.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

from google.genai import types

try:
    from src.product_matching.config import Config
except ImportError:
    try:
        from config import Config
    except ImportError:
        # Fallback configuration when config module is not available
        import os
        class Config:
            GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
            GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')


class EmailAction(Enum):
    """Possible actions for classified emails."""
    START_OFFER_AUTOMATION = "start_offer_automation"
    SEND_REPLY_ONLY = "send_reply_only" 
    DO_NOTHING = "do_nothing"


class EmailClassifier:
    """
    Classifies incoming emails to determine appropriate action.
    Uses LLM to analyze email content and context for intelligent routing.
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
                    wait_time = 0.5
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
    
    def __init__(self, gemini_client=None):
        """Initialize email classifier."""
        self.logger = logging.getLogger(__name__)
        
        # Use provided client or import AIAnalyzer's client
        if gemini_client:
            self.gemini_client = gemini_client
        else:
            from google import genai
            self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        self.logger.info("EmailClassifier initialized")
    
    async def classify_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an email to determine the appropriate action.
        
        Args:
            email_data: Dict containing email info (sender, subject, body, attachments)
            
        Returns:
            Dict with:
            - action: EmailAction enum value
            - confidence: float (0.0-1.0)
            - reasoning: str explaining the decision
            - suggested_reply: str (optional, for SEND_REPLY_ONLY cases)
        """
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        attachments = email_data.get('attachments', [])
        
        # Get attachment filenames for context
        attachment_names = [att.get('filename', 'unnamed') for att in attachments]
        
        self.logger.info(f"Classifying email from {sender}: {subject[:50]}...")
        self.logger.debug(f"Attachments: {attachment_names}")
        
        try:
            classification_result = await self._analyze_with_llm(
                sender=sender,
                subject=subject, 
                body=body,
                attachment_names=attachment_names,
                email_data=email_data
            )
            
            self.logger.info(f"Email classified as: {classification_result['action'].value}")
            self.logger.info(f"Confidence: {classification_result['confidence']:.2f}")
            self.logger.debug(f"Reasoning: {classification_result['reasoning']}")
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"Error classifying email: {e}")
            # Conservative fallback - assume it's an offer request
            return {
                'action': EmailAction.START_OFFER_AUTOMATION,
                'confidence': 0.5,
                'reasoning': f'Classification failed ({str(e)}), defaulting to offer automation for safety',
                'suggested_reply': None
            }
    
    async def _analyze_with_llm(self, sender: str, subject: str, body: str, 
                               attachment_names: List[str], email_data: Dict) -> Dict[str, Any]:
        """Use LLM to analyze email and determine classification."""
        
        # Build context about the email
        attachment_context = ""
        if attachment_names:
            attachment_context = f"\nATTACHMENTS: {', '.join(attachment_names)}"
        
        prompt = f"""Analyze this email to determine if it's a genuine offer automation request from a salesperson or requires different handling.

SENDER: {sender}
SUBJECT: {subject}
{attachment_context}

EMAIL BODY:
{body}

CONTEXT:
- This email comes from an allowed domain (metec.fi, lvi-wabek.fi, wcom-group.fi, climapri.com, climapri.fi)
- The sender is likely a salesperson or internal employee
- Our system creates automated offers for HVAC/plumbing products based on customer requests
- Salespeople forward customer requests to trigger automated offer creation

CLASSIFICATION RULES:
1. START_OFFER_AUTOMATION - Default choice for:
   - Customer product requests forwarded by salespeople
   - Emails with product lists, quotes, or inquiries
   - Any ambiguous case where it could be an offer request
   - Excel/PDF attachments with product information
   - Subject mentions: tarjous, offer, tuotteet, products, tilaus, order, etc.

2. SEND_REPLY_ONLY - Only for:
   - Out-of-office/vacation responses
   - General questions about the automation system itself
   - Administrative notifications
   - Meeting invitations unrelated to offers
   - Clear non-product inquiries

3. DO_NOTHING - Only for:
   - System notifications/automated emails
   - Email delivery confirmations
   - Spam or irrelevant content
   - Test emails

IMPORTANT: When in doubt, choose START_OFFER_AUTOMATION. It's better to process an unnecessary email than miss a genuine customer request.

Respond with JSON only:
{{
  "action": "start_offer_automation" | "send_reply_only" | "do_nothing",
  "confidence": 0.95,
  "reasoning": "Detailed explanation of why this classification was chosen",
  "suggested_reply": "Professional reply text (only if action is send_reply_only)"
}}

For suggested_reply, use Finnish if the original email is in Finnish, English otherwise. Keep replies professional and helpful."""

        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                candidate_count=1,
            )

            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            # Extract response text
            response_text = self._extract_response_text(response)
            
            if not response_text:
                raise Exception("No response from LLM")
            
            # Parse JSON response
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            result = json.loads(json_text)
            
            # Convert action string to enum
            action_str = result.get('action', 'start_offer_automation')
            if action_str == 'start_offer_automation':
                action = EmailAction.START_OFFER_AUTOMATION
            elif action_str == 'send_reply_only':
                action = EmailAction.SEND_REPLY_ONLY
            elif action_str == 'do_nothing':
                action = EmailAction.DO_NOTHING
            else:
                # Default fallback
                action = EmailAction.START_OFFER_AUTOMATION
            
            return {
                'action': action,
                'confidence': float(result.get('confidence', 0.8)),
                'reasoning': result.get('reasoning', 'No reasoning provided'),
                'suggested_reply': result.get('suggested_reply', None)
            }
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            raise
    
    def _extract_response_text(self, response) -> Optional[str]:
        """Extract text from Gemini API response."""
        try:
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        part = candidate.content.parts[0]
                        if hasattr(part, 'text') and part.text:
                            return part.text.strip()
            return None
        except Exception as e:
            self.logger.warning(f"Error extracting response text: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the classifier."""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'gemini_model': Config.GEMINI_MODEL,
            'api_key_configured': bool(Config.GEMINI_API_KEY)
        }