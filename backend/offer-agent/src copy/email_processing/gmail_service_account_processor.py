"""
Gmail Email Processor with Service Account Authentication
Fully automated Gmail API integration with zero human intervention.
"""

import os
import base64
import json
import asyncio
import pickle
from typing import Dict, List, Any, Optional
from datetime import datetime
from io import BytesIO
from pathlib import Path

# from google.auth.transport.requests import Request  # Not needed for service accounts
from google.oauth2 import service_account
# from google_auth_oauthlib.flow import InstalledAppFlow  # Not needed for service accounts
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class GmailServiceAccountProcessor:
    """Fully automated Gmail API integration using service account authentication."""
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        """Initialize Gmail service account processor."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.gmail_service = None
        self.credentials = None
        
        # Service account configuration
        self.service_account_file = os.getenv('GMAIL_SERVICE_ACCOUNT_FILE', 'config/gmail-service-account.json')
        self.delegated_email = os.getenv('GMAIL_DELEGATED_USER', os.getenv('MONITORED_EMAIL', 'automations@agent.lvi-wabek.fi'))
    
    async def initialize(self):
        """Initialize Gmail API service with Service Account authentication - ZERO user interaction."""
        try:
            # Check if service account file exists
            service_account_path = Path(self.service_account_file)
            if not service_account_path.exists():
                raise BaseOfferAutomationError(
                    f"Service account file not found: {self.service_account_file}\n"
                    "Please ensure the service account JSON file exists and is properly configured."
                )
            
            self.logger.info(f"Loading Gmail service account from: {self.service_account_file}")
            
            # Load service account credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                str(service_account_path),
                scopes=self.SCOPES
            )
            
            # Try delegation first, fall back to direct service account if unauthorized
            if self.delegated_email:
                try:
                    self.logger.info(f"Attempting to impersonate user: {self.delegated_email}")
                    self.credentials = self.credentials.with_subject(self.delegated_email)
                    
                    # Test the delegated credentials with a simple call
                    test_service = build('gmail', 'v1', credentials=self.credentials)
                    test_service.users().getProfile(userId='me').execute()
                    self.logger.info(f"✅ Successfully impersonating user: {self.delegated_email}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to impersonate {self.delegated_email}: {e}")
                    self.logger.info("🔄 Falling back to direct service account usage (without delegation)")
                    
                    # Reset to original credentials without delegation
                    self.credentials = service_account.Credentials.from_service_account_file(
                        str(service_account_path),
                        scopes=self.SCOPES
                    )
                    self.delegated_email = None  # Clear delegation
            
            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            
            self.logger.info(f"[SUCCESS] Gmail Service Account initialized successfully")
            self.logger.info(f"[SUCCESS] Delegated user: {self.delegated_email}")
            self.logger.info(f"[SUCCESS] ZERO user interaction required - fully automated!")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service account: {e}")
            raise BaseOfferAutomationError(f"Gmail service account initialization failed: {str(e)}")
    
    
    async def get_recent_emails(self, query: str = 'is:unread', max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent emails matching the query.
        
        Args:
            query: Gmail search query (default: unread emails)
            max_results: Maximum number of emails to retrieve
            
        Returns:
            List of email data dictionaries
        """
        if not self.gmail_service:
            await self.initialize()
        
        try:
            
            # Get list of messages
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = response.get('messages', [])
            
            # Get full content for each message
            emails = []
            for message in messages:
                email_data = await self._get_email_content(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            raise BaseOfferAutomationError(f"Failed to fetch emails: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}")
            raise BaseOfferAutomationError(f"Unexpected error fetching emails: {str(e)}")
    
    async def _get_email_content(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full email content including attachments.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Email data dictionary or None if failed
        """
        try:
            # Get full message
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {}
            if 'payload' in message and 'headers' in message['payload']:
                for header in message['payload']['headers']:
                    headers[header['name']] = header['value']
            
            # Extract email metadata
            email_data = {
                'message_id': message_id,
                'thread_id': message.get('threadId'),
                'label_ids': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
                'timestamp': message.get('internalDate'),
                'sender': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'headers': headers
            }
            
            # Extract body and attachments
            email_data['body'] = self._extract_email_body(message['payload'])
            email_data['attachments'] = await self._extract_attachments(message_id, message['payload'])
            
            self.logger.info(f"Extracted email: {headers.get('Subject', 'No Subject')[:50]}...")
            
            return email_data
            
        except Exception as e:
            self.logger.error(f"Error extracting email content for {message_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body text from payload, with enhanced forwarded email support."""
        body = ""
        all_parts = []
        
        try:
            self.logger.debug(f"🔍 Extracting email body from payload with mimeType: {payload.get('mimeType', 'unknown')}")
            
            # Handle multipart messages
            if 'parts' in payload:
                self.logger.debug(f"📧 Processing multipart message with {len(payload['parts'])} parts")
                
                for i, part in enumerate(payload['parts']):
                    part_mime = part.get('mimeType', 'unknown')
                    part_filename = part.get('filename', '')
                    self.logger.debug(f"   Part {i}: mimeType={part_mime}, filename='{part_filename}'")
                    
                    # Collect all text parts for comprehensive extraction
                    if part_mime == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            try:
                                part_body = base64.urlsafe_b64decode(data).decode('utf-8')
                                all_parts.append(part_body)
                                self.logger.debug(f"   ✅ Extracted {len(part_body)} chars from text/plain part")
                                if not body:  # Use first plain text as primary body
                                    body = part_body
                            except Exception as e:
                                self.logger.error(f"   ❌ Failed to decode text/plain part: {e}")
                    
                    elif part_mime == 'text/html' and not body:
                        data = part.get('body', {}).get('data', '')
                        if data:
                            try:
                                html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                                # Simple HTML to text conversion
                                import re
                                text_body = re.sub('<[^<]+?>', '', html_body)
                                all_parts.append(text_body)
                                body = text_body  # Fallback to HTML if no plain text
                                self.logger.debug(f"   ✅ Extracted {len(text_body)} chars from text/html part (converted)")
                            except Exception as e:
                                self.logger.error(f"   ❌ Failed to decode text/html part: {e}")
                    
                    # Handle nested parts (common in forwarded emails)
                    elif part_mime.startswith('multipart/'):
                        self.logger.debug(f"   🔄 Processing nested multipart: {part_mime}")
                        nested_body = self._extract_email_body(part)
                        if nested_body:
                            all_parts.append(nested_body)
                            if not body:
                                body = nested_body
                            self.logger.debug(f"   ✅ Extracted {len(nested_body)} chars from nested part")
                    
                    # Handle message/rfc822 (embedded emails - common in forwards)
                    elif part_mime == 'message/rfc822':
                        self.logger.debug(f"   📧 Found embedded email (forwarded content)")
                        if 'payload' in part:
                            embedded_body = self._extract_email_body(part['payload'])
                            if embedded_body:
                                all_parts.append(embedded_body)
                                if not body:
                                    body = embedded_body
                                self.logger.debug(f"   ✅ Extracted {len(embedded_body)} chars from embedded email")
            
            # Handle single part messages
            elif payload.get('body', {}).get('data'):
                data = payload['body']['data']
                try:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    self.logger.debug(f"📧 Extracted {len(body)} chars from single-part message")
                except Exception as e:
                    self.logger.error(f"❌ Failed to decode single-part message: {e}")
            
            # If we have multiple parts, combine them for comprehensive analysis
            if len(all_parts) > 1:
                combined_body = "\n\n--- EMAIL PART SEPARATOR ---\n\n".join(all_parts)
                self.logger.info(f"📧 Combined {len(all_parts)} email parts into {len(combined_body)} chars total")
                # Use combined body for forwarded email analysis
                body = combined_body
            
            self.logger.info(f"📧 Final extracted body length: {len(body)} characters")
            if len(body) > 100:
                preview = body[:200].replace('\n', ' ').replace('\r', ' ')
                self.logger.debug(f"📧 Body preview: {preview}...")
            
        except Exception as e:
            self.logger.error(f"Error extracting email body: {e}")
            body = ""
        
        return body.strip()
    
    async def _extract_attachments(self, message_id: str, payload: Dict) -> List[Dict[str, Any]]:
        """Extract email attachments with enhanced forwarded email support."""
        attachments = []
        
        try:
            self.logger.debug(f"🔍 Extracting attachments from message {message_id}")
            attachment_parts = self._find_attachment_parts(payload)
            self.logger.info(f"📎 Found {len(attachment_parts)} attachment parts")
            
            for i, part in enumerate(attachment_parts):
                filename = part.get('filename', f'attachment_{i}')
                attachment_id = part.get('body', {}).get('attachmentId')
                part_mime = part.get('mimeType', 'application/octet-stream')
                
                self.logger.debug(f"   Attachment {i}: filename='{filename}', mimeType='{part_mime}', attachmentId='{attachment_id}'")
                
                if attachment_id:
                    try:
                        # Get attachment data
                        attachment = self.gmail_service.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()
                        
                        # Decode attachment data
                        file_data = base64.urlsafe_b64decode(attachment['data'])
                        
                        attachment_info = {
                            'filename': filename,
                            'mime_type': part_mime,
                            'size': attachment.get('size', len(file_data)),
                            'data': file_data,
                            'source': 'gmail'
                        }
                        
                        attachments.append(attachment_info)
                        self.logger.info(f"✅ Extracted attachment: {filename} ({len(file_data)} bytes)")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to extract attachment {filename}: {e}")
                else:
                    self.logger.warning(f"⚠️ Attachment {filename} has no attachmentId - might be inline content")
        
        except Exception as e:
            self.logger.error(f"Error extracting attachments: {e}")
        
        self.logger.info(f"📎 Total attachments extracted: {len(attachments)}")
        return attachments
    
    def _find_attachment_parts(self, payload: Dict) -> List[Dict]:
        """Find all attachment parts in the email payload, including nested parts."""
        attachment_parts = []
        
        def _recursive_find(parts_payload, depth=0):
            indent = "  " * depth
            self.logger.debug(f"{indent}🔍 Searching for attachments at depth {depth}")
            
            if 'parts' in parts_payload:
                self.logger.debug(f"{indent}📧 Found {len(parts_payload['parts'])} parts")
                
                for i, part in enumerate(parts_payload['parts']):
                    part_mime = part.get('mimeType', 'unknown')
                    part_filename = part.get('filename', '')
                    has_attachment_id = bool(part.get('body', {}).get('attachmentId'))
                    
                    self.logger.debug(f"{indent}   Part {i}: {part_mime}, filename='{part_filename}', hasAttachmentId={has_attachment_id}")
                    
                    # Check if part has attachment
                    if part_filename or has_attachment_id:
                        attachment_parts.append(part)
                        self.logger.debug(f"{indent}   ✅ Added as attachment: {part_filename or 'unnamed'}")
                    
                    # Handle embedded emails (message/rfc822) - common in forwards
                    elif part_mime == 'message/rfc822' and 'payload' in part:
                        self.logger.debug(f"{indent}   📧 Processing embedded email")
                        _recursive_find(part['payload'], depth + 1)
                    
                    # Recursively check nested multipart
                    elif part_mime.startswith('multipart/'):
                        self.logger.debug(f"{indent}   🔄 Processing nested multipart: {part_mime}")
                        _recursive_find(part, depth + 1)
        
        _recursive_find(payload)
        
        self.logger.info(f"📎 Found {len(attachment_parts)} total attachment parts")
        return attachment_parts
    
    async def mark_email_as_read(self, message_id: str) -> bool:
        """Mark email as read."""
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            self.logger.info(f"Marked email as read: {message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark email as read: {e}")
            return False
    
    async def check_token_status(self) -> Dict[str, Any]:
        """Check the status of the service account credentials."""
        service_account_path = Path(self.service_account_file)
        
        if not service_account_path.exists():
            return {
                'status': 'no_service_account',
                'message': f'Service account file not found: {self.service_account_file}',
                'needs_auth': False  # Service accounts don't need OAuth
            }
        
        try:
            # Test loading the service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                str(service_account_path),
                scopes=self.SCOPES
            )
            
            return {
                'status': 'valid',
                'message': 'Service account credentials are valid and ready to use',
                'needs_auth': False,
                'service_account_email': credentials.service_account_email,
                'delegated_user': self.delegated_email
            }
            
        except Exception as e:
            return {
                'status': 'invalid_service_account',
                'message': f'Error loading service account: {str(e)}',
                'needs_auth': False  # Service accounts don't need OAuth
            }
    
    async def force_token_renewal(self) -> bool:
        """Service accounts don't need token renewal - they never expire."""
        self.logger.info("Service accounts don't require token renewal - credentials never expire")
        
        # Just reinitialize the service to refresh credentials if needed
        try:
            await self.initialize()
            self.logger.info("Service account credentials reinitialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Service account reinitialization failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Gmail service."""
        try:
            if not self.gmail_service:
                return {'status': 'unhealthy', 'error': 'Service not initialized'}
            
            # Test with a simple API call
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            
            # Also check token status
            token_status = await self.check_token_status()
            
            return {
                'status': 'healthy',
                'email_address': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal'),
                'token_status': token_status
            }
            
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)} 

