"""
AI analyzer module for identifying unclear Finnish HVAC product terms using Gemini
"""
import logging
import time
import json
import os
import sys
import re
from typing import List, Dict, Optional, Set
from google import genai
from google.genai import types
import io
import pandas as pd
from openai import OpenAI
try:
    from .config import Config
except ImportError:
    try:
        from config import Config
    except ImportError:
        # Fallback configuration when config module is not available
        import os
        class Config:
            GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
            GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
            GEMINI_MODEL_THINKING = os.getenv('GEMINI_MODEL_THINKING', 'gemini-2.5-pro')
            # OpenAI fallback key (used for large Excel container analysis)
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
            # Container analysis preference: 'gemini' or 'openai'
            CONTAINER_ANALYSIS_PREFERENCE = os.getenv('CONTAINER_ANALYSIS_PREFERENCE', 'gemini')

class AIAnalyzer:
    """Handles AI analysis of product names and company information using Gemini API"""
    
    def _retry_llm_request(self, request_func, *args, **kwargs):
        """Wrapper to retry LLM requests with appropriate wait times based on error type.
        
        - 503 errors: immediate retry (up to 3 times)
        - Rate limit errors (429): wait 10 seconds before retry
        - Other errors: exponential backoff
        """
        max_retries = 5
        base_wait = 1  # Base wait time in seconds
        
        for attempt in range(max_retries):
            try:
                # Call the wrapped function
                return request_func(*args, **kwargs)
                
            except Exception as e:
                error_str = str(e).lower()
                self.logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Check if it's the last attempt
                if attempt == max_retries - 1:
                    self.logger.error(f"LLM request failed after {max_retries} attempts")
                    raise
                
                # Determine wait time based on error type
                wait_time = base_wait
                
                if "503" in error_str or "service unavailable" in error_str:
                    # 503 errors: immediate retry (very short wait)
                    wait_time = 2
                    self.logger.info(f"503 error detected, retrying immediately (wait {wait_time}s)")
                    
                elif "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                    # Rate limit errors: wait 10 seconds
                    wait_time = 10
                    self.logger.info(f"Rate limit error detected, waiting {wait_time} seconds before retry")
                    
                elif "500" in error_str or "internal" in error_str:
                    # Internal server errors: exponential backoff
                    wait_time = base_wait * (2 ** attempt)
                    self.logger.info(f"Server error detected, waiting {wait_time} seconds (exponential backoff)")
                    
                else:
                    # Other errors: exponential backoff
                    wait_time = base_wait * (2 ** attempt)
                    self.logger.info(f"Unknown error, waiting {wait_time} seconds (exponential backoff)")
                
                # Wait before retrying
                time.sleep(wait_time)
        
        # This should never be reached due to the raise in the last attempt
        raise Exception(f"Failed to complete LLM request after {max_retries} attempts")
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.processed_texts = 0
        self.unclear_terms_found = 0
        self.api_calls_made = 0
        self.api_errors = 0
        
        # Track analyzed terms to avoid duplicates
        self.analyzed_terms: Set[str] = set()
        
        # Track products already added to the offer to avoid duplicates
        self.existing_products: List[Dict[str, str]] = []
        
        # User instructions extracted from email content (passed to product matcher)
        self.user_instructions: str = ""

        # Initialize OpenAI client
        self._init_openai_client()

    def reset_state(self) -> None:
        """Reset analyzer state for processing a new email.

        This should be called before processing each new email to ensure
        products from previous emails don't affect the current extraction.
        """
        self.processed_texts = 0
        self.unclear_terms_found = 0
        self.api_calls_made = 0
        self.api_errors = 0
        self.analyzed_terms.clear()
        self.existing_products.clear()
        self.user_instructions = ""
        self.logger.info("🔄 AIAnalyzer state reset for new email")

    def _init_openai_client(self) -> None:
        """Initialize OpenAI client (used for large Excel container analyses)."""
        try:
            openai_api_key = getattr(Config, 'OPENAI_API_KEY', '')
            if openai_api_key:
                self.openai_client = OpenAI(
                    api_key=openai_api_key,
                    base_url="https://api.openai.com/v1"  # Explicitly set OpenAI base URL
                )
            else:
                self.logger.warning("OpenAI API key not configured")
                self.openai_client = None
        except Exception as oe:
            self.logger.warning(f"Failed to initialize OpenAI client: {oe}")
            self.openai_client = None
    
    async def extract_company_information(self, email_body: str, sender: str, subject: str) -> Dict[str, str]:
        """
        Extract company name and information from email content using AI.
        
        Args:
            email_body: Email body content
            sender: Email sender address
            subject: Email subject line
            
        Returns:
            Dict with company_name and other extracted info
        """
        self.logger.info("Extracting company information from email")
        
        prompt = f"""Extract the company name from this email content. Look for:
1. Company name mentioned in the email body
2. Company name in email signature
3. Company name that can be inferred from the sender's email domain
4. Any business identification information

Email sender: {sender}
Email subject: {subject}

Email content:
{email_body}

Return only a JSON object with the following format:
{{
  "company_name": "extracted company name",
  "email_domain": "domain from email address",
  "confidence": "high/medium/low",
  "source": "where the name was found (body/signature/domain/subject)"
}}

If no clear company name is found, extract the most likely company name from available information.
"""

        try:
            self.api_calls_made += 1
            
            config = types.GenerateContentConfig(
                temperature=0.1,
                candidate_count=1,
            )

            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            # Extract text from response
            text = None
            if hasattr(response, 'text') and response.text:
                text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            part = candidate.content.parts[0]
                            if hasattr(part, 'text') and part.text:
                                text = part.text.strip()
                except Exception as e:
                    self.logger.warning(f"Error extracting text from candidates: {e}")

            if not text:
                self.logger.warning("No text content found in company extraction response")
                # Fallback: extract domain from email
                email_domain = sender.split('@')[-1] if '@' in sender else sender
                return {
                    'company_name': email_domain.replace('.fi', '').replace('.com', '').replace('www.', ''),
                    'email_domain': email_domain,
                    'confidence': 'low',
                    'source': 'domain_fallback'
                }

            # Parse JSON response
            try:
                import json
                json_text = text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                company_info = json.loads(json_text)
                self.logger.info(f"Extracted company info: {company_info}")
                return company_info
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse company extraction JSON: {e}")
                self.logger.error(f"Raw response: {text}")
                
                # Fallback: extract domain from email
                email_domain = sender.split('@')[-1] if '@' in sender else sender
                return {
                    'company_name': email_domain.replace('.fi', '').replace('.com', '').replace('www.', ''),
                    'email_domain': email_domain,
                    'confidence': 'low',
                    'source': 'domain_fallback'
                }

        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"Company extraction error: {e}")
            
            # Fallback: extract domain from email
            email_domain = sender.split('@')[-1] if '@' in sender else sender
            return {
                'company_name': email_domain.replace('.fi', '').replace('.com', '').replace('www.', ''),
                'email_domain': email_domain,
                'confidence': 'low',
                'source': 'error_fallback'
            }
    
    async def identify_unclear_terms(self, filtered_emails: List[Dict], excel_data: List[Dict], pdf_data: List[Dict],
                              on_unclear_term_found=None, on_match_found=None) -> List[Dict]:
        """
        Analyze emails, Excel data, and inline images to identify unclear HVAC product terms
        
        Args:
            filtered_emails: List of filtered email dictionaries
            excel_data: List of Excel data dictionaries
            on_unclear_term_found: Optional callback function for unclear terms (real-time updates)
            on_match_found: Optional callback function for matched products (real-time updates)
            
        Returns:
            List of unclear term dictionaries with context
        """
        self.logger.info("Starting AI analysis and product matching ...")
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from .product_matcher import ProductMatcher
        except ImportError:
            from product_matcher import ProductMatcher
        
        # Use ERPFactory to get the appropriate product repository based on ERP_TYPE
        try:
            from src.erp.factory import get_erp_factory
            factory = get_erp_factory()
            product_repository = factory.create_product_repository()
            self.logger.info(f"Using {factory.erp_name} product repository for matching")
        except Exception as e:
            self.logger.warning(f"Could not create product repository from factory: {e}. Falling back to legacy mode.")
            product_repository = None
        
        matcher = ProductMatcher(product_repository=product_repository)

        matched_products: List[Dict] = []
        unclear_terms: List[Dict] = []
        
        # Collect all terms for batch processing
        terms_to_process: List[Dict] = []

        pdf_map = {}
        for pdf_info in pdf_data:
            pdf_contents = pdf_info.get('pdf_contents', [])
            if not pdf_contents:
                continue

            key = (pdf_info.get('email_subject'), pdf_info.get('email_date'))
            pdf_items = []
            for pdf_content in pdf_contents:
                # PDF content is already limited to 40k per PDF, 120k total in pdf_processor
                # This is a safety fallback limit
                full_content = pdf_content.get('full_content', '')
                if len(full_content) > 200000:
                    full_content = full_content[:200000]
                
                pdf_items.append({
                    'filename': pdf_content.get('filename', 'PDF'),
                    'text': full_content,
                    'page_count': pdf_content.get('page_count', 0)
                })
            
            if pdf_items:
                pdf_map[key] = pdf_items

        # Track processed terms to avoid duplicates
        processed_terms = set()

        # --------------------------------------------------------------
        # 1. Extract full text from inline images and attach to emails
        # --------------------------------------------------------------
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        try:
            from .image_analyzer import ImageAnalyzer
        except ImportError:
            from image_analyzer import ImageAnalyzer
        image_analyzer = ImageAnalyzer()
        image_analyzer.analyze_inline_images(filtered_emails)

        # Gather image extraction stats
        image_stats = image_analyzer.get_analysis_stats()
        self.api_calls_made += image_stats['api_calls_made']
        self.api_errors += image_stats['api_errors']
        
        # Log image analysis results
        self.logger.info(f"🖼️ Image analysis complete: processed {image_stats['processed_images']} images, "
                        f"extracted {image_stats['unclear_terms_found']} text blocks")
        
        # Log which emails have image texts
        for email in filtered_emails:
            image_texts = email.get('image_texts', [])
            if image_texts:
                self.logger.info(f"📷 Email '{email.get('subject', 'unknown')[:30]}...' has {len(image_texts)} image text(s)")

        content_for_excel_analysis = []
        for email in filtered_emails:
            body = email.get('body', '').strip()

            # Retrieve image texts that were attached by ImageAnalyzer
            image_texts = email.get('image_texts', [])

            # Retrieve excel texts for this email
            key = (email.get('subject'), email.get('date'))

            content_for_excel_analysis.append({
                'subject': email.get('subject'),
                'date': email.get('date'),
                'body': body,
                'image_texts': image_texts
            })

        # --------------------------------------------------------------
        # 2. Process all Excel files individually
        # --------------------------------------------------------------
        excel_map = {}
        for excel_info in excel_data:
            excel_rows = excel_info.get('excel_data', [])
            if not excel_rows:
                self.logger.warning(f"❌ Excel file has no data: {excel_info.get('filename', 'Unknown')}")
                continue

            self.logger.info(f"🔍 Processing Excel file: {excel_info.get('filename', 'Unknown')} with {len(excel_rows)} rows")
            self.logger.debug(f"🔍 Sample Excel row: {excel_rows[0] if excel_rows else 'None'}")

            # Determine dataset size
            all_columns = set()
            for row in excel_rows:
                all_columns.update(row.keys())
            column_count = len([c for c in all_columns if not pd.isna(c) and str(c).strip() and str(c).lower() != 'nan'])

            self.logger.info(f"🔍 Excel dataset analysis: rows={len(excel_rows)}, cols={column_count}, columns={sorted(all_columns)[:5]}")

            # If large dataset, use container-based analysis directly
            if len(excel_rows) > 20 or column_count > 3:
                self.logger.info(f"📊 Large Excel detected (rows={len(excel_rows)}, cols={column_count}). Using container analyzer.")

                # Use container analysis based on preference
                products_dict = {}
                preference = getattr(Config, 'CONTAINER_ANALYSIS_PREFERENCE', 'gemini').lower()
                
                if preference == 'openai' and self.openai_client:
                    # Try OpenAI first, fallback to Gemini
                    self.logger.info("📋 Using OpenAI container analyzer (preferred)")
                    products_dict = self._openai_container_excel_analysis(excel_rows)
                    
                    if not products_dict:
                        self.logger.info("🔄 OpenAI container failed, falling back to Gemini container analyzer.")
                        products_dict = self._gemini_container_excel_analysis(excel_rows, content_for_excel_analysis)
                else:
                    # Try Gemini first, fallback to OpenAI if available
                    self.logger.info("📋 Using Gemini container analyzer (preferred)")
                    products_dict = self._gemini_container_excel_analysis(excel_rows, content_for_excel_analysis)
                    
                    if not products_dict and self.openai_client:
                        self.logger.info("🔄 Gemini container failed, falling back to OpenAI container analyzer.")
                        products_dict = self._openai_container_excel_analysis(excel_rows)

                # Note: Container analysis doesn't use _extract_product_terms, so we still need additional search here
                excel_text_for_additional_search = self._combine_excel_rows(excel_rows)
                additional_products = self._find_additional_products(products_dict, excel_text_for_additional_search)
                
                # Merge additional products
                if additional_products:
                    self.logger.info(f"🔍 Container analysis found {len(additional_products)} additional products, merging with initial {len(products_dict)}")
                    products_dict.update(additional_products)

                # Build minimal context for each product term
                base_context = {
                    'subject': excel_info.get('email_subject', f"Excel: {excel_info.get('filename', 'Unknown')}"),
                    'date': excel_info.get('email_date'),
                    'full_text': ''  # full_text not needed when coming from structured data
                }

                for product_name, product_data in products_dict.items():
                    if product_name.lower() in processed_terms:
                        continue
                    processed_terms.add(product_name.lower())

                    # Collect term for batch processing
                    terms_to_process.append({
                        'unclear_term': product_name,
                        'email_subject': base_context['subject'],
                        'email_date': base_context['date'],
                        'quantity': product_data.get('quantity', '1'),
                        'explanation': product_data.get('explanation', ''),
                        'source': 'excel_container'
                    })

                # Large Excel files are processed by container analysis, don't add to excel_map
                self.logger.info(f"✅ Large Excel file processed via container analysis: {excel_info.get('filename', 'Unknown')}")

            else:
                # For small/regular Excel files, fall back to existing Gemini table extraction
                self.logger.info(f"📋 Small Excel file (rows={len(excel_rows)}, cols={column_count}). Converting to text for prompt inclusion.")
                excel_text = self._combine_excel_rows(excel_rows)
                if not excel_text.strip():
                    continue

                key = (excel_info.get('email_subject'), excel_info.get('email_date'))
                excel_map.setdefault(key, []).append({
                    'filename': excel_info.get('filename', 'Excel'),
                    'text': excel_text
                })
                self.logger.info(f"📋 Added Excel text to excel_map for key {key}: {len(excel_text)} characters")


        # --------------------------------------------------------------
        # 3. Process each email with combined content (body + images + excel + pdf)
        # --------------------------------------------------------------
        combined_content = ""
        for email in filtered_emails:
            body = email.get('body', '').strip()

            # Retrieve image texts that were attached by ImageAnalyzer
            image_texts = email.get('image_texts', [])

            # Retrieve excel texts for this email
            key = (email.get('subject'), email.get('date'))
            excel_items = excel_map.get(key, [])

            # Retrieve PDF texts for this email
            pdf_items = pdf_map.get(key, [])

            # Skip emails that have no analyzable content
            if not body and not image_texts and not excel_items and not pdf_items:
                continue

            # Build combined content with clear headings
            sections = []
            if body:
                sections.append("# EMAIL CONTENT:\n" + body)

            for idx, img_text in enumerate(image_texts, start=1):
                sections.append(f"# IMAGE {idx} CONTENT:\n" + img_text)

            for idx, excel_item in enumerate(excel_items, start=1):
                sections.append(f"# EXCEL {idx} CONTENT ({excel_item['filename']}):\n" + excel_item['text'])

            for idx, pdf_item in enumerate(pdf_items, start=1):
                sections.append(f"# PDF {idx} CONTENT ({pdf_item['filename']}, {pdf_item['page_count']} pages):\n" + pdf_item['text'])

            combined_content = "\n\n".join(sections)


            self.logger.info(f"📧 Processing combined content for email '{email.get('subject', '')[:50]}...' (len={len(combined_content)})")

            product_terms_dict = self._extract_product_terms(combined_content)

            for product_name, product_data in product_terms_dict.items():
                if product_name.lower() in processed_terms:
                    self.logger.debug(f"⏭️ Skipping duplicate term: '{product_name}'")
                    continue
                processed_terms.add(product_name.lower())

                # Collect term for batch processing
                terms_to_process.append({
                    'unclear_term': product_name,
                    'email_subject': email.get('subject', ''),
                    'email_date': email.get('date', ''),
                    'quantity': product_data.get('quantity', '1'),
                    'explanation': product_data.get('explanation', ''),
                    'source': 'combined'
                })

        # --------------------------------------------------------------
        # BATCH PROCESSING: Process all collected terms at once
        # --------------------------------------------------------------
        if terms_to_process:
            # Restrict to first 200 products to prevent overwhelming the system
            original_count = len(terms_to_process)
            MAX_BATCH_SIZE = 100
            
            if original_count > MAX_BATCH_SIZE:
                self.logger.warning(f"⚠️ Found {original_count} products, restricting to first {MAX_BATCH_SIZE} for batch processing")
                terms_to_process = terms_to_process[:MAX_BATCH_SIZE]
                skipped_count = original_count - MAX_BATCH_SIZE
                self.logger.warning(f"⚠️ Skipping {skipped_count} products (items {MAX_BATCH_SIZE+1}-{original_count})")
            
            self.logger.info(f"🚀 Starting batch processing for {len(terms_to_process)} terms")
            
            # Pass user instructions to the matcher if available
            if self.user_instructions:
                self.logger.info(f"📝 Passing user instructions to matcher: {self.user_instructions[:100]}...")
            
            # Use batch matching function with user instructions
            batch_results = await matcher.match_terms_batch(terms_to_process, user_instructions=self.user_instructions)
            
            # Process batch results
            for result in batch_results:
                if result.get('matched_product_code') and result.get('matched_product_code') != 'NO_MATCH':
                    # This is a matched product
                    matched_dict = {
                        "unclear_term": result['unclear_term'],
                        "quantity": result.get('quantity', '1'),
                        "explanation": result.get('explanation', ''),
                        "matched_product_code": result['matched_product_code'],
                        "matched_product_name": result['matched_product_name'],
                        "email_subject": result['email_subject'],
                        "email_date": result['email_date'],
                        # Enhanced AI matching data
                        "ai_reasoning": result.get("ai_reasoning", "AI selected this product"),
                        "ai_confidence": result.get("ai_confidence", 0),
                        "original_customer_term": result.get("original_customer_term", result['unclear_term'])
                    }
                    matched_products.append(matched_dict)
                    self.logger.info(f"✅ MATCHED: '{result['unclear_term']}' → {result['matched_product_code']} (batch)")
                    
                    # Track this product
                    self.existing_products.append({
                        "product_code": result["matched_product_code"],
                        "product_name": result["matched_product_name"],
                        "customer_term": result['unclear_term']
                    })
                    
                    # Real-time callback for matched products
                    if on_match_found:
                        on_match_found(matched_dict)
                else:
                    # This is an unclear term
                    unclear_dict = {
                        "unclear_term": result['unclear_term'],
                        "quantity": result.get('quantity', '1'),
                        "explanation": result.get('explanation', ''),
                        "email_subject": result['email_subject'],
                        "email_date": result['email_date'],
                    }
                    unclear_terms.append(unclear_dict)
                    self.logger.info(f"❓ UNCLEAR: '{result['unclear_term']}' (no match found in batch)")
                    
                    # Real-time callback for unclear terms
                    if on_unclear_term_found:
                        on_unclear_term_found(unclear_dict)
            
            self.logger.info(f"✅ Batch processing complete: {len(matched_products)} matched, {len(unclear_terms)} unclear")
        
        # --------------------------------------------------------------
        # Deduplicate lists (ensure mutually exclusive)
        # --------------------------------------------------------------
        # Create keys for fast lookup
        matched_keys = {m['unclear_term'].lower() for m in matched_products}
        filtered_unclear = [u for u in unclear_terms if u['unclear_term'].lower() not in matched_keys]

        # Final dedup on unclear
        unique_unclear = self._remove_duplicates(filtered_unclear)

        self.logger.info(
            f"AI analysis complete. Processed {self.processed_texts} texts and {image_stats['processed_images']} images, "
            f"matched {len(matched_products)} products, "
            f"found {len(unique_unclear)} unclear terms, "
            f"made {self.api_calls_made} API calls, errors: {self.api_errors}"
        )

        return unique_unclear
    
    def _analyze_email_content(self, email: Dict) -> List[Dict]:
        """
        Analyze email body for unclear product terms
        
        Args:
            email: Email dictionary
            
        Returns:
            List of unclear term dictionaries
        """
        email_body = email.get('body', '').strip()
        if not email_body or len(email_body) < 10:
            return []
        
        # Analyze the email content
        unclear_terms_text = self._call_gemini_api(email_body, 'email')
        
        if unclear_terms_text:
            return self._parse_unclear_terms_response(unclear_terms_text, email, 'email')
        
        return []
    
    def _analyze_excel_content(self, excel_info: Dict) -> List[Dict]:
        """
        Analyze Excel content for unclear product terms
        
        Args:
            excel_info: Excel data dictionary
            
        Returns:
            List of unclear term dictionaries
        """
        excel_rows = excel_info.get('excel_data', [])
        if not excel_rows:
            return []
        
        # Combine Excel rows into text for analysis
        excel_text = self._combine_excel_rows(excel_rows)
        
        if not excel_text or len(excel_text.strip()) < 10:
            return []
        
        # Analyze the Excel content
        unclear_terms_text = self._call_gemini_api(excel_text, 'excel')
        
        if unclear_terms_text:
            # Create email-like context from Excel info
            excel_context = {
                'subject': f"Excel: {excel_info.get('filename', 'Unknown')}",
                'date': excel_info.get('email_date'),
                'sender': excel_info.get('email_sender', '')
            }
            return self._parse_unclear_terms_response(unclear_terms_text, excel_context, 'excel')
        
        return []
    
    def _combine_excel_rows(self, excel_rows: List[Dict]) -> str:
        """
        Combine Excel rows into analyzable table format
        
        Args:
            excel_rows: List of Excel row dictionaries
            
        Returns:
            Table-formatted text string
        """
        if not excel_rows:
            return ""
        
        # Get all unique column headers
        all_columns = set()
        for row in excel_rows:
            all_columns.update(row.keys())
        
        # Sort columns for consistent output
        columns = sorted(all_columns)
        
        # Remove empty or unnamed columns (check for NaN properly)
        columns = [col for col in columns if not pd.isna(col) and str(col).strip() and str(col).lower() != 'nan']
        
        if not columns:
            return ""
        
        # Create table format
        table_lines = []
        
        # Add header row
        header_row = " | ".join(str(col).strip() for col in columns)
        table_lines.append(header_row)
        
        # Add separator row
        separator = " | ".join("-" * min(len(str(col)), 15) for col in columns)
        table_lines.append(separator)
        
        # Add data rows
        for row in excel_rows:
            # Only include rows that have meaningful data
            row_values = []
            has_data = False
            
            for col in columns:
                value = row.get(col, "")
                # Properly check for NaN using pandas.isna() before converting to string
                if pd.isna(value) or not str(value).strip() or str(value).lower() == 'nan':
                    cleaned_value = ""
                else:
                    cleaned_value = str(value).strip()
                    has_data = True
                
                # Limit cell width for readability
                if len(cleaned_value) > 20:
                    cleaned_value = cleaned_value[:17] + "..."
                
                row_values.append(cleaned_value)
            
            # Only add rows with actual data
            if has_data:
                data_row = " | ".join(row_values)
                table_lines.append(data_row)
        

        return "\n".join(table_lines)

    def _extract_product_terms(self, content: str) -> Dict[str, Dict[str, str]]:
        """Extract ALL HVAC products from the given text using Gemini with improved accuracy.

        Returns a dictionary: {"product_name": {"quantity": "qty", "explanation": "explanation"}}"""
        if not content or len(content.strip()) < 5:
            self.logger.debug("Content too short or empty, skipping extraction")
            return {}

        self.logger.debug(f"Extracting products from content ({len(content)} chars): {content[:100]}...")

        # Format existing products context
        existing_products_context = ""
        if self.existing_products:
            existing_products_list = []
            for prod in self.existing_products:
                existing_products_list.append(f"- {prod['product_code']}: {prod['product_name']} (customer term: {prod['customer_term']})")
            existing_products_context = f"""
ALREADY ADDED PRODUCTS TO OFFER (do not extract these again):
{chr(10).join(existing_products_list)}

"""

        prompt = f"""You are an expert HVAC product extraction specialist. Extract ALL product-like items from email content, Excel tables, PDF documents, and images by default.

{existing_products_context}DEFAULT-INCLUDE RULES:
1. DEFAULT: Include products/line items unless the text explicitly says they should NOT be offered.
2. NEGATIVE/EXCLUSION PHRASES (exclude only those specific items): "ei tarjota", "poissuljettu", "ei mukana", "älä tarjoa", "ei sisälly", "erikseen" when it clearly excludes, "tarjous olemassa" for that specific item only, "kyselty" when it clearly means do not include.
3. SUPPLIER OFFERS: If the content is a supplier offer/quote (e.g., contains "Tarjous" or price/line-item tables), treat line items as intended to be quoted.
4. CONTEXT: Apply exclusions narrowly. Only exclude a line when the negation clearly applies to that exact item or explicitly listed group.
5. IMPORTANT: Do not include any products that are already listed above as "ALREADY ADDED PRODUCTS TO OFFER"

CONTENT TYPES:
- Email body text in Finnish
- Structured Excel tables with product specifications
- PDF offers, technical documents and specifications
- OCR text from images

🔴 CRITICAL: PRESERVE PRODUCT CODES IN KEYS!
If any product code/SKU/article number is mentioned (e.g., "OP123456", "ABC-100-25", "12345", "T-1234"), 
it MUST be included in the JSON key for that product!

PRODUCT CODE PATTERNS TO CAPTURE:
- Alphanumeric codes: OP123456, ABC-100, T-1234, KTS-160
- Pure numeric codes: 12345, 654321
- Supplier/manufacturer codes: Any code that looks like an internal product reference
- Codes in parentheses: "Kanava Ø125 (ABC-100)"
- Codes in columns: Product codes from Excel/PDF tables

EXTRACTION REQUIREMENTS:
1. Extract ONLY products the customer explicitly wants us to offer
2. Include quantities from MÄÄRÄ, KPL, M, M2, PCS, etc. columns or text
3. Keep original Finnish product names and technical specifications
4. Include model numbers, sizes, and technical details
5. For Excel: analyze table headers to understand data relationships
6. Default quantity to "1" if not specified but product is clearly wanted
7. 🔴 ALWAYS include any product code/SKU in the JSON key!

IMPORTANT: When extracting customer terms, include the FULL CONTEXTUAL DESCRIPTION. For example:
- If customer says "Sinkitty M-press" followed by a new line with "22-¾ SK 4kpl", the term should be "Sinkitty M-press 22-¾ SK"  
- If customer says "Kupari m-press osat" followed by "15 haara 1kpl", the term should be "Kupari m-press haara 15"
- If a product code is present: "OP123456 Kupariputki 22mm" → key should be "OP123456 Kupariputki 22mm"
- Always include the category/type/material context AND any product codes that apply to specific item

PRODUCT CATEGORIES (examples to recognize):
- Kanavat (ducts): Ø1250, Ø1000, Ø800, Ø630, Ø500, Ø400, Ø315, Ø250, Ø200, Ø160, Ø125, Ø100
- Päätelaitteet (terminals): KTS-160, KTS-125, KTS-100, STQA-125, STQA-100, säätöpelti, tuloilmalaite
- Liittimet ja osat: TH/LK (tehdasliittimet), MY (mutkat), LYP (liitosyhde), ÄV (äänenvaimentimet)
- Eristeet (insulation): AF 19MM, AF 13MM, LE 30MM, LE 50MM, LE 100MM, mineraalivilla
- Palopellit (fire dampers): KSO-200, KSO-160, KSO-125, KSO-100, savunpoistopelti
- Venttiilit: säätöventtiili, sulkuventtiili, kuristusventtiili, termostaattiventtiili
- Pumput: kiertovesipumppu, lämmönsiirrin, paisunta-astia
- Mittarit: lämpömittari, vesimittari, painemittari

QUALITY CHECKS:
1. Verify each product has a clear quantity (not just random numbers)
2. Ensure product names are complete (not just "125" but "Kanava Ø125" or "KTS-125")
3. Cross-reference with context to confirm customer wants this product
4. Exclude technical specifications that aren't product requests
5. 🔴 Verify all product codes from source are preserved in output keys!

OUTPUT FORMAT (JSON only):
{{
  "_user_instructions": "Any special instructions, context, or requirements from the user that the product matching agent should know (project info, brand preferences, quality requirements, tool use preferences in agent loop, etc.). Leave empty string if none.",
  "PRODUCT_CODE product_name_1": {{"quantity": "qty_with_unit", "explanation": "component_type_in_finnish"}},
  "PRODUCT_CODE product_name_2": {{"quantity": "qty_with_unit", "explanation": "component_type_in_finnish"}}
}}

EXAMPLE EXTRACTIONS:

Example 1 - With product codes from supplier:
Input: "Tarjous:\nOP-22-15 Kupariputki 22mm 5m - 10kpl\nOP-FIT-22 M-press kulma 22mm - 5kpl"
Output: {{
  "_user_instructions": "",
  "OP-22-15 Kupariputki 22mm 5m": {{"quantity": "10 kpl", "explanation": "kupariputki"}},
  "OP-FIT-22 M-press kulma 22mm": {{"quantity": "5 kpl", "explanation": "puristusliitos"}}
}}

Example 2 - Mixed codes and descriptions:
Input: "Kanavisto paketti: 12345 Kanava Ø1250 5kpl, KTS-160 säätöpelti 12kpl. Fläkt Woods tuotteita jos mahdollista."
Output: {{
  "_user_instructions": "Asiakas toivoo Fläkt Woods tuotteita jos mahdollista.",
  "12345 Kanava Ø1250": {{"quantity": "5 kpl", "explanation": "ilmanvaihtokanava"}},
  "KTS-160 säätöpelti": {{"quantity": "12 kpl", "explanation": "säätöventtiili"}}
}}

Example 3 - Excel with product code column:
Input: "Tuotekoodi | Tuote | Määrä\nABC-100 | Venttiili DN25 | 3\nABC-101 | Venttiili DN32 | 2"
Output: {{
  "_user_instructions": "",
  "ABC-100 Venttiili DN25": {{"quantity": "3 kpl", "explanation": "venttiili"}},
  "ABC-101 Venttiili DN32": {{"quantity": "2 kpl", "explanation": "venttiili"}}
}}

WHAT TO CAPTURE IN _user_instructions:
- Brand preferences (merkkitoive, Fläkt Woods, Lindab, etc.)
- Project/site information (projekti, kohde, työmaa)
- Quality requirements (laatu, materiaali)
- Special requests (erityistoiveet)
- Function calling preferences (i.e. match by product group, sku, etc.) 
- Any other context that helps match products correctly

If NO products wanted: {{"NO_PRODUCTS_FOUND": {{"quantity": "0", "explanation": "Ei tarjottavia tuotteita tunnistettu"}}, "_user_instructions": ""}}

CONTENT TO ANALYZE:
{content}"""

        self.logger.info(f"🤖 Calling Gemini model: {Config.GEMINI_MODEL_THINKING}")

        try:
            self.api_calls_made += 1
            self.processed_texts += 1

            config = types.GenerateContentConfig(
                temperature=0.3,
                candidate_count=1,
            )

            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL_THINKING,
                contents=prompt,  # Pass the prompt directly as string
                config=config,
            )

            if not response:
                self.logger.warning("❌ No response from Gemini API")
                return []
            print("response", response)
            # Debug: Show the full response structure for troubleshooting
            self.logger.info(f"🔍 Response type: {type(response)}")
            if hasattr(response, 'candidates'):
                self.logger.info(f"🔍 Number of candidates: {len(response.candidates) if response.candidates else 0}")
                if response.candidates:
                    candidate = response.candidates[0]
                    self.logger.info(f"🔍 Candidate type: {type(candidate)}")
                    if hasattr(candidate, 'content'):
                        self.logger.info(f"🔍 Content type: {type(candidate.content)}")
                        self.logger.info(f"🔍 Content: {candidate.content}")
                        
                        # Check for safety ratings or finish reason
                        if hasattr(candidate, 'finish_reason'):
                            self.logger.info(f"🔍 Finish reason: {candidate.finish_reason}")
                        if hasattr(candidate, 'safety_ratings'):
                            self.logger.info(f"🔍 Safety ratings: {candidate.safety_ratings}")

            # Handle different response formats for different Gemini models
            text = None
            
            # Try to get text from response.text (works for 2.0 Flash)
            if hasattr(response, 'text') and response.text:
                text = response.text.strip()
                self.logger.debug(f"✅ Got text from response.text")
            
            # Try to get text from candidates (works for 2.5 Pro)
            elif hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    
                    # Check if content was blocked for safety reasons
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                        if candidate.finish_reason != 'STOP':
                            self.logger.warning(f"❌ Content generation stopped due to: {candidate.finish_reason}")
                            # Try to extract partial content anyway
                    
                    if hasattr(candidate, 'content') and candidate.content:
                        content_obj = candidate.content
                        self.logger.debug(f"🔍 Content object: {content_obj}")
                        
                        # Check if parts exist and are not None
                        if hasattr(content_obj, 'parts') and content_obj.parts is not None:
                            if len(content_obj.parts) > 0:
                                part = content_obj.parts[0]
                                self.logger.debug(f"🔍 Part type: {type(part)}")
                                self.logger.debug(f"🔍 Part: {part}")
                                
                                if hasattr(part, 'text') and part.text:
                                    text = part.text.strip()
                                    self.logger.debug(f"✅ Got text from candidates[0].content.parts[0].text")
                                else:
                                    self.logger.warning(f"❌ Part has no text attribute or text is empty")
                            else:
                                self.logger.warning(f"❌ Parts array is empty")
                        else:
                            self.logger.warning(f"❌ Content has no parts or parts is None")
                            # Try alternative text extraction methods
                            if hasattr(content_obj, 'text'):
                                text = content_obj.text.strip()
                                self.logger.debug(f"✅ Got text from candidates[0].content.text")
                    else:
                        self.logger.warning(f"❌ Candidate has no content or content is None")
                        
                except (IndexError, AttributeError) as e:
                    self.logger.warning(f"❌ Error extracting text from candidates: {e}")
            
            # If still no text, try the direct text property one more time
            if not text and hasattr(response, 'text'):
                text = str(response.text).strip() if response.text else None
                if text:
                    self.logger.debug(f"✅ Got text from response.text (second attempt)")
            
            if not text:
                self.logger.warning("❌ No text content found in Gemini response")
                # Log the full response structure for debugging
                self.logger.warning(f"📄 Full response debug info:")
                self.logger.warning(f"   Response: {response}")
                if hasattr(response, 'candidates') and response.candidates:
                    for i, cand in enumerate(response.candidates):
                        self.logger.warning(f"   Candidate {i}: {cand}")
                return []
                
            self.logger.info(f"🤖 Raw Gemini response ({len(text)} chars): {text}")
            
            # Parse JSON response
            try:
                import json
                # Clean up response text in case there are markdown code blocks
                json_text = text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                # Handle Unicode characters that might cause JSON parsing issues
                # Various Unicode symbols in HVAC product names can cause "Invalid control character" errors
                try:
                    # First attempt: try parsing with strict=False to be more permissive
                    products_dict = json.loads(json_text, strict=False)
                except json.JSONDecodeError as unicode_error:
                    # If strict=False doesn't work, sanitize problematic Unicode characters
                    self.logger.warning(f"⚠️ JSON parsing failed due to Unicode chars in _extract_product_terms, attempting to sanitize: {unicode_error}")
                    
                    sanitized_json = json_text
                    
                    # Common problematic Unicode characters in HVAC product names:
                    unicode_replacements = {
                        # Degree symbols and related
                        'º': '°',      # U+00BA (masculine ordinal indicator) → U+00B0 (degree symbol)
                        '\u00ba': '°', # Same as above, explicit Unicode
                        '°': 'deg',    # U+00B0 (degree symbol) → text
                        
                        # Mathematical symbols that might appear
                        '±': '+/-',    # U+00B1 (plus-minus sign)
                        '²': '2',      # U+00B2 (superscript two)
                        '³': '3',      # U+00B3 (superscript three)
                        '¼': '1/4',    # U+00BC (vulgar fraction one quarter)
                        '½': '1/2',    # U+00BD (vulgar fraction one half)
                        '¾': '3/4',    # U+00BE (vulgar fraction three quarters)
                        
                        # Measurement symbols
                        'µ': 'u',      # U+00B5 (micro sign)
                        
                        # Other potentially problematic characters
                        '\u2013': '-', # En dash
                        '\u2014': '-', # Em dash
                        '\u2018': "'", # Left single quotation mark
                        '\u2019': "'", # Right single quotation mark
                        '\u201c': '"', # Left double quotation mark
                        '\u201d': '"', # Right double quotation mark
                    }
                    
                    # Apply all replacements
                    for unicode_char, replacement in unicode_replacements.items():
                        if unicode_char in sanitized_json:
                            sanitized_json = sanitized_json.replace(unicode_char, replacement)
                            self.logger.debug(f"🔧 Replaced '{unicode_char}' with '{replacement}' in _extract_product_terms")
                    
                    try:
                        products_dict = json.loads(sanitized_json, strict=False)
                        self.logger.info("✅ Successfully parsed JSON after Unicode sanitization in _extract_product_terms")
                    except json.JSONDecodeError as final_error:
                        # Last resort: log detailed error and fall back
                        self.logger.error(f"❌ Final JSON parsing failed even after sanitization in _extract_product_terms: {final_error}")
                        self.logger.error(f"Problematic JSON (first 500 chars): {sanitized_json[:500]}")
                        raise final_error  # Re-raise to trigger the outer exception handler
                
                # Check if no products found
                if "NO_PRODUCTS_FOUND" in products_dict:
                    self.logger.info("✅ Gemini found no HVAC products in text")
                    return {}
                
                # Validate format
                if not isinstance(products_dict, dict):
                    raise ValueError("Response is not a dictionary")
                
                # Extract and store user instructions (special key starting with _)
                user_instructions = products_dict.pop('_user_instructions', '')
                if user_instructions:
                    self.user_instructions = user_instructions
                    self.logger.info(f"📝 Extracted user instructions: {user_instructions[:100]}...")
                
                for product_name, product_data in products_dict.items():
                    # Skip any remaining underscore-prefixed metadata keys
                    if product_name.startswith('_'):
                        continue
                    if not isinstance(product_data, dict) or 'quantity' not in product_data or 'explanation' not in product_data:
                        raise ValueError(f"Invalid format for product: {product_name}")
                
                self.logger.info(f"🔍 Parsed {len(products_dict)} product terms from JSON response: {list(products_dict.keys())}")
                
                if products_dict:
                    self.logger.info(f"✅ Successfully found {len(products_dict)} products: {', '.join(list(products_dict.keys())[:3])}{'...' if len(products_dict) > 3 else ''}")
                    additional_products = {}
                    if len(products_dict) > 30:
                        try:
                            # Search for additional products that might have been missed
                            additional_products = self._find_additional_products(products_dict, content)
                        except Exception as e:
                            self.logger.warning(f"❌ Error searching for additional products: {e}")
                        # Merge additional products
                        if additional_products:
                            self.logger.info(f"🔍 Found {len(additional_products)} additional products in _extract_product_terms, merging with initial {len(products_dict)}")
                            products_dict.update(additional_products)
                            self.logger.info(f"✅ Final product count after additional search: {len(products_dict)}")
                else:
                    self.logger.warning(f"❌ No valid products parsed from response!")
                    
                return products_dict
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                self.logger.error(f"❌ Failed to parse JSON response: {e}")
                self.logger.error(f"📄 Raw response: {text}")
                # Fallback to empty dict
                return {}

        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"❌ Gemini extraction error: {e}")
            import traceback
            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {}

    def _find_additional_products(self, initial_products: Dict[str, Dict[str, str]], content: str) -> Dict[str, Dict[str, str]]:
        """
        Find any additional products that might have been missed in the initial extraction.
        This function can only ADD products, never remove them.
        
        Args:
            initial_products: Already extracted products from _extract_product_terms
            content: Original content to scan for missed products
            
        Returns:
            Dictionary of additional products found (if any)
        """
        if not content or len(content.strip()) < 5:
            self.logger.debug("Content too short for additional product search")
            return {}
            
        if not initial_products or "NO_PRODUCTS_FOUND" in initial_products:
            self.logger.debug("No initial products found, skipping additional search")
            return {}

        self.logger.info(f"🔍 Searching for additional products beyond the {len(initial_products)} already found")

        # Format the already found products for context
        found_products_list = []
        for product_name, product_data in initial_products.items():
            found_products_list.append(f"- {product_name}: {product_data.get('quantity', '1')} ({product_data.get('explanation', 'tuote')})")
        
        found_products_context = "\n".join(found_products_list)

        prompt = f"""You are an expert at finding missed HVAC products. I already extracted some products from this content, but I want to make sure I didn't miss any.

ALREADY FOUND PRODUCTS ({len(initial_products)}):
{found_products_context}

YOUR TASK: Carefully scan the content below for ANY additional products that were missed. 

CRITICAL RULES:
1. DEFAULT-INCLUDE: Treat line items, lists, tables and BOMs as intended to be quoted; add them unless there is explicit negative phrasing (e.g., "ei tarjota", "poissuljettu", "ei mukana", "älä tarjoa", "tarjous olemassa" for that item).
2. DO NOT include any products already in the "ALREADY FOUND" list above
3. ONLY add genuinely new products that were missed
4. Include products with implied quantities (default to "1" if not specified) for clear line items
5. Prefer adding a plausible missed item over being too conservative, but never duplicate

SEARCH FOR:
- Products mentioned with different terminology or abbreviations
- Products listed without category prefixes (e.g., "DN10 3/8" sk" vs "Palloventtiili DN10 3/8" sk")
- Products in different parts of the content (tables, lists, specifications)
- Accessories or related items that are clearly wanted
- Products mentioned indirectly but clearly intended for quotation
- Products with implied category names (e.g., just "125mm 5kpl" meaning "Kanava 125mm")
- Products where quantities are separated from names

OUTPUT FORMAT (JSON only):
{{
  "additional_product_1": {{"quantity": "qty_with_unit", "explanation": "component_type_in_finnish"}},
  "additional_product_2": {{"quantity": "qty_with_unit", "explanation": "component_type_in_finnish"}}
}}

If NO additional products found: {{"NO_ADDITIONAL_PRODUCTS": {{"quantity": "0", "explanation": "Ei löydetty lisätuotteita"}}}}

CONTENT TO SCAN FOR MISSED PRODUCTS:
{content}"""

        try:
            self.api_calls_made += 1
            
            config = types.GenerateContentConfig(
                temperature=0.2,  # Lower temperature for more focused search
                candidate_count=1,
            )

            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL_THINKING,
                contents=prompt,
                config=config,
            )

            if not response:
                self.logger.warning("❌ No response from additional products search")
                return {}

            # Extract text from response (same logic as main extraction)
            text = None
            if hasattr(response, 'text') and response.text:
                text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts is not None:
                            if len(candidate.content.parts) > 0:
                                part = candidate.content.parts[0]
                                if hasattr(part, 'text') and part.text:
                                    text = part.text.strip()
                except (IndexError, AttributeError) as e:
                    self.logger.warning(f"❌ Error extracting text from additional search response: {e}")

            if not text:
                self.logger.warning("❌ No text content found in additional products response")
                return {}

            self.logger.info(f"🔍 Additional products search response ({len(text)} chars): {text}")

            # Parse JSON response
            try:
                import json
                json_text = text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                additional_products = json.loads(json_text)
                
                # Check if no additional products found
                if "NO_ADDITIONAL_PRODUCTS" in additional_products:
                    self.logger.info("✅ No additional products found - extraction was complete")
                    return {}
                
                # Validate format
                if not isinstance(additional_products, dict):
                    raise ValueError("Response is not a dictionary")
                
                for product_name, product_data in additional_products.items():
                    if not isinstance(product_data, dict) or 'quantity' not in product_data or 'explanation' not in product_data:
                        raise ValueError(f"Invalid format for additional product: {product_name}")
                
                # Double-check we're not duplicating existing products (using smarter matching)
                existing_product_names = {name.lower().strip() for name in initial_products.keys()}
                # Also create a set of core product identifiers for better matching
                existing_product_cores = set()
                for name in initial_products.keys():
                    # Extract core identifiers (DN numbers, sizes, model numbers)
                    core_parts = []
                    name_lower = name.lower()
                    # Extract DN numbers
                    if 'dn' in name_lower:
                        dn_matches = re.findall(r'dn\d+', name_lower)
                        core_parts.extend(dn_matches)
                    # Extract sizes like 3/8", 1/2", etc.
                    size_matches = re.findall(r'\d+/\d+"|\d+mm|\d+ mm', name_lower)
                    core_parts.extend([s.replace(' ', '') for s in size_matches])
                    # Extract diameter sizes
                    if 'ø' in name_lower or 'putki' in name_lower:
                        diameter_matches = re.findall(r'\d+', name_lower)
                        core_parts.extend(diameter_matches[:2])  # Take first 2 numbers
                    
                    if core_parts:
                        existing_product_cores.add('_'.join(sorted(core_parts)))
                
                filtered_additional = {}
                
                for product_name, product_data in additional_products.items():
                    product_lower = product_name.lower().strip()
                    
                    # Check exact name match
                    if product_lower in existing_product_names:
                        self.logger.warning(f"⚠️ Skipping duplicate additional product (exact): {product_name}")
                        continue
                    
                    # Check core identifier match
                    is_duplicate = False
                    if existing_product_cores:
                        # Extract core identifiers from additional product
                        core_parts = []
                        if 'dn' in product_lower:
                            dn_matches = re.findall(r'dn\d+', product_lower)
                            core_parts.extend(dn_matches)
                        size_matches = re.findall(r'\d+/\d+"|\d+mm|\d+ mm', product_lower)
                        core_parts.extend([s.replace(' ', '') for s in size_matches])
                        if 'ø' in product_lower or 'putki' in product_lower:
                            diameter_matches = re.findall(r'\d+', product_lower)
                            core_parts.extend(diameter_matches[:2])
                        
                        if core_parts:
                            additional_core = '_'.join(sorted(core_parts))
                            if additional_core in existing_product_cores:
                                self.logger.warning(f"⚠️ Skipping duplicate additional product (core match): {product_name} (core: {additional_core})")
                                is_duplicate = True
                    
                    if not is_duplicate:
                        filtered_additional[product_name] = product_data
                
                if filtered_additional:
                    self.logger.info(f"✅ Found {len(filtered_additional)} additional products: {', '.join(list(filtered_additional.keys())[:3])}{'...' if len(filtered_additional) > 3 else ''}")
                else:
                    self.logger.info("✅ No new additional products after deduplication")
                    
                return filtered_additional
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                self.logger.error(f"❌ Failed to parse additional products JSON response: {e}")
                self.logger.error(f"📄 Raw response: {text}")
                return {}

        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"❌ Additional products search error: {e}")
            return {}
    
    def _call_gemini_api(self, content: str, content_type: str) -> Optional[str]:
        """
        Call Gemini API to analyze content for unclear terms
        
        Args:
            content: Text content to analyze
            content_type: Type of content (email/excel) for logging
            
        Returns:
            API response text or None if failed
        """
        # Use the simplified product extraction approach
        products = self._extract_product_terms(content)
        if products:
            return "\n".join(products)
        return None
    
    # ------------------------------------------------------------------
    # Response parsing and utilities
    # ------------------------------------------------------------------
    def _parse_unclear_terms_response(self, response_text: str, email_context: Dict, source_type: str) -> List[Dict]:
        """
        Parse Gemini response and create unclear terms list
        
        Args:
            response_text: Response from Gemini API
            email_context: Email context information
            source_type: Source type (email/excel)
            
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
            
            # Create unique key for deduplication
            term_key = f"{term.lower()}_{email_context.get('subject', '')}"
            
            if term_key not in self.analyzed_terms:
                self.analyzed_terms.add(term_key)
                
                unclear_term_dict = {
                    'unclear_term': term,
                    'email_subject': email_context.get('subject', ''),
                    'email_date': email_context.get('date'),
                    'source_type': source_type
                }
                
                unclear_terms.append(unclear_term_dict)
                self.unclear_terms_found += 1
        
        return unclear_terms
    
    def _remove_duplicates(self, unclear_terms: List[Dict]) -> List[Dict]:
        """
        Remove duplicate unclear terms based on term and email
        
        Args:
            unclear_terms: List of unclear term dictionaries
            
        Returns:
            List with duplicates removed
        """
        seen = set()
        unique_terms = []
        
        for term_dict in unclear_terms:
            # Create unique key
            key = f"{term_dict['unclear_term'].lower()}_{term_dict['email_subject']}"
            
            if key not in seen:
                seen.add(key)
                unique_terms.append(term_dict)
        
        return unique_terms
    
    def get_analysis_stats(self) -> Dict:
        """
        Get AI analysis statistics
        
        Returns:
            Dictionary with analysis statistics
        """
        return {
            'processed_texts': self.processed_texts,
            'unclear_terms_found': self.unclear_terms_found,
            'api_calls_made': self.api_calls_made,
            'api_errors': self.api_errors
        }

    def _openai_container_excel_analysis(self, excel_rows: List[Dict]) -> Dict[str, Dict[str, str]]:
        """
        Extract products from Excel data using OpenAI container-based analysis
        
        Args:
            excel_rows: List of Excel row dictionaries
            
        Returns:
            Dictionary of product terms
        """
        # If OpenAI client is not configured, fall back to Gemini-based extraction
        if not self.openai_client:
            self.logger.warning("OpenAI client not configured. Falling back to Gemini extraction for Excel data.")
            table_text = self._combine_excel_rows(excel_rows)
            return self._extract_product_terms(table_text)

        try:
            import json as _json

            # Convert Excel rows to CSV bytes
            df = pd.DataFrame(excel_rows)
            csv_bytes = df.to_csv(index=False).encode("utf-8")

            # Upload the CSV as a File object
            file_obj = self.openai_client.files.create(
                file=("excel_data.csv", io.BytesIO(csv_bytes)),
                purpose="assistants"
            )

            # Format existing products context
            existing_products_context = ""
            if self.existing_products:
                existing_products_list = []
                for prod in self.existing_products:
                    existing_products_list.append(f"- {prod['product_code']}: {prod['product_name']} (customer term: {prod['customer_term']})")
                existing_products_context = f"""
