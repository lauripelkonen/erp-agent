"""
Email content parsing and preprocessing for offer automation.
Handles Gmail API data, attachments, and natural language processing.
"""

import re
import email
import base64
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
import openpyxl
from io import BytesIO

from config.settings import get_settings
from utils.logger import get_logger
from utils.exceptions import EmailParsingError, AttachmentProcessingError


class EmailParser:
    """Enhanced email parser for Gmail API integration and content extraction."""
    
    def __init__(self):
        """Initialize email parser with configuration."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
    
    async def parse_email(self, email_content: Union[str, Dict], attachments: List[Dict] = None) -> Dict[str, Any]:
        """
        Parse email content and attachments into structured data.
        
        Args:
            email_content: Either raw email text or Gmail API email data dict
            attachments: List of attachment data (file content or Gmail attachment info)
            
        Returns:
            Dict containing parsed customer info, product requests, and metadata
        """
        try:
            # Handle different input formats
            if isinstance(email_content, dict):
                # Gmail API format
                return await self._parse_gmail_api_data(email_content, attachments)
            else:
                # Raw email text format
                return await self._parse_raw_email(email_content, attachments)
                
        except Exception as e:
            self.logger.error(f"Failed to parse email: {e}")
            raise EmailParsingError(
                f"Failed to parse email content: {str(e)}",
                context={'content_type': type(email_content).__name__}
            )
    
    async def _parse_gmail_api_data(self, email_data: Dict, attachments: List[Dict] = None) -> Dict[str, Any]:
        """Parse Gmail API email data format."""
        try:
            headers = email_data.get('headers', {})
            body = email_data.get('body', '')
            
            # Extract basic email metadata
            sender = headers.get('From', '')
            subject = headers.get('Subject', '')
            received_date = email_data.get('timestamp')
            
            self.logger.info(
                f"Parsing Gmail API email",
                extra={
                    'extra_fields': {
                        'sender': sender,
                        'subject': subject,
                        'message_id': email_data.get('message_id')
                    }
                }
            )
            
            # Parse customer information from email
            customer_info = self._extract_customer_info(body, sender, subject)
            
            # Parse product requests from email body
            product_requests = self._extract_product_requests(body)
            
            # Process attachments if provided
            attachment_data = []
            if attachments:
                attachment_data = await self._process_attachments(attachments)
                # Merge attachment product data with email requests
                for att_data in attachment_data:
                    if att_data.get('products'):
                        product_requests.extend(att_data['products'])
            
            return {
                'customer_info': customer_info,
                'product_requests': product_requests,
                'email_metadata': {
                    'sender': sender,
                    'subject': subject,
                    'received_date': received_date,
                    'message_id': email_data.get('message_id'),
                    'body_length': len(body),
                    'attachment_count': len(attachment_data)
                },
                'attachments_processed': attachment_data
            }
            
        except Exception as e:
            raise EmailParsingError(
                f"Failed to parse Gmail API data: {str(e)}",
                context={'email_keys': list(email_data.keys()) if email_data else []}
            )
    
    async def _parse_raw_email(self, email_content: str, attachments: List[Dict] = None) -> Dict[str, Any]:
        """Parse raw email text format."""
        try:
            # For raw text, treat the entire content as the body
            customer_info = self._extract_customer_info(email_content, '', '')
            product_requests = self._extract_product_requests(email_content)
            
            # Process attachments if provided
            attachment_data = []
            if attachments:
                attachment_data = await self._process_attachments(attachments)
                for att_data in attachment_data:
                    if att_data.get('products'):
                        product_requests.extend(att_data['products'])
            
            return {
                'customer_info': customer_info,
                'product_requests': product_requests,
                'email_metadata': {
                    'sender': 'unknown',
                    'subject': 'raw_content',
                    'received_date': datetime.utcnow().isoformat(),
                    'body_length': len(email_content),
                    'attachment_count': len(attachment_data)
                },
                'attachments_processed': attachment_data
            }
            
        except Exception as e:
            raise EmailParsingError(
                f"Failed to parse raw email: {str(e)}",
                context={'content_length': len(email_content) if email_content else 0}
            )
    
    def _extract_customer_info(self, body: str, sender: str = '', subject: str = '') -> Dict[str, Any]:
        """
        Extract customer identification information from email content.
        
        Args:
            body: Email body text
            sender: Sender email address
            subject: Email subject line
            
        Returns:
            Dict containing potential customer identifiers
        """
        customer_info = {
            'email_address': sender,
            'potential_names': [],
            'company_indicators': [],
            'contact_info': {},
            'search_terms': []
        }
        
        # Extract email domain for company identification
        if sender and '@' in sender:
            domain = sender.split('@')[1]
            if not domain.endswith(('.gmail.com', '.hotmail.com', '.yahoo.com', '.outlook.com')):
                customer_info['company_indicators'].append(domain)
        
        # Extract potential company names from email body
        company_patterns = [
            r'(?:from|regards|sincerely),?\s*([A-Z][a-zA-Z\s&.,]+(?:OY|Oy|Ltd|AB|Inc|Corp|Company))',
            r'([A-Z][a-zA-Z\s&.,]+(?:OY|Oy|Ltd|AB|Inc|Corp|Company))',
            r'([A-Z][a-zA-Z\s&.,]{3,30})\s*(?:needs|requires|ordering|would like)',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip(' .,')
                if len(clean_match) > 2:
                    customer_info['potential_names'].append(clean_match)
        
        # Extract contact information
        phone_pattern = r'(\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9})'
        phones = re.findall(phone_pattern, body)
        if phones:
            customer_info['contact_info']['phones'] = phones
        
        # Extract potential person names from signature
        name_patterns = [
            r'(?:best regards|regards|sincerely),?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\n.*(?:manager|director|sales)',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                customer_info['potential_names'].append(match.strip())
        
        # Create search terms for customer lookup
        all_terms = (
            customer_info['potential_names'] + 
            customer_info['company_indicators'] +
            [sender.split('@')[0] if '@' in sender else '']
        )
        
        # Clean and deduplicate search terms
        search_terms = []
        for term in all_terms:
            if term and len(term) > 2:
                # Remove common email artifacts
                clean_term = re.sub(r'[<>"\']', '', term)
                if clean_term not in search_terms:
                    search_terms.append(clean_term)
        
        customer_info['search_terms'] = search_terms[:10]  # Limit to top 10 terms
        
        self.logger.debug(
            f"Extracted customer info",
            extra={
                'extra_fields': {
                    'search_terms_count': len(search_terms),
                    'company_indicators': len(customer_info['company_indicators']),
                    'potential_names': len(customer_info['potential_names'])
                }
            }
        )
        
        return customer_info
    
    def _extract_product_requests(self, body: str) -> List[Dict[str, Any]]:
        """
        Extract product requests from email body text.
        
        Args:
            body: Email body text
            
        Returns:
            List of product request dictionaries
        """
        product_requests = []
        
        # Pattern for product codes (assuming Finnish product codes)
        product_code_pattern = r'\b(\d{6,8})\b'
        product_codes = re.findall(product_code_pattern, body)
        
        # Pattern for quantity + product description
        quantity_product_patterns = [
            r'(\d+)\s*(?:pcs|pc|kpl|pieces?)\s*(?:of\s*)?([A-Z][A-Za-z\s\-,]+)',
            r'(\d+)\s*x\s*([A-Z][A-Za-z\s\-,]+)',
            r'(\d+)\s+([A-Z][A-Za-z\s\-,]{5,})',
        ]
        
        for pattern in quantity_product_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for quantity, description in matches:
                product_requests.append({
                    'type': 'description_with_quantity',
                    'quantity': int(quantity),
                    'description': description.strip(' .,'),
                    'confidence': 0.8
                })
        
        # Pattern for product descriptions without explicit quantities
        description_patterns = [
            r'(?:need|require|want|order)\s+([A-Z][A-Za-z\s\-,]{5,})',
            r'([A-Z][A-Za-z\s\-,]{5,})\s*(?:needed|required|urgent)',
        ]
        
        for pattern in description_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for description in matches:
                clean_desc = description.strip(' .,')
                if len(clean_desc) > 5:
                    product_requests.append({
                        'type': 'description_only',
                        'quantity': 1,  # Default quantity
                        'description': clean_desc,
                        'confidence': 0.6
                    })
        
        # Add product codes as high-confidence requests
        for code in product_codes:
            product_requests.append({
                'type': 'product_code',
                'product_code': code,
                'quantity': 1,  # Default quantity
                'confidence': 0.9
            })
        
        # Remove duplicates and limit to reasonable number
        unique_requests = []
        seen_descriptions = set()
        
        for request in product_requests:
            desc_key = request.get('description', request.get('product_code', ''))
            if desc_key.lower() not in seen_descriptions:
                seen_descriptions.add(desc_key.lower())
                unique_requests.append(request)
        
        self.logger.info(
            f"Extracted {len(unique_requests)} product requests from email",
            extra={
                'extra_fields': {
                    'product_codes': len(product_codes),
                    'total_requests': len(product_requests),
                    'unique_requests': len(unique_requests)
                }
            }
        )
        
        return unique_requests[:20]  # Limit to 20 requests per email
    
    async def _process_attachments(self, attachments: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process email attachments to extract product data.
        
        Args:
            attachments: List of attachment data
            
        Returns:
            List of processed attachment data
        """
        processed_attachments = []
        
        for attachment in attachments:
            try:
                filename = attachment.get('filename', 'unknown')
                self.logger.info(f"Processing attachment: {filename}")
                
                # Check if it's a supported file type
                if not self._is_supported_attachment(filename):
                    self.logger.warning(f"Unsupported attachment type: {filename}")
                    continue
                
                # Get file content
                content = attachment.get('content')
                if not content:
                    self.logger.warning(f"No content found for attachment: {filename}")
                    continue
                
                # Process based on file type
                if filename.lower().endswith(('.xlsx', '.xls')):
                    attachment_data = await self._process_excel_attachment(content, filename)
                elif filename.lower().endswith('.csv'):
                    attachment_data = await self._process_csv_attachment(content, filename)
                else:
                    continue
                
                attachment_data['filename'] = filename
                processed_attachments.append(attachment_data)
                
            except Exception as e:
                self.logger.error(f"Failed to process attachment {filename}: {e}")
                raise AttachmentProcessingError(
                    f"Failed to process attachment",
                    attachment_name=filename,
                    context={'error': str(e)}
                )
        
        return processed_attachments
    
    def _is_supported_attachment(self, filename: str) -> bool:
        """Check if attachment file type is supported."""
        supported_extensions = ['.xlsx', '.xls', '.csv']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    async def _process_excel_attachment(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process Excel attachment to extract product data."""
        try:
            # Load Excel file
            workbook = openpyxl.load_workbook(BytesIO(content))
            sheet = workbook.active
            
            # Convert to DataFrame for easier processing
            data = []
            headers = []
            
            # Get headers from first row
            for cell in sheet[1]:
                headers.append(cell.value or f"Column_{len(headers)}")
            
            # Get data rows
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(cell is not None for cell in row):
                    data.append(row)
            
            df = pd.DataFrame(data, columns=headers)
            
            # Extract product information
            products = self._extract_products_from_dataframe(df, filename)
            
            return {
                'type': 'excel',
                'products': products,
                'row_count': len(df),
                'columns': headers
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process Excel file {filename}: {e}")
            raise AttachmentProcessingError(
                f"Failed to process Excel attachment: {str(e)}",
                attachment_name=filename
            )
    
    async def _process_csv_attachment(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process CSV attachment to extract product data."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(BytesIO(content), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not decode CSV file with any supported encoding")
            
            # Extract product information
            products = self._extract_products_from_dataframe(df, filename)
            
            return {
                'type': 'csv',
                'products': products,
                'row_count': len(df),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process CSV file {filename}: {e}")
            raise AttachmentProcessingError(
                f"Failed to process CSV attachment: {str(e)}",
                attachment_name=filename
            )
    
    def _extract_products_from_dataframe(self, df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
        """Extract product information from DataFrame."""
        products = []
        
        # Common column name mappings
        column_mappings = {
            'product_code': ['tuotekoodi', 'product_code', 'code', 'sku', 'item_code'],
            'product_name': ['tuotenimi', 'product_name', 'name', 'description', 'item_name'],
            'quantity': ['quantity', 'qty', 'määrä', 'kpl', 'amount'],
            'price': ['price', 'hinta', 'unit_price', 'ovh'],
            'unit': ['unit', 'yksikkö', 'uom']
        }
        
        # Find matching columns
        column_map = {}
        for standard_name, possible_names in column_mappings.items():
            for col in df.columns:
                if any(possible.lower() in col.lower() for possible in possible_names):
                    column_map[standard_name] = col
                    break
        
        # Extract products from each row
        for index, row in df.iterrows():
            try:
                product = {'type': 'attachment_product', 'confidence': 0.9}
                
                # Extract available fields
                if 'product_code' in column_map:
                    code = row[column_map['product_code']]
                    if pd.notna(code):
                        product['product_code'] = str(code).strip()
                
                if 'product_name' in column_map:
                    name = row[column_map['product_name']]
                    if pd.notna(name):
                        product['description'] = str(name).strip()
                
                if 'quantity' in column_map:
                    qty = row[column_map['quantity']]
                    if pd.notna(qty):
                        try:
                            product['quantity'] = float(qty)
                        except (ValueError, TypeError):
                            product['quantity'] = 1
                else:
                    product['quantity'] = 1
                
                if 'price' in column_map:
                    price = row[column_map['price']]
                    if pd.notna(price):
                        try:
                            product['suggested_price'] = float(price)
                        except (ValueError, TypeError):
                            pass
                
                if 'unit' in column_map:
                    unit = row[column_map['unit']]
                    if pd.notna(unit):
                        product['unit'] = str(unit).strip()
                
                # Only add product if it has either code or description
                if 'product_code' in product or 'description' in product:
                    product['source_file'] = filename
                    product['source_row'] = index + 2  # +2 for 1-indexed and header row
                    products.append(product)
                    
            except Exception as e:
                self.logger.warning(f"Failed to process row {index} in {filename}: {e}")
                continue
        
        self.logger.info(
            f"Extracted {len(products)} products from {filename}",
            extra={
                'extra_fields': {
                    'filename': filename,
                    'total_rows': len(df),
                    'products_extracted': len(products),
                    'columns_mapped': list(column_map.keys())
                }
            }
        )
        
        return products 