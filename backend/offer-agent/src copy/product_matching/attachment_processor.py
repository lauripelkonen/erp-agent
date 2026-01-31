"""
Attachment processor module for extracting and processing Excel files from emails
"""
import pandas as pd
import logging
import io
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from .config import Config

class AttachmentProcessor:
    """Handles Excel attachment extraction and processing from emails"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_attachments = 0
        self.excel_files_found = 0
        self.excel_files_processed = 0
        self.error_count = 0
    
    def extract_excel_content(self, filtered_emails: List[Dict]) -> List[Dict]:
        """
        Extract and process Excel content from email attachments
        
        Args:
            filtered_emails: List of filtered email dictionaries
            
        Returns:
            List of dictionaries containing Excel data with email context
        """
        self.logger.info("Starting Excel attachment processing...")
        excel_data = []
        
        for email in filtered_emails:
            if email.get('attachments'):
                email_excel_data = self._process_email_attachments(email)
                excel_data.extend(email_excel_data)
        
        self.logger.info(f"Excel processing complete. Found {self.excel_files_found} Excel files, "
                        f"processed {self.excel_files_processed}, errors: {self.error_count}")
        
        return excel_data
    
    def _process_email_attachments(self, email: Dict) -> List[Dict]:
        """
        Process all attachments in a single email
        
        Args:
            email: Email dictionary with attachment information
            
        Returns:
            List of Excel data dictionaries for this email
        """
        email_excel_data = []
        
        for attachment in email.get('attachments', []):
            self.processed_attachments += 1
            
            if self._is_excel_file(attachment['filename']):
                self.excel_files_found += 1
                excel_content = self._extract_excel_data(attachment, email)
                
                if excel_content:
                    email_excel_data.append(excel_content)
                    self.excel_files_processed += 1
        
        return email_excel_data
    
    def _is_excel_file(self, filename: str) -> bool:
        """
        Check if file is a supported spreadsheet file based on extension
        
        Args:
            filename: Name of the attachment file
            
        Returns:
            True if file is supported spreadsheet format, False otherwise
        """
        if not filename:
            return False
        
        file_extension = Path(filename.lower()).suffix
        return file_extension in Config.SUPPORTED_EXCEL_FORMATS
    
    def _extract_excel_data(self, attachment: Dict, email: Dict) -> Optional[Dict]:
        """
        Extract data from Excel attachment
        
        Args:
            attachment: Attachment dictionary with file info
            email: Email context information
            
        Returns:
            Dictionary with Excel data and email context, or None if failed
        """
        try:
            # Get attachment binary data
            attachment_obj = attachment.get('attachment_object')
            if not attachment_obj:
                self.logger.error(f"No attachment object for {attachment['filename']}")
                return None
            
            # Read attachment data (Aspose.Email format)
            try:
                if hasattr(attachment_obj, 'content_stream'):
                    # Aspose.Email attachment
                    attachment_data = attachment_obj.content_stream.to_array()
                else:
                    self.logger.error(f"Unexpected attachment object type for {attachment['filename']}")
                    return None
            except Exception as e:
                self.logger.error(f"Failed to read attachment {attachment['filename']}: {str(e)}")
                self.error_count += 1
                return None
            
            # Parse Excel file
            excel_content = self._parse_excel_content(attachment_data, attachment['filename'])
            
            if excel_content is None:
                return None
            
            # Create result dictionary with email context
            result = {
                'filename': attachment['filename'],
                'email_subject': email['subject'],
                'email_date': email['date'],
                'email_sender': email['sender'],
                'excel_data': excel_content,
                'row_count': len(excel_content) if excel_content else 0
            }
            
            self.logger.debug(f"Successfully processed Excel file: {attachment['filename']} "
                            f"({len(excel_content) if excel_content else 0} rows)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting Excel data from {attachment['filename']}: {str(e)}")
            self.error_count += 1
            return None
    
    def _parse_csv_content(self, attachment_data: bytes, filename: str) -> Optional[List[Dict]]:
        """
        Parse CSV file content and extract text data
        
        Args:
            attachment_data: Binary data of CSV file
            filename: Name of the CSV file for logging
            
        Returns:
            List of dictionaries representing CSV rows, or None if failed
        """
        try:
            self.logger.info(f"🔍 Processing CSV file: {filename}, data size: {len(attachment_data)} bytes")
            
            # Create StringIO object for pandas (CSV needs text mode)
            csv_text = attachment_data.decode('utf-8', errors='ignore')
            csv_buffer = io.StringIO(csv_text)
            
            # Read CSV file
            try:
                df = pd.read_csv(csv_buffer)
                self.logger.info(f"🔍 CSV DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            except Exception as e:
                self.logger.error(f"Failed to parse CSV file {filename}: {str(e)}")
                self.error_count += 1
                return None
            
            # Apply row limit
            if len(df) > Config.MAX_EXCEL_ROWS:
                self.logger.warning(f"CSV file {filename} has {len(df)} rows, "
                                  f"limiting to {Config.MAX_EXCEL_ROWS} rows")
                df = df.head(Config.MAX_EXCEL_ROWS)
            
            # Convert DataFrame to list of dictionaries
            csv_rows = []
            for index, row in df.iterrows():
                row_dict = {}
                for col_name, value in row.items():
                    if pd.isna(value):
                        clean_value = ""
                    else:
                        clean_value = str(value).strip()
                    row_dict[str(col_name)] = clean_value
                
                if any(val for val in row_dict.values() if val):
                    csv_rows.append(row_dict)
            
            self.logger.info(f"🔍 CSV parsing result: {len(csv_rows)} non-empty rows from {len(df)} total rows")
            return csv_rows
            
        except Exception as e:
            self.logger.error(f"Error parsing CSV content for {filename}: {str(e)}")
            self.error_count += 1
            return None
    
    def _parse_ods_content(self, attachment_data: bytes, filename: str) -> Optional[List[Dict]]:
        """
        Parse ODS file content and extract text data
        
        Args:
            attachment_data: Binary data of ODS file
            filename: Name of the ODS file for logging
            
        Returns:
            List of dictionaries representing ODS rows, or None if failed
        """
        try:
            self.logger.info(f"🔍 Processing ODS file: {filename}, data size: {len(attachment_data)} bytes")
            
            # Create BytesIO object for pandas
            ods_buffer = io.BytesIO(attachment_data)
            
            # Read ODS file using odfpy engine
            try:
                self.logger.info(f"🔍 Using odfpy engine for {filename}")
                df = pd.read_excel(ods_buffer, engine='odf')
                self.logger.info(f"🔍 ODS DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            except Exception as e:
                self.logger.error(f"Failed to parse ODS file {filename}: {str(e)}")
                self.error_count += 1
                return None
            
            # Apply row limit
            if len(df) > Config.MAX_EXCEL_ROWS:
                self.logger.warning(f"ODS file {filename} has {len(df)} rows, "
                                  f"limiting to {Config.MAX_EXCEL_ROWS} rows")
                df = df.head(Config.MAX_EXCEL_ROWS)
            
            # Convert DataFrame to list of dictionaries
            ods_rows = []
            for index, row in df.iterrows():
                row_dict = {}
                for col_name, value in row.items():
                    if pd.isna(value):
                        clean_value = ""
                    else:
                        clean_value = str(value).strip()
                    row_dict[str(col_name)] = clean_value
                
                if any(val for val in row_dict.values() if val):
                    ods_rows.append(row_dict)
            
            self.logger.info(f"🔍 ODS parsing result: {len(ods_rows)} non-empty rows from {len(df)} total rows")
            return ods_rows
            
        except Exception as e:
            self.logger.error(f"Error parsing ODS content for {filename}: {str(e)}")
            self.error_count += 1
            return None
    
    def _parse_excel_content(self, attachment_data: bytes, filename: str) -> Optional[List[Dict]]:
        """
        Parse Excel/CSV/ODS file content and extract text data
        
        Args:
            attachment_data: Binary data of file
            filename: Name of the file for logging
            
        Returns:
            List of dictionaries representing rows, or None if failed
        """
        # Route to appropriate parser based on file extension
        file_extension = Path(filename.lower()).suffix
        
        if file_extension == '.csv':
            return self._parse_csv_content(attachment_data, filename)
        elif file_extension == '.ods':
            return self._parse_ods_content(attachment_data, filename)
        elif file_extension in ['.xlsx', '.xls']:
            return self._parse_excel_xlsx_xls(attachment_data, filename)
        else:
            self.logger.error(f"Unsupported file format: {file_extension}")
            return None
    
    def _parse_excel_xlsx_xls(self, attachment_data: bytes, filename: str) -> Optional[List[Dict]]:
        """
        Parse Excel XLSX/XLS file content and extract text data
        
        Args:
            attachment_data: Binary data of Excel file
            filename: Name of the Excel file for logging
            
        Returns:
            List of dictionaries representing Excel rows, or None if failed
        """
        try:
            self.logger.info(f"🔍 Processing Excel file: {filename}, data size: {len(attachment_data)} bytes")
            
            # Create BytesIO object for pandas
            excel_buffer = io.BytesIO(attachment_data)
            
            # Try to read Excel file with pandas
            try:
                # Read Excel file - try multiple engines for compatibility
                if filename.lower().endswith('.xlsx'):
                    self.logger.info(f"🔍 Using openpyxl engine for {filename}")
                    
                    # First, let's see what sheets are available
                    try:
                        import openpyxl
                        excel_buffer.seek(0)  # Reset buffer position
                        workbook = openpyxl.load_workbook(excel_buffer, data_only=True)
                        sheet_names = workbook.sheetnames
                        self.logger.info(f"🔍 Available sheets: {sheet_names}")
                        
                        # Try reading each sheet
                        df = None
                        for sheet_name in sheet_names:
                            excel_buffer.seek(0)  # Reset buffer for pandas
                            try:
                                temp_df = pd.read_excel(excel_buffer, engine='openpyxl', sheet_name=sheet_name)
                                self.logger.info(f"🔍 Sheet '{sheet_name}': {temp_df.shape}")
                                if not temp_df.empty:
                                    df = temp_df
                                    self.logger.info(f"🔍 Using non-empty sheet: {sheet_name}")
                                    break
                            except Exception as sheet_e:
                                self.logger.warning(f"🔍 Failed to read sheet '{sheet_name}': {sheet_e}")
                        
                        if df is None:
                            # If no non-empty sheet found, use the first sheet
                            excel_buffer.seek(0)
                            df = pd.read_excel(excel_buffer, engine='openpyxl')
                        
                    except ImportError:
                        # Fallback if openpyxl not available for direct inspection
                        df = pd.read_excel(excel_buffer, engine='openpyxl')
                        
                else:
                    self.logger.info(f"🔍 Using xlrd engine for {filename}")
                    df = pd.read_excel(excel_buffer, engine='xlrd')
                
            except Exception as e:
                self.logger.error(f"Failed to parse Excel file {filename}: {str(e)}")
                self.error_count += 1
                return None
            
            # Apply row limit
            if len(df) > Config.MAX_EXCEL_ROWS:
                self.logger.warning(f"Excel file {filename} has {len(df)} rows, "
                                  f"limiting to {Config.MAX_EXCEL_ROWS} rows")
                df = df.head(Config.MAX_EXCEL_ROWS)
            
            # Convert DataFrame to list of dictionaries
            excel_rows = []
            self.logger.info(f"🔍 DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            
            for index, row in df.iterrows():
                # Convert row to dictionary and clean data
                row_dict = {}
                for col_name, value in row.items():
                    # Convert to string and clean
                    if pd.isna(value):
                        clean_value = ""
                    else:
                        clean_value = str(value).strip()
                    
                    # Store with column name
                    row_dict[str(col_name)] = clean_value
                
                # Only add rows that have some content
                if any(val for val in row_dict.values() if val):
                    excel_rows.append(row_dict)
                else:
                    self.logger.debug(f"🔍 Skipping empty row {index}: {row_dict}")
            
            self.logger.info(f"🔍 Excel parsing result: {len(excel_rows)} non-empty rows from {len(df)} total rows")
            if excel_rows:
                self.logger.debug(f"🔍 Sample row: {excel_rows[0]}")
            
            return excel_rows
            
        except Exception as e:
            self.logger.error(f"Error parsing Excel content for {filename}: {str(e)}")
            self.error_count += 1
            return None
    
    def get_excel_text_content(self, excel_data_list: List[Dict]) -> List[str]:
        """
        Extract all text content from Excel data for AI analysis
        
        Args:
            excel_data_list: List of Excel data dictionaries
            
        Returns:
            List of text strings containing all Excel content
        """
        text_content = []
        
        for excel_info in excel_data_list:
            excel_rows = excel_info.get('excel_data', [])
            
            # Combine all cell values into text chunks
            for row in excel_rows:
                row_text = " ".join(str(value) for value in row.values() if value)
                if row_text.strip():
                    text_content.append(row_text.strip())
        
        return text_content
    
    def get_processing_stats(self) -> Dict:
        """
        Get Excel processing statistics
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'processed_attachments': self.processed_attachments,
            'excel_files_found': self.excel_files_found,
            'excel_files_processed': self.excel_files_processed,
            'error_count': self.error_count
        } 