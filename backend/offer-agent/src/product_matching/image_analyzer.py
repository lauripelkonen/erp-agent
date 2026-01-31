"""
Image analyzer module for processing inline images from emails using Gemini Vision API
"""
import logging
import tempfile
import os
from typing import List, Dict, Optional
from pathlib import Path
import time

from google import genai
from google.genai import types
from .config import Config

class ImageAnalyzer:
    """Handles inline image extraction and analysis using Gemini Vision API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.processed_images = 0
        self.api_calls_made = 0
        self.api_errors = 0
        self.unclear_terms_found = 0
        self.temp_files_created = []
    
    def analyze_inline_images(self, filtered_emails: List[Dict]) -> List[Dict]:
        """
        Analyze inline images and image attachments from filtered emails **for full textual content only**.

        Extracted image text snippets are appended to each parent email dict under
        the key ``image_texts`` so that other analyzers can include them in a
        combined LLM prompt. A lightweight list of result dicts is also returned
        for optional downstream logging / debugging.
        
        Args:
            filtered_emails: List of filtered email dictionaries
        
        Returns:
            List of dictionaries with extracted text and basic context information
        """
        self.logger.info("Starting inline image analysis...")
        image_text_entries: List[Dict] = []
        
        try:
            for email in filtered_emails:
                email_subject = email.get('subject', 'unknown')[:50]
                self.logger.info(f"🔍 Analyzing email for images: {email_subject}...")
                
                # Process both inline_images and regular image attachments
                all_images = []
                
                # Add inline images if present
                inline_images = email.get('inline_images', [])
                if inline_images:
                    self.logger.info(f"Found {len(inline_images)} inline images in email: {email_subject}...")
                    all_images.extend(inline_images)
                else:
                    self.logger.debug(f"No inline_images key found in email: {email_subject}")
                
                # Add regular image attachments
                attachments = email.get('attachments', [])
                self.logger.info(f"📎 Email has {len(attachments)} total attachments")
                
                if attachments:
                    # Log all attachments for debugging
                    for i, att in enumerate(attachments):
                        att_filename = att.get('filename', 'unknown')
                        att_mime = att.get('mime_type', 'unknown')
                        has_data = 'data' in att and att.get('data') is not None
                        data_size = len(att.get('data', b'')) if has_data else 0
                        self.logger.debug(f"   Attachment {i}: filename='{att_filename}', mime_type='{att_mime}', has_data={has_data}, size={data_size}")
                    
                    image_attachments = [att for att in attachments if self._is_image_attachment(att)]
                    self.logger.info(f"🖼️ Found {len(image_attachments)} image attachments out of {len(attachments)} total in email: {email_subject}")
                    
                    if image_attachments:
                        for img_att in image_attachments:
                            self.logger.info(f"   ✅ Image: {img_att.get('filename', 'unknown')} ({img_att.get('mime_type', 'unknown')})")
                        all_images.extend(image_attachments)
                    else:
                        # Log why attachments weren't recognized as images
                        for att in attachments:
                            filename = att.get('filename', '')
                            mime = att.get('mime_type', '')
                            self.logger.debug(f"   ❌ Not an image: {filename} (mime: {mime})")
                
                # Process all found images
                for image_info in all_images:
                    extracted_text = self._analyze_single_image(image_info, email)

                    # If we managed to read some text, attach it to the parent email
                    if extracted_text:
                        # Keep a list of all extracted texts under the key 'image_texts'
                        email.setdefault('image_texts', []).append(extracted_text)

                        # Also collect a lightweight entry for external use / debugging
                        image_text_entries.append({
                            'email_subject': email.get('subject', ''),
                            'email_date': email.get('date'),
                            'image_filename': image_info.get('filename', 'unknown_image'),
                            'image_text': extracted_text,
                        })
            
            self.logger.info(f"Image analysis complete. Processed {self.processed_images} images, "
                           f"extracted {len(image_text_entries)} image text blocks, "
                           f"made {self.api_calls_made} API calls, errors: {self.api_errors}")
            
        finally:
            # Clean up temporary files
            self._cleanup_temp_files()
        
        return image_text_entries
    
    def _analyze_single_image(self, image_info: Dict, email: Dict) -> Optional[str]:
        """
        Analyze a single inline image and return the **raw extracted text** found in
        the image. No product-level parsing is performed here.

        Args:
            image_info: Image attachment information
            email: Email context information (unused here but kept for potential logging)

        Returns:
            The extracted text as a single string, or ``None`` if extraction failed.
        """
        try:
            # Step 1: write the image to a temporary file we control
            temp_image_path = self._extract_image_to_temp_file(image_info)
            if not temp_image_path:
                return None

            # Step 2: upload to Gemini
            uploaded_file = self._upload_image_to_gemini(temp_image_path)
            if not uploaded_file:
                return None

            # Step 3: call Gemini Vision to perform OCR / text extraction
            extracted_text = self._call_gemini_vision_api(uploaded_file)

            # Simple stat for how many successful extractions we did
            if extracted_text:
                self.unclear_terms_found += 1  # repurpose field for 'texts found'

            return extracted_text

        except Exception as e:
            self.logger.error(f"Error analyzing image {image_info.get('filename', 'unknown')}: {str(e)}")
            self.api_errors += 1
            return None
    
    def _extract_image_to_temp_file(self, image_info: Dict) -> Optional[str]:
        """
        Extract image data from attachment to temporary file
        Handles both standard attachments, multipart images, and Gmail API format
        
        Args:
            image_info: Image attachment information
            
        Returns:
            Path to temporary image file or None if failed
        """
        filename = image_info.get('filename', 'unknown')
        self.logger.info(f"🔄 Extracting image to temp file: {filename}")
        
        try:
            # Check if this is a multipart image (already extracted)
            if image_info.get('source') == 'multipart' and image_info.get('temp_file_path'):
                temp_path = image_info.get('temp_file_path')
                self.temp_files_created.append(temp_path)
                self.processed_images += 1
                self.logger.debug(f"Using pre-extracted multipart image: {temp_path}")
                return temp_path
            
            # Check for Gmail API format first (source == 'gmail' and raw bytes in 'data')
            gmail_source = image_info.get('source') == 'gmail'
            gmail_bytes = image_info.get('data') if isinstance(image_info.get('data'), (bytes, bytearray)) else None
            
            if gmail_source and gmail_bytes:
                self.logger.info(f"📧 Processing Gmail API image attachment: {filename} ({len(gmail_bytes)} bytes)")
            
            # Handle standard attachment object
            attachment_obj = image_info.get('attachment_object')
            
            if not attachment_obj and not gmail_bytes:
                self.logger.error(f"❌ No attachment data found for image: {filename}")
                self.logger.debug(f"   Image info keys: {list(image_info.keys())}")
                self.logger.debug(f"   source: {image_info.get('source')}, has data: {'data' in image_info}")
                return None
            
            # Get image binary data from standard attachment or raw bytes (gmail)
            image_data = None
            
            # Try MapiAttachment.save method (most reliable for Aspose.Email)
            try:
                # Create temporary file to save attachment
                temp_path_for_save = tempfile.NamedTemporaryFile(delete=False).name
                attachment_obj.save(temp_path_for_save)
                
                # Read the saved file
                with open(temp_path_for_save, 'rb') as f:
                    image_data = f.read()
                
                # Clean up temp save file
                os.unlink(temp_path_for_save)
                
                self.logger.debug(f"Extracted image data using save method: {len(image_data)} bytes")
                
            except Exception as save_error:
                self.logger.debug(f"Save method failed: {save_error}")
                
                # Fallback to direct data access methods
                try:
                    if attachment_obj:
                        if hasattr(attachment_obj, 'data') and attachment_obj.data:
                            image_data = attachment_obj.data
                        elif hasattr(attachment_obj, 'content') and attachment_obj.content:
                            image_data = attachment_obj.content
                        elif hasattr(attachment_obj, 'bin_data'):
                            image_data = attachment_obj.bin_data
                        elif hasattr(attachment_obj, 'object_data') and attachment_obj.object_data:
                            if hasattr(attachment_obj.object_data, 'bin_data'):
                                image_data = attachment_obj.object_data.bin_data
                            elif hasattr(attachment_obj.object_data, 'data'):
                                image_data = attachment_obj.object_data.data
                except Exception as direct_error:
                    self.logger.debug(f"Direct data access also failed: {direct_error}")
            
            # If still no data and we have Gmail bytes, use them
            if not image_data and gmail_bytes:
                image_data = gmail_bytes
            
            if not image_data:
                self.logger.error("Could not access image binary data from standard attachment")
                return None
            
            # Determine file extension
            filename = image_info.get('filename', '')
            if filename:
                file_ext = Path(filename).suffix.lower()
                if not file_ext:
                    file_ext = '.jpg'  # Default extension
            else:
                file_ext = '.jpg'  # Default extension
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(bytes(image_data))
                temp_path = temp_file.name
            
            self.temp_files_created.append(temp_path)
            self.processed_images += 1
            
            self.logger.debug(f"Extracted standard attachment image to temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Error extracting image to temp file: {str(e)}")
            return None
    
    def _upload_image_to_gemini(self, image_path: str) -> Optional[object]:
        """
        Upload image file to Gemini for analysis
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Uploaded file object or None if failed
        """
        try:
            # Infer mime type from extension for better compatibility
            ext = Path(image_path).suffix.lower()
            mime = 'image/jpeg'
            if ext == '.png':
                mime = 'image/png'
            elif ext in ['.jpg', '.jpeg']:
                mime = 'image/jpeg'
            elif ext in ['.gif']:
                mime = 'image/gif'
            elif ext in ['.bmp']:
                mime = 'image/bmp'
            elif ext in ['.tif', '.tiff']:
                mime = 'image/tiff'
            elif ext in ['.webp']:
                mime = 'image/webp'

            uploaded_file = self.gemini_client.files.upload(
                file=image_path,
                config=dict(mime_type=mime)
            )
            self.logger.debug(f"Uploaded image to Gemini: {image_path}")
            return uploaded_file
            
        except Exception as e:
            self.logger.error(f"Error uploading image to Gemini: {str(e)}")
            self.api_errors += 1
            return None
    
    def _call_gemini_vision_api(self, uploaded_file) -> Optional[str]:
        """
        Call Gemini Vision API to analyze image for unclear HVAC terms
        
        Args:
            uploaded_file: Gemini uploaded file object
            
        Returns:
            API response text or None if failed
        """
        prompt = self._create_image_analysis_prompt()
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                self.api_calls_made += 1
                
                # Configure API call
                config = types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistent results
                    candidate_count=1
                )
                
                # Build proper content parts with file_data and text
                parts = [
                    types.Part(text=prompt),
                    types.Part(file_data=types.FileData(
                        mime_type=getattr(uploaded_file, 'mime_type', 'image/jpeg'),
                        file_uri=getattr(uploaded_file, 'uri', None)
                    ))
                ]

                response = self.gemini_client.models.generate_content(
                    model=Config.GEMINI_MODEL,
                    contents=[types.Content(parts=parts, role="user")],
                    config=config
                )

                # Try multiple ways to extract text from response
                response_text = None
                if response:
                    # Check if response was truncated due to MAX_TOKENS
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                            finish_reason_str = str(candidate.finish_reason)
                            if 'MAX_TOKENS' in finish_reason_str:
                                self.logger.error(f"⚠️ Image text extraction hit MAX_TOKENS limit! The image likely contains more text than could be extracted. Consider increasing max_output_tokens.")
                                # Still try to get partial content
                    
                    # Method 1: Direct .text attribute
                    if hasattr(response, 'text') and response.text:
                        response_text = response.text.strip()
                    # Method 2: Through candidates
                    elif hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        response_text = part.text.strip()
                                        break

                if response_text:
                    self.logger.debug(f"Successfully analyzed image with Gemini Vision API (extracted {len(response_text)} chars)")
                    return response_text
                else:
                    self.logger.warning(f"Empty response from Gemini Vision API. Response object: {response}")
                    return None
                
            except Exception as e:
                self.api_errors += 1
                self.logger.error(f"Gemini Vision API error (attempt {attempt + 1}): {str(e)}")
                
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to analyze image after {Config.MAX_RETRIES} attempts")
        
        return None
    
    def _create_image_analysis_prompt(self) -> str:
        """
        Create prompt for Gemini Vision API to identify unclear HVAC terms in images
        
        Returns:
            Formatted prompt string for image analysis
        """
        examples_text = "\n".join([f"- {example}" for example in Config.HVAC_EXAMPLES])
        
        prompt = f"""Extract ALL the text from the image. Do not output absolutely anything else than the text content of the image:"""

        return prompt
    
    def _parse_image_analysis_response(self, response_text: str, email: Dict, image_info: Dict) -> List[Dict]:
        """
        Parse Gemini Vision response and create unclear terms list
        
        Args:
            response_text: Response from Gemini Vision API
            email: Email context information
            image_info: Image attachment information
            
        Returns:
            List of unclear term dictionaries
        """
        unclear_terms = []
        
        if "EI EPÄSELVIÄ TERMEJÄ" in response_text.upper():
            return unclear_terms
        
        # Split response into lines and clean
        lines = response_text.strip().split('\n')
        
        for line in lines:
            term = line.strip()
            
            # Skip empty lines, headers, or formatting
            if not term or len(term) < 2:
                continue
            
            # Remove list formatting if present
            term = term.lstrip('- *•').strip()
            
            if not term:
                continue
            
            unclear_term_dict = {
                'unclear_term': term,
                'email_subject': email.get('subject', ''),
                'email_date': email.get('date'),
                'source_type': 'image',
                'image_filename': image_info.get('filename', 'unknown_image')
            }
            
            unclear_terms.append(unclear_term_dict)
            self.unclear_terms_found += 1
        
        return unclear_terms
    
    def _cleanup_temp_files(self):
        """Clean up temporary image files"""
        for temp_file in self.temp_files_created:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    self.logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Could not clean up temp file {temp_file}: {str(e)}")
        
        self.temp_files_created.clear()
    
    def _is_image_attachment(self, attachment: Dict) -> bool:
        """
        Check if an attachment is an image file.
        
        Args:
            attachment: Attachment dictionary
            
        Returns:
            True if attachment is an image, False otherwise
        """
        filename = attachment.get('filename', '').lower()
        
        # Check file extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']
        if any(filename.endswith(ext) for ext in image_extensions):
            self.logger.debug(f"✅ Recognized as image by extension: {filename}")
            return True
        
        # Check MIME type if available (handles both 'mime_type' and 'mimeType' keys)
        mime_type = attachment.get('mime_type', attachment.get('mimeType', '')).lower()
        if mime_type.startswith('image/'):
            self.logger.debug(f"✅ Recognized as image by MIME type: {filename} ({mime_type})")
            return True
        
        self.logger.debug(f"❌ Not recognized as image: {filename} (mime: {mime_type})")
        return False
    
    def get_analysis_stats(self) -> Dict:
        """
        Get image analysis statistics
        
        Returns:
            Dictionary with analysis statistics
        """
        return {
            'processed_images': self.processed_images,
            'unclear_terms_found': self.unclear_terms_found,
            'api_calls_made': self.api_calls_made,
            'api_errors': self.api_errors
        } 