ALREADY ADDED PRODUCTS TO OFFER (do not extract these again):
{chr(10).join(existing_products_list)}

"""

            prompt =f"""You are an expert in Finnish HVAC product analysis. 

{existing_products_context}Using the code execution tool, read the uploaded CSV file and extract every HVAC product by default unless explicitly excluded.

CRITICAL: PRESERVE ALL PRODUCT CODES/SKUs IN JSON KEYS!
If ANY column contains product codes (Tuotekoodi, SKU, Koodi, Artikkelitunnus, etc.), 
these codes MUST be included at the START of each JSON key!

For each row that represents a product to be offered, gather:
1. The PRODUCT CODE/SKU first (if available in any column)
2. The exact product name as found in the spreadsheet
3. The quantity (default to 1 if missing) 
4. A brief Finnish explanation of the component type
5. IMPORTANT: Do not include any products that are already listed above as "ALREADY ADDED PRODUCTS TO OFFER"

PRODUCT CODE DETECTION:
- Look for columns named: Tuotekoodi, Koodi, SKU, Artikkelitunnus, Product Code, Artikkeli, Numero
- Also check for alphanumeric patterns that look like codes: ABC-123, OP12345, 654321
- Combine: "PRODUCT_CODE product_name" as the JSON key

Ignore rows that are clearly titles, empty or explicitly excluded from the offer.

