"""
Gmail Email Processor for Offer Automation
Handles Gmail API integration for retrieving emails and attachments.
"""

import os
import base64
import json
import asyncio
import pickle
from typing import Dict, List, Any, Optional
from datetime import datetime
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class GmailEmailProcessor:
    """Gmail API integration for processing incoming emails."""
    
    def __init__(self):
        """Initialize Gmail processor."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.gmail_service = None
        self._setup_gmail_service()
    
    def _setup_gmail_service(self):
        """Set up Gmail API service with OAuth2 authentication."""
        try:
            # OAuth2 scopes required for Gmail access
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
            
            credentials = None
            
            # Check for existing token
            token_path = '/app/config/gmail_token.pickle'
            if os.path.exists(token_path):
                self.logger.info("Loading existing Gmail OAuth2 token")
                try:
                    with open(token_path, 'rb') as token:
                        credentials = pickle.load(token)
                    
                    # Check if credentials are valid Credentials object
                    if isinstance(credentials, Credentials):
                        self.logger.info("Found valid OAuth2 Credentials object")
                        # Verify scopes if available
                        if hasattr(credentials, 'scopes') and credentials.scopes:
                            missing_scopes = [scope for scope in SCOPES if scope not in credentials.scopes]
                            if missing_scopes:
                                self.logger.warning(f"Token missing required scopes: {missing_scopes}")
                                credentials = None
                    else:
                        self.logger.warning("Token file contains unexpected format, will skip")
                        credentials = None
                        
                except Exception as e:
                    self.logger.error(f"Error loading token file: {e}")
                    credentials = None
            
            # If there are no (valid) credentials available, check for OAuth credentials
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    self.logger.info("Refreshing expired Gmail OAuth2 token")
                    credentials.refresh(Request())
                else:
                    # Check for OAuth credentials file
                    oauth_creds_path = '/app/config/gmail_oauth_credentials.json'
                    if not os.path.exists(oauth_creds_path):
                        self.logger.warning(f"Gmail OAuth credentials file not found: {oauth_creds_path}")
                        self.logger.warning("Gmail processing will be disabled")
                        self.logger.info("To enable Gmail reading, set up OAuth2 credentials")
                        return
                    
                    # Try to run OAuth flow (this won't work in Docker, but provides clear error)
                    self.logger.info("Attempting OAuth2 flow...")
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(oauth_creds_path, SCOPES)
                        # This will fail in Docker, but we use proper scopes
                        credentials = flow.run_local_server(port=0)
                        
                        # Save credentials
                        with open(token_path, 'wb') as token:
                            pickle.dump(credentials, token)
                            self.logger.info("Gmail OAuth2 token saved")
                            
                    except Exception as oauth_error:
                        self.logger.error(f"OAuth2 flow failed: {oauth_error}")
                        self.logger.warning("Gmail reading will be disabled - run OAuth setup locally first")
                        return
            
            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=credentials)
            self.logger.info("Gmail API service initialized successfully with OAuth2")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
            self.gmail_service = None
    
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
            raise BaseOfferAutomationError("Gmail service not initialized")
        
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
        """
        Extract email body text from payload.
        
        Args:
            payload: Gmail message payload
            
        Returns:
            Email body text
        """
        body = ""
        
        try:
            # Handle multipart messages
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
                    elif part.get('mimeType') == 'text/html' and not body:
                        # Fallback to HTML if no plain text
                        data = part.get('body', {}).get('data', '')
                        if data:
                            html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Simple HTML to text conversion
                            import re
                            body = re.sub('<[^<]+?>', '', html_body)
            
            # Handle single part messages
            elif payload.get('body', {}).get('data'):
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error extracting email body: {e}")
            body = ""
        
        return body.strip()
    
    async def _extract_attachments(self, message_id: str, payload: Dict) -> List[Dict[str, Any]]:
        """
        Extract email attachments.
        
        Args:
            message_id: Gmail message ID
            payload: Gmail message payload
            
        Returns:
            List of attachment data dictionaries
        """
        attachments = []
        
        try:
            # Find attachment parts
            parts = self._find_attachment_parts(payload)
            
            for part in parts:
                attachment_id = part.get('body', {}).get('attachmentId')
                filename = part.get('filename', 'unknown')
                mime_type = part.get('mimeType', '')
                
                if not attachment_id:
                    continue
                
                # Download attachment data
                try:
                    attachment = self.gmail_service.users().messages().attachments().get(
                        userId='me',
                        messageId=message_id,
                        id=attachment_id
                    ).execute()
                    
                    # Decode attachment data
                    file_data = base64.urlsafe_b64decode(attachment['data'])
                    
                    attachment_info = {
                        'filename': filename,
                        'mime_type': mime_type,
                        'size': len(file_data),
                        'data': file_data,
                        'attachment_id': attachment_id
                    }
                    
                    attachments.append(attachment_info)
                    self.logger.info(f"Extracted attachment: {filename} ({len(file_data)} bytes)")
                    
                except Exception as e:
                    self.logger.error(f"Error downloading attachment {filename}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting attachments: {e}")
        
        return attachments
    
    def _find_attachment_parts(self, payload: Dict) -> List[Dict]:
        """
        Recursively find attachment parts in email payload.
        
        Args:
            payload: Gmail message payload
            
        Returns:
            List of attachment parts
        """
        attachments = []
        
        # Check if this part is an attachment
        if payload.get('filename') and payload.get('body', {}).get('attachmentId'):
            attachments.append(payload)
        
        # Check nested parts
        if 'parts' in payload:
            for part in payload['parts']:
                attachments.extend(self._find_attachment_parts(part))
        
        return attachments
    
    async def mark_email_as_read(self, message_id: str) -> bool:
        """
        Mark email as read by removing UNREAD label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.gmail_service:
            return False
        
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            self.logger.info(f"Marked email {message_id} as read")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")
            return False
    
    async def setup_push_notifications(self, topic_name: str, project_id: str) -> bool:
        """
        Set up Gmail push notifications to Google Cloud Pub/Sub.
        
        Args:
            topic_name: Pub/Sub topic name
            project_id: Google Cloud project ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.gmail_service:
            return False
        
        try:
            topic_path = f"projects/{project_id}/topics/{topic_name}"
            
            # Set up Gmail watch
            watch_request = {
                'labelIds': ['INBOX'],
                'topicName': topic_path
            }
            
            result = self.gmail_service.users().watch(userId='me', body=watch_request).execute()
            
            self.logger.info(f"Gmail push notifications set up successfully")
            self.logger.info(f"History ID: {result.get('historyId')}")
            self.logger.info(f"Expiration: {result.get('expiration')}")
            
            # Save watch info for reference
            watch_info = {
                'historyId': result.get('historyId'),
                'expiration': result.get('expiration'),
                'topicName': topic_path,
                'setup_time': datetime.now().isoformat()
            }
            
            # Write to file if possible
            try:
                with open('/app/gmail_watch_info.json', 'w') as f:
                    json.dump(watch_info, f, indent=2)
                self.logger.info("Watch information saved to /app/gmail_watch_info.json")
            except Exception as e:
                self.logger.warning(f"Could not save watch info to file: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up Gmail push notifications: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Gmail service.
        
        Returns:
            Health status dictionary
        """
        if not self.gmail_service:
            return {
                'status': 'unhealthy',
                'error': 'Gmail service not initialized'
            }
        
        try:
            # Try to get user profile as a simple health check
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            
            return {
                'status': 'healthy',
                'email_address': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            } 

    async def fetch_email_data(self, email_address: str, history_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch recent email data based on Gmail push notification.
        
        Args:
            email_address: Email address from notification
            history_id: History ID from Gmail notification
            
        Returns:
            Email data dictionary or None if no new emails found
        """
        if not self.gmail_service:
            self.logger.warning("Gmail service not initialized - cannot fetch email data")
            return None
        
        try:
            self.logger.info(f"Fetching recent emails for {email_address} with history ID {history_id}")
            
            # Try to use history API first (more efficient)
            try:
                # Get history since the provided history ID
                history_response = self.gmail_service.users().history().list(
                    userId='me',
                    startHistoryId=history_id,
                    historyTypes=['messageAdded'],
                    maxResults=10
                ).execute()
                
                history_records = history_response.get('history', [])
                if history_records:
                    self.logger.info(f"Found {len(history_records)} history records")
                    
                    # Get the most recent message from history
                    for record in history_records:
                        if 'messagesAdded' in record:
                            for message_added in record['messagesAdded']:
                                message_id = message_added['message']['id']
                                email_data = await self._get_email_content(message_id)
                                if email_data:
                                    self.logger.info(f"Fetched email from history: {email_data.get('subject', 'No Subject')[:50]}...")
                                    return email_data
                
            except Exception as history_error:
                self.logger.info(f"History API failed: {history_error}, falling back to recent emails")
            
            # Fallback: Get recent unread emails
            recent_emails = await self.get_recent_emails(query='is:unread', max_results=5)
            
            if not recent_emails:
                self.logger.info("No recent unread emails found")
                return None
            
            # Return the most recent email
            most_recent = recent_emails[0]
            self.logger.info(f"Fetched email: {most_recent.get('subject', 'No Subject')[:50]}... from {most_recent.get('sender', 'Unknown')}")
            
            return most_recent
            
        except Exception as e:
            self.logger.error(f"Error fetching email data: {e}")
            return None 