"""
S3 Request Context Logger

Saves offer request context to S3 for later analysis by the learning agent.
This enables the system to compare AI-generated offers with user-corrected versions.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError

from src.utils.logger import get_logger


class OfferRequestLogger:
    """
    Logs offer request context to S3 for learning system analysis.
    
    Saves:
    - Original email content (body, subject, sender)
    - AI-matched products (with codes, quantities, confidence scores)
    - Offer metadata (number, ID, customer info)
    - Timestamp and processing metadata
    """
    
    def __init__(self):
        """Initialize the S3 logger with configuration from environment."""
        self.logger = get_logger(__name__)
        
        # Get S3 configuration from environment
        self.bucket_name = os.getenv('AWS_S3_BUCKET_LEARNING', 'offer-learning-data')
        self.region = os.getenv('AWS_REGION', 'eu-north-1')
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            self.logger.info(f"S3 Request Logger initialized with bucket: {self.bucket_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    async def save_offer_context(
        self,
        offer_number: str,
        email_data: Dict[str, Any],
        matched_products: List[Any],
        customer_info: Dict[str, Any],
        offer_pricing: Optional[Any] = None
    ) -> bool:
        """
        Save complete offer request context to S3.
        
        Args:
            offer_number: The Lemonsoft offer number
            email_data: Original email data (subject, body, sender, etc.)
            matched_products: List of ProductMatch objects from AI
            customer_info: Customer information from Lemonsoft
            offer_pricing: Optional OfferPricing object with line items
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.s3_client:
            self.logger.warning("S3 client not initialized, skipping offer context save")
            return False
        
        try:
            # Build the context data structure
            context_data = {
                'offer_number': offer_number,
                'timestamp': datetime.utcnow().isoformat(),
                'email': {
                    'subject': email_data.get('subject', ''),
                    'sender': email_data.get('sender', ''),
                    'body': email_data.get('body', ''),
                    'date': email_data.get('date', ''),
                    'message_id': email_data.get('message_id', '')
                },
                'customer': {
                    'id': customer_info.get('id'),
                    'number': customer_info.get('number'),
                    'name': customer_info.get('name', ''),
                    'street': customer_info.get('street', ''),
                    'city': customer_info.get('city', ''),
                    'postal_code': customer_info.get('postal_code', '')
                },
                'ai_matched_products': []
            }
            
            # Extract product match information
            for product in matched_products:
                product_data = {
                    'product_code': product.product_code,
                    'product_name': product.product_name,
                    'description': product.description,
                    'quantity': product.quantity_requested,
                    'unit': product.unit,
                    'price': product.price,
                    'confidence_score': product.confidence_score,
                    'match_method': product.match_method,
                    'product_group': product.product_group
                }
                
                # Add match details if available (includes AI reasoning)
                if hasattr(product, 'match_details') and product.match_details:
                    product_data['match_details'] = product.match_details
                
                context_data['ai_matched_products'].append(product_data)
            
            # Add pricing information if available
            if offer_pricing:
                context_data['pricing'] = {
                    'net_total': offer_pricing.net_total,
                    'vat_amount': offer_pricing.vat_amount,
                    'total_amount': offer_pricing.total_amount,
                    'total_discount_percent': offer_pricing.total_discount_percent,
                    'currency': offer_pricing.currency,
                    'line_items': []
                }
                
                # Add line item details
                for line_item in offer_pricing.line_items:
                    context_data['pricing']['line_items'].append({
                        'product_code': line_item.product_code,
                        'quantity': line_item.quantity,
                        'unit_price': line_item.unit_price,
                        'net_price': line_item.net_price,
                        'discount_percent': line_item.discount_percent,
                        'line_total': line_item.line_total,
                        'applied_rules': line_item.applied_rules
                    })
            
            # Generate S3 key with timestamp for uniqueness
            timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"offer-requests/{offer_number}_{timestamp_str}.json"
            
            # Convert to JSON
            json_data = json.dumps(context_data, indent=2, ensure_ascii=False)
            
            # Upload to S3
            # Note: S3 Metadata values must be strings
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'offer_number': str(offer_number),  # Convert to string
                    'timestamp': str(timestamp_str),    # Ensure string
                    'customer_name': str(customer_info.get('name', ''))[:100]  # Convert and limit metadata size
                }
            )
            
            self.logger.info(
                f"Saved offer request context to S3: {s3_key} "
                f"(Offer: {offer_number}, Products: {len(matched_products)})"
            )
            
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            self.logger.error(
                f"AWS S3 error saving offer context for {offer_number}: "
                f"{error_code} - {str(e)}"
            )
            return False
            
        except Exception as e:
            self.logger.error(
                f"Failed to save offer context to S3 for {offer_number}: {e}",
                exc_info=True
            )
            return False
    
    def get_offer_context(self, offer_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve offer request context from S3.
        
        Args:
            offer_number: The offer number to retrieve
            
        Returns:
            Dict with offer context data, or None if not found
        """
        if not self.s3_client:
            self.logger.warning("S3 client not initialized")
            return None
        
        try:
            # List objects with this offer number prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"offer-requests/{offer_number}_"
            )
            
            if 'Contents' not in response or not response['Contents']:
                self.logger.warning(f"No offer context found for {offer_number}")
                return None
            
            # Get the most recent file (they're sorted by timestamp in the key)
            latest_key = response['Contents'][-1]['Key']
            
            # Download the file
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=latest_key)
            json_data = obj['Body'].read().decode('utf-8')
            
            context_data = json.loads(json_data)
            
            self.logger.info(f"Retrieved offer context from S3: {latest_key}")
            
            return context_data
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            self.logger.error(
                f"AWS S3 error retrieving offer context for {offer_number}: "
                f"{error_code} - {str(e)}"
            )
            return None
            
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve offer context from S3 for {offer_number}: {e}",
                exc_info=True
            )
            return None
    
    def list_recent_offers(self, days: int = 3) -> List[str]:
        """
        List offer numbers from the past N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of offer numbers
        """
        if not self.s3_client:
            self.logger.warning("S3 client not initialized")
            return []
        
        try:
            # Calculate cutoff date
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # List all objects in offer-requests/
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='offer-requests/'
            )
            
            if 'Contents' not in response:
                return []
            
            # Extract offer numbers from recent files
            offer_numbers = set()
            for obj in response['Contents']:
                # Check if file is recent enough
                if obj['LastModified'].replace(tzinfo=None) >= cutoff_date:
                    # Extract offer number from key: offer-requests/{offer_number}_{timestamp}.json
                    key = obj['Key']
                    filename = key.split('/')[-1]  # Get filename
                    offer_number = filename.split('_')[0]  # Get part before first underscore
                    offer_numbers.add(offer_number)
            
            offer_list = sorted(list(offer_numbers))
            self.logger.info(f"Found {len(offer_list)} offers from past {days} days")
            
            return offer_list
            
        except Exception as e:
            self.logger.error(f"Failed to list recent offers: {e}", exc_info=True)
            return []