Generate Python code to:
1. Read the CSV file
2. Identify the product code column (if exists)
3. Analyze each row for HVAC products
4. Extract product CODES + names, quantities, and generate explanations
5. Output a JSON object with codes in keys


Return ONLY a JSON object in this exact format:
{{
  "PRODUCT_CODE product_name_1": {{"quantity": "qty", "explanation": "selitys"}},
  "PRODUCT_CODE product_name_2": {{"quantity": "qty", "explanation": "selitys"}}
}}

EXAMPLE - If CSV has columns "Koodi | Tuote | Määrä":
Input: ABC-100 | Venttiili DN25 | 3
Output: {{"ABC-100 Venttiili DN25": {{"quantity": "3", "explanation": "venttiili"}}}}

If no HVAC products found, return: {{"NO_PRODUCTS_FOUND": {{"quantity": "0", "explanation": "Ei löydetty HVAC-tuotteita"}}}}


MOST IMPORTANTLY; DO NOT HALLUCINATE. ONLY PROVIDE PRODUCT NAMES AND QUANTITIES PROVIDED IN THE FILE.
ALWAYS INCLUDE PRODUCT CODES FROM THE FILE IN YOUR OUTPUT KEYS!"""

            # Call the Responses API with the code interpreter tool and auto container
            response = self.openai_client.responses.create(
                model="gpt-4.1",  # Lightweight but code-capable model
                tools=[{
                    "type": "code_interpreter",
                    "container": {
                        "type": "auto",
                        "file_ids": [file_obj.id]
                    }
                }],
                tool_choice="auto",
                input=prompt
            )

            self.api_calls_made += 1

            result_text = (response.output_text or "").strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]  # strip the ```json
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            products_dict = _json.loads(result_text) if result_text else {}

            if not isinstance(products_dict, dict):
                self.logger.warning("OpenAI container returned unexpected format. Falling back to Gemini extraction.")
                raise ValueError("Unexpected format")

            self.logger.info(f"🗂️ OpenAI container extracted {len(products_dict)} products from Excel.")
            return products_dict

        except Exception as exc:
            self.logger.error(f"OpenAI container analysis failed: {exc}")
            self.api_errors += 1
            return {}

    def _openai_container_pdf_analysis(self, pdf_contents: List[Dict]) -> Dict[str, Dict[str, str]]:
        """
        Extract products from PDF content using OpenAI container-based analysis
        
        Args:
            pdf_contents: List of PDF content dictionaries
            
        Returns:
            Dictionary of product terms
        """
        # Implement the logic to extract products from PDF content using OpenAI container-based analysis
        # This is a placeholder and should be replaced with the actual implementation
        return {}

    def _gemini_container_excel_analysis(self, excel_rows: List[Dict], customer_email: str) -> Dict[str, Dict[str, str]]:
        """
        Extract products from Excel data using Gemini container-based analysis with file inputs
        
        Args:
            excel_rows: List of Excel row dictionaries
            
        Returns:
            Dictionary of product terms
        """
        try:
            import json as _json
            import tempfile
            import csv

            # Manually create pure CSV content to avoid any Excel metadata
            # Get all column headers from the data
            all_columns = set()
            for row in excel_rows:
                all_columns.update(row.keys())
            columns = sorted([col for col in all_columns if not pd.isna(col) and str(col).strip() and str(col).lower() != 'nan'])
            
            # Create temporary CSV file with manual CSV writing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as temp_file:
                writer = csv.writer(temp_file, quoting=csv.QUOTE_ALL)
                
                # Write header
                writer.writerow(columns)
                
                # Write data rows
                for row in excel_rows:
                    row_data = []
                    for col in columns:
                        value = row.get(col, "")
                        # Properly check for NaN using pandas.isna() before converting to string
                        if pd.isna(value) or not str(value).strip() or str(value).lower() == 'nan':
                            row_data.append("")
                        else:
                            row_data.append(str(value).strip())
                    writer.writerow(row_data)
                
                temp_file_path = temp_file.name

            try:
                # Upload the CSV file using Gemini Files API with explicit MIME type
                uploaded_file = self.gemini_client.files.upload(
                    file=temp_file_path,
                    config=dict(mime_type='text/csv')
                )
                
                self.logger.info(f"📤 Uploaded Excel data to Gemini Files API: {uploaded_file.uri}")

                # Format existing products context
                existing_products_context = ""
                if self.existing_products:
                    existing_products_list = []
                    for prod in self.existing_products:
                        existing_products_list.append(f"- {prod['product_code']}: {prod['product_name']} (customer term: {prod['customer_term']})")
                    existing_products_context = f"""
