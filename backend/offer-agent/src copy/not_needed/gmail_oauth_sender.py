"""
Gmail Email Sender with OAuth2 User Authentication
Sends emails using Gmail API with OAuth2 for personal Gmail accounts.
"""

import os
import base64
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import get_logger
from src.utils.exceptions import EmailSenderError
from src.notifications.pdf_generator import OfferConfirmationPDFGenerator


class GmailOAuthSender:
    """Gmail email sender using OAuth2 user authentication."""
    
    # Gmail API scopes for sending
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self):
        """Initialize Gmail OAuth sender."""
        self.logger = get_logger(__name__)
        self.service = None
        self.credentials = None
        self.sender_email = os.getenv('MONITORED_EMAIL', 'ai.tarjous.wcom@gmail.com')
        
        # OAuth2 files
        self.token_file = Path('config/gmail_token.pickle')
        self.credentials_file = Path('config/gmail_oauth_credentials.json')
        
        # PDF generator
        self.pdf_generator = OfferConfirmationPDFGenerator()
    
    async def initialize(self):
        """Initialize Gmail API service with OAuth2 authentication."""
        try:
            # Load existing credentials
            if self.token_file.exists():
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If no valid credentials, get them
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Try to refresh expired credentials
                    self.logger.info("Refreshing expired Gmail credentials...")
                    try:
                        self.credentials.refresh(Request())
                        self.logger.info("Gmail credentials refreshed successfully")
                    except Exception as refresh_error:
                        self.logger.warning(f"Failed to refresh Gmail credentials: {refresh_error}")
                        self.logger.info("Refresh token likely expired/revoked, starting fresh OAuth flow...")
                        
                        # Clear expired credentials and token file
                        self.credentials = None
                        if self.token_file.exists():
                            try:
                                self.token_file.unlink()
                                self.logger.info("Removed expired token file")
                            except Exception as e:
                                self.logger.warning(f"Could not remove token file: {e}")
                        
                        # Run fresh OAuth2 flow
                        await self._run_oauth_flow()
                else:
                    # Run OAuth2 flow
                    await self._run_oauth_flow()
                
                # Save credentials for next time
                self._save_credentials()
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            self.logger.info(f"Gmail OAuth sender initialized with email: {self.sender_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail OAuth sender: {e}")
            raise EmailSenderError(f"Gmail OAuth sender initialization failed: {str(e)}")
    
    async def _run_oauth_flow(self):
        """Run OAuth2 flow to get user credentials."""
        if not self.credentials_file.exists():
            raise EmailSenderError(
                f"OAuth2 credentials file not found: {self.credentials_file}\n"
                "Please download OAuth2 client credentials from Google Cloud Console\n"
                "and save as config/gmail_oauth_credentials.json"
            )
        
        self.logger.info("Starting OAuth2 flow for Gmail sending...")
        print("\n[GMAIL AUTH] Gmail Authorization Required for Sending")
        print("A web browser will open for you to authorize Gmail sending access.")
        print("This is a one-time setup process.")
        
        # Run OAuth2 flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_file), 
            self.SCOPES
        )
        
        # Use local server for callback with proper settings for long-lived tokens
        self.credentials = flow.run_local_server(
            port=0,
            access_type='offline',  # Critical for refresh tokens
            prompt='consent'        # Forces new refresh token generation
        )
        
        print("[SUCCESS] Gmail sending authorization completed successfully!")
        self.logger.info("OAuth2 flow for sending completed successfully")
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            # Ensure config directory exists
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            self.logger.debug("Gmail credentials saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save Gmail credentials: {e}")
    
    async def _ensure_valid_service(self):
        """Ensure Gmail service is valid and refresh if needed."""
        try:
            # If no service or credentials, initialize
            if not self.service or not self.credentials:
                self.logger.info("No Gmail service found, initializing...")
                await self.initialize()
                return
            
            # Check if credentials are expired and can be refreshed
            if self.credentials.expired and self.credentials.refresh_token:
                self.logger.info("Gmail credentials expired, attempting refresh...")
                try:
                    self.credentials.refresh(Request())
                    self._save_credentials()
                    # Rebuild service with refreshed credentials
                    self.service = build('gmail', 'v1', credentials=self.credentials)
                    self.logger.info("Gmail credentials refreshed successfully")
                    return
                except Exception as refresh_error:
                    self.logger.warning(f"Failed to refresh Gmail credentials: {refresh_error}")
                    self.logger.info("Refresh token likely expired/revoked, clearing stored credentials...")
                    
                    # Clear expired credentials and token file
                    self.credentials = None
                    self.service = None
                    if self.token_file.exists():
                        try:
                            self.token_file.unlink()
                            self.logger.info("Removed expired token file")
                        except Exception as e:
                            self.logger.warning(f"Could not remove token file: {e}")
                    
                    # Force fresh OAuth flow
                    self.logger.info("Starting fresh OAuth flow...")
                    await self._run_oauth_flow()
                    
                    # Save new credentials and build service
                    self._save_credentials()
                    self.service = build('gmail', 'v1', credentials=self.credentials)
                    self.logger.info("Fresh Gmail OAuth flow completed successfully")
                    return
            
            # Check if credentials are still invalid after refresh attempt
            elif not self.credentials.valid:
                self.logger.warning("Gmail credentials are invalid, starting fresh OAuth flow...")
                
                # Clear invalid credentials
                self.credentials = None
                self.service = None
                if self.token_file.exists():
                    try:
                        self.token_file.unlink()
                        self.logger.info("Removed invalid token file")
                    except Exception as e:
                        self.logger.warning(f"Could not remove token file: {e}")
                
                # Force fresh OAuth flow
                await self._run_oauth_flow()
                self._save_credentials()
                self.service = build('gmail', 'v1', credentials=self.credentials)
                self.logger.info("Fresh Gmail OAuth flow completed successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure valid Gmail service: {e}")
            raise EmailSenderError(f"Gmail service validation failed: {str(e)}")
    
    async def send_offer_confirmation(self, recipient_email: str, offer_details: Dict, 
                                     customer_details: Dict, product_matches: List[Dict],
                                     pricing_details: Dict, verification_results: Dict = None,
                                     original_email_data: Dict = None, credit_warning: str = None) -> bool:
        """
        Send offer confirmation email using OAuth2 Gmail API.
        
        Args:
            recipient_email: Email address to send to
            offer_details: Offer information
            customer_details: Customer information  
            product_matches: List of matched products
            pricing_details: Pricing information
            verification_results: Offer verification results
            original_email_data: Original email that triggered the offer
            credit_warning: Credit warning message if applicable
            
        Returns:
            bool: True if email sent successfully
        """
        # Ensure service is valid and refresh token if needed
        await self._ensure_valid_service()
        
        try:
            # Create email content
            subject = f"✅ Automaattitarjous luotu: {offer_details.get('offer_number')} - {customer_details.get('name', 'Asiakas')}"
            
            # Generate PDF attachment
            pdf_bytes = self.pdf_generator.generate_offer_confirmation_pdf(
                offer_details, customer_details, product_matches,
                pricing_details, verification_results, original_email_data, credit_warning
            )
            pdf_filename = self.pdf_generator.generate_filename(offer_details, customer_details)
            
            # Create email message with attachment
            message = MIMEMultipart('mixed')
            message['to'] = recipient_email
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Create simple text body referencing the PDF
            text_body = f"""
Hei / Hello,

Automaattisesti luotu tarjous on valmiina liitteenä PDF-tiedostona.
The automatically generated offer is ready as a PDF attachment.

Tarjous / Offer: {offer_details.get('offer_number', 'PENDING')}
Asiakas / Customer: {customer_details.get('name', 'N/A')}
Tuotteiden määrä / Products: {len(product_matches)}

{credit_warning if credit_warning else ''}

Ystävällisin terveisin / Best regards,
Automaattitarjousjärjestelmä / Automatic Offer System
            """.strip()
            
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            message.attach(text_part)
            
            # Attach PDF
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(pdf_bytes)
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
            message.attach(pdf_attachment)
            
            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email with retry logic for SSL errors
            import ssl
            import time
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    result = self.service.users().messages().send(
                        userId='me',
                        body={'raw': raw_message}
                    ).execute()
                    
                    self.logger.info(f"Offer confirmation email with PDF attachment sent successfully to {recipient_email}")
                    self.logger.info(f"Gmail message ID: {result.get('id')}, PDF filename: {pdf_filename}")
                    
                    return True
                    
                except (ssl.SSLEOFError, ssl.SSLError) as ssl_error:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"SSL error on attempt {attempt + 1}, retrying in {retry_delay} seconds: {ssl_error}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        # Recreate the service connection on SSL errors
                        try:
                            from googleapiclient.discovery import build
                            self.service = build('gmail', 'v1', credentials=self.credentials)
                            self.logger.info("Recreated Gmail service connection after SSL error")
                        except Exception as rebuild_error:
                            self.logger.error(f"Failed to rebuild Gmail service: {rebuild_error}")
                    else:
                        raise
            
        except HttpError as e:
            self.logger.error(f"Gmail API error sending email: {e}")
            raise EmailSenderError(f"Failed to send email via Gmail API: {str(e)}")
        except (ssl.SSLEOFError, ssl.SSLError) as ssl_error:
            self.logger.error(f"SSL error after {max_retries} retries: {ssl_error}")
            raise EmailSenderError(f"SSL error sending email after {max_retries} retries: {str(ssl_error)}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {e}")
            raise EmailSenderError(f"Failed to send email: {str(e)}")
    
    def _create_offer_confirmation_html(self, offer_details: Dict, customer_details: Dict,
                                       product_matches: List[Dict], pricing_details: Dict,
                                       verification_results: Dict = None, original_email_data: Dict = None,
                                       credit_warning: str = None) -> str:
        """Create HTML email body for offer confirmation."""
        
        offer_number = offer_details.get('offer_number', 'N/A')
        customer_name = customer_details.get('name', 'Tuntematon asiakas')
        net_total = pricing_details.get('net_total', 0)
        total_amount = pricing_details.get('total_amount', 0)
        vat_amount = pricing_details.get('vat_amount', 0)
        
        # Credit warning section with theme colors
        credit_section = ""
        if credit_warning:
            credit_section = f"""
            <div style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.15) 0%, rgba(230, 126, 0, 0.05) 100%); border: 1px solid rgba(255, 152, 0, 0.3); border-radius: 8px; padding: 20px; margin: 16px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 4px; height: 32px; background-color: rgb(255, 152, 0); border-radius: 2px; margin-right: 12px;"></div>
                    <h3 style="margin: 0; color: rgb(230, 126, 0); font-size: 18px; font-weight: 600;">⚠️ HUOMIO - LUOTTOKIELTO</h3>
                </div>
                <div style="padding: 16px; background-color: rgba(255, 152, 0, 0.1); border-radius: 6px; border-left: 4px solid rgb(255, 152, 0);">
                    <p style="margin: 0; color: rgb(230, 126, 0); font-size: 16px; font-weight: 600; line-height: 1.4;">{credit_warning}</p>
                </div>
            </div>
            """
        
        # Product list
        product_rows = ""
        for i, product in enumerate(product_matches, 1):
            product_code = product.get('product_code', 'N/A')
            product_name = product.get('product_name', 'Tuntematon tuote')
            quantity = product.get('quantity', 1)
            match_method = product.get('match_method', 'unknown')
            discount_method = product.get('discount_method', 'Listahinta')
            discount_percent = product.get('discount_percent', 0)
            line_total = product.get('line_total', 0)
            
            # Color code match method
            match_color = "#d4edda" if match_method == "direct" else "#fff3cd"
            
            # Modern row styling with theme colors
            row_bg = "rgba(83, 171, 32, 0.05)" if match_color == "#d4edda" else "rgba(255, 152, 0, 0.05)"
            border_style = "border-bottom: 1px solid rgb(228, 228, 227);" if i < len(product_matches) else ""
            
            product_rows += f"""
            <tr style="background-color: {row_bg}; {border_style}">
                <td style="padding: 12px 16px; font-size: 14px; color: rgba(0, 0, 0, 0.87); font-weight: 500;">#{i}</td>
                <td style="padding: 12px 16px; font-size: 14px; color: rgba(0, 0, 0, 0.87); font-family: 'Courier New', monospace; font-weight: 500;">{product_code}</td>
                <td style="padding: 12px 16px; font-size: 14px; color: rgba(0, 0, 0, 0.87);">{product_name}</td>
                <td style="padding: 12px 16px; font-size: 14px; color: rgba(0, 0, 0, 0.87); text-align: center; font-weight: 500;">{quantity}</td>
                <td style="padding: 12px 16px; font-size: 12px; color: rgba(0, 0, 0, 0.6);">
                    {f'<span style="background-color: rgba(83, 171, 32, 0.1); color: rgb(56, 142, 60); padding: 2px 6px; border-radius: 4px; font-weight: 500;">✓ {match_method}</span>' if match_color == "#d4edda" else f'<span style="background-color: rgba(255, 152, 0, 0.1); color: rgb(230, 126, 0); padding: 2px 6px; border-radius: 4px; font-weight: 500;">⚠ {match_method}</span>'}
                </td>
                <td style="padding: 12px 16px; font-size: 12px; color: rgba(0, 0, 0, 0.6);">{discount_method}</td>
                <td style="padding: 12px 16px; font-size: 14px; color: rgba(0, 0, 0, 0.87); text-align: center; font-weight: 500;">{discount_percent:.1f}%</td>
                <td style="padding: 12px 16px; font-size: 14px; color: rgb(203, 20, 20); text-align: right; font-weight: 600;">€{line_total:.2f}</td>
            </tr>
            """
        
        # Verification section with theme colors
        verification_section = ""
        if verification_results and not verification_results.get('success'):
            issues = verification_results.get('issues', [])
            verification_section = f"""
            <div style="background: linear-gradient(135deg, rgba(203, 20, 20, 0.1) 0%, rgba(153, 15, 15, 0.05) 100%); border: 1px solid rgba(203, 20, 20, 0.2); border-radius: 8px; padding: 20px; margin: 16px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 16px;">
                    <div style="width: 4px; height: 32px; background-color: rgb(203, 20, 20); border-radius: 2px; margin-right: 12px;"></div>
                    <h3 style="margin: 0; color: rgb(203, 20, 20); font-size: 18px; font-weight: 500;">⚠️ Tarjouksen varmennuksessa havaittiin ongelmia</h3>
                </div>
                <ul style="color: rgb(153, 15, 15); margin: 0; padding-left: 20px; line-height: 1.6;">
                    {''.join([f"<li style='margin-bottom: 8px; font-weight: 500;'>{issue}</li>" for issue in issues])}
                </ul>
                <div style="margin-top: 16px; padding: 12px; background-color: rgba(203, 20, 20, 0.05); border-radius: 6px; border-left: 4px solid rgb(203, 20, 20);">
                    <p style="margin: 0; font-size: 14px; color: rgb(153, 15, 15); font-weight: 500;">💡 Tarkista tarjous Lemonsoftista ennen lähettämistä asiakkaalle.</p>
                </div>
            </div>
            """
        
        # Original email section with theme colors
        original_email_section = ""
        if original_email_data:
            original_subject = original_email_data.get('subject', 'N/A')
            original_sender = original_email_data.get('sender', 'N/A')
            original_email_section = f"""
            <div style="background-color: #ffffff; border: 1px solid rgb(228, 228, 227); border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 4px; height: 24px; background-color: rgba(0, 0, 0, 0.12); border-radius: 2px; margin-right: 12px;"></div>
                    <h4 style="margin: 0; color: rgba(0, 0, 0, 0.87); font-size: 16px; font-weight: 500;">📧 Alkuperäinen sähköposti</h4>
                </div>
                <div style="display: grid; gap: 8px;">
                    <div>
                        <span style="font-size: 12px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">AIHE:</span>
                        <p style="margin: 2px 0 0 0; font-size: 14px; color: rgba(0, 0, 0, 0.87);">{original_subject}</p>
                    </div>
                    <div>
                        <span style="font-size: 12px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">LÄHETTÄJÄ:</span>
                        <p style="margin: 2px 0 0 0; font-size: 14px; color: rgba(0, 0, 0, 0.87);">{original_sender}</p>
                    </div>
                </div>
            </div>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="fi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Automaattitarjous luotu</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 0; background-color: #fafafa;">
            <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, rgb(203, 20, 20) 0%, rgb(153, 15, 15) 100%); color: #ffffff; padding: 24px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 500; text-shadow: 0 1px 2px rgba(0,0,0,0.2);">✅ Automaattitarjous luotu onnistuneesti</h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 16px;">Tarjous on valmis tarkistettavaksi Lemonsoftissa</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 24px;">
                    {credit_section}
                    
                    <!-- Offer Details Card -->
                    <div style="background-color: #ffffff; border: 1px solid rgb(228, 228, 227); border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; margin-bottom: 16px;">
                            <div style="width: 4px; height: 32px; background-color: rgb(203, 20, 20); border-radius: 2px; margin-right: 12px;"></div>
                            <h3 style="margin: 0; color: rgb(203, 20, 20); font-size: 20px; font-weight: 500;">📋 Tarjouksen tiedot</h3>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                            <div>
                                <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">TARJOUSNUMERO</p>
                                <p style="margin: 0; font-size: 18px; font-weight: 500; color: rgb(203, 20, 20);">{offer_number}</p>
                            </div>
                            <div>
                                <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">ASIAKAS</p>
                                <p style="margin: 0; font-size: 16px; color: rgba(0, 0, 0, 0.87);">{customer_name}</p>
                            </div>
                            <div>
                                <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">LUOTU</p>
                                <p style="margin: 0; font-size: 16px; color: rgba(0, 0, 0, 0.87);">{offer_details.get('created_at', 'N/A')}</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Pricing Summary Card -->
                    <div style="background: linear-gradient(135deg, rgb(83, 171, 32) 0%, rgb(56, 142, 60) 100%); color: #ffffff; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h3 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 500;">💰 Hinnoittelu</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                            <div style="text-align: center; padding: 12px; background-color: rgba(255,255,255,0.1); border-radius: 6px;">
                                <p style="margin: 0 0 4px 0; font-size: 14px; opacity: 0.9;">Netto</p>
                                <p style="margin: 0; font-size: 20px; font-weight: 500;">€{net_total:.2f}</p>
                            </div>
                            <div style="text-align: center; padding: 12px; background-color: rgba(255,255,255,0.1); border-radius: 6px;">
                                <p style="margin: 0 0 4px 0; font-size: 14px; opacity: 0.9;">ALV</p>
                                <p style="margin: 0; font-size: 20px; font-weight: 500;">€{vat_amount:.2f}</p>
                            </div>
                            <div style="text-align: center; padding: 12px; background-color: rgba(255,255,255,0.2); border-radius: 6px; border: 2px solid rgba(255,255,255,0.3);">
                                <p style="margin: 0 0 4px 0; font-size: 14px; font-weight: 500;">Yhteensä</p>
                                <p style="margin: 0; font-size: 24px; font-weight: 600;">€{total_amount:.2f}</p>
                            </div>
                            <div style="text-align: center; padding: 12px; background-color: rgba(255,255,255,0.1); border-radius: 6px;">
                                <p style="margin: 0 0 4px 0; font-size: 14px; opacity: 0.9;">Tuotteita</p>
                                <p style="margin: 0; font-size: 20px; font-weight: 500;">{len(product_matches)} kpl</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Products Table -->
                    <div style="background-color: #ffffff; border: 1px solid rgb(228, 228, 227); border-radius: 8px; margin: 16px 0; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="padding: 20px 20px 0 20px;">
                            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                                <div style="width: 4px; height: 32px; background-color: rgb(203, 20, 20); border-radius: 2px; margin-right: 12px;"></div>
                                <h3 style="margin: 0; color: rgb(203, 20, 20); font-size: 20px; font-weight: 500;">🛍️ Tuotteet ja hinnoittelu</h3>
                            </div>
                        </div>
                        
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="background-color: #f5f5f5; border-bottom: 1px solid rgb(228, 228, 227);">
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">#</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Koodi</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Tuote</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Määrä</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Tunnistus</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Alennussääntö</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Alennus</th>
                                        <th style="padding: 12px 16px; text-align: left; font-size: 14px; font-weight: 600; color: rgba(0, 0, 0, 0.6);">Yhteensä</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {product_rows}
                                </tbody>
                            </table>
                        </div>
                        
                        <div style="padding: 16px 20px; background-color: #fafafa; border-top: 1px solid rgb(228, 228, 227);">
                            <div style="font-size: 12px; color: rgba(0, 0, 0, 0.6);">
                                <strong style="color: rgba(0, 0, 0, 0.87);">Värikoodit:</strong>
                                <span style="background-color: rgba(83, 171, 32, 0.1); color: rgb(56, 142, 60); padding: 4px 8px; border-radius: 4px; margin-left: 8px; font-weight: 500;">✓ Suora osuma</span>
                                <span style="background-color: rgba(255, 152, 0, 0.1); color: rgb(230, 126, 0); padding: 4px 8px; border-radius: 4px; margin-left: 8px; font-weight: 500;">⚠ Epäselvä termi</span>
                            </div>
                        </div>
                    </div>
                    
                    {verification_section}
                    
                    {original_email_section}
                    
                    <!-- Next Steps Card -->
                    <div style="background: linear-gradient(135deg, rgba(83, 171, 32, 0.1) 0%, rgba(56, 142, 60, 0.05) 100%); border: 1px solid rgba(83, 171, 32, 0.2); border-radius: 8px; padding: 20px; margin: 24px 0;">
                        <div style="display: flex; align-items: center; margin-bottom: 16px;">
                            <div style="width: 4px; height: 32px; background-color: rgb(83, 171, 32); border-radius: 2px; margin-right: 12px;"></div>
                            <h3 style="margin: 0; color: rgb(56, 142, 60); font-size: 20px; font-weight: 500;">✅ Seuraavat vaiheet</h3>
                        </div>
                        <ol style="color: rgb(56, 142, 60); margin: 0; padding-left: 20px; line-height: 1.6;">
                            <li style="margin-bottom: 8px; font-weight: 500;">Avaa tarjous Lemonsoftista ja tarkista tiedot</li>
                            <li style="margin-bottom: 8px; font-weight: 500;">Muokkaa tarvittaessa manuaalisesti</li>
                            <li style="margin-bottom: 0; font-weight: 500;">Lähetä tarjous asiakkaalle</li>
                        </ol>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f5f5f5; border-top: 1px solid rgb(228, 228, 227); padding: 20px; text-align: center;">
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: rgba(0, 0, 0, 0.6);">Tämä on automaattisesti luotu viesti tarjousautomaatiojärjestelmästä.</p>
                    <p style="margin: 0; font-size: 12px; color: rgba(0, 0, 0, 0.87); font-weight: 500;">⚠️ Tarkista aina tarjouksen tiedot ennen lähettämistä asiakkaalle.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body 
    
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
        # Ensure service is valid and refresh token if needed
        await self._ensure_valid_service()
        
        try:
            # Create email content
            error_type = error_details.get('error_type', 'Unknown Error')
            error_message = error_details.get('error_message', 'No details available')
            customer_name = customer_details.get('name', 'Unknown Customer') if customer_details else 'Unknown Customer'
            
            subject = f"❌ Tarjouksen luonti epäonnistui - {customer_name}"
            
            # Create HTML email body
            html_body = self._create_error_notification_html(
                error_details, customer_details, original_email_data
            )
            
            # Create email message
            message = MIMEMultipart('alternative')
            message['to'] = recipient_email
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"Error notification email sent successfully to {recipient_email}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Gmail API error sending error notification: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending error notification: {e}", exc_info=True)
            return False
    
    def _create_error_notification_html(self, error_details: Dict, customer_details: Dict = None, 
                                       original_email_data: Dict = None) -> str:
        """Create HTML content for error notification email."""
        error_type = error_details.get('error_type', 'Unknown Error')
        error_message = error_details.get('error_message', 'No details available')
        customer_name = customer_details.get('name', 'Unknown Customer') if customer_details else 'Unknown Customer'
        
        # Error-specific sections with theme colors
        error_section = f"""
        <div style="background: linear-gradient(135deg, rgba(203, 20, 20, 0.1) 0%, rgba(153, 15, 15, 0.05) 100%); border: 1px solid rgba(203, 20, 20, 0.2); border-radius: 8px; padding: 20px; margin: 16px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 4px; height: 32px; background-color: rgb(203, 20, 20); border-radius: 2px; margin-right: 12px;"></div>
                <h3 style="margin: 0; color: rgb(203, 20, 20); font-size: 20px; font-weight: 500;">🚨 Virhetiedot</h3>
            </div>
            <div style="display: grid; gap: 12px;">
                <div>
                    <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">VIRHETYYPPI</p>
                    <p style="margin: 0; font-size: 16px; color: rgb(153, 15, 15); font-weight: 500;">{error_type}</p>
                </div>
                <div>
                    <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">VIRHEILMOITUS</p>
                    <p style="margin: 0; font-size: 14px; color: rgba(0, 0, 0, 0.87); line-height: 1.4;">{error_message}</p>
                </div>
            </div>
        </div>
        """
        
        # Customer details section with theme colors
        customer_section = ""
        if customer_details:
            customer_section = f"""
            <div style="background-color: #ffffff; border: 1px solid rgb(228, 228, 227); border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; margin-bottom: 16px;">
                    <div style="width: 4px; height: 32px; background-color: rgba(0, 0, 0, 0.12); border-radius: 2px; margin-right: 12px;"></div>
                    <h3 style="margin: 0; color: rgba(0, 0, 0, 0.87); font-size: 20px; font-weight: 500;">👤 Asiakkaan tiedot</h3>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                    <div>
                        <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">NIMI</p>
                        <p style="margin: 0; font-size: 16px; color: rgba(0, 0, 0, 0.87);">{customer_details.get('name', 'N/A')}</p>
                    </div>
                    <div>
                        <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">ASIAKASNUMERO</p>
                        <p style="margin: 0; font-size: 16px; color: rgba(0, 0, 0, 0.87);">{customer_details.get('number', 'N/A')}</p>
                    </div>
                    <div>
                        <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">KAUPUNKI</p>
                        <p style="margin: 0; font-size: 16px; color: rgba(0, 0, 0, 0.87);">{customer_details.get('city', 'N/A')}</p>
                    </div>
                </div>
            </div>
            """
        
        # Detailed error information for insufficient rows
        detailed_error_section = ""
        if error_details.get('context', {}).get('insufficient_rows'):
            details = error_details.get('context', {}).get('error_details', {})
            successful_rows = details.get('successful_rows', 0)
            total_attempted = details.get('total_products_attempted', 0)
            row_errors = details.get('row_errors', [])
            
            error_list = ""
            if row_errors:
                error_list = "<ul style='color: rgb(230, 126, 0); margin: 0; padding-left: 20px; line-height: 1.6;'>"
                for error in row_errors[:10]:  # Limit to first 10 errors
                    error_list += f"<li style='margin-bottom: 6px; font-size: 14px;'>{error}</li>"
                if len(row_errors) > 10:
                    error_list += f"<li style='margin-bottom: 0; font-size: 14px; font-style: italic;'>... ja {len(row_errors) - 10} muuta virhettä</li>"
                error_list += "</ul>"
            
            detailed_error_section = f"""
            <div style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(230, 126, 0, 0.05) 100%); border: 1px solid rgba(255, 152, 0, 0.2); border-radius: 8px; padding: 20px; margin: 16px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 16px;">
                    <div style="width: 4px; height: 32px; background-color: rgb(255, 152, 0); border-radius: 2px; margin-right: 12px;"></div>
                    <h3 style="margin: 0; color: rgb(230, 126, 0); font-size: 20px; font-weight: 500;">📊 Virheen yksityiskohdat</h3>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                    <div style="text-align: center; padding: 12px; background-color: rgba(203, 20, 20, 0.1); border-radius: 6px;">
                        <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6);">Onnistuneet rivit</p>
                        <p style="margin: 0; font-size: 24px; font-weight: 600; color: rgb(203, 20, 20);">{successful_rows}</p>
                    </div>
                    <div style="text-align: center; padding: 12px; background-color: rgba(255, 152, 0, 0.1); border-radius: 6px;">
                        <p style="margin: 0 0 4px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6);">Yritetyt tuotteet</p>
                        <p style="margin: 0; font-size: 24px; font-weight: 600; color: rgb(230, 126, 0);">{total_attempted}</p>
                    </div>
                </div>
                {f'''<div style="background-color: rgba(255, 152, 0, 0.05); border-radius: 6px; padding: 16px;">
                    <p style="margin: 0 0 12px 0; font-size: 14px; color: rgba(0, 0, 0, 0.6); font-weight: 500;">EPÄONNISTUNEET TUOTERIVIT:</p>
                    {error_list}
                </div>''' if error_list else ''}
            </div>
            """
        
        # Original email section
        original_email_section = ""
        if original_email_data:
            original_subject = original_email_data.get('subject', 'N/A')
            original_sender = original_email_data.get('sender', 'N/A')
            original_email_section = f"""
            <div style="background-color: #f8f9fa; border-radius: 4px; padding: 12px; margin: 16px 0;">
                <strong>📧 Alkuperäinen sähköposti:</strong><br>
                <strong>Aihe:</strong> {original_subject}<br>
                <strong>Lähettäjä:</strong> {original_sender}
            </div>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="fi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tarjouksen luonti epäonnistui</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 0; background-color: #fafafa;">
            <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, rgb(203, 20, 20) 0%, rgb(153, 15, 15) 100%); color: #ffffff; padding: 24px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 500; text-shadow: 0 1px 2px rgba(0,0,0,0.2);">❌ Tarjouksen luonti epäonnistui</h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 16px;">Automaattinen tarjouksen luonti ei onnistunut</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 24px;">
                    <!-- Customer Info -->
                    <div style="background-color: #ffffff; border: 1px solid rgb(228, 228, 227); border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <p style="margin: 0; font-size: 16px; color: rgba(0, 0, 0, 0.87); line-height: 1.5;">
                            Automaattinen tarjouksen luonti epäonnistui seuraavan asiakkaan osalta: 
                            <strong style="color: rgb(203, 20, 20);">{customer_name}</strong>
                        </p>
                    </div>
                    
                    {error_section}
                    
                    {detailed_error_section}
                    
                    {customer_section}
                    
                    {original_email_section}
                    
                    <!-- Recommended Actions Card -->
                    <div style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(230, 126, 0, 0.05) 100%); border: 1px solid rgba(255, 152, 0, 0.2); border-radius: 8px; padding: 20px; margin: 24px 0;">
                        <div style="display: flex; align-items: center; margin-bottom: 16px;">
                            <div style="width: 4px; height: 32px; background-color: rgb(255, 152, 0); border-radius: 2px; margin-right: 12px;"></div>
                            <h3 style="margin: 0; color: rgb(230, 126, 0); font-size: 20px; font-weight: 500;">🔧 Suositellut toimenpiteet</h3>
                        </div>
                        <ol style="color: rgb(230, 126, 0); margin: 0; padding-left: 20px; line-height: 1.6;">
                            <li style="margin-bottom: 8px; font-weight: 500;">Tarkista asiakkaan tiedot ja tuotteiden saatavuus</li>
                            <li style="margin-bottom: 8px; font-weight: 500;">Luo tarjous manuaalisesti Lemonsoftissa</li>
                            <li style="margin-bottom: 0; font-weight: 500;">Ota yhteyttä järjestelmän ylläpitoon jos ongelma toistuu</li>
                        </ol>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f5f5f5; border-top: 1px solid rgb(228, 228, 227); padding: 20px; text-align: center;">
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: rgba(0, 0, 0, 0.6);">Tämä on automaattisesti luotu virheilmoitus tarjousautomaatiojärjestelmästä.</p>
                    <p style="margin: 0; font-size: 12px; color: rgba(0, 0, 0, 0.87); font-weight: 500;">🕒 Aikaleima: {error_details.get('timestamp', 'N/A')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body