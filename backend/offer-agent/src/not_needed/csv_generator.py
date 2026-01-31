"""
CSV generator module for creating output files with unclear HVAC terms
"""
import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Set
from pathlib import Path

from .config import Config

class CSVGenerator:
    """Handles CSV output generation for unclear terms"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_file_path = None
        self.terms_written = 0
        self.duplicates_prevented = 0
    
    def create_csv(self, unclear_terms: List[Dict], processed_emails: List[Dict] = None) -> str:
        """
        Create CSV file with unclear terms data
        
        Args:
            unclear_terms: List of unclear term dictionaries
            processed_emails: List of processed emails (for empty CSV case)
            
        Returns:
            Path to the created CSV file
        """
        if not unclear_terms:
            self.logger.warning("No unclear terms to write to CSV")
            return self._create_empty_csv(processed_emails)
        
        # Remove duplicates
        unique_terms = self._remove_final_duplicates(unclear_terms)
        
        # Create output file path
        self.output_file_path = os.path.join(Config.OUTPUT_DIR, Config.OUTPUT_CSV_NAME)
        
        self.logger.info(f"Creating CSV file: {self.output_file_path}")
        
        try:
            # Write CSV file with proper Finnish encoding
            with open(self.output_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=Config.CSV_COLUMNS)
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                for term_dict in unique_terms:
                    # Format the data for CSV
                    csv_row = self._format_csv_row(term_dict)
                    writer.writerow(csv_row)
                    self.terms_written += 1
            
            self.logger.info(f"CSV file created successfully: {self.output_file_path}")
            self.logger.info(f"Written {self.terms_written} unique terms, "
                           f"prevented {self.duplicates_prevented} duplicates")
            
            return self.output_file_path
            
        except Exception as e:
            self.logger.error(f"Error creating CSV file: {str(e)}")
            raise
    
    def _create_empty_csv(self, processed_emails: List[Dict] = None) -> str:
        """
        Create empty CSV file when no unclear terms found
        
        Args:
            processed_emails: List of processed emails to include in empty CSV
        
        Returns:
            Path to the created empty CSV file
        """
        self.output_file_path = os.path.join(Config.OUTPUT_DIR, Config.OUTPUT_CSV_NAME)
        
        try:
            with open(self.output_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=Config.CSV_COLUMNS)
                writer.writeheader()
                
                # If we have processed emails, include them with "no unclear terms" message
                if processed_emails:
                    for email in processed_emails:
                        email_date = email.get('date')
                        if email_date:
                            if hasattr(email_date, 'strftime'):
                                formatted_date = email_date.strftime('%Y-%m-%d')
                            else:
                                formatted_date = str(email_date)[:10]
                        else:
                            formatted_date = ''
                        
                        message_row = {
                            'unclear_term': 'No unclear terms found',
                            'email_subject': email.get('subject', 'Unknown subject').strip(),
                            'email_date': formatted_date,
                            'source_type': 'email',
                            'source_file': ''
                        }
                        writer.writerow(message_row)
                else:
                    # Fallback message when no emails provided
                    message_row = {
                        'unclear_term': 'No unclear terms found',
                        'email_subject': 'Analysis completed but no unclear HVAC terms were identified',
                        'email_date': datetime.now().strftime('%Y-%m-%d'),
                        'source_type': 'system',
                        'source_file': ''
                    }
                    writer.writerow(message_row)
            
            self.logger.info(f"Empty CSV file created: {self.output_file_path}")
            return self.output_file_path
            
        except Exception as e:
            self.logger.error(f"Error creating empty CSV file: {str(e)}")
            raise
    
    def _remove_final_duplicates(self, unclear_terms: List[Dict]) -> List[Dict]:
        """
        Final deduplication based on unclear term text only
        
        Args:
            unclear_terms: List of unclear term dictionaries
            
        Returns:
            List with final duplicates removed
        """
        seen_terms: Set[str] = set()
        unique_terms = []
        
        for term_dict in unclear_terms:
            term_text = term_dict.get('unclear_term', '').strip().lower()
            
            if term_text and term_text not in seen_terms:
                seen_terms.add(term_text)
                unique_terms.append(term_dict)
            else:
                self.duplicates_prevented += 1
        
        return unique_terms
    
    def _format_csv_row(self, term_dict: Dict) -> Dict:
        """
        Format unclear term dictionary for CSV output
        
        Args:
            term_dict: Unclear term dictionary
            
        Returns:
            Formatted dictionary for CSV writing
        """
        # Format date
        email_date = term_dict.get('email_date')
        if email_date:
            if hasattr(email_date, 'strftime'):
                formatted_date = email_date.strftime('%Y-%m-%d')
            else:
                formatted_date = str(email_date)[:10]  # Take first 10 chars if string
        else:
            formatted_date = ''
        
        # Determine source type and file
        source_type = term_dict.get('source_type', 'email')  # Default to email for backward compatibility
        source_file = ''
        
        if source_type == 'image':
            source_file = term_dict.get('image_filename', '')
        elif source_type == 'excel':
            source_file = term_dict.get('filename', '')
        
        # Create clean CSV row
        csv_row = {
            'unclear_term': str(term_dict.get('unclear_term', '')).strip(),
            'email_subject': str(term_dict.get('email_subject', '')).strip(),
            'email_date': formatted_date,
            'source_type': source_type,
            'source_file': source_file
        }
        
        return csv_row
    
    def get_output_stats(self) -> Dict:
        """
        Get CSV generation statistics
        
        Returns:
            Dictionary with output statistics
        """
        return {
            'output_file': self.output_file_path,
            'terms_written': self.terms_written,
            'duplicates_prevented': self.duplicates_prevented
        } 