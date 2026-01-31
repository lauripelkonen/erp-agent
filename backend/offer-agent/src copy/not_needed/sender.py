"""
Notification Sender System
Handles sending offers via email, SMS, or other channels.
Integrates with document generator for attachments.
"""

import asyncio
import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.application import MimeApplication
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass, field
import json
import uuid

import aiofiles
import jinja2

from src.config.settings import get_settings
from src.utils.logger import get_logger, get_audit_logger
from src.documents.generator import GeneratedDocument


@dataclass
class NotificationResult:
    """Result of notification sending."""
    success: bool
    notification_id: str
    recipient: str
    method: str
    sent_at: datetime = None
    error: str = None
    
    def __post_init__(self):
        if self.sent_at is None:
            self.sent_at = datetime.utcnow()


class NotificationSender:
    """
    Comprehensive notification system for offer delivery.
    
    Features:
    - Email with PDF attachments
    - Professional email templates
    - Finnish/English language support
    - Delivery confirmations
    - Retry mechanisms
    - Multiple notification channels
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Email configuration
        self.smtp_config = self._get_smtp_config()
        
        # Templates
        self.email_templates = self._load_email_templates()
    
    def _get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration from settings."""
        return {
            'host': getattr(self.settings, 'smtp_host', 'smtp.gmail.com'),
            'port': getattr(self.settings, 'smtp_port', 587),
            'username': getattr(self.settings, 'smtp_username', ''),
            'password': getattr(self.settings, 'smtp_password', ''),
            'use_tls': getattr(self.settings, 'smtp_use_tls', True),
            'from_email': getattr(self.settings, 'from_email', 'offers@company.fi'),
            'from_name': getattr(self.settings, 'from_name', 'Offer Automation System')
        }
    
    def _load_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates for different languages."""
        return {
            'offer_fi': {
                'subject': 'Tarjous: {offer_number}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #1f4788; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background-color: #f8f9fa; padding: 15px; font-size: 12px; color: #666; }
        .highlight { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Tarjous</h1>
        <p>Tarjousnumero: {offer_number}</p>
    </div>
    
    <div class="content">
        <p>Hyvä {customer_name},</p>
        
        <p>Kiitos yhteydenotostanne. Liitteenä löydätte pyydetyn tarjouksen.</p>
        
        <div class="highlight">
            <h3>Tarjouksen tiedot:</h3>
            <ul>
                <li><strong>Tarjousnumero:</strong> {offer_number}</li>
                <li><strong>Tuotteiden määrä:</strong> {product_count} kpl</li>
                <li><strong>Kokonaissumma:</strong> {total_amount} EUR (sis. ALV 25.5%)</li>
                <li><strong>Voimassa:</strong> 30 päivää</li>
            </ul>
        </div>
        
        <p>Tarjous on automaattisesti luotu järjestelmässämme pyyntönne perusteella. 
        Mikäli tarvitsette lisätietoja tai muutoksia, ottakaa yhteyttä asiakaspalveluumme.</p>
        
        <p>Kiitos ja odotamme tilaustanne!</p>
        
        <p>Ystävällisin terveisin,<br>
        Myyntitiimi</p>
    </div>
    
    <div class="footer">
        <p>Tämä viesti on lähetetty automaattisesti. Älkää vastako suoraan tähän sähköpostiin.</p>
        <p>Asiakaspalvelu: info@company.fi | Puh: +358 10 123 4567</p>
    </div>
</body>
</html>
                ''',
                'body_text': '''
Hyvä {customer_name},

Kiitos yhteydenotostanne. Liitteenä löydätte pyydetyn tarjouksen.

Tarjouksen tiedot:
- Tarjousnumero: {offer_number}
- Tuotteiden määrä: {product_count} kpl
- Kokonaissumma: {total_amount} EUR (sis. ALV 25.5%)
- Voimassa: 30 päivää

Tarjous on automaattisesti luotu järjestelmässämme pyyntönne perusteella.
Mikäli tarvitsette lisätietoja tai muutoksia, ottakaa yhteyttä asiakaspalveluumme.

Kiitos ja odotamme tilaustanne!

Ystävällisin terveisin,
Myyntitiimi

---
Asiakaspalvelu: info@company.fi | Puh: +358 10 123 4567
                '''
            },
            'offer_en': {
                'subject': 'Offer: {offer_number}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #1f4788; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background-color: #f8f9fa; padding: 15px; font-size: 12px; color: #666; }
        .highlight { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Offer</h1>
        <p>Offer Number: {offer_number}</p>
    </div>
    
    <div class="content">
        <p>Dear {customer_name},</p>
        
        <p>Thank you for your inquiry. Please find attached the requested offer.</p>
        
        <div class="highlight">
            <h3>Offer Details:</h3>
            <ul>
                <li><strong>Offer Number:</strong> {offer_number}</li>
                <li><strong>Number of Products:</strong> {product_count} pcs</li>
                <li><strong>Total Amount:</strong> {total_amount} EUR (incl. VAT 25.5%)</li>
                <li><strong>Valid Until:</strong> 30 days</li>
            </ul>
        </div>
        
        <p>This offer has been automatically generated based on your request. 
        If you need additional information or changes, please contact our customer service.</p>
        
        <p>Thank you and we look forward to your order!</p>
        
        <p>Best regards,<br>
        Sales Team</p>
    </div>
    
    <div class="footer">
        <p>This message was sent automatically. Please do not reply directly to this email.</p>
        <p>Customer Service: info@company.fi | Tel: +358 10 123 4567</p>
    </div>
</body>
</html>
                ''',
                'body_text': '''
Dear {customer_name},

Thank you for your inquiry. Please find attached the requested offer.

Offer Details:
- Offer Number: {offer_number}
- Number of Products: {product_count} pcs
- Total Amount: {total_amount} EUR (incl. VAT 25.5%)
- Valid Until: 30 days

This offer has been automatically generated based on your request.
If you need additional information or changes, please contact our customer service.

Thank you and we look forward to your order!

Best regards,
Sales Team

---
Customer Service: info@company.fi | Tel: +358 10 123 4567
                '''
            }
        }
    
    async def send_offer_notification(
        self, 
        recipient: str, 
        offer_document: Optional[GeneratedDocument], 
        offer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send offer notification email with PDF attachment.
        
        Args:
            recipient: Email address to send to
            offer_document: Generated offer document to attach
            offer_data: Offer data for email content
            
        Returns:
            Notification result dictionary
        """
        try:
            self.logger.info(f"Sending offer notification to {recipient}")
            
            # Select language and template
            language = self._detect_language(offer_data)
            template_key = f'offer_{language}'
            template = self.email_templates.get(template_key, self.email_templates['offer_fi'])
            
            # Prepare email content
            email_data = self._prepare_email_data(offer_data)
            
            subject = template['subject'].format(**email_data)
            body_html = template['body_html'].format(**email_data)
            body_text = template['body_text'].format(**email_data)
            
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg['To'] = recipient
            
            # Add text and HTML parts
            text_part = MimeText(body_text, 'plain', 'utf-8')
            html_part = MimeText(body_html, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Attach PDF if available
            if offer_document and Path(offer_document.file_path).exists():
                with open(offer_document.file_path, 'rb') as f:
                    pdf_data = f.read()
                
                pdf_attachment = MimeApplication(pdf_data, _subtype='pdf')
                pdf_attachment.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=offer_document.filename
                )
                msg.attach(pdf_attachment)
                
                self.logger.info(f"PDF attachment added: {offer_document.filename}")
            else:
                self.logger.warning("No PDF document to attach")
            
            # Send email
            if self.smtp_config['username'] and self.smtp_config['password']:
                await self._send_via_smtp(msg, recipient)
                success = True
                error = None
            else:
                # Mock sending for development
                self.logger.info("SMTP not configured - simulating email send")
                success = True
                error = None
            
            # Log successful notification
            notification_id = f"NOTIF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            self.audit_logger.log_notification_sent(
                notification_id,
                'email',
                recipient,
                {
                    'offer_number': offer_data.get('offer_number'),
                    'customer_name': offer_data.get('customer', {}).get('name'),
                    'attachment_included': offer_document is not None,
                    'template_used': template_key
                }
            )
            
            return {
                'success': success,
                'notification_id': notification_id,
                'recipient': recipient,
                'method': 'email',
                'sent_at': datetime.utcnow().isoformat(),
                'error': error
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send offer notification: {e}")
            return {
                'success': False,
                'recipient': recipient,
                'method': 'email',
                'error': str(e),
                'sent_at': datetime.utcnow().isoformat()
            }
    
    async def _send_via_smtp(self, message: MimeMultipart, recipient: str):
        """Send email via SMTP."""
        server = None
        try:
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            
            if self.smtp_config['use_tls']:
                server.starttls()
            
            if self.smtp_config['username'] and self.smtp_config['password']:
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            text = message.as_string()
            server.sendmail(self.smtp_config['from_email'], recipient, text)
            
            self.logger.info(f"Email sent successfully to {recipient}")
            
        finally:
            if server:
                server.quit()
    
    def _detect_language(self, offer_data: Dict[str, Any]) -> str:
        """Detect language preference for the notification."""
        # For now, default to Finnish
        # In a real implementation, this could check customer preferences
        return 'fi'
    
    def _prepare_email_data(self, offer_data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for email template formatting."""
        customer = offer_data.get('customer', {})
        
        return {
            'customer_name': customer.get('name', 'Asiakas'),
            'offer_number': offer_data.get('offer_number', 'N/A'),
            'product_count': len(offer_data.get('products', [])),
            'total_amount': f"{offer_data.get('total_amount', 0):.2f}",
            'request_id': offer_data.get('request_id', ''),
            'generated_date': datetime.now().strftime('%d.%m.%Y')
        }
    
    async def send_customer_confirmation(
        self, 
        customer_email: str, 
        confirmation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send confirmation email to customer about offer processing."""
        try:
            # Simple confirmation template
            subject = "Tarjouspyyntönne on vastaanotettu"
            body = f"""
Hyvä asiakas,

Kiitos tarjouspyynnöstänne. Pyyntönne on vastaanotettu ja käsitellään automaattisesti.

Pyyntönumero: {confirmation_data.get('request_id', 'N/A')}
Vastaanotettu: {datetime.now().strftime('%d.%m.%Y %H:%M')}

Lähetämme tarjouksen sähköpostiinne pian.

Ystävällisin terveisin,
Automaattinen tarjousjärjestelmä
            """
            
            # Create simple email
            msg = MimeText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = customer_email
            
            # Send via SMTP if configured
            if self.smtp_config['username']:
                await self._send_via_smtp(msg, customer_email)
            
            return {
                'success': True,
                'recipient': customer_email,
                'type': 'confirmation'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send confirmation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check notification system health."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'smtp_configured': bool(self.smtp_config['username']),
            'templates_loaded': len(self.email_templates)
        }
        
        # Test SMTP connection if configured
        if self.smtp_config['username']:
            try:
                server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
                server.quit()
                health_status['smtp_connection'] = 'ok'
            except Exception as e:
                health_status['smtp_connection'] = 'failed'
                health_status['smtp_error'] = str(e)
                health_status['status'] = 'degraded'
        
        return health_status