"""
HVAC Offer Request Product Name Extractor
Main entry point for processing PST emails and extracting unclear product terms
"""
import logging
import sys
from datetime import datetime
import os

from .config import Config

def setup_logging():
    """Set up logging configuration"""
    log_filename = os.path.join(Config.LOGS_DIR, f"hvac_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("HVAC Offer Extractor started")
    logger.info(f"Processing emails from {Config.START_DATE.strftime('%Y-%m-%d')} to {Config.END_DATE.strftime('%Y-%m-%d')}")
    logger.info(f"PST file location: {Config.PST_FILE_PATH}")
    
    return logger

def main():
    """Main execution function"""
    logger = setup_logging()
    
    try:
        # Validate PST file exists
        if not os.path.exists(Config.PST_FILE_PATH):
            logger.error(f"PST file not found: {Config.PST_FILE_PATH}")
            sys.exit(1)
        
        logger.info("Starting HVAC offer extraction process...")
        
        # Import and initialize modules
        from email_processor import EmailProcessor
        from attachment_processor import AttachmentProcessor  
        from ai_analyzer import AIAnalyzer
        from csv_generator import CSVGenerator
        
        # Step 1: Process emails from PST file
        logger.info("Step 1: Processing emails from PST file...")
        email_processor = EmailProcessor()
        filtered_emails = email_processor.process_pst_file(Config.PST_FILE_PATH)
        
        email_stats = email_processor.get_processing_stats()
        logger.info(f"Email processing stats: {email_stats}")
        
        # Step 2: Extract Excel attachments
        logger.info("Step 2: Processing Excel attachments...")
        attachment_processor = AttachmentProcessor()
        excel_data = attachment_processor.extract_excel_content(filtered_emails)
        
        excel_stats = attachment_processor.get_processing_stats()
        logger.info(f"Excel processing stats: {excel_stats}")
        
        # Step 3: Analyze with AI
        logger.info("Step 3: Analyzing product names with AI...")
        ai_analyzer = AIAnalyzer()
        unclear_terms = ai_analyzer.identify_unclear_terms(filtered_emails, excel_data)
        
        ai_stats = ai_analyzer.get_analysis_stats()
        logger.info(f"AI analysis stats: {ai_stats}")
        
        # Step 4: Generate CSV output
        logger.info("Step 4: Generating CSV output...")
        csv_generator = CSVGenerator()
        output_file = csv_generator.create_csv(unclear_terms, filtered_emails)
        
        csv_stats = csv_generator.get_output_stats()
        logger.info(f"CSV generation stats: {csv_stats}")
        
        # Final success message
        logger.info("=" * 60)
        logger.info("HVAC offer extraction completed successfully!")
        logger.info(f"Output file created: {output_file}")
        logger.info(f"Total unclear terms found: {len(unclear_terms)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 