#!/usr/bin/env python3
"""
Enhanced Webhook API for Offer Automation System
Handles direct EventBridge events and runs as a persistent Fargate service.
"""

import asyncio
import base64
import json
import logging
import os
import signal
import sys
import aiohttp
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import socket
import pyodbc

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Google Cloud Pub/Sub imports
try:
    from google.cloud import pubsub_v1
    PUBSUB_AVAILABLE = True
except ImportError:
    PUBSUB_AVAILABLE = False
    logging.warning("Google Cloud Pub/Sub library not available. Pull subscription disabled.")

# Add src to path for imports
sys.path.insert(0, '/app/src')

from src.main import OfferAutomationOrchestrator
from src.utils.logger import setup_logging, get_logger, get_audit_logger
from src.email_processing.gmail_service_account_processor import GmailServiceAccountProcessor
from src.config.settings import get_settings


# Dynamic DNS functionality removed - not needed for core offer automation service
# Container networking should use load balancers or service discovery instead


class FargateOfferAutomationService:
    """
    Persistent Fargate service for handling offer automation.
    Processes EventBridge events and Gmail notifications.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        self.settings = get_settings()
        self.orchestrator = None
        self.is_running = False
        self.gmail_processor = None
        self.pubsub_task = None
        self.pubsub_subscriber = None
        self.processed_count = 0
        self.start_time = datetime.utcnow()

    async def initialize(self):
        """Initialize all service components."""
        try:
            self.logger.info("Initializing Fargate Offer Automation Service...")
            
            # Skip dynamic DNS update - not needed for core functionality
            self.logger.info("🌐 Dynamic DNS disabled - using load balancer/service discovery")
            
            # Initialize orchestrator and components
            self.orchestrator = OfferAutomationOrchestrator()
            await self.orchestrator.initialize()
            
            # Initialize Gmail processor (using Service Account like main.py)
            self.gmail_processor = GmailServiceAccountProcessor()
            await self.gmail_processor.initialize()
            
            # Set up Gmail watch for push notifications
            await self._setup_gmail_watch()
            
            # Initialize Pub/Sub pull subscription
            await self._initialize_pubsub_pull()
            
            self.is_running = True
            self.logger.info("✅ Fargate service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Fargate service: {e}", exc_info=True)
            raise

    async def _setup_gmail_watch(self):
        """Set up Gmail watch for push notifications to Pub/Sub topic."""
        try:
            if not self.gmail_processor or not hasattr(self.gmail_processor, 'gmail_service'):
                self.logger.warning("Gmail processor not available - skipping watch setup")
                return
            
            if not self.gmail_processor.gmail_service:
                self.logger.warning("Gmail service not initialized - skipping watch setup")
                return
            
            # Configuration from environment
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'calcium-verbena-463208-e5')
            topic_name = os.getenv('PUBSUB_TOPIC', 'gmail-notifications')
            
            self.logger.info(f"🎯 Setting up Gmail watch for push notifications...")
            self.logger.info(f"   Project: {project_id}")
            self.logger.info(f"   Topic: {topic_name}")
            
            # Configure the watch request
            watch_request = {
                'topicName': f'projects/{project_id}/topics/{topic_name}',
                'labelIds': ['INBOX'],  # Watch INBOX only
                'labelFilterAction': 'include'
            }
            
            # Set up the watch
            watch_result = self.gmail_processor.gmail_service.users().watch(
                userId='me',
                body=watch_request
            ).execute()
            
            self.logger.info("✅ Gmail watch configured successfully!")
            self.logger.info(f"   History ID: {watch_result.get('historyId')}")
            
            # Calculate and log expiration time
            if watch_result.get('expiration'):
                from datetime import datetime
                exp_timestamp = int(watch_result.get('expiration')) / 1000
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                self.logger.info(f"   Expires at: {exp_datetime}")
                
                # Check if expiration is soon (less than 1 day)
                from datetime import timedelta
                if exp_datetime < datetime.now() + timedelta(days=1):
                    self.logger.warning("⚠️ Watch expires soon - will need renewal")
                else:
                    remaining = exp_datetime - datetime.now()
                    self.logger.info(f"✅ Watch is valid for {remaining}")
            
        except Exception as e:
            self.logger.error(f"Failed to set up Gmail watch: {e}", exc_info=True)
            self.logger.error("Gmail push notifications will not work without watch setup")
            
            # Check for common error types
            error_str = str(e).lower()
            if "permission" in error_str:
                self.logger.error("🔐 Permission error - check service account permissions for Gmail API and Pub/Sub")
            elif "topic" in error_str:
                self.logger.error("📡 Topic error - check if Pub/Sub topic exists and is accessible")
            elif "quota" in error_str:
                self.logger.error("📊 Quota error - check Gmail API quotas")
            
            # Don't fail service startup for watch setup errors
            self.logger.warning("⚠️ Continuing service startup without Gmail watch (Pub/Sub won't receive messages)")

    async def _initialize_pubsub_pull(self):
        """Initialize Google Cloud Pub/Sub pull subscription for Gmail notifications."""
        if not PUBSUB_AVAILABLE:
            self.logger.warning("Pub/Sub library not available - pull subscription disabled")
            return
            
        try:
            # Configuration from environment
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'outstanding-ion-469610-a0')
            subscription_name = os.getenv('PUBSUB_SUBSCRIPTION', 'gmail-to-fargate')
            credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/app/config/gmail-service-account.json')
            
            # Check if credentials file exists
            if not os.path.exists(credentials_file):
                self.logger.warning(f"Google Cloud credentials not found at {credentials_file}")
                self.logger.info("Pub/Sub pull subscription disabled - set GOOGLE_APPLICATION_CREDENTIALS")
                return
            
            # Set environment variable for Google Cloud authentication
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
            
            # Initialize Pub/Sub subscriber
            self.pubsub_subscriber = pubsub_v1.SubscriberClient()
            subscription_path = self.pubsub_subscriber.subscription_path(project_id, subscription_name)
            
            self.logger.info(f"🔗 Initializing Pub/Sub pull subscription: {subscription_path}")
            
            # Start background polling task
            self.pubsub_task = asyncio.create_task(self._pubsub_pull_loop(subscription_path))
            self.logger.info("✅ Pub/Sub pull subscription initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pub/Sub pull subscription: {e}")
            self.logger.warning("Gmail notifications will only work via direct webhook calls")

    async def _pubsub_pull_loop(self, subscription_path: str):
        """Background task that continuously pulls messages from Pub/Sub subscription."""
        # Force logging to flush to stdout immediately
        import sys
        
        self.logger.info(f"[PUBSUB] Starting Pub/Sub pull loop for {subscription_path}")
        sys.stdout.flush()
        
        pull_count = 0
        message_count = 0
        
        while self.is_running:
            try:
                pull_count += 1
                
                # Log every 10 pulls to show the loop is active
                if pull_count % 10 == 0:
                    sys.stdout.flush()
                
                # Use synchronous pull with shorter timeout in async context
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.pubsub_subscriber.pull(
                        subscription=subscription_path,
                        max_messages=10,  # Process up to 10 messages at once
                        timeout=3.0  # 3 second timeout to reduce 504 errors
                    )
                )
                
                if response.received_messages:
                    message_count += len(response.received_messages)
                    self.logger.info(f"[PUBSUB] Received {len(response.received_messages)} Gmail notification(s) - Total processed: {message_count}")
                    sys.stdout.flush()
                    
                    # Process each message
                    ack_ids = []
                    for received_message in response.received_messages:
                        try:
                            # Extract message data
                            message_data = received_message.message.data.decode('utf-8')
                            gmail_data = json.loads(message_data)
                            
                            email_address = gmail_data.get('emailAddress', 'unknown')
                            history_id = gmail_data.get('historyId', 'unknown')
                            
                            self.logger.info(f"[EMAIL] Processing Gmail notification - Email: {email_address}, History: {history_id}")
                            sys.stdout.flush()
                            
                            # Check if sender is from allowed domains
                            if email_address and not self._is_sender_allowed(email_address):
                                self.logger.info(f"[EMAIL] Gmail notification ignored - {email_address} not from allowed domains")
                                sys.stdout.flush()
                                ack_ids.append(received_message.ack_id)
                                continue
                            
                            # Convert to EventBridge format and process
                            event_data = {
                                'source': 'google.pubsub.pull',
                                'detail-type': 'Gmail Push Notification',
                                'detail': {
                                    'message': {
                                        'data': base64.b64encode(message_data.encode()).decode(),
                                        'messageId': received_message.message.message_id,
                                        'publishTime': received_message.message.publish_time.isoformat()
                                    }
                                }
                            }
                            
                            self.logger.info(f"[EMAIL] Starting email processing for {email_address}")
                            sys.stdout.flush()
                            
                            # Process the event
                            result = await self.process_eventbridge_event(event_data)
                            
                            if result.get('success'):
                                self.logger.info(f"[EMAIL] SUCCESS: Email processing successful for {email_address}")
                            else:
                                self.logger.error(f"[EMAIL] FAILED: Email processing failed for {email_address}: {result.get('error', 'Unknown error')}")
                            sys.stdout.flush()
                            
                            # Mark message for acknowledgment
                            ack_ids.append(received_message.ack_id)
                            
                        except Exception as e:
                            self.logger.error(f"[ERROR] Error processing Pub/Sub message: {e}")
                            sys.stdout.flush()
                            # Don't acknowledge failed messages - they'll be retried
                    
                    # Acknowledge successfully processed messages
                    if ack_ids:
                        await loop.run_in_executor(
                            None,
                            lambda: self.pubsub_subscriber.acknowledge(
                                subscription=subscription_path,
                                ack_ids=ack_ids
                            )
                        )
                        self.logger.info(f"[PUBSUB] Acknowledged {len(ack_ids)} processed messages")
                        sys.stdout.flush()
                
                else:
                    # No messages received, wait a bit before next pull
                    await asyncio.sleep(5)
                    
            except Exception as e:
                # Handle different types of errors
                error_msg = str(e).lower()
                if "deadline exceeded" in error_msg or "504" in error_msg:
                    # This is normal - no messages available, just continue
                    await asyncio.sleep(2)  # Small delay to prevent busy-waiting
                elif "permission denied" in error_msg or "403" in error_msg:
                    self.logger.error(f"[ERROR] Pub/Sub permission error: {e}")
                    sys.stdout.flush()
                    await asyncio.sleep(30)  # Wait longer for auth issues
                else:
                    self.logger.error(f"[ERROR] Error in Pub/Sub pull loop: {e}")
                    sys.stdout.flush()
                    await asyncio.sleep(5)  # Shorter wait for other errors
        
        self.logger.info("[PUBSUB] Pub/Sub pull loop stopped")
        sys.stdout.flush()

    def _is_sender_allowed(self, sender_email: str) -> bool:
        """
        Check if the sender email is from an allowed domain.
        
        Args:
            sender_email: Email address of the sender
            
        Returns:
            True if sender is from allowed domain, False otherwise
        """
        if not sender_email:
            return False
            
        allowed_domains = self.settings.get_allowed_senders()
        if not allowed_domains:
            # If no allowed senders configured, allow all
            return True
            
        # Extract domain from email
        try:
            # Handle sender formats like "Name <email@domain.com>" or just "email@domain.com"
            import re
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender_email)
            if not email_match:
                return False
            
            actual_email = email_match.group(0)
            sender_domain = actual_email.split('@')[1].lower()
            
            # Check against allowed domains
            for allowed_domain in allowed_domains:
                allowed_domain = allowed_domain.strip().lower()
                
                # Handle domain patterns like @lvi-wabek.fi
                if allowed_domain.startswith('@'):
                    allowed_domain = allowed_domain[1:]
                
                # Exact domain match or subdomain match
                if sender_domain == allowed_domain or sender_domain.endswith('.' + allowed_domain):
                    self.logger.info(f"✅ Sender {sender_email} allowed (email: {actual_email}, matches {allowed_domain})")
                    return True
            
            self.logger.warning(f"❌ Sender {sender_email} rejected (email: {actual_email}, domain: {sender_domain}) - not from allowed domains: {allowed_domains}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking sender domain: {e}")
            return False
    
    async def process_eventbridge_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process EventBridge email notification event.
        
        Args:
            event_data: EventBridge event containing Gmail notification
            
        Returns:
            Processing result
        """
        request_id = f"fargate-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{self.processed_count}"
        
        try:
            self.logger.info(f"Processing EventBridge event", extra={
                'extra_fields': {
                    'request_id': request_id,
                    'event_source': event_data.get('source'),
                    'detail_type': event_data.get('detail-type')
                }
            })
            
            # Extract Gmail notification data
            detail = event_data.get('detail', {})
            
            # Check if this is a test event
            if event_data.get('source') == 'test' or detail.get('test'):
                return await self._handle_test_event(request_id)
            
            # Parse Gmail push notification
            gmail_data = await self._parse_gmail_notification(detail)
            
            if not gmail_data:
                self.logger.warning("No valid Gmail data found in event")
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': 'No valid Gmail data'
                }
            
            # Get recent unread emails (GmailOAuthProcessor doesn't have fetch_email_data)
            # We'll get the most recent unread email instead
            emails = await self.gmail_processor.get_recent_emails(
                query="is:unread", 
                max_results=1
            )
            
            if not emails:
                self.logger.warning("No unread emails found")
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': 'No unread emails found'
                }
            
            email_data = emails[0]  # Get the most recent unread email
            
            if not email_data:
                self.logger.warning("Could not fetch email data")
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': 'Could not fetch email data'
                }
            
            # Domain filtering: Check if sender is from allowed domains
            sender_email = email_data.get('sender', '')
            if not self._is_sender_allowed(sender_email):
                self.logger.info(f"🚫 Email from {sender_email} ignored - not from allowed domains")
                
                # CRITICAL: Mark email as read even when ignored to prevent infinite loop
                message_id = email_data.get('message_id')
                if message_id:
                    try:
                        await self.gmail_processor.mark_email_as_read(message_id)
                        self.logger.info(f"✅ Ignored email marked as read: {message_id}")
                    except Exception as mark_error:
                        self.logger.error(f"Failed to mark ignored email as read: {mark_error}")
                
                return {
                    'success': True,
                    'request_id': request_id,
                    'message': f'Email ignored - sender not from allowed domains',
                    'sender': sender_email,
                    'action': 'ignored'
                }
            
            # Process the email through the orchestrator
            result = await self.orchestrator.process_email_offer_request(email_data)
            result['request_id'] = request_id
            
            # CRITICAL: Mark email as read after processing to prevent infinite loop
            message_id = email_data.get('message_id')
            if message_id:
                try:
                    await self.gmail_processor.mark_email_as_read(message_id)
                    if result.get('success'):
                        self.logger.info(f"✅ Successfully processed email marked as read: {message_id}")
                    else:
                        self.logger.info(f"⚠️ Failed processing email marked as read: {message_id}")
                except Exception as mark_error:
                    self.logger.error(f"Failed to mark processed email as read: {mark_error}")
            
            self.processed_count += 1
            
            self.audit_logger.info("EventBridge email event processed", extra={
                'extra_fields': {
                    'request_id': request_id,
                    'success': result.get('success'),
                    'processed_count': self.processed_count,
                    'sender': sender_email
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing EventBridge event: {e}", exc_info=True)
            
            self.audit_logger.error("EventBridge event processing failed", extra={
                'extra_fields': {
                    'request_id': request_id,
                    'error': str(e)
                }
            })
            
            return {
                'success': False,
                'request_id': request_id,
                'error': str(e)
            }
    
    async def _handle_test_event(self, request_id: str) -> Dict[str, Any]:
        """Handle test events for health checking."""
        self.logger.info("Processing test event")
        
        # Perform a quick health check
        health_status = await self.orchestrator.health_check()
        
        return {
            'success': True,
            'request_id': request_id,
            'message': 'Test event processed successfully',
            'health_status': health_status,
            'service_info': {
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'processed_count': self.processed_count,
                'is_running': self.is_running
            }
        }
    
    async def _parse_gmail_notification(self, detail: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Gmail push notification from EventBridge detail."""
        try:
            # EventBridge may contain the message in different formats
            if 'message' in detail:
                message_data = detail['message']
                
                # Handle base64 encoded data
                if 'data' in message_data:
                    decoded_data = base64.b64decode(message_data['data']).decode('utf-8')
                    gmail_data = json.loads(decoded_data)
                    
                    return {
                        'email_address': gmail_data.get('emailAddress'),
                        'history_id': gmail_data.get('historyId'),
                        'source': 'gmail_pubsub'
                    }
            
            # Handle direct data
            elif 'emailAddress' in detail:
                return {
                    'email_address': detail.get('emailAddress'),
                    'history_id': detail.get('historyId'),
                    'source': 'gmail_direct'
                }
            
            self.logger.warning(f"Unknown Gmail notification format: {detail}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing Gmail notification: {e}", exc_info=True)
            return None
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        status = {
            'status': 'running' if self.is_running else 'stopped',
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': uptime,
            'processed_count': self.processed_count,
            'components': {}
        }
        
        if self.orchestrator:
            health_status = await self.orchestrator.health_check()
            status['components'] = health_status.get('components', {})
        
        return status
    
    async def shutdown(self):
        """Gracefully shutdown the service and cleanup resources."""
        self.logger.info("Shutting down Fargate service...")
        
        # Stop the service flag first
        self.is_running = False
        
        try:
            # Cancel Pub/Sub polling task
            if self.pubsub_task and not self.pubsub_task.done():
                self.logger.info("🔌 Stopping Pub/Sub pull task...")
                self.pubsub_task.cancel()
                try:
                    await self.pubsub_task
                except asyncio.CancelledError:
                    pass
            
            # Close Pub/Sub subscriber
            if self.pubsub_subscriber:
                self.logger.info("🔌 Closing Pub/Sub subscriber...")
                self.pubsub_subscriber.close()
            
            # Shutdown orchestrator
            if self.orchestrator:
                await self.orchestrator.close()
            
            self.logger.info("✅ Fargate service shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)


# Global service instance
service_instance: Optional[FargateOfferAutomationService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global service_instance
    
    # Startup
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting Fargate Offer Automation Service...")
        
        service_instance = FargateOfferAutomationService()
        await service_instance.initialize()
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(service_instance.shutdown())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info("✅ Fargate service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        raise
    
    yield  # Application runs here
    
    # Shutdown
    if service_instance:
        await service_instance.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Offer Automation Service",
    description="Fargate-based offer automation service for email processing",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/eventbridge/email")
async def handle_eventbridge_email(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Handle EventBridge email notification events.
    This endpoint is called directly by AWS EventBridge.
    """
    global service_instance
    
    if not service_instance or not service_instance.is_running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        event_data = await request.json()
        
        # Process in background to return quickly to EventBridge
        background_tasks.add_task(
            service_instance.process_eventbridge_event,
            event_data
        )
        
        return JSONResponse({
            'success': True,
            'message': 'Event queued for processing',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error handling EventBridge event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/gmail")
async def handle_gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Handle Gmail push notification webhooks (fallback for direct Pub/Sub).
    Includes domain filtering to only process emails from allowed domains.
    """
    global service_instance
    
    if not service_instance or not service_instance.is_running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        # Parse Pub/Sub message
        body = await request.json()
        
        # Extract and log basic info for debugging
        message_data = body.get('message', {})
        if 'data' in message_data:
            try:
                decoded_data = base64.b64decode(message_data['data']).decode('utf-8')
                gmail_data = json.loads(decoded_data)
                email_address = gmail_data.get('emailAddress', 'unknown')
                history_id = gmail_data.get('historyId', 'unknown')
                
                service_instance.logger.info(f"📧 Gmail webhook received - Email: {email_address}, History: {history_id}")
                
                # Quick domain check before processing (optimization)
                if email_address and not service_instance._is_sender_allowed(email_address):
                    service_instance.logger.info(f"🚫 Gmail notification ignored - {email_address} not from allowed domains")
                    return JSONResponse({
                        'success': True,
                        'message': 'Notification ignored - not from allowed domains',
                        'email_address': email_address,
                        'action': 'ignored',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                service_instance.logger.warning(f"Could not decode Gmail data for pre-filtering: {e}")
        
        # Convert to EventBridge format for processing
        event_data = {
            'source': 'google.pubsub',
            'detail-type': 'Gmail Push Notification',
            'detail': body
        }
        
        # Process in background (domain filtering will happen again in process_eventbridge_event)
        background_tasks.add_task(
            service_instance.process_eventbridge_event,
            event_data
        )
        
        return JSONResponse({
            'success': True,
            'message': 'Gmail webhook processed',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error handling Gmail webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for load balancer and monitoring."""
    global service_instance
    
    if not service_instance:
        return JSONResponse(
            status_code=503,
            content={'status': 'unhealthy', 'reason': 'Service not initialized'}
        )
    
    try:
        status = await service_instance.get_service_status()
        
        if status['status'] == 'running':
            return JSONResponse(content=status)
        else:
            return JSONResponse(status_code=503, content=status)
            
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={'status': 'unhealthy', 'error': str(e)}
        )


@app.get("/status")
async def get_status() -> JSONResponse:
    """Get detailed service status and statistics."""
    global service_instance
    
    if not service_instance:
        return JSONResponse(
            status_code=503,
            content={'error': 'Service not initialized'}
        )
    
    try:
        status = await service_instance.get_service_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logging.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_endpoint(background_tasks: BackgroundTasks) -> JSONResponse:
    """Test endpoint for manual triggering and health checks."""
    global service_instance
    
    if not service_instance or not service_instance.is_running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Create test event
    test_event = {
        'source': 'test',
        'detail-type': 'Test Event',
        'detail': {'test': True}
    }
    
    # Process test event
    result = await service_instance.process_eventbridge_event(test_event)
    
    return JSONResponse(content=result)


@app.get("/diagnostic")
async def diagnostic_check() -> JSONResponse:
    """
    Comprehensive diagnostic endpoint to test connectivity and network configuration.
    Tests outbound IP, database connectivity, and other network parameters.
    """
    global service_instance
    
    diagnostic_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'service_status': 'running' if service_instance and service_instance.is_running else 'not_ready',
        'outbound_ip': None,
        'database_connectivity': {},
        'api_connectivity': {},
        'network_info': {}
    }
    
    logger = get_logger(__name__)
    
    # Test 1: Get outbound IP
    try:
        logger.info("Testing outbound IP...")
        
        # Method 1: Using httpbin.org
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get('https://httpbin.org/ip') as response:
                if response.status == 200:
                    ip_data = await response.json()
                    diagnostic_results['outbound_ip'] = ip_data.get('origin', 'unknown')
                    logger.info(f"Outbound IP: {diagnostic_results['outbound_ip']}")
                    
                    # Check if using NAT instance
                    if diagnostic_results['outbound_ip'] == "13.51.43.232":
                        diagnostic_results['nat_instance_status'] = "✅ Using NAT instance IP!"
                    else:
                        diagnostic_results['nat_instance_status'] = f"⚠️ Not using NAT instance IP (expected: 13.51.43.232)"
                else:
                    diagnostic_results['outbound_ip_error'] = f"HTTP {response.status}"
                    
    except Exception as e:
        diagnostic_results['outbound_ip_error'] = str(e)
        logger.error(f"Outbound IP test failed: {e}")
    
    # Test 2: Database connectivity  
    try:
        logger.info("Testing database connectivity...")
        
        db_host = "10.201.164.123"
        db_port = 1433
        
        # Test 2a: Socket connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((db_host, db_port))
            sock.close()
            
            if result == 0:
                diagnostic_results['database_connectivity']['socket_test'] = "✅ Port reachable"
            else:
                diagnostic_results['database_connectivity']['socket_test'] = f"❌ Port not reachable (error: {result})"
                
        except Exception as e:
            diagnostic_results['database_connectivity']['socket_test'] = f"❌ Socket error: {str(e)}"
        
        # Test 2b: SQL Server connection
        try:
            connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={db_host},{db_port};DATABASE=LemonDB16;UID=laurip;PWD=Ss2sa9))nPls;Encrypt=no;TrustServerCertificate=yes"
            
            conn = pyodbc.connect(connection_string, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row and row[0] == 1:
                diagnostic_results['database_connectivity']['sql_test'] = "✅ Database connection successful!"
            else:
                diagnostic_results['database_connectivity']['sql_test'] = "❌ Unexpected result from database"
                
        except Exception as e:
            diagnostic_results['database_connectivity']['sql_test'] = f"❌ SQL connection failed: {str(e)}"
            
    except Exception as e:
        diagnostic_results['database_connectivity']['general_error'] = str(e)
        logger.error(f"Database connectivity test failed: {e}")
    
    # Test 3: API connectivity (verification)
    try:
        logger.info("Testing API connectivity...")
        
        api_host = "10.201.164.118"
        
        # Test 3a: Socket connectivity to API
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((api_host, 443))
            sock.close()
            
            if result == 0:
                diagnostic_results['api_connectivity']['socket_test'] = "✅ API port reachable"
            else:
                diagnostic_results['api_connectivity']['socket_test'] = f"❌ API port not reachable"
                
        except Exception as e:
            diagnostic_results['api_connectivity']['socket_test'] = f"❌ API socket error: {str(e)}"
        
        # Test 3b: HTTP request to API
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f'https://{api_host}/LemonRest', ssl=False) as response:
                    diagnostic_results['api_connectivity']['http_test'] = f"✅ API HTTP response: {response.status}"
                    
        except Exception as e:
            diagnostic_results['api_connectivity']['http_test'] = f"❌ API HTTP error: {str(e)}"
            
    except Exception as e:
        diagnostic_results['api_connectivity']['general_error'] = str(e)
        logger.error(f"API connectivity test failed: {e}")
    
    # Test 4: Network info
    try:
        import subprocess
        
        # Get container hostname
        diagnostic_results['network_info']['hostname'] = socket.gethostname()
        
        # Get default route (if available)
        try:
            result = subprocess.run(['ip', 'route', 'show'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                diagnostic_results['network_info']['default_route'] = result.stdout.strip()
        except:
            diagnostic_results['network_info']['default_route'] = "Not available"
            
        # Get network interfaces (if available)  
        try:
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                diagnostic_results['network_info']['interfaces'] = result.stdout.strip()
        except:
            diagnostic_results['network_info']['interfaces'] = "Not available"
            
    except Exception as e:
        diagnostic_results['network_info']['error'] = str(e)
    
    # Summary
    diagnostic_results['summary'] = {
        'outbound_ip_obtained': diagnostic_results['outbound_ip'] is not None,
        'using_nat_instance': diagnostic_results['outbound_ip'] == "13.51.43.232",
        'database_socket_ok': "✅" in diagnostic_results.get('database_connectivity', {}).get('socket_test', ''),
        'database_sql_ok': "✅" in diagnostic_results.get('database_connectivity', {}).get('sql_test', ''),
        'api_connectivity_ok': "✅" in diagnostic_results.get('api_connectivity', {}).get('socket_test', '')
    }
    
    logger.info(f"Diagnostic completed: {diagnostic_results['summary']}")
    
    return JSONResponse({
        'success': True,
        'diagnostics': diagnostic_results
    })


def main():
    """Main entry point for Fargate container."""
    # Check if we're running in EventBridge direct mode
    trigger_mode = os.getenv('TRIGGER_MODE', 'webhook')
    
    if trigger_mode == 'eventbridge_direct':
        # Handle single EventBridge event and exit
        import asyncio
        
        async def handle_single_event():
            setup_logging()
            logger = get_logger(__name__)
            
            try:
                # Get event data from environment
                event_data_str = os.getenv('GMAIL_EVENT_DATA')
                if not event_data_str:
                    logger.error("No event data provided")
                    return
                
                event_data = json.loads(event_data_str)
                
                service = FargateOfferAutomationService()
                await service.initialize()
                
                result = await service.process_eventbridge_event(event_data)
                
                logger.info(f"Event processing result: {result}")
                
                await service.shutdown()
                
            except Exception as e:
                logger.error(f"Error processing single event: {e}", exc_info=True)
                sys.exit(1)
        
        asyncio.run(handle_single_event())
    
    else:
        # Run as persistent service with FastAPI
        port = int(os.getenv('PORT', 8080))
        host = os.getenv('HOST', '0.0.0.0')
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )


if __name__ == "__main__":
    main() 