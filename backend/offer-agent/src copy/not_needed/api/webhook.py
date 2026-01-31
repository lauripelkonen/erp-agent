#!/usr/bin/env python3
"""
FastAPI webhook application for handling Gmail push notifications.
Integrates with the main offer automation system.
"""

import os
import json
import base64
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config.settings import get_settings
from utils.logger import setup_logging, get_logger
from main import OfferAutomationSystem


class GmailEmailProcessor:
    """Gmail API integration for processing emails."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.gmail_service = self._setup_gmail_service()
        self.offer_system = OfferAutomationSystem()
    
    def _setup_gmail_service(self):
        """Set up Gmail API service."""
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/app/credentials.json')
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        service = build('gmail', 'v1', credentials=credentials)
        self.logger.info("Gmail service initialized")
        return service
    
    def get_email_content(self, message_id: str) -> Dict[str, Any]:
        """Retrieve email content from Gmail."""
        message = self.gmail_service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()
        
        headers = message['payload'].get('headers', [])
        email_data = {
            'message_id': message_id,
            'headers': {h['name']: h['value'] for h in headers},
            'body': self._extract_body(message['payload']),
            'attachments': []
        }
        return email_data
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload.get('body', {}).get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        return ""
    
    async def process_email_for_offers(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process email through offer automation system."""
        body = email_data.get('body', '')
        result = await self.offer_system.process_email_request(body, [])
        return result


# FastAPI app
app = FastAPI(title="Email Processor")
setup_logging()
processor = GmailEmailProcessor()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/webhook/email")
async def handle_email_notification(request: Request, background_tasks: BackgroundTasks):
    """Handle Gmail push notifications."""
    try:
        body = await request.body()
        data = json.loads(body)
        
        if 'message' in data:
            message_data = json.loads(base64.b64decode(data['message']['data']).decode('utf-8'))
            
            # Get recent messages
            response = processor.gmail_service.users().messages().list(
                userId='me', maxResults=1, q='is:unread'
            ).execute()
            
            messages = response.get('messages', [])
            if messages:
                message_id = messages[0]['id']
                background_tasks.add_task(process_single_email, message_id)
                return {"status": "processing", "message_id": message_id}
            
        return {"status": "no_messages"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_single_email(message_id: str):
    """Background task to process email."""
    try:
        email_data = processor.get_email_content(message_id)
        result = await processor.process_email_for_offers(email_data)
        processor.logger.info(f"Email {message_id} processed: {result.get('status')}")
    except Exception as e:
        processor.logger.error(f"Failed to process email {message_id}: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 