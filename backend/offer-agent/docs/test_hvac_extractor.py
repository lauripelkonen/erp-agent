"""
Test version of HVAC offer extractor with limited processing for testing AI functionality.
This script processes only the first 2 emails containing 'tarjouspyyntö' for faster testing.
"""
import os
import sys
import logging
import csv
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from config import Config

def setup_test_logging():
    """Setup logging configuration for test run"""
    # Create logs directory if it doesn't exist
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    
    # Configure logging with detailed format
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                os.path.join(Config.LOGS_DIR, 'test_hvac_extractor.log'),
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("HVAC Offer Extractor TEST MODE started")
    logger.info("Processing emails with PDF attachments (first 2 found)")
    logger.info(f"PST file location: {Config.PST_FILE_PATH}")
    
    return logger

class RealtimeCSVWriter:
    """Handles real-time CSV writing as products are processed"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unclear_csv_path = None
        self.matched_csv_path = None
        self.unclear_written = 0
        self.matched_written = 0
        self._initialize_csvs()
    
    def _initialize_csvs(self):
        """Initialize both CSV files with headers"""
        # Ensure output directory exists
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        
        # Initialize unclear terms CSV
        self.unclear_csv_path = os.path.join(Config.OUTPUT_DIR, f"TEST_{Config.OUTPUT_CSV_NAME}")
        try:
            with open(self.unclear_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=Config.CSV_COLUMNS)
                writer.writeheader()
            self.logger.info(f"✅ Unclear terms CSV initialized: {self.unclear_csv_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize unclear terms CSV: {e}")
            raise
        
        # Initialize matched products CSV
        self.matched_csv_path = os.path.join(Config.OUTPUT_DIR, f"TEST_matched_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        matched_columns = ['unclear_term', 'quantity', 'explanation', 'email_subject', 'email_date', 'source_type', 
                          'matched_product_code', 'matched_product_name', 'confidence_reason']
        try:
            with open(self.matched_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=matched_columns)
                writer.writeheader()
            self.logger.info(f"✅ Matched products CSV initialized: {self.matched_csv_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize matched products CSV: {e}")
            raise
        
        self.logger.info(f"✅ Real-time CSVs initialized:")
        self.logger.info(f"   📝 Unclear terms: {self.unclear_csv_path}")
        self.logger.info(f"   ✨ Matched products: {self.matched_csv_path}")
        
        # Verify files exist
        if not os.path.exists(self.unclear_csv_path):
            self.logger.error(f"❌ Unclear terms CSV not found after creation: {self.unclear_csv_path}")
        if not os.path.exists(self.matched_csv_path):
            self.logger.error(f"❌ Matched products CSV not found after creation: {self.matched_csv_path}")
    
    def write_unclear_term(self, term_dict: Dict):
        """Write a single unclear term to CSV in real-time"""
        try:
            # Format the data
            csv_row = self._format_unclear_row(term_dict)
            
            # Append to CSV
            with open(self.unclear_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=Config.CSV_COLUMNS)
                writer.writerow(csv_row)
                f.flush()  # Force write to disk immediately
            
            self.unclear_written += 1
            self.logger.info(f"💾 Added unclear term: '{term_dict.get('unclear_term', 'N/A')}' → {self.unclear_csv_path}")
            
        except Exception as e:
            self.logger.error(f"Error writing unclear term to CSV: {e}")
    
    def write_matched_product(self, match_dict: Dict):
        """Write a single matched product to CSV in real-time"""
        try:
            self.logger.debug(f"📝 Writing matched product to CSV: {match_dict}")
            
            # Format the data
            csv_row = self._format_matched_row(match_dict)
            self.logger.debug(f"📝 Formatted row: {csv_row}")
            
            # Append to CSV
            with open(self.matched_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                matched_columns = ['unclear_term', 'quantity', 'explanation', 'email_subject', 'email_date', 'source_type', 
                                 'matched_product_code', 'matched_product_name', 'confidence_reason']
                writer = csv.DictWriter(f, fieldnames=matched_columns)
                writer.writerow(csv_row)
                f.flush()  # Force write to disk immediately
            
            self.matched_written += 1
            self.logger.info(f"✅ Added matched product: '{match_dict.get('unclear_term', 'N/A')}' → {match_dict.get('matched_product_name', 'N/A')} → {self.matched_csv_path}")
            
        except Exception as e:
            self.logger.error(f"Error writing matched product to CSV: {e}")
            self.logger.error(f"Match dict was: {match_dict}")
    
    def _format_unclear_row(self, term_dict: Dict) -> Dict:
        """Format unclear term dictionary for CSV output"""
        # Format date
        email_date = term_dict.get('email_date')
        if email_date:
            if hasattr(email_date, 'strftime'):
                formatted_date = email_date.strftime('%Y-%m-%d')
            else:
                formatted_date = str(email_date)[:10]
        else:
            formatted_date = ''
        
        # Determine source info
        source_type = term_dict.get('source_type', 'email')
        source_file = ''
        
        if source_type == 'image':
            source_file = term_dict.get('image_filename', '')
        elif source_type == 'excel':
            source_file = term_dict.get('filename', '')
        
        return {
            'unclear_term': str(term_dict.get('unclear_term', '')).strip(),
            'quantity': str(term_dict.get('quantity', '1')).strip(),
            'explanation': str(term_dict.get('explanation', '')).strip(),
            'email_subject': str(term_dict.get('email_subject', '')).strip(),
            'email_date': formatted_date,
            'source_type': source_type,
            'source_file': source_file
        }
    
    def _format_matched_row(self, match_dict: Dict) -> Dict:
        """Format matched product dictionary for CSV output"""
        # Format date
        email_date = match_dict.get('email_date')
        if email_date:
            if hasattr(email_date, 'strftime'):
                formatted_date = email_date.strftime('%Y-%m-%d')
            else:
                formatted_date = str(email_date)[:10]
        else:
            formatted_date = ''
        
        # Determine source info
        source_type = match_dict.get('source_type', 'email')
        
        return {
            'unclear_term': str(match_dict.get('unclear_term', '')).strip(),
            'quantity': str(match_dict.get('quantity', '1')).strip(),
            'explanation': str(match_dict.get('explanation', '')).strip(),
            'email_subject': str(match_dict.get('email_subject', '')).strip(),
            'email_date': formatted_date,
            'source_type': source_type,
            'matched_product_code': str(match_dict.get('matched_product_code', '')).strip(),
            'matched_product_name': str(match_dict.get('matched_product_name', '')).strip(),
            'confidence_reason': str(match_dict.get('confidence_reason', '')).strip()
        }
    
    def get_stats(self):
        """Get writing statistics"""
        return {
            'unclear_written': self.unclear_written,
            'matched_written': self.matched_written,
            'unclear_csv_path': self.unclear_csv_path,
            'matched_csv_path': self.matched_csv_path
        }

class TestEmailProcessor:
    """Modified email processor that finds emails with PDF attachments"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_count = 0
        self.filtered_count = 0
        self.error_count = 0
        self.target_emails_found = 0
        self.max_target_emails = 2
        self.max_search_emails = 1000  # Add reasonable search limit to prevent endless processing
    
    def process_pst_file(self, pst_file_path: str):
        """Process PST file and return first target emails using libratom"""
        from email_processor import EmailProcessor
        from libratom.lib.pff import PffArchive
        
        # Use the original processor but with custom logic
        original_processor = EmailProcessor()
        
        self.logger.info(f"Opening PST file: {pst_file_path}")
        
        try:
            # Open PST file using libratom
            with PffArchive(pst_file_path) as archive:
                filtered_emails = []
                
                # Process messages until we find target emails
                self._process_messages_limited(archive, filtered_emails, original_processor)
                
                self.logger.info(f"Test processing complete. Processed: {self.processed_count}, "
                               f"Found target emails: {self.target_emails_found}")
                
                return filtered_emails
            
        except Exception as e:
            self.logger.error(f"Error opening PST file: {str(e)}")
            raise
    
    def _process_messages_limited(self, archive, filtered_emails, original_processor):
        """Process messages using libratom but stop after finding target number of emails"""
        try:
            # Iterate through all messages in the PST archive
            for message in archive.messages():
                if self.target_emails_found >= self.max_target_emails:
                    break
                    
                # Stop if we've searched enough emails
                if self.processed_count >= self.max_search_emails:
                    self.logger.info(f"🔍 Reached search limit of {self.max_search_emails} emails. Stopping search.")
                    break
                    
                try:
                    self._process_message_limited(message, filtered_emails, original_processor)
                except Exception as e:
                    self.logger.debug(f"Error processing message: {str(e)}")
                    self.error_count += 1
                    
                # Log progress every 100 emails to show we're searching
                if self.processed_count % 100 == 0:
                    self.logger.info(f"📧 Searched {self.processed_count} emails so far, found {self.target_emails_found} with PDFs...")
                    
        except Exception as e:
            self.logger.error(f"Error processing PST messages: {str(e)}")
            self.error_count += 1
    
    def _process_message_limited(self, message, filtered_emails, original_processor):
        """Process message and add to filtered list if it contains PDF attachments"""
        try:
            self.processed_count += 1
            
            # Extract email data using original processor logic
            email_data = original_processor._extract_email_data(message)
            
            if email_data is None:
                return
            
            # Look for PDF attachments - PDFs should be in attachments, not inline images
            attachments = email_data.get('attachments', [])
            
            pdf_attachments = []
            for att in attachments:
                filename = att.get('filename', 'no_filename').lower()
                # Only check for actual PDF files
                if filename.endswith('.pdf') or '.pdf' in filename:
                    pdf_attachments.append(att)
            
            # If this email has PDF attachments, add it to the filtered list
            if pdf_attachments:
                filtered_emails.append(email_data)
                self.target_emails_found += 1
                self.filtered_count += 1
                
                self.logger.info(f"✅ Found email with PDFs #{self.target_emails_found}: {email_data['subject'][:100]}")
                self.logger.info(f"   📅 Date: {email_data['date']}")
                self.logger.info(f"   📧 From: {email_data['sender']}")
                self.logger.info(f"   📎 Total Attachments: {len(attachments)}")
                self.logger.info(f"   📄 PDF Files Found: {len(pdf_attachments)}")
                for i, pdf in enumerate(pdf_attachments, 1):
                    self.logger.info(f"      📄 PDF {i}: {pdf.get('filename', 'unknown.pdf')}")
                
                if self.target_emails_found >= self.max_target_emails:
                    self.logger.info(f"🎯 Target reached! Found {self.max_target_emails} emails with PDFs. Stopping search.")
            else:
                # Log emails with tarjouspyyntö but no PDFs for debugging
                subject = email_data.get('subject', '').lower()
                if any(keyword in subject for keyword in ["tarjouspyyntö", "rek nok"]):
                    self.logger.debug(f"🔍 Tarjouspyyntö email without PDFs: '{email_data.get('subject', '')[:80]}'")
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            self.error_count += 1
    
    def get_processing_stats(self):
        """Get processing statistics"""
        return {
            'processed_count': self.processed_count,
            'filtered_count': self.filtered_count,
            'error_count': self.error_count,
            'target_emails_found': self.target_emails_found
        }

