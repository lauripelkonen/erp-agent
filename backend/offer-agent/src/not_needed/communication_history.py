"""
Customer Communication History Manager
Tracks all customer communications, preferences, and interaction patterns.
Provides insights for improving customer engagement and communication strategies.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import get_settings
from src.utils.logger import get_logger, get_audit_logger


class CommunicationType(Enum):
    """Types of customer communications."""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    CHAT = "chat"
    WEBHOOK = "webhook"
    SYSTEM_NOTIFICATION = "system_notification"


class CommunicationStatus(Enum):
    """Status of communications."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


@dataclass
class CustomerPreferences:
    """Customer communication preferences."""
    customer_id: str
    preferred_language: str = "fi"
    preferred_channels: List[str] = field(default_factory=lambda: ["email"])
    email_frequency: str = "normal"  # high, normal, low
    marketing_consent: bool = False
    notification_types: Dict[str, bool] = field(default_factory=dict)
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    timezone: str = "Europe/Helsinki"
    
    def allows_channel(self, channel: str) -> bool:
        """Check if customer allows this communication channel."""
        return channel in self.preferred_channels
    
    def allows_notification_type(self, notification_type: str) -> bool:
        """Check if customer allows this type of notification."""
        return self.notification_types.get(notification_type, True)


# Database models
Base = declarative_base()

