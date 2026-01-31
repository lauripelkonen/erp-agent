"""
Email notification service for sending confirmation emails via Gmail API
"""

import os
import base64
import logging
from typing import Dict, Any, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class EmailSenderError(BaseOfferAutomationError):
    """Email sending related errors."""
    pass


class GmailSender:
    """Gmail API email sender with service account authentication."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.service = None
        self.sender_email = os.getenv('MONITORED_EMAIL', 'ai.tarjous.wcom@gmail.com')
        self.delegated_email = os.getenv('GMAIL_DELEGATED_EMAIL')
        
    async def initialize(self):
        """Initialize Gmail API service with service account credentials."""
        try:
            service_account_path = os.getenv('GMAIL_SERVICE_ACCOUNT_FILE')
            if not service_account_path or not os.path.exists(service_account_path):
                raise EmailSenderError(f"Gmail service account file not found: {service_account_path}")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=self.SCOPES
            )
            
            # Enable domain-wide delegation if needed
            if self.delegated_email and hasattr(credentials, 'with_subject'):
                credentials = credentials.with_subject(self.delegated_email)
                self.logger.info(f"Using domain-wide delegation for email: {self.delegated_email}")
            elif hasattr(credentials, 'with_subject'):
                credentials = credentials.with_subject(self.sender_email)
                self.logger.info(f"Using service account email: {self.sender_email}")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=credentials)
            
            self.logger.info(f"Gmail sender initialized with email: {self.sender_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail sender: {e}")
            raise EmailSenderError(f"Gmail initialization failed: {str(e)}")
    
    async def send_offer_confirmation(
        self,
        recipient_email: str,
        offer_details: Dict[str, Any],
        customer_details: Dict[str, Any],
        product_matches: List[Dict[str, Any]],
        pricing_details: Dict[str, Any],
        verification_results: Dict[str, Any] = None,
        original_email_data: Dict[str, Any] = None,
        credit_warning: str = None
    ) -> bool:
        """
        Send offer confirmation email to the salesperson.
        
        Args:
            recipient_email: Email of the salesperson who forwarded the request
            offer_details: Created offer information
            customer_details: Customer information
            product_matches: List of matched products with success status
            pricing_details: Pricing information including discount methods
            verification_results: Results of verification process
            original_email_data: Original email data for reference
            credit_warning: Warning message if customer has credit denial
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.service:
                await self.initialize()
            
            # Generate email content
            subject = self._generate_subject(offer_details, customer_details, credit_warning)
            html_body = self._generate_html_body(
                offer_details, customer_details, product_matches, 
                pricing_details, verification_results, original_email_data, credit_warning
            )
            
            # Create and send email
            message = self._create_message(recipient_email, subject, html_body)
            await self._send_message(message)
            
            self.logger.info(f"Offer confirmation email sent to {recipient_email} for offer {offer_details.get('offer_number')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send offer confirmation email: {e}")
            return False
    
    def _generate_subject(self, offer_details: Dict, customer_details: Dict, credit_warning: str = None) -> str:
        """Generate email subject line."""
        offer_number = offer_details.get('offer_number', 'N/A')
        customer_name = customer_details.get('name', 'Unknown Customer')
        
        base_subject = f"Tarjous {offer_number} valmis asiakkaalle {customer_name}"
        
        # Add credit warning to subject if present
        if credit_warning:
            return f"⚠️ LUOTTOKIELTO - {base_subject}"
        
        return base_subject
    
    def _generate_html_body(
        self,
        offer_details: Dict[str, Any],
        customer_details: Dict[str, Any],
        product_matches: List[Dict[str, Any]],
        pricing_details: Dict[str, Any],
        verification_results: Dict[str, Any] = None,
        original_email_data: Dict[str, Any] = None,
        credit_warning: str = None
    ) -> str:
        """Generate HTML email body with offer confirmation details."""
        
        # Extract key information
        offer_number = offer_details.get('offer_number', 'N/A')
        customer_number = customer_details.get('number', customer_details.get('id', 'N/A'))
        customer_name = customer_details.get('name', 'Unknown Customer')
        total_rows = len(product_matches)
        total_price = pricing_details.get('net_total', 0.0)
        
        # Calculate successful matches (not fallback method)
        successful_matches = [
            match for match in product_matches 
            if match.get('match_method') != 'fallback'
        ]
        successful_count = len(successful_matches)
        success_percentage = (successful_count / total_rows * 100) if total_rows > 0 else 0
        
        # Generate product match table
        product_table = self._generate_product_table(product_matches)
        
        # Generate discount methods summary
        discount_summary = self._generate_discount_summary(pricing_details)
        
        # Original email details
        original_subject = original_email_data.get('subject', 'N/A')
        original_sender = original_email_data.get('sender', 'N/A')
        original_date = original_email_data.get('date', 'N/A')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 20px; }}
                .highlight {{ background-color: #e6ffe6; padding: 10px; border-radius: 5px; }}
                .warning {{ background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .credit-warning {{ background-color: #f8d7da; border: 2px solid #dc3545; padding: 15px; border-radius: 5px; margin: 15px 0; color: #721c24; font-weight: bold; font-size: 16px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: #008000; font-weight: bold; }}
                .fallback {{ color: #ff8800; font-weight: bold; }}
                .failed {{ color: #ff0000; font-weight: bold; }}
                .price {{ font-weight: bold; color: #0066cc; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🎯 Tarjous luotu automaattisesti</h2>
                <p><strong>Tarjous {offer_number}</strong> on valmis ja lähetetty Lemonsoftiin!</p>
            </div>
            
            {self._generate_credit_warning_section(credit_warning)}
            
            <div class="section">
                <h3>📋 Tarjouksen tiedot</h3>
                <ul>
                    <li><strong>Tarjousnumero:</strong> {offer_number}</li>
                    <li><strong>Asiakasnumero:</strong> {customer_number}</li>
                    <li><strong>Asiakkaan nimi:</strong> {customer_name}</li>
                    <li><strong>Rivien määrä:</strong> {total_rows}</li>
                    <li><strong>Kokonaishinta (alv 0%):</strong> <span class="price">€{total_price:.2f}</span></li>
                </ul>
            </div>
            
            <div class="section highlight">
                <h3>✅ Tuotteiden tunnistus</h3>
                <p><strong>{successful_count}/{total_rows}</strong> tuotetta tunnistettu onnistuneesti 
                   (<strong>{success_percentage:.1f}%</strong>)</p>
            </div>
            
            <div class="section">
                <h3>🛍️ Tuoterivit ja alennukset</h3>
                {product_table}
            </div>
            
            <div class="section">
                <h3>💰 Alennusmenetelmät</h3>
                {discount_summary}
            </div>
            
            <div class="section">
                <h3>📧 Alkuperäinen sähköposti</h3>
                <ul>
                    <li><strong>Lähettäjä:</strong> {original_sender}</li>
                    <li><strong>Aihe:</strong> {original_subject}</li>
                    <li><strong>Päivämäärä:</strong> {original_date}</li>
                </ul>
            </div>
            
            <div class="section">
                <h3>🚀 Seuraavat toimet</h3>
                <ul>
                    <li>Tarkista tarjous Lemonsoftissa</li>
                    <li>Täydennä tarvittaessa lisätietoja</li>
                    <li>Lähetä tarjous asiakkaalle</li>
                </ul>
            </div>
            
            <hr style="margin-top: 30px;">
            <p style="color: #666; font-size: 12px;">
                Tämä viesti on lähetetty automaattisesti tarjousautomaatiojärjestelmästä.<br>
                Luotu: {datetime.now().strftime('%d.%m.%Y %H:%M')}
            </p>
        </body>
        </html>
        """
        
        return html_body
    
    def _generate_credit_warning_section(self, credit_warning: str) -> str:
        """Generate credit warning section if applicable."""
        if not credit_warning:
            return ""
        
        return f"""
            <div class="credit-warning">
                <h3>🚨 TÄRKEÄ HUOMAUTUS</h3>
                <p>{credit_warning}</p>
                <p><strong>Toimenpide:</strong> Tarkista että toimitusehdoksi on asetettu 33 (ennakkomaksu)!</p>
            </div>
        """
    
    def _generate_product_table(self, product_matches: List[Dict[str, Any]]) -> str:
        """Generate HTML table of product matches."""
        if not product_matches:
            return "<p>Ei tuotteita löytynyt.</p>"
        
        table_rows = []
        for i, match in enumerate(product_matches, 1):
            product_code = match.get('product_code', 'N/A')
            product_name = match.get('product_name', 'N/A')
            quantity = match.get('quantity', 0)
            match_method = match.get('match_method', 'unknown')
            discount_method = match.get('discount_method', 'Listahinta')
            discount_percent = match.get('discount_percent', 0)
            line_total = match.get('line_total', 0)
            
            # Status styling
            if match_method == 'fallback':
                status_class = "fallback"
                status_text = "Varatuote"
            elif match_method in ['direct', 'semantic', 'regex']:
                status_class = "success"
                status_text = "Onnistunut"
            else:
                status_class = "failed"
                status_text = "Epäonnistunut"
            
            table_rows.append(f"""
                <tr>
                    <td>{i}</td>
                    <td>{product_code}</td>
                    <td>{product_name}</td>
                    <td>{quantity}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{discount_method}</td>
                    <td>{discount_percent:.1f}%</td>
                    <td>€{line_total:.2f}</td>
                </tr>
            """)
        
        table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Tuotekoodi</th>
                    <th>Tuotenimi</th>
                    <th>Määrä</th>
                    <th>Tunnistus</th>
                    <th>Alennusmenetelmä</th>
                    <th>Alennus-%</th>
                    <th>Rivin summa</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        
        return table_html
    
    def _generate_discount_summary(self, pricing_details: Dict[str, Any]) -> str:
        """Generate discount methods summary."""
        line_items = pricing_details.get('line_items', [])
        
        if not line_items:
            return "<p>Ei alennustietoja saatavilla.</p>"
        
        # Count discount methods
        discount_methods = {}
        for item in line_items:
            applied_rules = item.get('applied_rules', ['Listahinta'])
            if not applied_rules:
                applied_rules = ['Listahinta']
            
            method = ', '.join(applied_rules)
            discount_methods[method] = discount_methods.get(method, 0) + 1
        
        summary_rows = []
        for method, count in discount_methods.items():
            summary_rows.append(f"<li><strong>{method}:</strong> {count} tuotetta</li>")
        
        return f"<ul>{''.join(summary_rows)}</ul>"
    
    def _create_message(self, to: str, subject: str, html_body: str) -> Dict:
        """Create Gmail API message."""
        # Create multipart message
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = self.sender_email
        message['subject'] = subject
        
        # Add HTML part
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
    
    async def _send_message(self, message: Dict):
        """Send email message via Gmail API."""
        try:
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            self.logger.info(f"Email sent successfully. Message ID: {result.get('id')}")
            return result
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            raise EmailSenderError(f"Failed to send email: {error}")
        except Exception as error:
            self.logger.error(f"Unexpected error sending email: {error}")
            raise EmailSenderError(f"Failed to send email: {error}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Gmail API connectivity."""
        try:
            if not self.service:
                await self.initialize()
            
            # Test API connection
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                'status': 'healthy',
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal', 0)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            } 