ALREADY ADDED PRODUCTS TO OFFER (do not extract these again):
{chr(10).join(existing_products_list)}

"""

                prompt = f"""You are an expert in Finnish HVAC product analysis. 

{existing_products_context}Using the code execution tool, read the uploaded CSV file and extract every HVAC product by default unless explicitly excluded.

🔴 CRITICAL: PRESERVE ALL PRODUCT CODES/SKUs IN JSON KEYS!
If ANY column contains product codes (Tuotekoodi, SKU, Koodi, Artikkelitunnus, etc.), 
these codes MUST be included at the START of each JSON key!

For each row that represents a product to be offered, gather:
1. The PRODUCT CODE/SKU first (if available in any column)
2. The exact product name as found in the spreadsheet
3. The quantity (default to 1 if missing) 
4. A brief Finnish explanation of the component type
5. IMPORTANT: Do not include any products that are already listed above as "ALREADY ADDED PRODUCTS TO OFFER"

PRODUCT CODE DETECTION:
- Look for columns named: Tuotekoodi, Koodi, SKU, Artikkelitunnus, Product Code, Artikkeli, Numero
- Also check for alphanumeric patterns that look like codes: ABC-123, OP12345, 654321
- Combine: "PRODUCT_CODE product_name" as the JSON key

Ignore rows that are clearly titles, empty or explicitly excluded from the offer.

