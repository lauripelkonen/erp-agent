"""
PDF processor module for extracting and filtering PDF attachments in HVAC offer analysis
Uses Mistral OCR as primary method with standard PDF extraction as fallback
"""
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import base64

from google import genai
from google.genai import types
from .config import Config

# Mistral OCR imports
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError as e:
    MISTRAL_AVAILABLE = False
    # Log detailed import error for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🐛 DEBUG: Mistral import failed - ImportError: {e}")
    logger.info(f"🐛 DEBUG: Import error type: {type(e).__name__}")
    import traceback
    logger.info(f"🐛 DEBUG: Full import traceback: {traceback.format_exc()}")
except Exception as e:
    MISTRAL_AVAILABLE = False
    # Log any other import errors
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🐛 DEBUG: Mistral import failed - {type(e).__name__}: {e}")
    import traceback
    logger.info(f"🐛 DEBUG: Full import traceback: {traceback.format_exc()}")
    Mistral = None

class PDFProcessor:
    """Handles PDF attachment extraction and content filtering using Mistral OCR as primary method"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # Initialize Mistral OCR client if available
        self.mistral_client = None
        self.logger.info(f"🐛 DEBUG: MISTRAL_AVAILABLE: {MISTRAL_AVAILABLE}")
        self.logger.info(f"🐛 DEBUG: hasattr(Config, 'MISTRAL_API_KEY'): {hasattr(Config, 'MISTRAL_API_KEY')}")
        if hasattr(Config, 'MISTRAL_API_KEY'):
            self.logger.info(f"🐛 DEBUG: MISTRAL_API_KEY length: {len(Config.MISTRAL_API_KEY) if Config.MISTRAL_API_KEY else 0}")

        
        if MISTRAL_AVAILABLE and hasattr(Config, 'MISTRAL_API_KEY') and Config.MISTRAL_API_KEY:
            try:
                self.logger.info(f"🐛 DEBUG: Attempting to initialize Mistral client...")
                self.mistral_client = Mistral(api_key=Config.MISTRAL_API_KEY)
                self.logger.info("✅ Mistral OCR client initialized as primary PDF processing method")
            except Exception as e:
                self.logger.warning(f"🐛 DEBUG: Failed to initialize Mistral OCR client: {e}")
                import traceback
                self.logger.error(f"🐛 DEBUG: Full traceback: {traceback.format_exc()}")
                self.mistral_client = None
        else:
            if not MISTRAL_AVAILABLE:
                self.logger.info("🐛 DEBUG: Mistral import not available")
            if not hasattr(Config, 'MISTRAL_API_KEY'):
                self.logger.info("🐛 DEBUG: Config.MISTRAL_API_KEY not found")
            if hasattr(Config, 'MISTRAL_API_KEY') and not Config.MISTRAL_API_KEY:
                self.logger.info("🐛 DEBUG: Config.MISTRAL_API_KEY is None or empty")
            self.logger.info("ℹ️ Mistral OCR not available - using standard PDF processing only")
        
        # Statistics
        self.processed_pdfs = 0
        self.filtered_pdfs = 0
        self.api_calls_made = 0
        self.api_errors = 0
        self.ocr_fallback_used = 0
        self.ocr_success_count = 0
    
    def extract_pdf_content(self, filtered_emails: List[Dict]) -> List[Dict]:
        """
        Extract and filter PDF content from email attachments
        
        Args:
            filtered_emails: List of filtered email dictionaries
            
        Returns:
            List of PDF data dictionaries with filtered content
        """
        self.logger.info("Starting PDF attachment processing...")
        
        pdf_data = []
        
        for email in filtered_emails:
            attachments = email.get('attachments', [])
            self.logger.info(f"🐛 DEBUG: Email has {len(attachments)} total attachments")
            
            for i, att in enumerate(attachments):
                self.logger.info(f"🐛 DEBUG: Attachment {i+1}: type={type(att)}, keys={list(att.keys()) if isinstance(att, dict) else 'NOT A DICT'}")
                if isinstance(att, dict):
                    self.logger.info(f"🐛 DEBUG: Attachment {i+1} filename: {att.get('filename', 'NO_FILENAME')}")
                    self.logger.info(f"🐛 DEBUG: Attachment {i+1} size: {att.get('size', 'NO_SIZE')}")
                    self.logger.info(f"🐛 DEBUG: Attachment {i+1} mime_type: {att.get('mime_type', 'NO_MIME_TYPE')}")
            
            pdf_attachments = [att for att in attachments if att.get('filename', '').lower().endswith('.pdf')]
            self.logger.info(f"🐛 DEBUG: Found {len(pdf_attachments)} PDF attachments out of {len(attachments)} total")
            
            if not pdf_attachments:
                continue
            
            # Limit to first 10 PDF attachments
            if len(pdf_attachments) > 10:
                self.logger.info(f"Found {len(pdf_attachments)} PDFs, processing first 10")
                pdf_attachments = pdf_attachments[:10]
            
            self.logger.info(f"Processing {len(pdf_attachments)} PDF attachments for email: {email.get('subject', '')[:50]}")
            
            # Extract content from PDFs
            pdf_contents = self._extract_pdf_attachments(pdf_attachments, email)
            
            if pdf_contents:
                # Filter PDFs that contain product lists
                relevant_pdfs = self._filter_relevant_pdfs(pdf_contents, email)
                
                if relevant_pdfs:
                    pdf_data.append({
                        'email_subject': email.get('subject', ''),
                        'email_date': email.get('date'),
                        'email_sender': email.get('sender', ''),
                        'pdf_contents': relevant_pdfs
                    })
        
        self.logger.info(f"PDF processing complete. Processed {self.processed_pdfs} PDFs, "
                        f"filtered {self.filtered_pdfs} relevant PDFs")
        
        return pdf_data
    
    def _extract_pdf_attachments(self, pdf_attachments: List[Dict], email: Dict) -> List[Dict]:
        """
        Extract content from PDF attachments
        
        Args:
            pdf_attachments: List of PDF attachment dictionaries
            email: Email context
            
        Returns:
            List of PDF content dictionaries
        """
        self.logger.info(f"🐛 DEBUG: _extract_pdf_attachments called with {len(pdf_attachments)} PDFs")
        pdf_contents = []
        
        for i, attachment in enumerate(pdf_attachments):
            try:
                self.logger.info(f"🐛 DEBUG: Processing PDF attachment {i+1}/{len(pdf_attachments)}")
                self.logger.info(f"🐛 DEBUG: Attachment type: {type(attachment)}")
                self.logger.info(f"🐛 DEBUG: Attachment keys: {list(attachment.keys()) if isinstance(attachment, dict) else 'NOT A DICT'}")
                
                filename = attachment.get('filename', 'unknown.pdf')
                self.logger.info(f"🐛 DEBUG: Processing PDF filename: {filename}")
                
                content_data = self._get_attachment_binary_content(attachment)
                
                if not content_data:
                    self.logger.warning(f"🐛 DEBUG: No content data for PDF: {filename}")
                    continue
                else:
                    self.logger.info(f"🐛 DEBUG: Successfully got content data for {filename}, size: {len(content_data)} bytes")
                
                # Save to temporary file for processing
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(content_data)
                    temp_path = temp_file.name
                
                try:
                    # Check page count and extract content
                    page_count, full_content, preview_content = self._process_pdf_file(temp_path, content_data, filename)
                    
                    if page_count is None or not full_content:
                        continue
                    
                    self.processed_pdfs += 1
                    
                    # Truncate each PDF to 40k characters max (will apply 120k total limit later)
                    MAX_SINGLE_PDF_CHARS = 40000
                    truncated_content = full_content[:MAX_SINGLE_PDF_CHARS]
                    
                    pdf_contents.append({
                        'filename': filename,
                        'page_count': page_count,
                        'preview_content': preview_content,  # First 4000 chars
                        'full_content': truncated_content,   # Truncated to 40k chars max
                        'original_length': len(full_content),
                        'email_subject': email.get('subject', ''),
                        'email_date': email.get('date')
                    })
                    
                    truncation_note = f" (truncated from {len(full_content)})" if len(full_content) > MAX_SINGLE_PDF_CHARS else ""
                    self.logger.info(f"Extracted PDF content: {filename} ({page_count} pages, "
                                   f"{len(truncated_content)} chars{truncation_note})")
                
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
            except Exception as e:
                self.logger.error(f"Error processing PDF {attachment.get('filename', 'unknown')}: {e}")
                continue
        
        return pdf_contents
    
    def _get_attachment_binary_content(self, attachment: Dict) -> Optional[bytes]:
        """Extract binary content from the attachment"""
        try:
            self.logger.info(f"🐛 DEBUG: _get_attachment_binary_content called for attachment")
            self.logger.info(f"🐛 DEBUG: Attachment type: {type(attachment)}")
            self.logger.info(f"🐛 DEBUG: Attachment keys: {list(attachment.keys()) if isinstance(attachment, dict) else 'NOT A DICT'}")
            
            if isinstance(attachment, dict):
                for key, value in attachment.items():
                    if key in ['data', 'content', 'attachment_object']:
                        self.logger.info(f"🐛 DEBUG: Key '{key}' -> type: {type(value)}, "
                                       f"length: {len(value) if hasattr(value, '__len__') else 'N/A'}")
                    else:
                        self.logger.info(f"🐛 DEBUG: Key '{key}' -> {str(value)[:100]}...")
            
            # For Gmail attachments, binary data is stored directly in 'data' field
            if 'data' in attachment:
                data = attachment['data']
                self.logger.info(f"🐛 DEBUG: Found 'data' field, type: {type(data)}, length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                if isinstance(data, bytes):
                    self.logger.info(f"🐛 DEBUG: Data is bytes, returning {len(data)} bytes")
                    return data
                else:
                    self.logger.warning(f"🐛 DEBUG: Data is not bytes, it's {type(data)}, trying to convert")
                    if hasattr(data, 'encode'):
                        return data.encode()
                    else:
                        self.logger.error(f"🐛 DEBUG: Cannot convert data to bytes")
                        return None
            
            # For custom AttachmentObject from Gmail conversion
            elif 'attachment_object' in attachment:
                self.logger.info(f"🐛 DEBUG: Processing custom attachment_object")
                attachment_obj = attachment['attachment_object']
                self.logger.info(f"🐛 DEBUG: attachment_object type: {type(attachment_obj)}")
                self.logger.info(f"🐛 DEBUG: attachment_object attributes: {[attr for attr in dir(attachment_obj) if not attr.startswith('_')]}")
                
                # Try different methods to access binary content from custom AttachmentObject
                try:
                    # Method 1: Try .data attribute
                    if hasattr(attachment_obj, 'data'):
                        self.logger.info(f"🐛 DEBUG: Trying attachment_obj.data")
                        data = attachment_obj.data
                        self.logger.info(f"🐛 DEBUG: attachment_obj.data type: {type(data)}, length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                        if isinstance(data, bytes):
                            return data
                        elif data is not None:
                            self.logger.warning(f"🐛 DEBUG: attachment_obj.data is not bytes: {type(data)}")
                    
                    # Method 2: Try .content attribute
                    if hasattr(attachment_obj, 'content'):
                        self.logger.info(f"🐛 DEBUG: Trying attachment_obj.content")
                        content = attachment_obj.content
                        self.logger.info(f"🐛 DEBUG: attachment_obj.content type: {type(content)}, length: {len(content) if hasattr(content, '__len__') else 'N/A'}")
                        if isinstance(content, bytes):
                            return content
                        elif content is not None:
                            self.logger.warning(f"🐛 DEBUG: attachment_obj.content is not bytes: {type(content)}")
                    
                    # Method 3: Try .get_data() method
                    if hasattr(attachment_obj, 'get_data'):
                        self.logger.info(f"🐛 DEBUG: Trying attachment_obj.get_data()")
                        data = attachment_obj.get_data()
                        self.logger.info(f"🐛 DEBUG: attachment_obj.get_data() type: {type(data)}, length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                        if isinstance(data, bytes):
                            return data
                        elif data is not None:
                            self.logger.warning(f"🐛 DEBUG: attachment_obj.get_data() is not bytes: {type(data)}")
                    
                    # Method 4: Try calling the object if it's callable
                    if callable(attachment_obj):
                        self.logger.info(f"🐛 DEBUG: Trying to call attachment_obj()")
                        data = attachment_obj()
                        self.logger.info(f"🐛 DEBUG: attachment_obj() type: {type(data)}, length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                        if isinstance(data, bytes):
                            return data
                        elif data is not None:
                            self.logger.warning(f"🐛 DEBUG: attachment_obj() is not bytes: {type(data)}")
                    
                    self.logger.warning(f"🐛 DEBUG: Could not extract binary data from custom attachment_object")
                    return None
                    
                except Exception as e:
                    self.logger.warning(f"🐛 DEBUG: Error accessing custom attachment_object content: {e}")
                    import traceback
                    self.logger.error(f"🐛 DEBUG: Full traceback: {traceback.format_exc()}")
                    return None
            
            # For libratom attachments, the attachment object is stored
            elif attachment.get('source') == 'libratom':
                self.logger.info(f"🐛 DEBUG: Processing libratom attachment")
                attachment_obj = attachment.get('attachment_object')
                if attachment_obj:
                    self.logger.info(f"🐛 DEBUG: attachment_object type: {type(attachment_obj)}")
                    self.logger.info(f"🐛 DEBUG: attachment_object attributes: {dir(attachment_obj)}")
                    # Try different methods to access binary content from libratom
                    try:
                        # Method 1: Try .read_buffer() method (pypff specific)
                        if hasattr(attachment_obj, 'read_buffer'):
                            self.logger.info(f"🐛 DEBUG: Trying read_buffer method")
                            # Read the entire attachment content
                            size = attachment_obj.size
                            return attachment_obj.read_buffer(size)
                        # Method 2: Try .data attribute
                        elif hasattr(attachment_obj, 'data'):
                            self.logger.info(f"🐛 DEBUG: Trying data attribute")
                            return attachment_obj.data
                        # Method 3: Try .content attribute
                        elif hasattr(attachment_obj, 'content'):
                            self.logger.info(f"🐛 DEBUG: Trying content attribute")
                            return attachment_obj.content
                        # Method 4: Try calling the object if it's callable
                        elif callable(attachment_obj):
                            self.logger.info(f"🐛 DEBUG: Trying callable object")
                            return attachment_obj()
                        # Method 5: Try .read() method
                        elif hasattr(attachment_obj, 'read'):
                            self.logger.info(f"🐛 DEBUG: Trying read method")
                            return attachment_obj.read()
                        # Method 6: Try .get_data() method
                        elif hasattr(attachment_obj, 'get_data'):
                            self.logger.info(f"🐛 DEBUG: Trying get_data method")
                            return attachment_obj.get_data()
                        # Method 7: Try .bytes property
                        elif hasattr(attachment_obj, 'bytes'):
                            self.logger.info(f"🐛 DEBUG: Trying bytes property")
                            return attachment_obj.bytes
                        else:
                            self.logger.warning(f"🐛 DEBUG: Unknown libratom attachment object type: {type(attachment_obj)}")
                            self.logger.debug(f"🐛 DEBUG: Available attributes: {dir(attachment_obj)}")
                            return None
                    except Exception as e:
                        self.logger.warning(f"🐛 DEBUG: Error accessing libratom attachment content: {e}")
                        return None
                else:
                    self.logger.warning(f"🐛 DEBUG: No attachment_object found in libratom attachment")
            else:
                self.logger.info(f"🐛 DEBUG: Processing as Aspose.Email attachment")
                # For Aspose.Email attachments
                content = attachment.get('content')
                self.logger.info(f"🐛 DEBUG: Found 'content' field, type: {type(content)}, "
                               f"length: {len(content) if hasattr(content, '__len__') else 'N/A'}")
                return content
                
        except Exception as e:
            self.logger.error(f"🐛 DEBUG: Error extracting binary content: {e}")
            import traceback
            self.logger.error(f"🐛 DEBUG: Full traceback: {traceback.format_exc()}")
            return None
        
        self.logger.warning(f"🐛 DEBUG: No valid attachment content found, returning None")
        return None
    
    def _process_pdf_file(self, pdf_path: str, content_data: bytes = None, filename: str = "unknown.pdf") -> tuple:
        """
        Process PDF file and extract content using Mistral OCR as primary method
        
        Args:
            pdf_path: Path to PDF file
            content_data: Binary content of PDF (for Mistral OCR)
            filename: Original filename for logging
            
        Returns:
            Tuple of (page_count, full_content, preview_content)
        """
        # Use Mistral OCR as primary method if available
        self.logger.info(f"🐛 DEBUG: Mistral client available: {self.mistral_client is not None}")
        self.logger.info(f"🐛 DEBUG: Content data available: {content_data is not None}, size: {len(content_data) if content_data else 'N/A'}")
        
        if self.mistral_client and content_data:
            self.logger.info(f"🔍 Using Mistral OCR as primary method for {filename}")
            ocr_result = self._extract_with_mistral_ocr(content_data, filename)
            if ocr_result:
                page_count, full_content = ocr_result
                preview_content = full_content[:4000]
                self.ocr_success_count += 1
                self.logger.info(f"✅ Mistral OCR extraction successful for {filename} ({len(full_content)} chars)")
                return page_count, full_content, preview_content
            else:
                self.logger.warning(f"⚠️ Mistral OCR extraction failed for {filename}, trying standard method")
        else:
            if not self.mistral_client:
                self.logger.warning(f"🐛 DEBUG: Mistral client not available, skipping OCR for {filename}")
            if not content_data:
                self.logger.warning(f"🐛 DEBUG: No content data available, skipping OCR for {filename}")
        
        # Fallback to standard PDF processing if Mistral OCR failed or unavailable
        try:
            from langchain_community.document_loaders import PyPDFLoader
            
            # Load PDF with langchain
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            if documents:
                page_count = len(documents)
                full_content = "\n".join([doc.page_content for doc in documents])
                
                # Check if we got meaningful content (not just whitespace/garbage)
                meaningful_content = full_content.strip()
                if len(meaningful_content) > 50:  # At least 50 chars of meaningful content
                    preview_content = full_content[:4000]
                    self.ocr_fallback_used += 1  # Track that we used fallback method
                    self.logger.info(f"✅ Standard PDF extraction successful for {filename}")
                    return page_count, full_content, preview_content
                else:
                    self.logger.warning(f"⚠️ Standard PDF extraction yielded minimal content ({len(meaningful_content)} chars) for {filename}")
            else:
                self.logger.warning(f"⚠️ No documents extracted from PDF: {filename}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Standard PDF extraction failed for {filename}: {e}")
        
        self.logger.error(f"❌ Both Mistral OCR and standard extraction failed for {filename}")
        return None, None, None
    
    def _extract_with_mistral_ocr(self, content_data: bytes, filename: str) -> Optional[tuple]:
        """
        Extract content from PDF using Mistral OCR
        
        Args:
            content_data: Binary PDF content
            filename: Original filename for logging
            
        Returns:
            Tuple of (page_count, full_content) or None if failed
        """
        try:
            self.logger.info(f"🐛 DEBUG: Starting Mistral OCR for {filename}")
            
            # Encode PDF to base64
            base64_pdf = base64.b64encode(content_data).decode('utf-8')
            self.logger.info(f"🐛 DEBUG: Base64 encoded PDF length: {len(base64_pdf)} chars")
            
            # Call Mistral OCR API
            self.api_calls_made += 1
            self.logger.info(f"🐛 DEBUG: Making Mistral OCR API call...")
            
            ocr_response = self.mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                include_image_base64=False  # We don't need images for text extraction
            )
            
            self.logger.info(f"🐛 DEBUG: OCR response received: {type(ocr_response)}")
            self.logger.info(f"🐛 DEBUG: OCR response is None: {ocr_response is None}")
            
            if not ocr_response:
                self.logger.warning(f"🐛 DEBUG: Empty response from Mistral OCR for {filename}")
                return None
            
            # Log response attributes for debugging
            self.logger.info(f"🐛 DEBUG: OCR response attributes: {[attr for attr in dir(ocr_response) if not attr.startswith('_')]}")
            if hasattr(ocr_response, '__dict__'):
                self.logger.info(f"🐛 DEBUG: OCR response dict keys: {list(ocr_response.__dict__.keys())}")
            
            # Extract markdown content from OCR response
            markdown_content = ""
            
            # Mistral OCR returns content in pages[].markdown format
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                self.logger.info(f"🐛 DEBUG: Found pages attribute with {len(ocr_response.pages)} pages")
                # Combine all page content
                page_contents = []
                for page in ocr_response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        page_contents.append(page.markdown)
                        self.logger.info(f"🐛 DEBUG: Page {getattr(page, 'index', '?')} markdown length: {len(page.markdown)}")
                
                markdown_content = "\n".join(page_contents)
                self.logger.info(f"🐛 DEBUG: Combined all pages, total length: {len(markdown_content)}")
            
            elif hasattr(ocr_response, 'content') and ocr_response.content:
                self.logger.info(f"🐛 DEBUG: Found content attribute: {type(ocr_response.content)}")
                markdown_content = ocr_response.content
            elif hasattr(ocr_response, 'text') and ocr_response.text:
                self.logger.info(f"🐛 DEBUG: Found text attribute: {type(ocr_response.text)}")
                markdown_content = ocr_response.text
            else:
                self.logger.info(f"🐛 DEBUG: No pages, content, or text attribute found")
                # Try to extract from response attributes
                self.logger.info(f"🐛 DEBUG: OCR response attributes: {dir(ocr_response)}")
                if hasattr(ocr_response, '__dict__'):
                    self.logger.info(f"🐛 DEBUG: OCR response dict: {ocr_response.__dict__}")
                
                # Look for common content fields
                for attr in ['content', 'text', 'markdown', 'result', 'output', 'data', 'response']:
                    if hasattr(ocr_response, attr):
                        content = getattr(ocr_response, attr)
                        self.logger.info(f"🐛 DEBUG: Attribute '{attr}' found: type={type(content)}, content={str(content)[:200]}...")
                        if content and isinstance(content, str):
                            markdown_content = content
                            break
            
            self.logger.info(f"🐛 DEBUG: Final markdown_content length: {len(markdown_content) if markdown_content else 0}")
            if markdown_content:
                self.logger.info(f"🐛 DEBUG: First 200 chars of content: {markdown_content[:200]}...")
            
            if not markdown_content or len(markdown_content.strip()) < 10:
                self.logger.warning(f"🐛 DEBUG: Minimal or no content from Mistral OCR for {filename} (length: {len(markdown_content.strip()) if markdown_content else 0})")
                return None
            
            # Estimate page count (rough estimate based on content length and typical page breaks)
            # Look for page break indicators in markdown or estimate from content length
            estimated_page_count = max(1, len(markdown_content) // 2000)  # Rough estimate
            
            self.logger.info(f"🔍 Mistral OCR extracted {len(markdown_content)} chars from {filename}")
            return estimated_page_count, markdown_content
            
        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"🐛 DEBUG: Mistral OCR extraction failed for {filename}: {e}")
            import traceback
            self.logger.error(f"🐛 DEBUG: Full traceback: {traceback.format_exc()}")
            return None
    
    def _filter_relevant_pdfs(self, pdf_contents: List[Dict], email: Dict) -> List[Dict]:
        """
        Use LLM to filter PDFs that contain clear product lists
        
        Args:
            pdf_contents: List of PDF content dictionaries
            email: Email context
            
        Returns:
            List of relevant PDF content dictionaries with full content (max 120k chars total)
        """
        if not pdf_contents:
            return []
        
        # Build prompt with preview content from all PDFs
        prompt_parts = ["We have these PDF attachments in an offer request for a Finnish HVAC wholesaler. "
                       "Your task is to decide which PDFs if any include a CLEAR product list of which the customer wants an offer. "
                       "It must be a clear list of products. Below is content from each pdf's first 4000 characters for you to analyze:"]
        
        for i, pdf in enumerate(pdf_contents, 1):
            prompt_parts.append(f"\n\n# PDF {i} CONTENT ({pdf['filename']}):\n{pdf['preview_content']}")
        
        prompt_parts.append("\n\nRespond with only the PDF numbers (e.g., '1,3,5') that contain clear product lists. "
                           "If none contain clear product lists, respond with 'NONE'.")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            self.api_calls_made += 1
            
            config = types.GenerateContentConfig(
                temperature=0.1,
                candidate_count=1,
            )
            
            response = self.gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
            
            if not response:
                self.logger.warning("No response from Gemini API for PDF filtering")
                return []
            
            # Extract response text
            response_text = self._extract_response_text(response)
            if not response_text:
                return []
            
            self.logger.info(f"PDF filtering response: {response_text}")
            
            # Parse response to get relevant PDF indices
            relevant_indices = self._parse_pdf_indices(response_text)
            
            # Return PDFs with full content for relevant indices, applying 120k total limit
            MAX_TOTAL_PDF_CHARS = 120000
            relevant_pdfs = []
            total_chars = 0
            
            for index in relevant_indices:
                if 1 <= index <= len(pdf_contents):
                    pdf = pdf_contents[index - 1]  # Convert to 0-based index
                    pdf_content = pdf['full_content']
                    
                    # Check if adding this PDF would exceed total limit
                    remaining_space = MAX_TOTAL_PDF_CHARS - total_chars
                    if remaining_space <= 0:
                        self.logger.warning(f"Reached 120k char limit, skipping remaining PDFs")
                        break
                    
                    # Truncate if needed to fit within total limit
                    if len(pdf_content) > remaining_space:
                        pdf_content = pdf_content[:remaining_space]
                        self.logger.info(f"Truncated {pdf['filename']} to {remaining_space} chars to fit 120k limit")
                    
                    relevant_pdfs.append({
                        'filename': pdf['filename'],
                        'full_content': pdf_content,
                        'page_count': pdf['page_count']
                    })
                    total_chars += len(pdf_content)
                    self.filtered_pdfs += 1
            
            self.logger.info(f"Filtered {len(relevant_pdfs)} relevant PDFs from {len(pdf_contents)} total ({total_chars} chars total)")
            
            return relevant_pdfs
            
        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"Error filtering PDFs with LLM: {e}")
            return []
    
    def _extract_response_text(self, response) -> Optional[str]:
        """Extract text from Gemini API response"""
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
            self.logger.error(f"Error extracting response text: {e}")
            return None
    
    def _parse_pdf_indices(self, response_text: str) -> List[int]:
        """
        Parse PDF indices from LLM response
        
        Args:
            response_text: Response from LLM
            
        Returns:
            List of PDF indices (1-based)
        """
        if not response_text or response_text.upper().strip() == 'NONE':
            return []
        
        indices = []
        # Look for numbers in the response
        import re
        numbers = re.findall(r'\b(\d+)\b', response_text)
        
        for num_str in numbers:
            try:
                index = int(num_str)
                if index > 0:  # Only positive indices
                    indices.append(index)
            except ValueError:
                continue
        
        return sorted(list(set(indices)))  # Remove duplicates and sort
    
    def get_processing_stats(self) -> Dict:
        """Get PDF processing statistics"""
        return {
            'processed_pdfs': self.processed_pdfs,
            'filtered_pdfs': self.filtered_pdfs,
            'api_calls_made': self.api_calls_made,
            'api_errors': self.api_errors,
            'ocr_fallback_used': self.ocr_fallback_used,
            'ocr_success_count': self.ocr_success_count,
            'mistral_ocr_available': self.mistral_client is not None
        } 

    def _extract_full_content(self, attachment: Dict) -> Optional[str]:
        """Extract full content from PDF for analysis (max 40k chars)"""
        try:
            filename = attachment.get('filename', 'unknown.pdf')
            content_data = self._get_attachment_binary_content(attachment)
            
            if not content_data:
                self.logger.warning(f"No content data for PDF: {filename}")
                return None
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(content_data)
                temp_path = temp_file.name
            
            try:
                # Extract content
                page_count, full_content, preview_content = self._process_pdf_file(temp_path, content_data, filename)
                
                if page_count is None or not full_content:
                    return None
                
                self.processed_pdfs += 1
                
                # Truncate to 40k characters max
                MAX_SINGLE_PDF_CHARS = 40000
                truncated_content = full_content[:MAX_SINGLE_PDF_CHARS]
                
                truncation_note = f" (truncated from {len(full_content)})" if len(full_content) > MAX_SINGLE_PDF_CHARS else ""
                self.logger.info(f"Extracted PDF content: {filename} ({page_count} pages, "
                               f"{len(truncated_content)} chars{truncation_note})")
                
                return truncated_content
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error extracting full content: {e}")
            return None 