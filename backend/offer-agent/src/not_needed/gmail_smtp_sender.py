"""
Gmail SMTP Sender - Zero User Interaction with App Password
Uses Gmail App Password for completely automated email sending.
Never expires, never requires OAuth.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.exceptions import EmailSenderError


class GmailSMTPSender:
    """Zero-touch Gmail sender using App Password authentication."""
    
    def __init__(self):
        """Initialize Gmail SMTP sender."""
        self.logger = get_logger(__name__)
        
        # SMTP configuration
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = os.getenv('SENDER_EMAIL', os.getenv('MONITORED_EMAIL', 'ai.tarjous.wcom@gmail.com'))
        self.app_password = os.getenv('GMAIL_APP_PASSWORD', os.getenv('EMAIL_PASSWORD'))
        
        if not self.app_password:
            raise EmailSenderError(
                "Gmail App Password not found. Please set GMAIL_APP_PASSWORD environment variable.\n"
                "To create an App Password:\n"
                "1. Go to Google Account settings\n"
                "2. Security → 2-Step Verification (must be enabled)\n"
                "3. App passwords → Generate password for 'Mail'\n"
                "4. Use the 16-character password in your .env file"
            )
        
        self.logger.info(f"Gmail SMTP Sender initialized for: {self.sender_email}")
    
    async def initialize(self):
        """Initialize SMTP sender - always ready, no authentication needed until sending."""
        self.logger.info("[SUCCESS] Gmail SMTP Sender ready - App Password authentication")
        self.logger.info("[SUCCESS] ZERO user interaction required - fully automated!")
    
    async def send_stock_alert_email(self, recipient_email: str, warehouse_info: Dict, 
                                   negative_products: List[Dict]) -> bool:
        """
        Send stock alert email using SMTP with App Password.
        
        Args:
            recipient_email: Email address to send to
            warehouse_info: Dictionary with warehouse name and email
            negative_products: List of products with negative stock
            
        Returns:
            bool: True if email sent successfully
        """
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
            message['From'] = self.sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # Send via SMTP with App Password - ZERO user interaction!
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
            
            self.logger.info(f"[SUCCESS] Stock alert email sent via SMTP!")
            self.logger.info(f"   Recipient: {recipient_email}")
            self.logger.info(f"   Warehouse: {warehouse_name}")
            self.logger.info(f"   Products: {len(negative_products)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send stock alert email via SMTP: {e}")
            return False
    
    async def send_offer_confirmation(self, recipient_email: str, offer_details: Dict, 
                                     customer_details: Dict, product_matches: List[Dict],
                                     pricing_details: Dict, verification_results: Dict = None,
                                     pdf_content: bytes = None) -> bool:
        """Send offer confirmation email via SMTP."""
        try:
            subject = f"Tarjous valmis - {customer_details.get('name', 'Asiakas')}"
            
            html_body = f"""
            <html>
            <body>
                <h2>Tarjous on valmis</h2>
                <p>Hei,</p>
                <p>Tarjous asiakkaalle <strong>{customer_details.get('name', 'N/A')}</strong> on valmis.</p>
                <p>Tuotteita tarjouksessa: {len(product_matches)}</p>
                <p>Kokonaishinta: {pricing_details.get('total_price_with_vat', 0):.2f} €</p>
                <p>Terveisin,<br>LVI-Wabek Tarjousautomaatio</p>
            </body>
            </html>
            """
            
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # Add PDF attachment if provided
            if pdf_content:
                from email.mime.application import MIMEApplication
                pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename='tarjous.pdf')
                message.attach(pdf_attachment)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
            
            self.logger.info(f"[SUCCESS] Offer confirmation email sent via SMTP!")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send offer confirmation email via SMTP: {e}")
            return False