class CommunicationHistoryModel(Base):
    """SQLAlchemy model for communication history."""
    __tablename__ = 'communication_history'
    
    communication_id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    offer_id = Column(String(36), index=True)
    request_id = Column(String(36), index=True)
    
    communication_type = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    
    subject = Column(String(500))
    content_preview = Column(Text)
    full_content = Column(Text)
    
    sender = Column(String(255))
    recipient = Column(String(255))
    
    status = Column(String(20), default=CommunicationStatus.PENDING.value)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    
    tracking_data = Column(JSON)
    metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomerPreferencesModel(Base):
    """SQLAlchemy model for customer preferences."""
    __tablename__ = 'customer_preferences'
    
    customer_id = Column(String(36), primary_key=True)
    preferred_language = Column(String(5), default='fi')
    preferred_channels = Column(JSON, default=list)
    email_frequency = Column(String(20), default='normal')
    marketing_consent = Column(Boolean, default=False)
    notification_types = Column(JSON, default=dict)
    quiet_hours_start = Column(String(5))
    quiet_hours_end = Column(String(5))
    timezone = Column(String(50), default='Europe/Helsinki')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunicationInsightsModel(Base):
    """SQLAlchemy model for communication insights."""
    __tablename__ = 'communication_insights'
    
    insight_id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    
    # Engagement metrics
    total_communications = Column(Integer, default=0)
    email_open_rate = Column(Float, default=0.0)
    email_click_rate = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    average_response_time_hours = Column(Float, default=0.0)
    
    # Behavioral patterns
    preferred_contact_hours = Column(JSON)  # Hour distribution
    device_preferences = Column(JSON)      # Desktop/mobile patterns
    engagement_trends = Column(JSON)       # Monthly engagement data
    
    # Preferences learned from behavior
    learned_preferences = Column(JSON)
    
    last_calculated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommunicationHistoryManager:
    """
    Customer communication history and preference management system.
    
    Features:
    - Complete communication history tracking
    - Customer preference management
    - Engagement analytics and insights
    - Behavioral pattern analysis
    - Communication optimization recommendations
    - GDPR compliance tools
    - Automated preference learning
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Database setup
        self.engine = create_engine(getattr(self.settings, 'database_url', 'sqlite:///communications.db'))
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
    
    async def record_communication(
        self,
        customer_id: str,
        communication_type: CommunicationType,
        channel: str,
        direction: str,  # "inbound" or "outbound"
        content: Dict[str, Any],
        offer_id: str = None,
        request_id: str = None,
        tracking_data: Dict[str, Any] = None
    ) -> str:
        """Record a communication in the history."""
        
        communication_id = str(uuid.uuid4())
        
        try:
            # Create preview of content
            content_preview = self._create_content_preview(content)
            
            communication = CommunicationHistoryModel(
                communication_id=communication_id,
                customer_id=customer_id,
                offer_id=offer_id,
                request_id=request_id,
                communication_type=communication_type.value,
                channel=channel,
                direction=direction,
                subject=content.get('subject', ''),
                content_preview=content_preview,
                full_content=content.get('full_content', ''),
                sender=content.get('sender', ''),
                recipient=content.get('recipient', ''),
                tracking_data=tracking_data or {},
                metadata=content.get('metadata', {})
            )
            
            self.db_session.add(communication)
            self.db_session.commit()
            
            self.logger.info(f"Communication recorded: {communication_id}")
            
            # Update customer insights asynchronously
            await self._update_customer_insights(customer_id)
            
            return communication_id
            
        except Exception as e:
            self.logger.error(f"Failed to record communication: {e}")
            self.db_session.rollback()
            raise
    
    def _create_content_preview(self, content: Dict[str, Any], max_length: int = 200) -> str:
        """Create a preview of the communication content."""
        preview_text = ""
        
        if 'subject' in content:
            preview_text = content['subject'] + " - "
        
        if 'text_content' in content:
            text = content['text_content']
        elif 'html_content' in content:
            # Strip HTML tags for preview
            import re
            text = re.sub(r'<[^>]+>', '', content['html_content'])
        else:
            text = str(content)
        
        preview_text += text[:max_length - len(preview_text)]
        if len(text) > max_length - len(preview_text):
            preview_text += "..."
        
        return preview_text
    
    async def update_communication_status(
        self,
        communication_id: str,
        status: CommunicationStatus,
        event_data: Dict[str, Any] = None
    ):
        """Update the status of a communication."""
        
        try:
            communication = self.db_session.query(CommunicationHistoryModel).filter_by(
                communication_id=communication_id
            ).first()
            
            if not communication:
                self.logger.warning(f"Communication not found: {communication_id}")
                return
            
            communication.status = status.value
            communication.updated_at = datetime.utcnow()
            
            # Update specific timestamp fields
            now = datetime.utcnow()
            if status == CommunicationStatus.SENT:
                communication.sent_at = now
            elif status == CommunicationStatus.DELIVERED:
                communication.delivered_at = now
            elif status == CommunicationStatus.OPENED:
                communication.opened_at = now
            elif status == CommunicationStatus.CLICKED:
                communication.clicked_at = now
            elif status == CommunicationStatus.REPLIED:
                communication.replied_at = now
            
            # Update tracking data
            if event_data:
                current_tracking = communication.tracking_data or {}
                current_tracking.update(event_data)
                communication.tracking_data = current_tracking
            
            self.db_session.commit()
            
            # Update customer insights
            await self._update_customer_insights(communication.customer_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update communication status: {e}")
            self.db_session.rollback()
    
    async def get_customer_preferences(self, customer_id: str) -> CustomerPreferences:
        """Get customer communication preferences."""
        
        prefs = self.db_session.query(CustomerPreferencesModel).filter_by(
            customer_id=customer_id
        ).first()
        
        if prefs:
            return CustomerPreferences(
                customer_id=customer_id,
                preferred_language=prefs.preferred_language,
                preferred_channels=prefs.preferred_channels or ["email"],
                email_frequency=prefs.email_frequency,
                marketing_consent=prefs.marketing_consent,
                notification_types=prefs.notification_types or {},
                quiet_hours_start=prefs.quiet_hours_start,
                quiet_hours_end=prefs.quiet_hours_end,
                timezone=prefs.timezone
            )
        else:
            # Return default preferences
            return CustomerPreferences(customer_id=customer_id)
    
    async def update_customer_preferences(
        self,
        customer_id: str,
        preferences: CustomerPreferences
    ):
        """Update customer communication preferences."""
        
        try:
            existing = self.db_session.query(CustomerPreferencesModel).filter_by(
                customer_id=customer_id
            ).first()
            
            if existing:
                # Update existing preferences
                existing.preferred_language = preferences.preferred_language
                existing.preferred_channels = preferences.preferred_channels
                existing.email_frequency = preferences.email_frequency
                existing.marketing_consent = preferences.marketing_consent
                existing.notification_types = preferences.notification_types
                existing.quiet_hours_start = preferences.quiet_hours_start
                existing.quiet_hours_end = preferences.quiet_hours_end
                existing.timezone = preferences.timezone
                existing.updated_at = datetime.utcnow()
            else:
                # Create new preferences
                new_prefs = CustomerPreferencesModel(
                    customer_id=customer_id,
                    preferred_language=preferences.preferred_language,
                    preferred_channels=preferences.preferred_channels,
                    email_frequency=preferences.email_frequency,
                    marketing_consent=preferences.marketing_consent,
                    notification_types=preferences.notification_types,
                    quiet_hours_start=preferences.quiet_hours_start,
                    quiet_hours_end=preferences.quiet_hours_end,
                    timezone=preferences.timezone
                )
                self.db_session.add(new_prefs)
            
            self.db_session.commit()
            
            self.audit_logger.log_customer_preferences_updated(
                customer_id,
                {
                    'language': preferences.preferred_language,
                    'channels': preferences.preferred_channels,
                    'marketing_consent': preferences.marketing_consent
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update customer preferences: {e}")
            self.db_session.rollback()
            raise
    
    async def get_communication_history(
        self,
        customer_id: str,
        limit: int = 50,
        communication_type: Optional[CommunicationType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get customer communication history."""
        
        query = self.db_session.query(CommunicationHistoryModel).filter_by(
            customer_id=customer_id
        )
        
        if communication_type:
            query = query.filter_by(communication_type=communication_type.value)
        
        if date_from:
            query = query.filter(CommunicationHistoryModel.created_at >= date_from)
        
        if date_to:
            query = query.filter(CommunicationHistoryModel.created_at <= date_to)
        
        communications = query.order_by(
            CommunicationHistoryModel.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                'communication_id': comm.communication_id,
                'type': comm.communication_type,
                'channel': comm.channel,
                'direction': comm.direction,
                'subject': comm.subject,
                'content_preview': comm.content_preview,
                'status': comm.status,
                'sent_at': comm.sent_at.isoformat() if comm.sent_at else None,
                'delivered_at': comm.delivered_at.isoformat() if comm.delivered_at else None,
                'opened_at': comm.opened_at.isoformat() if comm.opened_at else None,
                'clicked_at': comm.clicked_at.isoformat() if comm.clicked_at else None,
                'replied_at': comm.replied_at.isoformat() if comm.replied_at else None,
                'created_at': comm.created_at.isoformat(),
                'metadata': comm.metadata or {}
            }
            for comm in communications
        ]
    
    async def _update_customer_insights(self, customer_id: str):
        """Update customer communication insights based on history."""
        
        try:
            # Get communication history for analysis
            since_date = datetime.utcnow() - timedelta(days=90)  # Last 90 days
            
            communications = self.db_session.query(CommunicationHistoryModel).filter(
                CommunicationHistoryModel.customer_id == customer_id,
                CommunicationHistoryModel.created_at >= since_date
            ).all()
            
            if not communications:
                return
            
            # Calculate metrics
            total_comms = len(communications)
            email_comms = [c for c in communications if c.communication_type == 'email' and c.direction == 'outbound']
            
            email_opens = len([c for c in email_comms if c.opened_at])
            email_clicks = len([c for c in email_comms if c.clicked_at])
            responses = len([c for c in communications if c.replied_at])
            
            email_open_rate = (email_opens / len(email_comms)) * 100 if email_comms else 0
            email_click_rate = (email_clicks / len(email_comms)) * 100 if email_comms else 0
            response_rate = (responses / total_comms) * 100 if total_comms else 0
            
            # Calculate average response time
            response_times = []
            for comm in communications:
                if comm.sent_at and comm.replied_at:
                    response_time = (comm.replied_at - comm.sent_at).total_seconds() / 3600  # Hours
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Analyze preferred contact hours
            contact_hours = {}
            for comm in communications:
                if comm.opened_at:
                    hour = comm.opened_at.hour
                    contact_hours[hour] = contact_hours.get(hour, 0) + 1
            
            # Update or create insights
            existing_insights = self.db_session.query(CommunicationInsightsModel).filter_by(
                customer_id=customer_id
            ).first()
            
            insights_data = {
                'total_communications': total_comms,
                'email_open_rate': email_open_rate,
                'email_click_rate': email_click_rate,
                'response_rate': response_rate,
                'average_response_time_hours': avg_response_time,
                'preferred_contact_hours': contact_hours,
                'last_calculated': datetime.utcnow()
            }
            
            if existing_insights:
                for key, value in insights_data.items():
                    setattr(existing_insights, key, value)
            else:
                new_insights = CommunicationInsightsModel(
                    insight_id=str(uuid.uuid4()),
                    customer_id=customer_id,
                    **insights_data
                )
                self.db_session.add(new_insights)
            
            self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update customer insights: {e}")
            self.db_session.rollback()
    
    async def get_customer_insights(self, customer_id: str) -> Dict[str, Any]:
        """Get customer communication insights."""
        
        insights = self.db_session.query(CommunicationInsightsModel).filter_by(
            customer_id=customer_id
        ).first()
        
        if not insights:
            # Trigger insights calculation
            await self._update_customer_insights(customer_id)
            insights = self.db_session.query(CommunicationInsightsModel).filter_by(
                customer_id=customer_id
            ).first()
        
        if insights:
            return {
                'customer_id': customer_id,
                'total_communications': insights.total_communications,
                'email_open_rate': insights.email_open_rate,
                'email_click_rate': insights.email_click_rate,
                'response_rate': insights.response_rate,
                'average_response_time_hours': insights.average_response_time_hours,
                'preferred_contact_hours': insights.preferred_contact_hours or {},
                'device_preferences': insights.device_preferences or {},
                'engagement_trends': insights.engagement_trends or {},
                'learned_preferences': insights.learned_preferences or {},
                'last_calculated': insights.last_calculated.isoformat() if insights.last_calculated else None
            }
        else:
            return {
                'customer_id': customer_id,
                'total_communications': 0,
                'email_open_rate': 0,
                'email_click_rate': 0,
                'response_rate': 0,
                'average_response_time_hours': 0,
                'preferred_contact_hours': {},
                'device_preferences': {},
                'engagement_trends': {},
                'learned_preferences': {},
                'last_calculated': None
            }
    
    async def get_communication_recommendations(self, customer_id: str) -> Dict[str, Any]:
        """Get personalized communication recommendations for a customer."""
        
        insights = await self.get_customer_insights(customer_id)
        preferences = await self.get_customer_preferences(customer_id)
        
        recommendations = {
            'optimal_send_time': None,
            'recommended_channel': 'email',
            'content_suggestions': [],
            'frequency_recommendation': 'normal',
            'engagement_prediction': 'medium'
        }
        
        # Analyze optimal send time
        if insights['preferred_contact_hours']:
            best_hour = max(insights['preferred_contact_hours'], key=insights['preferred_contact_hours'].get)
            recommendations['optimal_send_time'] = f"{best_hour:02d}:00"
        
        # Recommend channel based on engagement
        if insights['email_open_rate'] > 30:
            recommendations['recommended_channel'] = 'email'
        elif insights['response_rate'] > 50:
            recommendations['recommended_channel'] = 'email'
        else:
            recommendations['recommended_channel'] = preferences.preferred_channels[0] if preferences.preferred_channels else 'email'
        
        # Engagement prediction
        if insights['email_open_rate'] > 40 and insights['response_rate'] > 30:
            recommendations['engagement_prediction'] = 'high'
        elif insights['email_open_rate'] < 15 or insights['response_rate'] < 10:
            recommendations['engagement_prediction'] = 'low'
        
        # Content suggestions based on behavior
        if insights['email_click_rate'] > 20:
            recommendations['content_suggestions'].append('Include actionable links and clear CTAs')
        
        if insights['average_response_time_hours'] < 2:
            recommendations['content_suggestions'].append('Customer is highly responsive - consider time-sensitive offers')
        
        return recommendations
    
    async def export_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """Export all customer communication data (GDPR compliance)."""
        
        history = await self.get_communication_history(customer_id, limit=1000)
        preferences = await self.get_customer_preferences(customer_id)
        insights = await self.get_customer_insights(customer_id)
        
        return {
            'customer_id': customer_id,
            'export_date': datetime.utcnow().isoformat(),
            'communication_history': history,
            'preferences': {
                'preferred_language': preferences.preferred_language,
                'preferred_channels': preferences.preferred_channels,
                'email_frequency': preferences.email_frequency,
                'marketing_consent': preferences.marketing_consent,
                'notification_types': preferences.notification_types,
                'quiet_hours': {
                    'start': preferences.quiet_hours_start,
                    'end': preferences.quiet_hours_end
                },
                'timezone': preferences.timezone
            },
            'insights': insights
        }
    
    async def delete_customer_data(self, customer_id: str) -> bool:
        """Delete all customer communication data (GDPR right to be forgotten)."""
        
        try:
            # Delete communication history
            self.db_session.query(CommunicationHistoryModel).filter_by(
                customer_id=customer_id
            ).delete()
            
            # Delete preferences
            self.db_session.query(CustomerPreferencesModel).filter_by(
                customer_id=customer_id
            ).delete()
            
            # Delete insights
            self.db_session.query(CommunicationInsightsModel).filter_by(
                customer_id=customer_id
            ).delete()
            
            self.db_session.commit()
            
            self.audit_logger.log_customer_data_deleted(
                customer_id,
                {
                    'deleted_at': datetime.utcnow().isoformat(),
                    'reason': 'GDPR right to be forgotten'
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete customer data: {e}")
            self.db_session.rollback()
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for communication history system."""
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database_connection': 'ok',
            'recent_activity': {}
        }
        
        try:
            # Check database connectivity
            self.db_session.execute('SELECT 1')
            
            # Get recent activity stats
            since_24h = datetime.utcnow() - timedelta(hours=24)
            recent_comms = self.db_session.query(CommunicationHistoryModel).filter(
                CommunicationHistoryModel.created_at >= since_24h
            ).count()
            
            health_status['recent_activity'] = {
                'communications_24h': recent_comms,
                'active_customers': self.db_session.query(CustomerPreferencesModel).count()
            }
            
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['database_connection'] = f'error: {e}'
        
        return health_status