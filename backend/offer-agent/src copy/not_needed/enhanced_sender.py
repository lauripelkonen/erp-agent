"""
Enhanced Notification Sender
Integrates advanced delivery tracking, customer preferences, and communication history.
Provides production-ready notification delivery with analytics and optimization.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.notifications.delivery_tracker import (
    DeliveryTracker, NotificationJob, DeliveryChannel, DeliveryStatus
)
from src.notifications.communication_history import (
    CommunicationHistoryManager, CommunicationType, CustomerPreferences
)
from src.notifications.sender import NotificationSender as BasicNotificationSender
from src.documents.generator import GeneratedDocument
from src.config.settings import get_settings
from src.utils.logger import get_logger, get_audit_logger


@dataclass
class EnhancedNotificationRequest:
    """Enhanced notification request with tracking and preferences."""
    recipient: str
    content: Dict[str, Any]
    channel: DeliveryChannel = DeliveryChannel.EMAIL
    customer_id: Optional[str] = None
    offer_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Scheduling options
    priority: int = 5
    scheduled_for: Optional[datetime] = None
    
    # Tracking options
    track_opens: bool = True
    track_clicks: bool = True
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_minutes: int = 5
    
    # Webhook callbacks
    success_webhook: Optional[str] = None
    failure_webhook: Optional[str] = None
    
    # Document attachment
    document: Optional[GeneratedDocument] = None


class EnhancedNotificationSender:
    """
    Production-ready notification sender with advanced features.
    
    Features:
    - Intelligent delivery routing based on customer preferences
    - Comprehensive tracking and analytics
    - Retry mechanisms with exponential backoff
    - Customer communication history management
    - Personalized send time optimization
    - Multi-channel delivery (email, SMS, webhooks)
    - GDPR compliance and preference management
    - Real-time delivery monitoring
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Initialize components
        self.delivery_tracker = DeliveryTracker()
        self.communication_history = CommunicationHistoryManager()
        self.basic_sender = BasicNotificationSender()
        
        # Start background workers
        self._workers_started = False
    
    async def ensure_workers_started(self):
        """Ensure background workers are started."""
        if not self._workers_started:
            await self.delivery_tracker.start_processing_workers(num_workers=3)
            self._workers_started = True
    
    async def send_notification(self, request: EnhancedNotificationRequest) -> Dict[str, Any]:
        """
        Send enhanced notification with tracking and optimization.
        
        Args:
            request: Enhanced notification request with all options
            
        Returns:
            Notification result with tracking information
        """
        await self.ensure_workers_started()
        
        try:
            # Step 1: Apply customer preferences and optimization
            optimized_request = await self._optimize_notification(request)
            
            # Step 2: Check if notification should be sent
            should_send, reason = await self._should_send_notification(optimized_request)
            if not should_send:
                return {
                    'success': False,
                    'reason': reason,
                    'skipped': True,
                    'recipient': request.recipient
                }
            
            # Step 3: Record communication in history
            communication_id = await self._record_outbound_communication(optimized_request)
            
            # Step 4: Prepare notification job for delivery tracker
            job = await self._create_notification_job(optimized_request, communication_id)
            
            # Step 5: Queue for delivery
            job_id = await self.delivery_tracker.queue_notification(job)
            
            # Step 6: Return tracking information
            result = {
                'success': True,
                'job_id': job_id,
                'communication_id': communication_id,
                'recipient': request.recipient,
                'channel': request.channel.value,
                'scheduled_for': request.scheduled_for.isoformat() if request.scheduled_for else None,
                'tracking_enabled': request.track_opens or request.track_clicks,
                'optimizations_applied': optimized_request != request
            }
            
            self.logger.info(f"Enhanced notification queued: {job_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Enhanced notification failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'recipient': request.recipient
            }
    
    async def _optimize_notification(self, request: EnhancedNotificationRequest) -> EnhancedNotificationRequest:
        """Apply customer preferences and intelligent optimizations."""
        
        if not request.customer_id:
            return request  # Can't optimize without customer ID
        
        try:
            # Get customer preferences and insights
            preferences = await self.communication_history.get_customer_preferences(request.customer_id)
            recommendations = await self.communication_history.get_communication_recommendations(request.customer_id)
            
            # Create optimized copy
            optimized = request
            
            # Channel optimization
            if not preferences.allows_channel(request.channel.value):
                # Switch to preferred channel if current one not allowed
                preferred_channels = preferences.preferred_channels
                if preferred_channels and preferred_channels[0] != request.channel.value:
                    try:
                        optimized.channel = DeliveryChannel(preferred_channels[0])
                        self.logger.info(f"Switched channel to customer preference: {preferred_channels[0]}")
                    except ValueError:
                        # Invalid channel in preferences, keep original
                        pass
            
            # Timing optimization
            if not request.scheduled_for and recommendations.get('optimal_send_time'):
                optimal_time = recommendations['optimal_send_time']
                now = datetime.utcnow()
                
                # Parse optimal hour and schedule for next occurrence
                try:
                    optimal_hour = int(optimal_time.split(':')[0])
                    
                    # Schedule for optimal time today or tomorrow
                    scheduled = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
                    if scheduled <= now:
                        scheduled += timedelta(days=1)
                    
                    # Don't schedule too far in the future for urgent notifications
                    if request.priority >= 8 or (scheduled - now).total_seconds() > 86400:  # 24 hours
                        pass  # Send immediately for high priority or if optimization delays too much
                    else:
                        optimized.scheduled_for = scheduled
                        self.logger.info(f"Optimized send time: {scheduled}")
                        
                except (ValueError, IndexError):
                    pass  # Invalid optimal time format
            
            # Language optimization
            if preferences.preferred_language and 'language' not in optimized.content:
                optimized.content['language'] = preferences.preferred_language
            
            return optimized
            
        except Exception as e:
            self.logger.warning(f"Failed to optimize notification: {e}")
            return request
    
    async def _should_send_notification(self, request: EnhancedNotificationRequest) -> tuple[bool, Optional[str]]:
        """Check if notification should be sent based on preferences and frequency."""
        
        if not request.customer_id:
            return True, None  # Always send if no customer context
        
        try:
            preferences = await self.communication_history.get_customer_preferences(request.customer_id)
            
            # Check if customer allows this type of notification
            notification_type = request.content.get('notification_type', 'offer')
            if not preferences.allows_notification_type(notification_type):
                return False, f"Customer has disabled {notification_type} notifications"
            
            # Check quiet hours
            if preferences.quiet_hours_start and preferences.quiet_hours_end:
                now = datetime.utcnow()
                current_time = now.strftime('%H:%M')
                
                if preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end:
                    # Schedule for after quiet hours instead of blocking
                    quiet_end_hour = int(preferences.quiet_hours_end.split(':')[0])
                    scheduled = now.replace(hour=quiet_end_hour, minute=0, second=0, microsecond=0)
                    if scheduled <= now:
                        scheduled += timedelta(days=1)
                    
                    request.scheduled_for = scheduled
                    self.logger.info(f"Scheduled after quiet hours: {scheduled}")
            
            # Check frequency limits
            if preferences.email_frequency == 'low':
                # Check if we've sent recently
                recent_history = await self.communication_history.get_communication_history(
                    request.customer_id,
                    limit=10,
                    date_from=datetime.utcnow() - timedelta(days=7)
                )
                
                recent_emails = [h for h in recent_history if h['type'] == 'email' and h['direction'] == 'outbound']
                if len(recent_emails) >= 2:  # Max 2 emails per week for low frequency
                    return False, "Customer frequency preference (low) exceeded"
            
            return True, None
            
        except Exception as e:
            self.logger.warning(f"Failed to check notification preferences: {e}")
            return True, None  # Default to sending on error
    
    async def _record_outbound_communication(self, request: EnhancedNotificationRequest) -> str:
        """Record the outbound communication in history."""
        
        content_data = {
            'subject': request.content.get('subject', 'Notification'),
            'sender': request.content.get('from_email', 'system@company.fi'),
            'recipient': request.recipient,
            'text_content': request.content.get('text_content', ''),
            'html_content': request.content.get('html_content', ''),
            'full_content': str(request.content),
            'metadata': {
                'priority': request.priority,
                'channel': request.channel.value,
                'tracking_enabled': request.track_opens or request.track_clicks,
                'has_attachment': request.document is not None
            }
        }
        
        return await self.communication_history.record_communication(
            customer_id=request.customer_id or 'unknown',
            communication_type=CommunicationType.EMAIL if request.channel == DeliveryChannel.EMAIL else CommunicationType.SMS,
            channel=request.channel.value,
            direction='outbound',
            content=content_data,
            offer_id=request.offer_id,
            request_id=request.request_id
        )
    
    async def _create_notification_job(
        self, 
        request: EnhancedNotificationRequest, 
        communication_id: str
    ) -> NotificationJob:
        """Create notification job for delivery tracker."""
        
        # Prepare content for delivery
        job_content = dict(request.content)
        
        # Add attachment if present
        if request.document:
            job_content['attachment'] = {
                'filename': request.document.filename,
                'file_path': request.document.file_path,
                'content_type': request.document.content_type,
                'file_size': request.document.file_size
            }
        
        # Set expiration time
        expires_at = None
        if request.priority < 3:  # Low priority notifications expire after 7 days
            expires_at = datetime.utcnow() + timedelta(days=7)
        elif request.priority < 7:  # Normal priority expire after 3 days
            expires_at = datetime.utcnow() + timedelta(days=3)
        # High priority notifications don't expire
        
        job = NotificationJob(
            job_id="",  # Will be generated by delivery tracker
            recipient=request.recipient,
            channel=request.channel,
            content=job_content,
            priority=request.priority,
            scheduled_for=request.scheduled_for,
            max_retries=request.max_retries,
            retry_delay_seconds=request.retry_delay_minutes * 60,
            expires_at=expires_at,
            success_webhook=request.success_webhook,
            failure_webhook=request.failure_webhook
        )
        
        # Store communication ID in job metadata for tracking updates
        job.content['communication_id'] = communication_id
        
        return job
    
    async def handle_delivery_event(self, job_id: str, status: DeliveryStatus, event_data: Dict[str, Any] = None):
        """Handle delivery status updates and update communication history."""
        
        try:
            # Get communication ID from job
            communication_id = event_data.get('communication_id') if event_data else None
            
            if communication_id:
                # Map delivery status to communication status
                from notifications.communication_history import CommunicationStatus
                
                status_mapping = {
                    DeliveryStatus.SENT: CommunicationStatus.SENT,
                    DeliveryStatus.DELIVERED: CommunicationStatus.DELIVERED,
                    DeliveryStatus.OPENED: CommunicationStatus.OPENED,
                    DeliveryStatus.CLICKED: CommunicationStatus.CLICKED,
                    DeliveryStatus.BOUNCED: CommunicationStatus.BOUNCED,
                    DeliveryStatus.FAILED: CommunicationStatus.FAILED
                }
                
                comm_status = status_mapping.get(status)
                if comm_status:
                    await self.communication_history.update_communication_status(
                        communication_id,
                        comm_status,
                        event_data
                    )
            
            self.logger.info(f"Delivery event processed: {job_id} -> {status.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle delivery event: {e}")
    
    async def send_offer_notification(
        self,
        recipient: str,
        offer_document: Optional[GeneratedDocument],
        offer_data: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced offer notification with optimization and tracking.
        Backward compatibility method for existing code.
        """
        
        # Prepare content from offer data
        customer = offer_data.get('customer', {})
        content = {
            'subject': f"Tarjous: {offer_data.get('offer_number', 'N/A')}",
            'from_email': 'offers@company.fi',
            'from_name': 'Offer Automation System',
            'text_content': self._generate_text_content(offer_data),
            'html_content': self._generate_html_content(offer_data),
            'notification_type': 'offer',
            'language': 'fi'
        }
        
        # Create enhanced request
        request = EnhancedNotificationRequest(
            recipient=recipient,
            content=content,
            channel=DeliveryChannel.EMAIL,
            customer_id=customer_id or customer.get('id'),
            offer_id=offer_data.get('offer_id'),
            request_id=offer_data.get('request_id'),
            priority=7,  # High priority for offers
            track_opens=True,
            track_clicks=True,
            document=offer_document
        )
        
        return await self.send_notification(request)
    
    def _generate_text_content(self, offer_data: Dict[str, Any]) -> str:
        """Generate text content for offer email."""
        customer = offer_data.get('customer', {})
        
        return f"""
Hyvä {customer.get('name', 'asiakas')},

Kiitos tarjouspyynnöstänne. Liitteenä löydätte pyydetyn tarjouksen.

Tarjouksen tiedot:
- Tarjousnumero: {offer_data.get('offer_number', 'N/A')}
- Tuotteiden määrä: {len(offer_data.get('products', []))} kpl
- Kokonaissumma: {offer_data.get('total_amount', 0):.2f} EUR (sis. ALV 25.5%)

Tarjous on voimassa 30 päivää.

Ystävällisin terveisin,
Automaattinen tarjousjärjestelmä
        """.strip()
    
    def _generate_html_content(self, offer_data: Dict[str, Any]) -> str:
        """Generate HTML content for offer email."""
        customer = offer_data.get('customer', {})
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #1f4788; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .highlight {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Tarjous</h1>
    </div>
    
    <div class="content">
        <p>Hyvä {customer.get('name', 'asiakas')},</p>
        
        <p>Kiitos tarjouspyynnöstänne. Liitteenä löydätte pyydetyn tarjouksen.</p>
        
        <div class="highlight">
            <h3>Tarjouksen tiedot:</h3>
            <ul>
                <li><strong>Tarjousnumero:</strong> {offer_data.get('offer_number', 'N/A')}</li>
                <li><strong>Tuotteiden määrä:</strong> {len(offer_data.get('products', []))} kpl</li>
                <li><strong>Kokonaissumma:</strong> {offer_data.get('total_amount', 0):.2f} EUR (sis. ALV 25.5%)</li>
            </ul>
        </div>
        
        <p>Tarjous on voimassa 30 päivää.</p>
        
        <p>Ystävällisin terveisin,<br>
        Automaattinen tarjousjärjestelmä</p>
    </div>
</body>
</html>
        """.strip()
    
    async def get_delivery_statistics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive delivery statistics."""
        return await self.delivery_tracker.get_delivery_stats(time_range_hours)
    
    async def get_customer_communication_insights(self, customer_id: str) -> Dict[str, Any]:
        """Get customer communication insights and recommendations."""
        return await self.communication_history.get_customer_insights(customer_id)
    
    async def update_customer_preferences(self, customer_id: str, preferences: Dict[str, Any]):
        """Update customer communication preferences."""
        customer_prefs = CustomerPreferences(
            customer_id=customer_id,
            preferred_language=preferences.get('language', 'fi'),
            preferred_channels=preferences.get('channels', ['email']),
            email_frequency=preferences.get('frequency', 'normal'),
            marketing_consent=preferences.get('marketing_consent', False),
            notification_types=preferences.get('notification_types', {}),
            quiet_hours_start=preferences.get('quiet_hours_start'),
            quiet_hours_end=preferences.get('quiet_hours_end'),
            timezone=preferences.get('timezone', 'Europe/Helsinki')
        )
        
        await self.communication_history.update_customer_preferences(customer_id, customer_prefs)
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of enhanced notification system."""
        
        # Get component health checks
        delivery_health = await self.delivery_tracker.health_check()
        history_health = await self.communication_history.health_check()
        basic_sender_health = await self.basic_sender.health_check()
        
        # Combine results
        overall_status = 'healthy'
        if (delivery_health['status'] != 'healthy' or 
            history_health['status'] != 'healthy' or 
            basic_sender_health['status'] != 'healthy'):
            overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'delivery_tracker': delivery_health,
                'communication_history': history_health,
                'basic_sender': basic_sender_health
            },
            'workers_started': self._workers_started
        }