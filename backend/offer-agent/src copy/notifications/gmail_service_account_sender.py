"""
Gmail Service Account Sender - ZERO User Interaction Required
Fully automated Gmail sending using service account authentication.
Never expires, never requires OAuth browser flow.
"""

import os
import base64
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io

from src.utils.logger import get_logger
from src.utils.exceptions import EmailSenderError


class GmailServiceAccountSender:
    """Zero-touch Gmail sender using service account authentication."""
    
    # Gmail API scopes - must match domain-wide delegation configuration
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        """Initialize Gmail service account sender."""
        self.logger = get_logger(__name__)
        self.service = None
        self.credentials = None
        
        # Service account configuration
        self.service_account_file = os.getenv('GMAIL_SERVICE_ACCOUNT_FILE', 'config/gmail-service-account.json')
        self.sender_email = os.getenv('EMAIL_FROM_ADDRESS', os.getenv('MONITORED_EMAIL', 'automations@agent.lvi-wabek.fi'))
        
        self.logger.info(f"Gmail Service Account Sender initialized for: {self.sender_email}")
    
    async def initialize(self):
        """Initialize Gmail API service with Service Account - ZERO user interaction required."""
        try:
            # Check if service account file exists
            service_account_path = Path(self.service_account_file)
            if not service_account_path.exists():
                raise EmailSenderError(
                    f"Gmail service account file not found: {self.service_account_file}\\n"
                    f"Please ensure the service account JSON file exists.\\n"
                    f"This file contains the private key for automated Gmail access.\\n"
                    f"Expected location: {service_account_path.absolute()}"
                )
            
            self.logger.info(f"Loading Gmail service account from: {self.service_account_file}")
            
            # Load service account credentials - NO USER INTERACTION REQUIRED
            self.credentials = service_account.Credentials.from_service_account_file(
                str(service_account_path),
                scopes=self.SCOPES
            )
            
            # Set up domain-wide delegation (impersonation) - same as working test
            if self.sender_email:
                self.logger.info(f"Setting up domain-wide delegation for: {self.sender_email}")
                self.credentials = self.credentials.with_subject(self.sender_email)
            
            # Build Gmail service with timeout configuration - credentials automatically refresh and never expire!
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            # Configure timeout for service requests
            self.service._http.timeout = 120  # 2 minutes timeout for large attachments
            
            self.logger.info("[SUCCESS] Gmail Service Account initialized successfully")
            self.logger.info(f"[SUCCESS] Sender email: {self.sender_email}")
            self.logger.info("[SUCCESS] ZERO user interaction required - fully automated!")
            
        except FileNotFoundError as e:
            self.logger.error(f"Service account file not found: {e}")
            raise EmailSenderError(f"Gmail service account file missing: {str(e)}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid service account JSON file: {e}")
            raise EmailSenderError(f"Invalid service account file format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service account: {e}")
            raise EmailSenderError(f"Gmail service account initialization failed: {str(e)}")
    
    async def _ensure_valid_service(self):
        """Ensure Gmail service is available - service accounts never need refresh!"""
        if not self.service or not self.credentials:
            self.logger.info("Gmail service not initialized, initializing now...")
            await self.initialize()
        
        # Service account credentials never expire - no refresh needed!
        self.logger.debug("Gmail service account credentials are always valid")
    
    async def _send_with_retry(self, message_data: Dict, max_retries: int = 3, base_delay: float = 1.0) -> Dict:
        """
        Send email with exponential backoff retry logic for timeout handling.
        
        Args:
            message_data: Gmail API message data
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            
        Returns:
            Dict: Gmail API response
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Sending email attempt {attempt + 1}/{max_retries + 1}")
                start_time = time.time()
                
                # Send the email with timeout handling
                result = self.service.users().messages().send(
                    userId='me',
                    body=message_data
                ).execute()
                
                elapsed_time = time.time() - start_time
                self.logger.info(f"Email sent successfully on attempt {attempt + 1} (took {elapsed_time:.1f} seconds)")
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a timeout or temporary error
                is_retryable = (
                    "timeout" in str(e).lower() or
                    "timed out" in str(e).lower() or
                    isinstance(e, HttpError) and e.resp.status >= 500
                )
                
                if attempt < max_retries and is_retryable:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Email send attempt {attempt + 1} failed with retryable error: {e}")
                    self.logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # Last attempt or non-retryable error
                    self.logger.error(f"Email send attempt {attempt + 1} failed: {e}")
                    break
        
        # All retries failed
        raise last_exception
    
    def _optimize_pdf_for_email(self, pdf_bytes: bytes, max_size_mb: float = 15.0) -> bytes:
        """
        Optimize PDF size for email if it's too large.
        
        Args:
            pdf_bytes: Original PDF bytes
            max_size_mb: Maximum size in MB before optimization
            
        Returns:
            bytes: Optimized PDF bytes (or original if already small enough)
        """
        current_size_mb = len(pdf_bytes) / (1024 * 1024)
        
        if current_size_mb <= max_size_mb:
            self.logger.debug(f"PDF size ({current_size_mb:.2f} MB) is within limits, no optimization needed")
            return pdf_bytes
        
        self.logger.info(f"PDF size ({current_size_mb:.2f} MB) exceeds {max_size_mb} MB, attempting optimization...")
        
        try:
            # Try to use PyPDF2 for basic optimization if available
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy pages with optimization
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Write optimized PDF
            optimized_bytes = io.BytesIO()
            pdf_writer.write(optimized_bytes)
            optimized_pdf = optimized_bytes.getvalue()
            
            new_size_mb = len(optimized_pdf) / (1024 * 1024)
            self.logger.info(f"PDF optimized: {current_size_mb:.2f} MB -> {new_size_mb:.2f} MB")
            
            return optimized_pdf
            
        except ImportError:
            self.logger.warning("PyPDF2 not available for PDF optimization, using original PDF")
            return pdf_bytes
        except Exception as e:
            self.logger.warning(f"PDF optimization failed: {e}, using original PDF")
            return pdf_bytes
    
    async def send_stock_alert_email(self, recipient_email: str, warehouse_info: Dict, 
                                   negative_products: List[Dict]) -> bool:
        """
        Send stock alert email for negative stock products.
        
        Args:
            recipient_email: Email address to send to
            warehouse_info: Dictionary with warehouse name and email
            negative_products: List of products with negative stock
            
        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid - no user interaction needed!
        await self._ensure_valid_service()
        
        try:
            warehouse_name = warehouse_info['name']
            
            # Create email content
            subject = f"TUOTTEITA MIINUKSELLA - {warehouse_name}"
            
            # Create product list HTML
            product_rows = ""
            for product in negative_products:
                product_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{product['product_code']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{product['product_description']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: #cc0000; font-weight: bold;">
                    {product['current_stock']}
                </td>
            </tr>
            """
            
            html_body = f"""
        <!DOCTYPE html>
        <html lang="fi">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #cc0000; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background-color: #333; color: white; padding: 10px; text-align: left; }}
                .footer {{ margin-top: 30px; padding: 20px; background-color: #f0f0f0; text-align: center; }}
                .warning {{ color: #cc0000; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>TUOTTEITA MIINUKSELLA</h1>
                    <p>{warehouse_name}</p>
                </div>
                
                <div class="content">
                    <p><strong>Tämä on automaattinen viesti.</strong></p>
                    
                    <p>Myymälässä <strong>{warehouse_name}</strong> seuraavat tuotteet ovat miinussaldoilla:</p>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Tuotekoodi</th>
                                <th>Tuotekuvaus</th>
                                <th>Saldo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {product_rows}
                        </tbody>
                    </table>
                    
                    <p style="margin-top: 20px;">
                        <span class="warning">Yhteensä {len(negative_products)} tuotetta miinussaldolla.</span>
                    </p>
                    
                    <p>Ole hyvä ja päivitä saldot mahdollisimman pian.</p>
                </div>
                
                <div class="footer">
                    <p>Tämä viesti on lähetetty automaattisesti varastonseurantajärjestelmästä.</p>
                    <p>Tarkistusaika: {datetime.now().strftime('%d.%m.%Y klo %H:%M')}</p>
                    <p><strong>ÄLÄ VASTAA TÄHÄN VIESTIIN.</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
            
            # Create email message
            message = MIMEMultipart('alternative')
            message['to'] = self._clean_email_address(recipient_email)
            message['from'] = self.sender_email
            message['subject'] = subject
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send email via Gmail API with retry logic - service account automatically handles authentication
            result = await self._send_with_retry({'raw': raw_message})
            
            message_id = result.get('id')
            self.logger.info(f"[SUCCESS] Stock alert email sent successfully!")
            self.logger.info(f"   Recipient: {recipient_email}")
            self.logger.info(f"   Warehouse: {warehouse_name}")
            self.logger.info(f"   Products: {len(negative_products)}")
            self.logger.info(f"   Message ID: {message_id}")
            
            return True
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send stock alert email: {e}")
            return False
    
    async def send_offer_confirmation(self, recipient_email: str, offer_details: Dict, 
                                     customer_details: Dict, product_matches: List[Dict],
                                     pricing_details: Dict, verification_results: Dict = None,
                                     original_email_data: Dict = None, credit_warning: str = None) -> bool:
        """
        Send offer confirmation email with PDF attachment.
        
        Args:
            recipient_email: Email address to send to
            offer_details: Dictionary with offer information
            customer_details: Dictionary with customer information  
            product_matches: List of matched products
            pricing_details: Dictionary with pricing information
            verification_results: Optional verification results
            original_email_data: Original email that triggered the offer
            credit_warning: Credit warning message if applicable
            
        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid - no user interaction needed!
        await self._ensure_valid_service()
        
        try:
            # Create email content using the same logic as OAuth sender
            subject = f"Automaattitarjous luotu: {offer_details.get('offer_number')} - {customer_details.get('name', 'Asiakas')}"
            
            self.logger.info("Generating PDF attachment...")
            
            # Generate PDF attachment using PDF generator (import here to match OAuth sender pattern)
            from src.notifications.pdf_generator import OfferConfirmationPDFGenerator
            pdf_generator = OfferConfirmationPDFGenerator()
            
            pdf_bytes = pdf_generator.generate_offer_confirmation_pdf(
                offer_details, customer_details, product_matches,
                pricing_details, verification_results, original_email_data, credit_warning
            )
            pdf_filename = pdf_generator.generate_filename(offer_details, customer_details)
            
            self.logger.info(f"PDF generated successfully: {pdf_filename}, size: {len(pdf_bytes)} bytes")
            
            # Optimize PDF for email if it's too large
            optimized_pdf_bytes = self._optimize_pdf_for_email(pdf_bytes)
            
            # Create email message with attachment
            message = MIMEMultipart('mixed')
            message['to'] = self._clean_email_address(recipient_email)
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Create simple text body referencing the PDF (Finnish only)
            text_body = f"""
Hei,

Automaattisesti luotu tarjous on valmiina liitteenä PDF-tiedostona.

Tarjous: {offer_details.get('offer_number', 'PENDING')}
Asiakas: {customer_details.get('name', 'N/A')}
Tuotteiden määrä: {len(product_matches)}

{credit_warning if credit_warning else ''}

Ystävällisin terveisin,
Automaattitarjousjärjestelmä
            """.strip()
            
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            message.attach(text_part)
            
            # Attach optimized PDF
            from email.mime.base import MIMEBase
            from email import encoders
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(optimized_pdf_bytes)
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
            message.attach(pdf_attachment)
            
            # Convert to base64 encoded string
            message_bytes = message.as_bytes()
            message_size_mb = len(message_bytes) / (1024 * 1024)
            
            self.logger.info(f"Preparing to send email (size: {message_size_mb:.2f} MB)...")
            
            if message_size_mb > 23:  # Gmail API limit is 25MB, hard limit at 23MB
                self.logger.error(f"Email size ({message_size_mb:.2f} MB) exceeds Gmail limits - cannot send")
                raise Exception(f"Email too large for Gmail API: {message_size_mb:.2f} MB > 23 MB limit")
            elif message_size_mb > 15:  # Warn for large emails
                self.logger.warning(f"Large email size ({message_size_mb:.2f} MB) - may take longer to send")
            
            raw_message = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
            
            self.logger.info("Sending email via Gmail API with retry logic...")
            
            # Send the email with retry mechanism for timeout handling
            result = await self._send_with_retry(
                message_data={'raw': raw_message},
                max_retries=3,
                base_delay=2.0  # Start with 2 seconds for large attachments
            )
            
            self.logger.info(f"Offer confirmation email with PDF attachment sent successfully to {recipient_email}")
            self.logger.info(f"Gmail message ID: {result.get('id')}, PDF filename: {pdf_filename}")
            self.logger.info(f"Email size: {message_size_mb:.2f} MB")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send offer confirmation email: {e}")
            return False
    
    async def send_process_starting_confirmation(self, recipient_email: str, email_data: Dict[str, Any], 
                                               classification_result: Dict[str, Any] = None) -> bool:
        """
        Send AI-generated confirmation that offer automation process is starting.
        
        Args:
            recipient_email: Email address to send to
            email_data: Original email data that triggered the process
            classification_result: Classification details from EmailClassifier
            
        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid - no user interaction needed!
        await self._ensure_valid_service()
        
        try:
            # Generate AI confirmation response
            ai_response = await self._generate_starting_confirmation_with_ai(email_data, classification_result)
            
            if not ai_response:
                # Fallback to basic confirmation if AI fails
                self.logger.warning("AI confirmation generation failed, using fallback")
                sender = email_data.get('sender', 'Unknown')
                subject = email_data.get('subject', 'No Subject')
                
                email_subject = f"Aloitetaan tarjousprosessi - {subject[:30]}..."
                text_body = f"""
Hei / Hello,

Kiitos sähköpostistasi! Olen vastaanottanut pyyntösi ja aloitan automaattisen tarjousprosessin.
Thank you for your email! I have received your request and am starting the automatic offer process.

Alkuperäinen viesti / Original message: {subject}
Lähettäjä / Sender: {sender}

Saat pian toisen sähköpostin kun tarjous on valmis.
You will receive another email shortly when the offer is ready.

Ystävällisin terveisin / Best regards,
Automaattitarjousjärjestelmä / Automatic Offer System
                """.strip()
            else:
                email_subject = ai_response['subject']
                text_body = ai_response['body']
            
            # Create and send email
            message = MIMEText(text_body, 'plain', 'utf-8')
            message['to'] = self._clean_email_address(recipient_email)
            message['from'] = self.sender_email
            message['subject'] = email_subject
            
            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.logger.info(f"Sending AI-generated process starting confirmation to {recipient_email}")
            
            # Send the email with retry logic
            result = await self._send_with_retry({'raw': raw_message})
            
            self.logger.info(f"AI-generated process starting confirmation sent successfully to {recipient_email}")
            self.logger.info(f"Gmail message ID: {result.get('id')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send process starting confirmation: {e}")
            return False
    
    async def _generate_starting_confirmation_with_ai(self, email_data: Dict[str, Any], 
                                                     classification_result: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate AI-powered starting confirmation email."""
        try:
            # Import Gemini client
            from google import genai
            from google.genai import types
            
            # Use same config as other components
            try:
                from src.product_matching.config import Config
                gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                model = Config.GEMINI_MODEL
            except ImportError:
                import os
                api_key = os.getenv('GEMINI_API_KEY', '')
                if not api_key:
                    self.logger.warning("No Gemini API key available for AI confirmation")
                    return None
                gemini_client = genai.Client(api_key=api_key)
                model = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
            
            sender = email_data.get('sender', 'Unknown')
            subject = email_data.get('subject', 'No Subject')
            body = email_data.get('body', '')
            attachments = email_data.get('attachments', [])
            
            # Get attachment filenames for context
            attachment_names = [att.get('filename', 'unnamed') for att in attachments]
            attachment_context = f"\nLiitteet / Attachments: {', '.join(attachment_names)}" if attachment_names else ""
            
            # Get classification reasoning if available
            classification_context = ""
            if classification_result:
                confidence = classification_result.get('confidence', 0.8)
                reasoning = classification_result.get('reasoning', '')
                classification_context = f"\nLuokittelun luottamustaso / Classification confidence: {confidence:.1%}"
            
            # Extract sender name and company context
            sender_name, sender_company = self._parse_sender_info(sender)
            
            prompt = f"""Kirjoita ammattimainen sähköpostivastaus, jossa vahvistat että aloitat automaattisen tarjousprosessin.

ALKUPERÄINEN SÄHKÖPOSTI:
Lähettäjä: {sender}
Lähettäjän nimi: {sender_name}
Lähettäjän yritys: {sender_company}
Aihe: {subject}
{attachment_context}
{classification_context}

Sisältö:
{body[:1000]}{"..." if len(body) > 1000 else ""}

KONTEKSTI:
- Lähettäjä {sender_name} on välittänyt asiakkaan tarjouspyynnön
- Lähettäjä työskentelee yrityksessä {sender_company}
- Vastaat henkilökohtaisesti lähettäjälle {sender_name}
- Lähettäjä odottaa että käsittelet tämän automaattisesti

OHJEISTUS:
- Puhuttele lähettäjää nimellä ({sender_name})
- Kirjoita VAIN suomeksi - älä käytä englantia
- Ole ystävällinen ja ammattimainen
- Vahvista että aloitat tarjousprosessin
- Mainitse että {sender_name} saa toisen viestin kun tarjous on valmis
- Viittaa alkuperäiseen pyyntöön luonnollisesti
- Älä lupaa liikoja - pidä odotukset realistisina
- Käytä lyhyttä, ytimekästä tyyliä
- Allekirjoita PELKÄSTÄÄN: "//WCOM Intelligence". ÄLÄ KÄYTÄ OLLENKAAN "ystävällisin terveisin" tai "best regards" tai jotain muuta.
- Sano allekirjoutuksen jälkeen, että virhetilanteessa ota yhteyttä lauri.pelkonen@lvi-wabek.fi
- Kiitä {sender_name}:ta pyynnön välittämisestä

MUOTO:
Vastaa JSON-muodossa:
{{
  "subject": "Sähköpostin aiherivi suomeksi",
  "body": "Sähköpostin sisältö vain suomeksi"
}}

Älä käytä markdown-muotoiluja tai ```json``` tageja."""

            config = types.GenerateContentConfig(
                temperature=0.3,  # Slightly more creative than classification
                candidate_count=1,
            )

            response = gemini_client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            # Extract response text
            response_text = self._extract_ai_response_text(response)
            
            if not response_text:
                self.logger.warning("No response from AI for starting confirmation")
                return None
            
            # Parse JSON response
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            result = json.loads(json_text)
            
            # Validate response
            if 'subject' not in result or 'body' not in result:
                self.logger.warning("AI response missing required fields")
                return None
            
            self.logger.info("AI-generated starting confirmation created successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"AI confirmation generation failed: {e}")
            return None
    
    def _parse_sender_info(self, sender: str) -> tuple[str, str]:
        """
        Parse sender email to extract name and company information.
        
        Args:
            sender: Email sender (e.g., "John Doe <john.doe@metec.fi>" or "john.doe@metec.fi")
            
        Returns:
            tuple: (sender_name, sender_company)
        """
        try:
            # Handle format: "Name <email@domain.com>"
            if '<' in sender and '>' in sender:
                name_part = sender[:sender.index('<')].strip()
                email_part = sender[sender.index('<')+1:sender.index('>')]
            else:
                # Handle format: "email@domain.com"
                name_part = ""
                email_part = sender.strip()
            
            # Extract domain and map to company
            if '@' in email_part:
                domain = email_part.split('@')[1].lower()
                
                # Map domains to company names
                company_mapping = {
                    'metec.fi': 'Metec',
                    'lvi-wabek.fi': 'LVI-WaBeK',
                    'climapri.fi': 'Climapri',
                    'climapri.com': 'Climapri',
                    'wcom-group.fi': 'Wcom Group'
                }
                
                sender_company = company_mapping.get(domain, domain.split('.')[0].title())
                
                # Extract name from email if not provided
                if not name_part:
                    email_user = email_part.split('@')[0]
                    # Convert email format to readable name (e.g., "john.doe" -> "John Doe")
                    if '.' in email_user:
                        name_parts = email_user.split('.')
                        sender_name = ' '.join(part.title() for part in name_parts)
                    else:
                        sender_name = email_user.title()
                else:
                    sender_name = name_part
            else:
                sender_name = "Käyttäjä"
                sender_company = "Tuntematon yritys"
            
            return sender_name, sender_company
            
        except Exception as e:
            self.logger.warning(f"Error parsing sender info: {e}")
            return "Käyttäjä", "Tuntematon yritys"
    
    def _extract_ai_response_text(self, response) -> Optional[str]:
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
            self.logger.warning(f"Error extracting AI response text: {e}")
            return None
    
    def _clean_email_address(self, email_address: str) -> str:
        """
        Clean email address to ensure valid Gmail API format.
        
        Handles formats like:
        - "Name" <email@domain.com> -> Name <email@domain.com>
        - Name <email@domain.com> -> Name <email@domain.com>
        - email@domain.com -> email@domain.com
        
        Also handles RFC 2047 encoding for non-ASCII characters in display names.
        
        Args:
            email_address: Raw email address string
            
        Returns:
            str: Cleaned email address with properly encoded non-ASCII characters
        """
        try:
            import re
            from email.header import Header
            from email.utils import parseaddr, formataddr
            
            # First remove problematic quotes
            # Pattern: "Name" <email> -> Name <email>
            # Also handle empty quotes: "" <email> -> <email>
            cleaned = re.sub(r'^"([^"]*)"\s*<', lambda m: f'{m.group(1).strip()} <' if m.group(1).strip() else '<', email_address.strip())
            
            # Parse the email address into name and address components
            name, addr = parseaddr(cleaned)
            
            # If there's a name with non-ASCII characters, encode it properly
            if name:
                try:
                    # Check if name contains non-ASCII characters
                    name.encode('ascii')
                    # If it's pure ASCII, use as-is
                    result = formataddr((name, addr))
                except UnicodeEncodeError:
                    # Name contains non-ASCII characters, need RFC 2047 encoding
                    # Use Header to properly encode the name part
                    encoded_name = Header(name, 'utf-8').encode()
                    # Format the address with the encoded name
                    result = f"{encoded_name} <{addr}>"
            else:
                # No name part, just return the address
                result = addr
            
            self.logger.debug(f"Email address cleaned: '{email_address}' -> '{result}'")
            return result
            
        except Exception as e:
            self.logger.warning(f"Error cleaning email address '{email_address}': {e}")
            # Fallback: try to extract just the email address part
            import re
            match = re.search(r'<([^>]+)>', email_address)
            if match:
                return match.group(1)
            return email_address.strip()
    
    async def send_classification_reply(self, recipient_email: str, suggested_reply: str, 
                                      email_data: Dict[str, Any]) -> bool:
        """
        Send a contextual reply for emails that don't require offer automation.
        
        Args:
            recipient_email: Email address to send to
            suggested_reply: The reply text to send
            email_data: Original email data
            
        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid - no user interaction needed!
        await self._ensure_valid_service()
        
        try:
            original_subject = email_data.get('subject', 'No Subject')
            
            # Create email content with Re: prefix
            reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
            
            # Create and send email
            message = MIMEText(suggested_reply, 'plain', 'utf-8')
            message['to'] = self._clean_email_address(recipient_email)
            message['from'] = self.sender_email
            message['subject'] = reply_subject
            
            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.logger.info(f"Sending classification reply to {recipient_email}")
            
            # Send the email with retry logic
            result = await self._send_with_retry({'raw': raw_message})
            
            self.logger.info(f"Classification reply sent successfully to {recipient_email}")
            self.logger.info(f"Gmail message ID: {result.get('id')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send classification reply: {e}")
            return False
    
    async def send_no_customer_found_notification(self, recipient_email: str, original_subject: str,
                                                 attempted_names: List[str], email_data: Dict = None) -> bool:
        """
        Send notification email when no customer is found in the database.

        Args:
            recipient_email: Email address to send to (sales person)
            original_subject: Subject of the original email
            attempted_names: List of company names that were attempted
            email_data: Original email data

        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid - no user interaction needed!
        await self._ensure_valid_service()

        try:
            # Format attempted names for display
            names_tried = ', '.join(f"'{name}'" for name in attempted_names if name)

            # Create email content
            subject = f"Asiakasta ei löytynyt - {original_subject[:50]}..."

            # Create helpful text body for sales person
            text_body = f"""
Hei,

Automaattinen tarjousjärjestelmä ei löytänyt asiakasta tietokannasta.

Yritetyt yritysnimet: {names_tried}

Toimenpiteet:
1. Varmista, että asiakkaan nimi on kirjoitettu oikein sähköpostissa
2. Lisää asiakkaan nimi tai asiakasnumero selkeästi viestiin
3. Jos asiakas on uusi, lisää se ensin Lemonsoftiin

Voit yrittää uudelleen lähettämällä sähköpostin, jossa mainitset selkeästi:
- Asiakkaan virallinen nimi (esim. "Yritys Oy")
- TAI asiakasnumero (esim. "Asiakasnumero: 123456")

Alkuperäinen viesti: {original_subject}
Lähettäjä: {email_data.get('sender', 'Unknown') if email_data else 'Unknown'}

Ystävällisin terveisin,
Automaattitarjousjärjestelmä
            """.strip()

            # Create email message
            message = MIMEText(text_body, 'plain', 'utf-8')
            message['to'] = self._clean_email_address(recipient_email)
            message['from'] = self.sender_email
            message['subject'] = subject

            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            self.logger.info(f"Sending no customer found notification to {recipient_email}")

            # Send the email with retry logic
            result = await self._send_with_retry({'raw': raw_message})

            self.logger.info(f"No customer found notification sent successfully to {recipient_email}")
            self.logger.info(f"Gmail message ID: {result.get('id')}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send no customer found notification: {e}")
            return False

    async def send_offer_error_notification(self, recipient_email: str, error_details: Dict,
                                          customer_details: Dict = None,
                                          original_email_data: Dict = None) -> bool:
        """
        Send error notification email when offer creation fails.

        Args:
            recipient_email: Email address to send to
            error_details: Details about the error that occurred
            customer_details: Customer information if available
            original_email_data: Original email that triggered the offer

        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid - no user interaction needed!
        await self._ensure_valid_service()

        try:
            # Create email content
            error_type = error_details.get('error_type', 'Unknown Error')
            error_message = error_details.get('error_message', 'No details available')
            customer_name = customer_details.get('name', 'Unknown Customer') if customer_details else 'Unknown Customer'

            subject = f"Tarjouksen luonti epäonnistui - {customer_name}"

            # Create simple text body for error notification
            text_body = f"""
Hei / Hello,

Automaattisen tarjouksen luonti epäonnistui.
The automatic offer creation failed.

Asiakas / Customer: {customer_name}
Virhetyyppi / Error Type: {error_type}
Virheilmoitus / Error Message: {error_message}

Toimenpiteet / Actions needed:
1. Tarkista asiakkaan tiedot / Check customer details
2. Luo tarjous manuaalisesti / Create offer manually
3. Ota yhteyttä järjestelmän ylläpitoon / Contact system admin

Ystävällisin terveisin / Best regards,
Automaattitarjousjärjestelmä / Automatic Offer System
            """.strip()

            # Create email message
            message = MIMEText(text_body, 'plain', 'utf-8')
            message['to'] = self._clean_email_address(recipient_email)
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email with retry logic
            result = await self._send_with_retry({'raw': raw_message})
            
            self.logger.info(f"Error notification email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send error notification email: {e}")
            return False