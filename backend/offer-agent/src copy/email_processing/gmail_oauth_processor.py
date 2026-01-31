"""
Gmail Email Processor with OAuth2 User Authentication
Handles Gmail API integration using OAuth2 for personal Gmail accounts.
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

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class GmailOAuthProcessor:
    """Gmail API integration using OAuth2 user authentication for personal Gmail."""
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        """Initialize Gmail OAuth processor."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.gmail_service = None
        self.credentials = None
        
        # OAuth2 files
        self.token_file = Path('config/gmail_token.pickle')
        self.credentials_file = Path('config/gmail_oauth_credentials.json')
    
    async def initialize(self):
        """Initialize Gmail API service with OAuth2 authentication."""
        try:
            # Load existing credentials
            if self.token_file.exists():
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If no valid credentials, get them
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    try:
                        # Refresh expired credentials
                        self.logger.info("Refreshing expired Gmail credentials...")
                        self.credentials.refresh(Request())
                        self.logger.info("Gmail credentials refreshed successfully")
                    except Exception as refresh_error:
                        # Refresh failed (token revoked/expired), get new credentials
                        self.logger.warning(f"Token refresh failed: {refresh_error}")
                        self.logger.info("Running fresh OAuth flow to get new credentials...")
                        await self._run_oauth_flow()
                else:
                    # Run OAuth2 flow
                    self.logger.info("No valid credentials found, running OAuth flow...")
                    await self._run_oauth_flow()
                
                # Save credentials for next time
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
                    self.logger.info("Gmail credentials saved successfully")
            
            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            self.logger.info("Gmail OAuth API service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail OAuth service: {e}")
            raise BaseOfferAutomationError(f"Gmail OAuth initialization failed: {str(e)}")
    
    async def _run_oauth_flow(self):
        """Run OAuth2 flow to get user credentials."""
        if not self.credentials_file.exists():
            raise BaseOfferAutomationError(
                f"OAuth2 credentials file not found: {self.credentials_file}\n"
                "Please download OAuth2 client credentials from Google Cloud Console\n"
                "and save as config/gmail_oauth_credentials.json"
            )
        
        self.logger.info("Starting OAuth2 flow for Gmail access...")
        print("\n🔐 Gmail Authorization Required")
        print("A web browser will open for you to authorize Gmail access.")
        print("This is a one-time setup process.")
        
        # Run OAuth2 flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_file), 
            self.SCOPES
        )
        
        # Use local server for callback
        self.credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        
        print("✅ Gmail authorization completed successfully!")
        self.logger.info("OAuth2 flow completed successfully")
    
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
            self.logger.info(f"Fetching emails with query: '{query}', max: {max_results}")
            
            # Get list of messages
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = response.get('messages', [])
            self.logger.info(f"Found {len(messages)} messages")
            
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
                            'data': file_data
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
        """Mark email as read with retry logic for SSL errors."""
        import ssl
        import time
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                
                self.logger.info(f"Marked email as read: {message_id}")
                return True
                
            except (ssl.SSLEOFError, ssl.SSLError) as ssl_error:
                if attempt < max_retries - 1:
                    self.logger.warning(f"SSL error marking email as read (attempt {attempt + 1}), retrying in {retry_delay}s: {ssl_error}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    # Recreate Gmail service connection on SSL errors
                    try:
                        from googleapiclient.discovery import build
                        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
                        self.logger.info("Recreated Gmail service connection after SSL error")
                    except Exception as rebuild_error:
                        self.logger.error(f"Failed to rebuild Gmail service: {rebuild_error}")
                else:
                    self.logger.error(f"Failed to mark email as read after {max_retries} retries: {ssl_error}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Failed to mark email as read: {e}")
                return False
                
        return False
    
    async def check_token_status(self) -> Dict[str, Any]:
        """Check the status of the current OAuth token."""
        if not self.token_file.exists():
            return {
                'status': 'no_token',
                'message': 'No token file found',
                'needs_auth': True
            }
        
        try:
            with open(self.token_file, 'rb') as token:
                credentials = pickle.load(token)
            
            if not credentials:
                return {
                    'status': 'invalid_token',
                    'message': 'Token file exists but contains no credentials',
                    'needs_auth': True
                }
            
            if credentials.valid:
                return {
                    'status': 'valid',
                    'message': 'Token is valid and ready to use',
                    'needs_auth': False,
                    'expires_at': credentials.expiry.isoformat() if credentials.expiry else 'Unknown'
                }
            elif credentials.expired and credentials.refresh_token:
                return {
                    'status': 'expired_but_refreshable',
                    'message': 'Token is expired but can be refreshed automatically',
                    'needs_auth': False,
                    'expires_at': credentials.expiry.isoformat() if credentials.expiry else 'Unknown'
                }
            else:
                return {
                    'status': 'expired_no_refresh',
                    'message': 'Token is expired and cannot be refreshed',
                    'needs_auth': True
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error reading token: {str(e)}',
                'needs_auth': True
            }
    
    async def force_token_renewal(self) -> bool:
        """Force a fresh OAuth flow to renew the token."""
        try:
            self.logger.info("Forcing fresh token renewal...")
            
            # Delete existing token
            if self.token_file.exists():
                self.token_file.unlink()
                self.logger.info("Deleted existing token file")
            
            # Run fresh OAuth flow
            await self._run_oauth_flow()
            
            # Save new credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            
            self.logger.info("Token renewal completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Token renewal failed: {e}")
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
