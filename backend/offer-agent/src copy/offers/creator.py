"""
Offer Creation Service
Integrates product matching results with Lemonsoft API to create complete offers.
Handles pricing, customer data, and offer generation workflow.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid

from config.settings import get_settings
from utils.logger import get_logger, get_audit_logger
from utils.exceptions import ExternalServiceError, ValidationError
from lemonsoft.api_client import (
    LemonsoftAPIClient, LemonsoftOffer, LemonsoftOfferLine, 
    LemonsoftCustomer, LemonsoftAPIError
)
from products.matcher import ProductMatch
from customer.lookup import CustomerMatch


@dataclass
class OfferCreationRequest:
    """Request for creating an offer."""
    customer_match: CustomerMatch
    product_matches: List[ProductMatch]
    email_context: Dict[str, Any]
    special_instructions: str = ""
    delivery_terms: str = ""
    payment_terms: str = "Net 30"
    valid_for_days: int = 30
    currency: str = "EUR"
    reference: str = ""


@dataclass
class OfferCreationResult:
    """Result of offer creation process."""
    success: bool
    offer_id: str = ""
    offer_number: str = ""
    lemonsoft_offer: Optional[LemonsoftOffer] = None
    customer_created: bool = False
    product_issues: List[Dict[str, Any]] = None
    total_amount: float = 0.0
    validation_warnings: List[str] = None
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        if self.product_issues is None:
            self.product_issues = []
        if self.validation_warnings is None:
            self.validation_warnings = []


class OfferCreationService:
    """
    Service for creating offers by integrating product matches with Lemonsoft API.
    
    Responsibilities:
    - Customer data validation and creation
    - Product validation and pricing retrieval
    - Offer line item generation
    - Lemonsoft offer creation
    - Error handling and rollback
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Will be initialized when needed
        self.lemonsoft_client: Optional[LemonsoftAPIClient] = None
    
    async def initialize(self):
        """Initialize the offer creation service."""
        if self.lemonsoft_client is None:
            self.lemonsoft_client = LemonsoftAPIClient()
            await self.lemonsoft_client.initialize()
            self.logger.info("Offer creation service initialized")
    
    async def create_offer(self, request: OfferCreationRequest) -> OfferCreationResult:
        """
        Create a complete offer in Lemonsoft from product matches and customer data.
        
        Args:
            request: Offer creation request with all necessary data
            
        Returns:
            Offer creation result with success status and details
        """
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        try:
            await self.initialize()
            
            self.logger.info(
                f"Creating offer for customer {request.customer_match.customer_name}",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'customer_id': request.customer_match.customer_id,
                        'product_count': len(request.product_matches)
                    }
                }
            )
            
            # Step 1: Validate and prepare customer
            customer_result = await self._prepare_customer(request.customer_match)
            
            # Step 2: Validate and price products
            pricing_result = await self._prepare_products_and_pricing(
                request.product_matches, 
                customer_result['customer_id']
            )
            
            # Step 3: Create offer lines
            offer_lines = await self._create_offer_lines(
                pricing_result['products'], 
                request.product_matches
            )
            
            # Step 4: Calculate totals and create offer
            lemonsoft_offer = await self._create_lemonsoft_offer(
                customer_result,
                offer_lines,
                request
            )
            
            # Step 5: Create offer in Lemonsoft
            created_offer = await self.lemonsoft_client.create_offer(lemonsoft_offer)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create successful result
            result = OfferCreationResult(
                success=True,
                offer_id=created_offer.offer_id,
                offer_number=created_offer.offer_number,
                lemonsoft_offer=created_offer,
                customer_created=customer_result.get('was_created', False),
                product_issues=pricing_result.get('issues', []),
                total_amount=created_offer.total_amount,
                validation_warnings=pricing_result.get('warnings', []),
                processing_time_seconds=processing_time
            )
            
            # Log successful creation
            self.audit_logger.log_offer_created(
                created_offer.offer_id,
                customer_result['customer_id'],
                {
                    'offer_number': created_offer.offer_number,
                    'total_amount': created_offer.total_amount,
                    'line_count': len(created_offer.lines),
                    'processing_time': processing_time,
                    'product_issues': len(pricing_result.get('issues', [])),
                    'customer_created': customer_result.get('was_created', False)
                }
            )
            
            self.logger.info(
                f"Successfully created offer {created_offer.offer_number} (€{created_offer.total_amount:.2f})",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'offer_id': created_offer.offer_id,
                        'processing_time': processing_time
                    }
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.error(
                f"Failed to create offer: {e}",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'customer_id': request.customer_match.customer_id,
                        'processing_time': processing_time
                    }
                }
            )
            
            # Return failure result
            return OfferCreationResult(
                success=False,
                validation_warnings=[f"Offer creation failed: {str(e)}"],
                processing_time_seconds=processing_time
            )
    
    async def _prepare_customer(self, customer_match: CustomerMatch) -> Dict[str, Any]:
        """
        Prepare customer data for offer creation.
        
        Returns customer information and whether customer was created.
        """
        try:
            # First, try to get existing customer
            if customer_match.customer_id:
                existing_customer = await self.lemonsoft_client.get_customer(customer_match.customer_id)
                if existing_customer:
                    self.logger.debug(f"Found existing customer: {existing_customer.name}")
                    return {
                        'customer_id': existing_customer.customer_id,
                        'customer_data': existing_customer,
                        'was_created': False
                    }
            
            # Search by email if no direct ID match
            if customer_match.email:
                search_results = await self.lemonsoft_client.search_customers(
                    email=customer_match.email,
                    limit=1
                )
                
                if search_results:
                    customer = search_results[0]
                    self.logger.debug(f"Found customer by email: {customer.name}")
                    return {
                        'customer_id': customer.customer_id,
                        'customer_data': customer,
                        'was_created': False
                    }
            
            # No existing customer found, create new one
            self.logger.info(f"Creating new customer: {customer_match.customer_name}")
            
            customer_data = {
                'name': customer_match.customer_name,
                'contact_person': customer_match.contact_person or '',
                'email': customer_match.email or '',
                'phone': customer_match.phone or '',
                'address': customer_match.address or {},
                'payment_terms': 'Net 30',
                'currency': 'EUR'
            }
            
            # Add company-specific data from match details
            if customer_match.match_details:
                company_data = customer_match.match_details.get('customer_data', {})
                if company_data.get('business_id'):
                    customer_data['vat_number'] = company_data['business_id']
                if company_data.get('customer_group'):
                    customer_data['customer_group'] = company_data['customer_group']
            
            created_customer = await self.lemonsoft_client.create_customer(customer_data)
            
            self.logger.info(f"Created new customer: {created_customer.name} (ID: {created_customer.customer_id})")
            
            return {
                'customer_id': created_customer.customer_id,
                'customer_data': created_customer,
                'was_created': True
            }
            
        except Exception as e:
            self.logger.error(f"Customer preparation failed: {e}")
            raise ExternalServiceError(
                f"Failed to prepare customer data: {str(e)}",
                service="offer_creation",
                context={'customer_name': customer_match.customer_name}
            )
    
    async def _prepare_products_and_pricing(
        self, 
        product_matches: List[ProductMatch], 
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Validate products and retrieve pricing information.
        
        Returns product data, pricing, and any issues found.
        """
        products = []
        issues = []
        warnings = []
        
        for match in product_matches:
            try:
                # Skip unknown products (code 9000)
                if match.product_code == "9000":
                    issues.append({
                        'product_description': match.description,
                        'issue': 'unknown_product',
                        'message': 'Product requires manual identification',
                        'confidence': match.confidence_score
                    })
                    continue
                
                # Get product from Lemonsoft
                lemonsoft_product = await self.lemonsoft_client.get_product(match.product_code)
                
                if not lemonsoft_product:
                    # Product not found in Lemonsoft
                    issues.append({
                        'product_code': match.product_code,
                        'product_name': match.product_name,
                        'issue': 'product_not_found',
                        'message': f'Product {match.product_code} not found in Lemonsoft',
                        'confidence': match.confidence_score
                    })
                    continue
                
                # Get pricing for this customer and quantity
                pricing_info = await self.lemonsoft_client.get_product_pricing(
                    match.product_code,
                    customer_id,
                    match.quantity_requested
                )
                
                # Check stock availability
                if lemonsoft_product.available_quantity < match.quantity_requested:
                    warnings.append(
                        f"Product {match.product_code}: Requested {match.quantity_requested}, "
                        f"only {lemonsoft_product.available_quantity} available"
                    )
                
                # Add confidence warning for low-confidence matches
                if match.confidence_score < 0.7:
                    warnings.append(
                        f"Product {match.product_code}: Low confidence match ({match.confidence_score:.1%}) - "
                        f"please verify product selection"
                    )
                
                product_data = {
                    'match': match,
                    'lemonsoft_product': lemonsoft_product,
                    'pricing': pricing_info,
                    'unit_price': pricing_info.get('unitPrice', lemonsoft_product.unit_price),
                    'available_quantity': lemonsoft_product.available_quantity
                }
                
                products.append(product_data)
                
            except Exception as e:
                self.logger.warning(f"Failed to process product {match.product_code}: {e}")
                issues.append({
                    'product_code': match.product_code,
                    'product_name': match.product_name,
                    'issue': 'processing_error',
                    'message': f'Error processing product: {str(e)}',
                    'confidence': match.confidence_score
                })
        
        return {
            'products': products,
            'issues': issues,
            'warnings': warnings
        }
    
    async def _create_offer_lines(
        self, 
        product_data: List[Dict], 
        original_matches: List[ProductMatch]
    ) -> List[LemonsoftOfferLine]:
        """Create offer lines from product data and matches."""
        offer_lines = []
        
        for product_info in product_data:
            match = product_info['match']
            lemonsoft_product = product_info['lemonsoft_product']
            pricing = product_info['pricing']
            
            # Calculate line pricing
            unit_price = product_info['unit_price']
            quantity = match.quantity_requested
            line_total = unit_price * quantity
            
            # Apply any volume discounts from pricing
            discount_percent = pricing.get('discountPercent', 0.0)
            discount_amount = line_total * (discount_percent / 100)
            
            # Calculate VAT
            vat_rate = lemonsoft_product.vat_rate
            net_total = line_total - discount_amount
            vat_amount = net_total * (vat_rate / 100)
            
            # Create offer line
            offer_line = LemonsoftOfferLine(
                product_code=lemonsoft_product.product_code,
                product_name=lemonsoft_product.name,
                description=lemonsoft_product.description,
                quantity=quantity,
                unit=lemonsoft_product.unit,
                unit_price=unit_price,
                discount_percent=discount_percent,
                discount_amount=discount_amount,
                line_total=net_total,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                delivery_time=pricing.get('deliveryTime', ''),
                notes=self._create_line_notes(match, product_info)
            )
            
            offer_lines.append(offer_line)
        
        return offer_lines
    
    def _create_line_notes(self, match: ProductMatch, product_info: Dict) -> str:
        """Create notes for offer line based on match quality and details."""
        notes = []
        
        # Add confidence information for manual review
        if match.confidence_score < 0.8:
            notes.append(f"Auto-match confidence: {match.confidence_score:.1%}")
        
        # Add original search query if different from product name
        if match.search_query and match.search_query.lower() not in product_info['lemonsoft_product'].name.lower():
            notes.append(f"Requested: {match.search_query}")
        
        # Add match method information
        if match.match_method == "rag_similarity":
            notes.append("Found via AI similarity search")
        elif match.match_method == "agentic_search":
            notes.append("Found via intelligent search")
        
        # Add stock availability note
        available = product_info['available_quantity']
        if available < match.quantity_requested:
            notes.append(f"Stock: {available} available")
        
        return " | ".join(notes)
    
    async def _create_lemonsoft_offer(
        self,
        customer_result: Dict[str, Any],
        offer_lines: List[LemonsoftOfferLine],
        request: OfferCreationRequest
    ) -> LemonsoftOffer:
        """Create Lemonsoft offer object with all calculated data."""
        
        customer_data = customer_result['customer_data']
        
        # Calculate totals
        subtotal = sum(line.line_total for line in offer_lines)
        total_discount = sum(line.discount_amount for line in offer_lines)
        total_vat = sum(line.vat_amount for line in offer_lines)
        total_amount = subtotal + total_vat
        
        # Create offer
        offer = LemonsoftOffer(
            customer_id=customer_data.customer_id,
            customer_name=customer_data.name,
            contact_person=customer_data.contact_person,
            offer_date=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=request.valid_for_days),
            currency=request.currency,
            payment_terms=request.payment_terms or customer_data.payment_terms,
            delivery_terms=request.delivery_terms,
            reference=request.reference,
            notes=self._create_offer_notes(request),
            lines=offer_lines,
            subtotal=subtotal,
            total_discount=total_discount,
            vat_amount=total_vat,
            total_amount=total_amount,
            status="draft",
            created_by=self.settings.lemonsoft_user_id
        )
        
        return offer
    
    def _create_offer_notes(self, request: OfferCreationRequest) -> str:
        """Create offer-level notes."""
        notes = []
        
        # Add automation information
        notes.append("Automatically generated from email request")
        
        # Add email context
        if request.email_context.get('subject'):
            notes.append(f"Email subject: {request.email_context['subject']}")
        
        if request.email_context.get('date'):
            notes.append(f"Request date: {request.email_context['date']}")
        
        # Add special instructions
        if request.special_instructions:
            notes.append(f"Special instructions: {request.special_instructions}")
        
        # Add product matching summary
        unknown_products = len([m for m in request.product_matches if m.product_code == "9000"])
        if unknown_products > 0:
            notes.append(f"Note: {unknown_products} products require manual identification")
        
        low_confidence = len([m for m in request.product_matches if m.confidence_score < 0.7])
        if low_confidence > 0:
            notes.append(f"Note: {low_confidence} products have low confidence matches")
        
        return "\n".join(notes)
    
    async def close(self):
        """Close the offer creation service."""
        if self.lemonsoft_client:
            await self.lemonsoft_client.close()
            self.lemonsoft_client = None
        
        self.logger.info("Offer creation service closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of offer creation service."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        try:
            # Check Lemonsoft API connection
            await self.initialize()
            lemonsoft_health = await self.lemonsoft_client.health_check()
            health_status['components']['lemonsoft'] = lemonsoft_health['status']
            
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['components']['lemonsoft'] = f'unhealthy: {str(e)}'
        
        return health_status 