class RealtimeAIAnalyzer:
    """Modified AI analyzer that writes to CSV in real-time"""
    
    def __init__(self, csv_writer: RealtimeCSVWriter):
        self.csv_writer = csv_writer
        self.logger = logging.getLogger(__name__)
        
        # Import and initialize the original analyzer
        from ai_analyzer import AIAnalyzer
        self.ai_analyzer = AIAnalyzer()
    
    def analyze_with_realtime_output(self, filtered_emails: List[Dict], excel_data: List[Dict], pdf_data: List[Dict]):
        """Analyze emails and write results to CSV in real-time"""
        self.logger.info("🤖 Starting real-time AI analysis...")
        
        # Define callback functions for real-time CSV updates
        def on_unclear_term_found(unclear_dict):
            """Callback to write unclear terms to CSV immediately"""
            self.csv_writer.write_unclear_term(unclear_dict)
        
        def on_match_found(match_dict):
            """Callback to write matched products to CSV immediately"""
            self.csv_writer.write_matched_product(match_dict)
        
        # Use the main identify_unclear_terms method with real-time callbacks
        unclear_terms = self.ai_analyzer.identify_unclear_terms(
            filtered_emails, 
            excel_data,
            pdf_data,
            on_unclear_term_found=on_unclear_term_found,
            on_match_found=on_match_found
        )
        
        self.logger.info(f"🎉 Analysis complete! Found {len(unclear_terms)} unclear terms total")
        
        # Return stats
        return self.csv_writer.get_stats()