Generate Python code to:
1. Read the CSV file
2. Identify the product code column (if exists)
3. Analyze each row for HVAC products
4. Extract product CODES + names, quantities, and generate explanations
5. Output a JSON object with codes in keys


Return ONLY a JSON object in this exact format:
{{
  "PRODUCT_CODE product_name_1": {{"quantity": "qty", "explanation": "selitys"}},
  "PRODUCT_CODE product_name_2": {{"quantity": "qty", "explanation": "selitys"}}
}}

EXAMPLE - If CSV has columns "Koodi | Tuote | Määrä":
Input: ABC-100 | Venttiili DN25 | 3
Output: {{"ABC-100 Venttiili DN25": {{"quantity": "3", "explanation": "venttiili"}}}}

If no HVAC products found, return: {{"NO_PRODUCTS_FOUND": {{"quantity": "0", "explanation": "Ei löydetty HVAC-tuotteita"}}}}


MOST IMPORTANTLY; DO NOT HALLUCINATE. ONLY PROVIDE PRODUCT NAMES AND QUANTITIES PROVIDED IN THE FILE.
🔴 ALWAYS INCLUDE PRODUCT CODES FROM THE FILE IN YOUR OUTPUT KEYS!

Do NOT output ANYTHING else than the JSON object.


Customer's email:

