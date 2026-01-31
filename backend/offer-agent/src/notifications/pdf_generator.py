"""
PDF Generator for Offer Confirmations
Generates professional PDF documents for offer confirmations.
"""

import os
import io
from datetime import datetime
from typing import Dict, List, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.para import Paragraph as ParagraphFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.utils.logger import get_logger


class OfferConfirmationPDFGenerator:
    """Generates PDF documents for offer confirmations."""
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.logger = get_logger(__name__)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue,
            alignment=TA_LEFT,
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='WarningText',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.red,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ))
    
    def _truncate_text(self, text: str, max_length: int = 30) -> str:
        """Truncate text to maximum length."""
        if not text:
            return ''
        text = str(text)
        if len(text) > max_length:
            return text[:max_length-3] + '...'
        return text
    
    def generate_offer_confirmation_pdf(
        self,
        offer_details: Dict,
        customer_details: Dict,
        product_matches: List[Dict],
        pricing_details: Dict,
        verification_results: Dict = None,
        original_email_data: Dict = None,
        credit_warning: str = None
    ) -> bytes:
        """
        Generate a PDF document for offer confirmation.
        
        Args:
            offer_details: Details about the offer
            customer_details: Customer information
            product_matches: List of matched products
            pricing_details: Pricing information
            verification_results: Lemonsoft verification results
            original_email_data: Original email data
            credit_warning: Credit denial warning if applicable
            
        Returns:
            bytes: PDF document as bytes
        """
        self.logger.info(f"Generating PDF for offer: {offer_details.get('offer_number', 'UNKNOWN')}")
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Build the story (content)
        story = []
        
        # Title
        story.append(Paragraph("TARJOUSVAHVISTUS", self.styles['CustomTitle']))
        story.append(Spacer(1, 15))
        
        # Credit warning (if applicable)
        if credit_warning:
            story.append(Paragraph("HUOMIO: Asiakkaalla on luottokielto", self.styles['WarningText']))
            story.append(Spacer(1, 15))
        
        # Offer and Customer Information Section
        story.append(Paragraph("TARJOUS- JA ASIAKASTIEDOT", self.styles['SectionHeader']))
        
        offer_info_data = [
            ['Tarjousnumero:', offer_details.get('offer_number', 'ODOTTAA')],
            ['Asiakaskoodi:', customer_details.get('number', '-')],
            ['Asiakasnimi:', customer_details.get('name', '-')],
            ['Osoite:', customer_details.get('street', '-')],
            ['Postinumero:', f"{customer_details.get('postal_code', '')} {customer_details.get('city', '')}".strip() or '-'],
            ['Yhteyshenkilö:', customer_details.get('ceo_contact', '-')],
            ['Päivämäärä:', datetime.now().strftime('%d.%m.%Y')],
            ['Tuotteiden määrä:', str(len(product_matches))],
        ]
        
        if customer_details.get('deny_credit'):
            offer_info_data.append(['Luottokielto:', 'KYLLÄ'])
        
        offer_table = Table(offer_info_data, colWidths=[30*mm, 140*mm])
        offer_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(offer_table)
        story.append(Spacer(1, 15))
        
        # Products Section - Single table with all products
        story.append(Paragraph("TUOTTEET", self.styles['SectionHeader']))
        
        if product_matches:
            # Create header row
            product_data = [[
                'Nro',
                'Tuotekoodi',
                'Tuotenimi',
                'Laatu',
                'Määrittely',
                'Asiakkaan tuote',
                'Määrä',
                'Yks.hinta',
                'Ale-%',
                'Yhteensä',
                'AI-%'
            ]]
            
            # Add product rows
            for i, product in enumerate(product_matches, 1):
                # Get corresponding pricing details if available
                line_total = 0
                unit_price = 0
                discount_percent = 0
                
                if i-1 < len(pricing_details.get('line_items', [])):
                    line_item = pricing_details['line_items'][i-1]
                    line_total = line_item.get('line_total', 0)
                    discount_percent = line_item.get('discount_percent', 0)
                    unit_price = line_item.get('unit_price', 0)
                
                # Check if product code is "9000" for red font
                product_code = product.get('product_code', '-')
                is_red_product = product_code == "9000"
                
                # Create paragraphs for text that may wrap
                product_name_para = Paragraph(
                    product.get('product_name', '-'),
                    self.styles['Normal']
                )
                customer_term_para = Paragraph(
                    product.get('original_customer_term', product.get('product_name', '-')),
                    self.styles['Normal']
                )

                # Get quality and specification - wrap in Paragraph for text wrapping
                quality_para = Paragraph(
                    product.get('quality', '-'),
                    self.styles['Normal']
                )
                specification = product.get('specification', '-')

                # Add main product row
                product_data.append([
                    str(i),
                    product.get('product_code', '-'),
                    product_name_para,
                    quality_para,
                    specification,
                    customer_term_para,
                    str(product.get('quantity', 1)),
                    f"{unit_price:.2f}€",
                    f"{discount_percent:.0f}%" if discount_percent > 0 else '0%',
                    f"{line_total:.2f}€",
                    f"{product.get('ai_confidence', 0)}%"
                ])
                
                # Add indented AI reasoning row below each product
                ai_reasoning = product.get('ai_reasoning', 'Ei saatavilla')
                reasoning_para = Paragraph(
                    f"<i>AI-perustelu: {ai_reasoning}</i>",
                    self.styles['InfoText']
                )

                # Add reasoning row with empty cells except for the reasoning text spanning multiple columns
                product_data.append([
                    '',  # Empty number
                    '',  # Empty product code
                    reasoning_para,  # AI reasoning spans across name columns
                    '',  # Empty quality
                    '',  # Empty specification
                    '',  # Empty customer term
                    '',  # Empty quantity
                    '',  # Empty unit price
                    '',  # Empty discount
                    '',  # Empty total
                    ''   # Empty AI confidence
                ])
            
            # Column widths optimized for A4 with margins - adjusted to accommodate new columns
            col_widths = [
                7*mm,    # Nro
                18*mm,   # Tuotekoodi
                28*mm,   # Tuotenimi
                15*mm,   # Laatu
                20*mm,   # Määrittely
                25*mm,   # Asiakkaan tuote
                10*mm,   # Määrä
                15*mm,   # Yks.hinta
                9*mm,    # Ale-%
                16*mm,   # Yhteensä
                9*mm     # AI-%
            ]
            
            product_table = Table(product_data, colWidths=col_widths, repeatRows=1)
            
            # Style the table - minimal styling with only bold headers and prices
            table_style = [
                # Header row styling - bold only
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                
                # All data cells - normal font
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 7),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                
                # Minimal padding
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                
                # Numeric columns - right align and bold for prices
                ('ALIGN', (6, 1), (6, -1), 'RIGHT'),  # Määrä (shifted by 2)
                ('ALIGN', (7, 1), (7, -1), 'RIGHT'),  # Yks.hinta (shifted by 2)
                ('FONT', (7, 1), (7, -1), 'Helvetica-Bold', 7),  # Bold prices
                ('ALIGN', (8, 1), (8, -1), 'RIGHT'),  # Ale-% (shifted by 2)
                ('ALIGN', (9, 1), (9, -1), 'RIGHT'),  # Yhteensä (shifted by 2)
                ('FONT', (9, 1), (9, -1), 'Helvetica-Bold', 7),  # Bold total prices
                ('ALIGN', (10, 1), (10, -1), 'RIGHT'),  # AI-% (shifted by 2)
                
                # Add some spacing between rows to ensure clean row separation
                ('SPACEBEFORE', (0, 1), (-1, -1), 2),
                ('SPACEAFTER', (0, 0), (-1, -1), 2),
            ]
            
            
            # Color AI confidence based on value and style AI reasoning rows
            for i, product in enumerate(product_matches, 1):
                # Product rows are at positions 1, 3, 5, 7... (since we have AI reasoning rows in between)
                product_row = (i * 2) - 1
                reasoning_row = i * 2
                
                # Check if product code is "9000" for red font
                product_code = product.get('product_code', '-')
                is_red_product = product_code == "9000"
                
                if is_red_product:
                    # Apply red color to entire row for product code "9000"
                    table_style.append(('TEXTCOLOR', (0, product_row), (-1, product_row), colors.red))
                    table_style.append(('FONT', (0, product_row), (-1, product_row), 'Helvetica-Bold', 7))
                
                ai_confidence = product.get('ai_confidence', 0)
                if ai_confidence >= 80:
                    color = colors.green
                elif ai_confidence >= 60:
                    color = colors.orange
                else:
                    color = colors.red
                
                # Only apply AI confidence color if not a red product (9000)
                if not is_red_product:
                    table_style.append(('TEXTCOLOR', (10, product_row), (10, product_row), color))  # AI-% column shifted by 2
                    table_style.append(('FONT', (10, product_row), (10, product_row), 'Helvetica-Bold', 7))
                
                # Style AI reasoning rows with indentation and smaller font
                table_style.append(('LEFTPADDING', (2, reasoning_row), (2, reasoning_row), 15))  # Indent reasoning
                table_style.append(('FONT', (2, reasoning_row), (2, reasoning_row), 'Helvetica-Oblique', 6))  # Smaller italic font
                table_style.append(('TEXTCOLOR', (2, reasoning_row), (2, reasoning_row), colors.grey))  # Grey color
                
                # Span the AI reasoning across multiple columns for better readability
                table_style.append(('SPAN', (2, reasoning_row), (8, reasoning_row)))  # Span from product name to discount columns (shifted by 2)
            
            product_table.setStyle(TableStyle(table_style))
            story.append(product_table)
            
            # Summary section
            if pricing_details.get('net_total') is not None:
                story.append(Spacer(1, 15))
                story.append(Paragraph("YHTEENVETO", self.styles['SectionHeader']))
                
                summary_data = [
                    ['', 'Netto (alv 0%):', f"{pricing_details.get('net_total', 0):.2f}€"],
                    ['', 'ALV 25.5%:', f"{pricing_details.get('vat_amount', 0):.2f}€"],
                    ['', 'YHTEENSÄ:', f"{pricing_details.get('total_amount', 0):.2f}€"]
                ]
                
                summary_table = Table(
                    summary_data, 
                    colWidths=[100*mm, 40*mm, 30*mm]
                )
                summary_table.setStyle(TableStyle([
                    ('FONT', (1, 0), (-1, -2), 'Helvetica', 10),
                    ('FONT', (1, -1), (-1, -1), 'Helvetica-Bold', 12),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('TEXTCOLOR', (1, -1), (-1, -1), colors.darkblue),
                    ('LINEABOVE', (1, -1), (-1, -1), 1, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(summary_table)
        else:
            story.append(Paragraph("Ei tunnistettuja tuotteita", self.styles['InfoText']))
        
        story.append(Spacer(1, 20))
        
        # Original Email Information
        if original_email_data:
            story.append(Paragraph("ALKUPERÄINEN VIESTI", self.styles['SectionHeader']))
            
            email_info_data = [
                ['Lähettäjä:', original_email_data.get('sender', '-')],
                ['Aihe:', original_email_data.get('subject', '-')],
                ['Päivämäärä:', original_email_data.get('date', '-')],
            ]
            
            email_table = Table(email_info_data, colWidths=[30*mm, 140*mm])
            email_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(email_table)
            story.append(Spacer(1, 15))
        
        # Verification status
        if verification_results and verification_results.get('success'):
            story.append(Paragraph("TILA", self.styles['SectionHeader']))
            story.append(Paragraph("✅ Tarjous luotu onnistuneesti Lemonsoft-järjestelmään", self.styles['InfoText']))
        elif offer_details.get('offer_number') == 'PENDING_API_CONNECTION':
            story.append(Paragraph("HUOMAUTUS", self.styles['SectionHeader']))
            story.append(Paragraph("⚠️ Tarjous odottaa API-yhteyttä Lemonsoft-järjestelmään", self.styles['InfoText']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Dokumentti luotu automaattisesti {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            self.styles['InfoText']
        ))
        
        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        self.logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        return pdf_bytes
    
    def generate_filename(self, offer_details: Dict, customer_details: Dict) -> str:
        """Generate a filename for the PDF."""
        offer_number = offer_details.get('offer_number', 'ODOTTAA')
        customer_name = customer_details.get('name', 'Asiakas')
        
        # Clean customer name for filename
        safe_customer = ''.join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
        safe_customer = safe_customer.replace(' ', '_')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"Tarjous_{offer_number}_{safe_customer}_{timestamp}.pdf"