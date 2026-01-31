"""
Document Generation System
Creates professional PDF offers from Lemonsoft offer data with Finnish business formatting.
Supports templates, multi-language content, and automated document management.
"""

import asyncio
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import uuid
import os
import tempfile
import base64

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config.settings import get_settings
from utils.logger import get_logger, get_audit_logger
from utils.exceptions import DocumentGenerationError, ValidationError
from lemonsoft.api_client import LemonsoftOffer, LemonsoftOfferLine


@dataclass
class DocumentTemplate:
    """Document template configuration."""
    template_id: str
    name: str
    description: str
    template_path: str
    language: str = "fi"
    currency: str = "EUR"
    page_size: tuple = A4
    margins: Dict[str, float] = None
    
    def __post_init__(self):
        if self.margins is None:
            self.margins = {
                'top': 2.5 * cm,
                'bottom': 2.5 * cm,
                'left': 2.0 * cm,
                'right': 2.0 * cm
            }


@dataclass
class GeneratedDocument:
    """Generated document information."""
    document_id: str
    filename: str
    file_path: str
    content_type: str = "application/pdf"
    file_size: int = 0
    generated_at: datetime = None
    template_used: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class OfferDocumentGenerator:
    """
    Professional document generator for offers with Finnish business formatting.
    
    Features:
    - Professional PDF generation with ReportLab
    - Finnish business standards compliance
    - Multi-language support (Finnish/English)
    - Template system for different document types
    - Automatic calculations and formatting
    - Company branding integration
    - Digital signature preparation
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Document storage configuration
        self.output_dir = Path(self.settings.temp_dir) / "documents"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Template configuration
        self.templates = self._initialize_templates()
        
        # Style configuration
        self.styles = self._initialize_styles()
        
        # Company information
        self.company_info = self._get_company_info()
    
    def _initialize_templates(self) -> Dict[str, DocumentTemplate]:
        """Initialize document templates."""
        return {
            'offer_fi': DocumentTemplate(
                template_id='offer_fi',
                name='Finnish Offer Template',
                description='Standard Finnish business offer template',
                template_path='templates/offer_fi.html',
                language='fi',
                currency='EUR'
            ),
            'offer_en': DocumentTemplate(
                template_id='offer_en',
                name='English Offer Template',
                description='Standard English business offer template',
                template_path='templates/offer_en.html',
                language='en',
                currency='EUR'
            )
        }
    
    def _initialize_styles(self) -> Dict[str, Any]:
        """Initialize document styles."""
        styles = getSampleStyleSheet()
        
        # Custom styles for Finnish business documents
        custom_styles = {
            'CompanyName': ParagraphStyle(
                'CompanyName',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.HexColor('#1f4788'),
                alignment=TA_LEFT
            ),
            'OfferTitle': ParagraphStyle(
                'OfferTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.HexColor('#1f4788'),
                alignment=TA_CENTER
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=16,
                textColor=colors.HexColor('#2c5aa0'),
                alignment=TA_LEFT
            ),
            'CustomerInfo': ParagraphStyle(
                'CustomerInfo',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                alignment=TA_LEFT
            ),
            'TableHeader': ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.white,
                alignment=TA_CENTER
            ),
            'TableCell': ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_LEFT
            ),
            'TableCellRight': ParagraphStyle(
                'TableCellRight',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_RIGHT
            ),
            'TotalLine': ParagraphStyle(
                'TotalLine',
                parent=styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                alignment=TA_RIGHT
            ),
            'Footer': ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            ),
            'Terms': ParagraphStyle(
                'Terms',
                parent=styles['Normal'],
                fontSize=8,
                spaceAfter=4,
                alignment=TA_JUSTIFY
            )
        }
        
        return {**styles, **custom_styles}
    
    def _get_company_info(self) -> Dict[str, str]:
        """Get company information for document headers."""
        return {
            'name': 'Your Company Name Oy',
            'address': 'Yrityskatu 1',
            'postal_code': '00100',
            'city': 'Helsinki',
            'country': 'Finland',
            'phone': '+358 10 123 4567',
            'email': 'info@yourcompany.fi',
            'website': 'www.yourcompany.fi',
            'business_id': '1234567-8',
            'vat_number': 'FI12345678',
            'bank_account': 'FI21 1234 5600 0007 85',
            'bank_name': 'Nordea Bank Oyj',
            'swift_code': 'NDEAFIHH'
        }
    
    async def generate_offer(self, offer_data: Dict[str, Any]) -> GeneratedDocument:
        """
        Generate professional offer PDF document.
        
        Args:
            offer_data: Complete offer information including Lemonsoft data
            
        Returns:
            Generated document information
        """
        document_id = str(uuid.uuid4())
        
        try:
            self.logger.info(
                f"Generating offer document",
                extra={
                    'extra_fields': {
                        'document_id': document_id,
                        'offer_id': offer_data.get('offer_id'),
                        'customer': offer_data.get('customer', {}).get('name')
                    }
                }
            )
            
            # Determine template and language
            template = self._select_template(offer_data)
            
            # Generate filename
            offer_number = offer_data.get('offer_number', f"OFFER-{document_id[:8]}")
            customer_name = offer_data.get('customer', {}).get('name', 'Customer')
            safe_customer_name = self._sanitize_filename(customer_name)
            
            filename = f"{offer_number}_{safe_customer_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            file_path = self.output_dir / filename
            
            # Generate PDF document
            await self._generate_pdf_document(offer_data, file_path, template)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Create document record
            document = GeneratedDocument(
                document_id=document_id,
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                template_used=template.template_id,
                metadata={
                    'offer_id': offer_data.get('offer_id'),
                    'offer_number': offer_number,
                    'customer_id': offer_data.get('customer', {}).get('id'),
                    'customer_name': customer_name,
                    'total_amount': offer_data.get('total_amount'),
                    'currency': offer_data.get('lemonsoft_offer', LemonsoftOffer()).currency,
                    'language': template.language
                }
            )
            
            # Log successful generation
            self.audit_logger.log_document_generated(
                document_id,
                'offer_pdf',
                offer_data.get('offer_id', ''),
                {
                    'filename': filename,
                    'file_size': file_size,
                    'template': template.template_id,
                    'customer_id': offer_data.get('customer', {}).get('id')
                }
            )
            
            self.logger.info(f"Generated offer document: {filename} ({file_size} bytes)")
            
            return document
            
        except Exception as e:
            self.logger.error(f"Failed to generate offer document: {e}")
            raise DocumentGenerationError(
                f"Document generation failed: {str(e)}",
                context={
                    'document_id': document_id,
                    'offer_id': offer_data.get('offer_id')
                }
            )
    
    async def _generate_pdf_document(
        self, 
        offer_data: Dict[str, Any], 
        file_path: Path, 
        template: DocumentTemplate
    ):
        """Generate the actual PDF document."""
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=template.page_size,
            topMargin=template.margins['top'],
            bottomMargin=template.margins['bottom'],
            leftMargin=template.margins['left'],
            rightMargin=template.margins['right']
        )
        
        # Build document content
        story = []
        
        # Header section
        story.extend(self._create_header_section(offer_data, template))
        
        # Customer information section
        story.extend(self._create_customer_section(offer_data, template))
        
        # Offer details section
        story.extend(self._create_offer_details_section(offer_data, template))
        
        # Products table
        story.extend(self._create_products_table(offer_data, template))
        
        # Totals section
        story.extend(self._create_totals_section(offer_data, template))
        
        # Terms and conditions
        story.extend(self._create_terms_section(offer_data, template))
        
        # Footer
        story.extend(self._create_footer_section(offer_data, template))
        
        # Build PDF
        doc.build(story, onFirstPage=self._create_page_header, onLaterPages=self._create_page_header)
    
    def _create_header_section(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create document header section."""
        story = []
        
        # Company name and logo area
        story.append(Paragraph(self.company_info['name'], self.styles['CompanyName']))
        story.append(Spacer(1, 10))
        
        # Offer title
        if template.language == 'fi':
            title = "TARJOUS"
        else:
            title = "OFFER"
        
        story.append(Paragraph(title, self.styles['OfferTitle']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_customer_section(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create customer information section."""
        story = []
        
        customer = offer_data.get('customer', {})
        lemonsoft_offer = offer_data.get('lemonsoft_offer')
        
        # Create two-column layout for company info and customer info
        company_col = [
            Paragraph(f"<b>{self.company_info['name']}</b>", self.styles['CustomerInfo']),
            Paragraph(self.company_info['address'], self.styles['CustomerInfo']),
            Paragraph(f"{self.company_info['postal_code']} {self.company_info['city']}", self.styles['CustomerInfo']),
            Paragraph(f"Puh: {self.company_info['phone']}", self.styles['CustomerInfo']),
            Paragraph(f"Email: {self.company_info['email']}", self.styles['CustomerInfo']),
            Paragraph(f"Y-tunnus: {self.company_info['business_id']}", self.styles['CustomerInfo']),
            Paragraph(f"ALV-nro: {self.company_info['vat_number']}", self.styles['CustomerInfo']),
        ]
        
        customer_col = [
            Paragraph(f"<b>{customer.get('name', 'Customer')}</b>", self.styles['CustomerInfo']),
        ]
        
        if lemonsoft_offer and lemonsoft_offer.contact_person:
            customer_col.append(Paragraph(f"Yhteyshenkilö: {lemonsoft_offer.contact_person}", self.styles['CustomerInfo']))
        
        if customer.get('address'):
            addr = customer['address']
            if isinstance(addr, dict):
                if addr.get('street'):
                    customer_col.append(Paragraph(addr['street'], self.styles['CustomerInfo']))
                if addr.get('postal_code') and addr.get('city'):
                    customer_col.append(Paragraph(f"{addr['postal_code']} {addr['city']}", self.styles['CustomerInfo']))
            else:
                customer_col.append(Paragraph(str(addr), self.styles['CustomerInfo']))
        
        if customer.get('email'):
            customer_col.append(Paragraph(f"Email: {customer['email']}", self.styles['CustomerInfo']))
        
        if customer.get('phone'):
            customer_col.append(Paragraph(f"Puh: {customer['phone']}", self.styles['CustomerInfo']))
        
        # Create table for two-column layout
        info_data = []
        max_rows = max(len(company_col), len(customer_col))
        
        for i in range(max_rows):
            company_cell = company_col[i] if i < len(company_col) else ""
            customer_cell = customer_col[i] if i < len(customer_col) else ""
            info_data.append([company_cell, customer_cell])
        
        info_table = Table(info_data, colWidths=[8*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_offer_details_section(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create offer details section."""
        story = []
        
        lemonsoft_offer = offer_data.get('lemonsoft_offer')
        
        if lemonsoft_offer:
            offer_number = lemonsoft_offer.offer_number
            offer_date = lemonsoft_offer.offer_date.strftime('%d.%m.%Y') if lemonsoft_offer.offer_date else datetime.now().strftime('%d.%m.%Y')
            valid_until = lemonsoft_offer.valid_until.strftime('%d.%m.%Y') if lemonsoft_offer.valid_until else (datetime.now() + timedelta(days=30)).strftime('%d.%m.%Y')
            reference = lemonsoft_offer.reference or offer_data.get('request_id', '')[:8]
        else:
            offer_number = offer_data.get('offer_number', 'N/A')
            offer_date = datetime.now().strftime('%d.%m.%Y')
            valid_until = (datetime.now() + timedelta(days=30)).strftime('%d.%m.%Y')
            reference = offer_data.get('request_id', '')[:8]
        
        # Offer details table
        details_data = [
            ['Tarjousnumero:', offer_number],
            ['Päivämäärä:', offer_date],
            ['Voimassa:', valid_until],
            ['Viite:', reference],
        ]
        
        details_table = Table(details_data, colWidths=[4*cm, 6*cm])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_products_table(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create products table section."""
        story = []
        
        # Section header
        story.append(Paragraph("Tarjotut tuotteet", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        # Table headers
        headers = [
            Paragraph('<b>Tuotekoodi</b>', self.styles['TableHeader']),
            Paragraph('<b>Tuotenimi</b>', self.styles['TableHeader']),
            Paragraph('<b>Määrä</b>', self.styles['TableHeader']),
            Paragraph('<b>Yks.</b>', self.styles['TableHeader']),
            Paragraph('<b>À-hinta €</b>', self.styles['TableHeader']),
            Paragraph('<b>Yhteensä €</b>', self.styles['TableHeader'])
        ]
        
        # Prepare table data
        table_data = [headers]
        
        lemonsoft_offer = offer_data.get('lemonsoft_offer')
        
        if lemonsoft_offer and lemonsoft_offer.lines:
            # Use Lemonsoft offer lines
            for line in lemonsoft_offer.lines:
                row = [
                    Paragraph(line.product_code, self.styles['TableCell']),
                    Paragraph(line.product_name, self.styles['TableCell']),
                    Paragraph(str(int(line.quantity)), self.styles['TableCellRight']),
                    Paragraph(line.unit, self.styles['TableCell']),
                    Paragraph(f"{line.unit_price:.2f}", self.styles['TableCellRight']),
                    Paragraph(f"{line.line_total:.2f}", self.styles['TableCellRight'])
                ]
                table_data.append(row)
        else:
            # Fallback to product matches
            product_matches = offer_data.get('products', [])
            for match in product_matches:
                if match.product_code == "9000":  # Skip unknown products
                    continue
                
                total = match.price * match.quantity_requested
                row = [
                    Paragraph(match.product_code, self.styles['TableCell']),
                    Paragraph(match.product_name, self.styles['TableCell']),
                    Paragraph(str(match.quantity_requested), self.styles['TableCellRight']),
                    Paragraph(match.unit, self.styles['TableCell']),
                    Paragraph(f"{match.price:.2f}", self.styles['TableCellRight']),
                    Paragraph(f"{total:.2f}", self.styles['TableCellRight'])
                ]
                table_data.append(row)
        
        # Create table
        products_table = Table(table_data, colWidths=[3*cm, 6*cm, 1.5*cm, 1*cm, 2*cm, 2.5*cm])
        products_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            
            # Alternate row coloring
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        story.append(products_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_totals_section(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create totals section."""
        story = []
        
        lemonsoft_offer = offer_data.get('lemonsoft_offer')
        
        if lemonsoft_offer:
            subtotal = lemonsoft_offer.subtotal
            vat_amount = lemonsoft_offer.vat_amount
            total_amount = lemonsoft_offer.total_amount
            currency = lemonsoft_offer.currency
        else:
            total_amount = offer_data.get('total_amount', 0)
            subtotal = total_amount / 1.255  # Assume 25.5% VAT
            vat_amount = total_amount - subtotal
            currency = 'EUR'
        
        # Create totals table
        totals_data = [
            ['', '', '', 'Yhteensä (alv 0%):', f"{subtotal:.2f} {currency}"],
            ['', '', '', 'ALV (25.5%):', f"{vat_amount:.2f} {currency}"],
            ['', '', '', '', ''],
            ['', '', '', 'YHTEENSÄ:', f"{total_amount:.2f} {currency}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[3*cm, 6*cm, 1.5*cm, 3*cm, 2.5*cm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('LINEBELOW', (3, 2), (-1, 2), 1, colors.black),
            ('FONTNAME', (3, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (3, 3), (-1, 3), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _create_terms_section(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create terms and conditions section."""
        story = []
        
        # Section header
        story.append(Paragraph("Toimitusehdot", self.styles['SectionHeader']))
        
        lemonsoft_offer = offer_data.get('lemonsoft_offer')
        
        # Terms content
        terms = []
        
        if lemonsoft_offer:
            if lemonsoft_offer.payment_terms:
                terms.append(f"Maksuehdot: {lemonsoft_offer.payment_terms}")
            
            if lemonsoft_offer.delivery_terms:
                terms.append(f"Toimitusehdot: {lemonsoft_offer.delivery_terms}")
            
            if lemonsoft_offer.notes:
                terms.append(f"Lisätiedot: {lemonsoft_offer.notes}")
        
        # Default terms
        default_terms = [
            "Hinnat ovat voimassa 30 päivää tarjouksen päivämäärästä.",
            "Hinnat sisältävät arvonlisäveron 25.5%.",
            "Toimitusaika normaalisti 2-3 arkipäivää.",
            "Reklamaatiot tulee tehdä 7 päivän kuluessa toimituksesta."
        ]
        
        all_terms = terms + default_terms
        
        for term in all_terms:
            story.append(Paragraph(f"• {term}", self.styles['Terms']))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_footer_section(self, offer_data: Dict[str, Any], template: DocumentTemplate) -> List:
        """Create footer section."""
        story = []
        
        # Thank you message
        story.append(Paragraph("Kiitos kiinnostuksestanne!", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        # Contact information
        contact_text = (
            f"Lisätietoja antaa: {self.company_info['email']} | "
            f"Puh: {self.company_info['phone']} | "
            f"{self.company_info['website']}"
        )
        story.append(Paragraph(contact_text, self.styles['Footer']))
        
        return story
    
    def _create_page_header(self, canvas_obj, doc):
        """Create page header with company info."""
        canvas_obj.saveState()
        
        # Add a subtle header line
        canvas_obj.setStrokeColor(colors.HexColor('#1f4788'))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(doc.leftMargin, doc.height + doc.topMargin - 30, 
                       doc.width + doc.leftMargin, doc.height + doc.topMargin - 30)
        
        # Page number (except first page)
        if hasattr(doc, 'page') and doc.page > 1:
            canvas_obj.setFont('Helvetica', 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            canvas_obj.drawRightString(
                doc.width + doc.leftMargin, 
                doc.height + doc.topMargin - 20,
                f"Sivu {doc.page}"
            )
        
        canvas_obj.restoreState()
    
    def _select_template(self, offer_data: Dict[str, Any]) -> DocumentTemplate:
        """Select appropriate template based on offer data."""
        # For now, default to Finnish template
        return self.templates['offer_fi']
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove extra spaces and limit length
        sanitized = '_'.join(sanitized.split())
        return sanitized[:50]  # Limit to 50 characters
    
    async def get_document(self, document_id: str) -> Optional[GeneratedDocument]:
        """Retrieve generated document by ID."""
        # In a real implementation, this would query a database
        # For now, this is a placeholder
        return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete generated document."""
        try:
            # In a real implementation, this would remove from database and filesystem
            self.logger.info(f"Document {document_id} deletion requested")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def get_document_url(self, document: GeneratedDocument, expires_in_hours: int = 24) -> str:
        """Generate download URL for document."""
        # In a real implementation, this would generate a signed URL
        return f"/documents/download/{document.document_id}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of document generation system."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'output_directory': str(self.output_dir),
            'output_directory_exists': self.output_dir.exists(),
            'templates_available': len(self.templates),
            'disk_space_available': True  # Simplified check
        }
        
        try:
            # Check if output directory is writable
            test_file = self.output_dir / 'test_write.tmp'
            test_file.write_text('test')
            test_file.unlink()
            health_status['output_directory_writable'] = True
        except Exception as e:
            health_status['output_directory_writable'] = False
            health_status['status'] = 'degraded'
            health_status['error'] = str(e)
        
        return health_status