def main():
    """Main test execution function with real-time CSV updates"""
    logger = setup_test_logging()
    
    try:
        # Validate PST file exists
        if not os.path.exists(Config.PST_FILE_PATH):
            logger.error(f"PST file not found: {Config.PST_FILE_PATH}")
            sys.exit(1)
        
        logger.info("Starting HVAC offer extraction TEST with REAL-TIME CSV updates...")
        logger.info("=" * 70)
        
        # Initialize real-time CSV writer
        csv_writer = RealtimeCSVWriter()
        
        # Step 1: Process target emails from PST file
        logger.info("Step 1: Finding emails with PDF attachments...")
        test_processor = TestEmailProcessor()
        filtered_emails = test_processor.process_pst_file(Config.PST_FILE_PATH)
        
        email_stats = test_processor.get_processing_stats()
        logger.info(f"Email processing stats: {email_stats}")
        
        if not filtered_emails:
            logger.warning("No emails with PDF attachments found! Check PST file and search criteria.")
            return
        
        # Step 2: Extract Excel attachments
        logger.info("Step 2: Processing Excel attachments...")
        from attachment_processor import AttachmentProcessor
        attachment_processor = AttachmentProcessor()
        excel_data = attachment_processor.extract_excel_content(filtered_emails)
        
        excel_stats = attachment_processor.get_processing_stats()
        logger.info(f"Excel processing stats: {excel_stats}")
        
        # Step 2.5: Extract PDF attachments
        logger.info("Step 2.5: Processing PDF attachments...")
        from pdf_processor import PDFProcessor
        pdf_processor = PDFProcessor()
        pdf_data = pdf_processor.extract_pdf_content(filtered_emails)
        
        pdf_stats = pdf_processor.get_processing_stats()
        logger.info(f"PDF processing stats: {pdf_stats}")
        
        # Step 3: Analyze with AI and write to CSV in real-time
        logger.info("Step 3: Analyzing with AI and updating CSVs in real-time...")
        realtime_analyzer = RealtimeAIAnalyzer(csv_writer)
        analysis_stats = realtime_analyzer.analyze_with_realtime_output(filtered_emails, excel_data, pdf_data)
        
        # Final statistics
        logger.info("=" * 70)
        logger.info("🎉 HVAC offer extraction TEST with REAL-TIME updates completed!")
        logger.info(f"📁 Unclear terms CSV: {analysis_stats['unclear_csv_path']}")
        logger.info(f"📁 Matched products CSV: {analysis_stats['matched_csv_path']}")
        logger.info(f"🔍 Unclear terms written: {analysis_stats['unclear_written']}")
        logger.info(f"✅ Matched products written: {analysis_stats['matched_written']}")
        logger.info(f"📧 Emails processed: {email_stats['target_emails_found']}")
        logger.info(f"📄 PDFs processed: {pdf_stats['processed_pdfs']}")
        logger.info(f"🎯 PDFs filtered as relevant: {pdf_stats['filtered_pdfs']}")
        
        # Verify CSV files exist and show their sizes
        unclear_path = analysis_stats['unclear_csv_path']
        matched_path = analysis_stats['matched_csv_path']
        
        if os.path.exists(unclear_path):
            unclear_size = os.path.getsize(unclear_path)
            logger.info(f"📋 Unclear terms CSV exists: {unclear_size} bytes")
        else:
            logger.error(f"❌ Unclear terms CSV not found: {unclear_path}")
            
        if os.path.exists(matched_path):
            matched_size = os.path.getsize(matched_path)
            logger.info(f"📋 Matched products CSV exists: {matched_size} bytes")
        else:
            logger.error(f"❌ Matched products CSV not found: {matched_path}")
        
        logger.info("=" * 70)
        
        logger.info("\n✅ Real-time test completed! CSVs were updated as products were found.")
        
    except Exception as e:
        logger.error(f"Error during test processing: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 