{customer_email}

"""

                config = types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
                    temperature=0.1
                )

                # Structure content with proper user role and file data
                content_parts = [
                    types.Part(text=prompt),
                    types.Part(file_data=types.FileData(
                        mime_type="text/csv",
                        file_uri=uploaded_file.uri
                    ))
                ]
                
                response = self._retry_llm_request(
                    self.gemini_client.models.generate_content,
                    model=Config.GEMINI_MODEL_THINKING,
                    contents=[types.Content(parts=content_parts, role="user")],
                    config=config,
                )

                self.api_calls_made += 1

                # Extract result from response
                result_text = ""
                
                # Process all parts of the response
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                # Get text content
                                if hasattr(part, 'text') and part.text:
                                    result_text += part.text + "\n"
                                    
                                # Log code execution if present
                                if hasattr(part, 'executable_code') and part.executable_code:
                                    self.logger.info(f"🐍 Gemini executed code:\n{part.executable_code.code}")
                                    
                                # Get code execution results
                                if hasattr(part, 'code_execution_result') and part.code_execution_result:
                                    if hasattr(part.code_execution_result, 'output'):
                                        result_text += part.code_execution_result.output + "\n"
                                        self.logger.info(f"📊 Code execution output:\n{part.code_execution_result.output}")

                # Clean up the result text to extract JSON
                result_text = result_text.strip()
                
                # Look for JSON in the response
                json_text = "{}"
                
                # First try to extract from code blocks
                if "```json" in result_text:
                    json_start = result_text.find("```json") + 7
                    json_end = result_text.find("```", json_start)
                    if json_end > json_start:
                        json_text = result_text[json_start:json_end].strip()
                else:
                    # Fallback: try to find complete JSON object
                    json_start = result_text.find('{')
                    if json_start >= 0:
                        # Find matching closing brace by counting braces
                        brace_count = 0
                        json_end = json_start
                        for i, char in enumerate(result_text[json_start:], json_start):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        
                        if brace_count == 0:  # Found complete JSON object
                            json_text = result_text[json_start:json_end]
                # write into file json content
                with open('json_content.json', 'w', encoding='utf-8') as f:
                    f.write(json_text)

                # Parse JSON response
                try:
                    self.logger.info(f"🔍 Attempting to parse JSON: {json_text[:200]}...")
                    
                    # Handle Unicode characters that might cause JSON parsing issues
                    # Various Unicode symbols in HVAC product names can cause "Invalid control character" errors
                    if json_text:
                        # First attempt: try parsing with strict=False to be more permissive
                        try:
                            products_dict = _json.loads(json_text, strict=False)
                        except _json.JSONDecodeError as unicode_error:
                            # If strict=False doesn't work, sanitize problematic Unicode characters
                            self.logger.warning(f"⚠️ JSON parsing failed due to Unicode chars, attempting to sanitize: {unicode_error}")
                            
                            sanitized_json = json_text
                            
                            # Common problematic Unicode characters in HVAC product names:
                            unicode_replacements = {
                                # Degree symbols and related
                                'º': '°',      # U+00BA (masculine ordinal indicator) → U+00B0 (degree symbol)
                                '\u00ba': '°', # Same as above, explicit Unicode
                                '°': 'deg',    # U+00B0 (degree symbol) → text
                                
                                # Mathematical symbols that might appear
                                '±': '+/-',    # U+00B1 (plus-minus sign)
                                '²': '2',      # U+00B2 (superscript two)
                                '³': '3',      # U+00B3 (superscript three)
                                '¼': '1/4',    # U+00BC (vulgar fraction one quarter)
                                '½': '1/2',    # U+00BD (vulgar fraction one half)
                                '¾': '3/4',    # U+00BE (vulgar fraction three quarters)
                                
                                # Measurement symbols
                                'µ': 'u',      # U+00B5 (micro sign)
                                
                                # Other potentially problematic characters
                                '\u2013': '-', # En dash
                                '\u2014': '-', # Em dash
                                '\u2018': "'", # Left single quotation mark
                                '\u2019': "'", # Right single quotation mark
                                '\u201c': '"', # Left double quotation mark
                                '\u201d': '"', # Right double quotation mark
                            }
                            
                            # Apply all replacements
                            for unicode_char, replacement in unicode_replacements.items():
                                if unicode_char in sanitized_json:
                                    sanitized_json = sanitized_json.replace(unicode_char, replacement)
                                    self.logger.debug(f"🔧 Replaced '{unicode_char}' with '{replacement}'")
                            
                            try:
                                products_dict = _json.loads(sanitized_json, strict=False)
                                self.logger.info("✅ Successfully parsed JSON after Unicode sanitization")
                            except _json.JSONDecodeError as final_error:
                                # Last resort: try to extract valid JSON manually
                                self.logger.error(f"❌ Final JSON parsing failed even after sanitization: {final_error}")
                                self.logger.error(f"Problematic JSON (first 500 chars): {sanitized_json[:500]}")
                                products_dict = {}
                    else:
                        products_dict = {}
                    self.logger.info(f"🔍 Parsed products_dict with {len(products_dict)} items")
                    
                    # Check if no products found
                    if "NO_PRODUCTS_FOUND" in products_dict:
                        self.logger.info("✅ Gemini container found no HVAC products in Excel")
                        return {}
                    
                    if not isinstance(products_dict, dict):
                        self.logger.warning("Gemini container returned unexpected format. Falling back to regular extraction.")
                        raise ValueError("Unexpected format")

                    self.logger.info(f"🗂️ Gemini container extracted {len(products_dict)} products from Excel.")
                    return products_dict
                    
                except (_json.JSONDecodeError, ValueError) as json_error:
                    self.logger.error(f"Failed to parse Gemini container JSON: {json_error}")
                    self.logger.error(f"Raw result: {result_text}")
                    return {}

            except Exception as inner_exc:
                self.logger.error(f"Gemini container inner analysis failed: {inner_exc}")
                self.api_errors += 1
                return {}
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

        except Exception as exc:
            self.logger.error(f"Gemini container analysis failed: {exc}")
            self.api_errors += 1
            time.sleep(10)
            # Fallback to regular Gemini extraction
            table_text = self._combine_excel_rows(excel_rows)
            return self._extract_product_terms(table_text)
