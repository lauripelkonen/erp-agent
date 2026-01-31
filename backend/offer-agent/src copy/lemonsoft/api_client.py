"""
Lemonsoft API Client
Comprehensive integration with Lemonsoft ERP system for offer creation and management.
Handles authentication, rate limiting, error handling, and all offer-related operations.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid
import hashlib

import httpx
from httpx import AsyncClient, HTTPStatusError, RequestError

from src.config.settings import get_settings
from src.config.constants import BusinessConstants, TechnicalConstants, LemonsoftConstants
from src.utils.logger import get_logger, get_audit_logger
from src.utils.exceptions import BaseOfferAutomationError, ValidationError
from src.utils.retry import retry_on_exception, EXTERNAL_API_RETRY_CONFIG


@dataclass
class LemonsoftCredentials:
    """Lemonsoft API credentials and configuration."""
    username: str
    password: str
    database: str
    api_key: str
    base_url: str
    user_id: str = ""


@dataclass
class LemonsoftCustomer:
    """Lemonsoft customer data structure."""
    customer_id: str
    customer_number: str
    name: str
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: Dict[str, str] = None
    payment_terms: str = "Net 30"
    currency: str = BusinessConstants.DEFAULT_CURRENCY
    price_list_id: str = ""
    customer_group: str = ""
    vat_number: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.address is None:
            self.address = {}


@dataclass
class LemonsoftProduct:
    """Lemonsoft product data structure."""
    product_id: str
    product_code: str
    name: str
    description: str = ""
    unit: str = BusinessConstants.DEFAULT_UNIT
    unit_price: float = BusinessConstants.DEFAULT_PRODUCT_PRICE
    vat_rate: float = BusinessConstants.DEFAULT_VAT_RATE
    product_group: str = ""
    stock_balance: float = 0.0
    reserved_quantity: float = 0.0
    available_quantity: float = 0.0
    supplier_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.supplier_info is None:
            self.supplier_info = {}
    
    @property
    def list_price(self) -> float:
        """Alias for unit_price to match calculator expectations."""
        return self.unit_price


@dataclass
class LemonsoftOfferLine:
    """Lemonsoft offer line item."""
    line_id: str = ""
    product_code: str = ""
    product_name: str = ""
    description: str = ""
    quantity: float = 1.0
    unit: str = BusinessConstants.DEFAULT_UNIT
    unit_price: float = BusinessConstants.DEFAULT_PRODUCT_PRICE
    discount_percent: float = BusinessConstants.DEFAULT_DISCOUNT_PERCENT
    discount_amount: float = BusinessConstants.DEFAULT_DISCOUNT_AMOUNT
    line_total: float = 0.0
    vat_rate: float = BusinessConstants.DEFAULT_VAT_RATE
    vat_amount: float = 0.0
    delivery_time: str = BusinessConstants.DEFAULT_DELIVERY_TIME
    notes: str = ""


@dataclass
class LemonsoftOffer:
    """Lemonsoft offer data structure."""
    offer_id: str = ""
    offer_number: str = ""
    customer_id: str = ""
    customer_name: str = ""
    contact_person: str = ""
    offer_date: datetime = None
    valid_until: datetime = None
    currency: str = BusinessConstants.DEFAULT_CURRENCY
    payment_terms: str = BusinessConstants.DEFAULT_PAYMENT_TERMS
    delivery_terms: str = ""
    reference: str = ""
    notes: str = ""
    lines: List[LemonsoftOfferLine] = None
    subtotal: float = 0.0
    total_discount: float = 0.0
    vat_amount: float = 0.0
    total_amount: float = 0.0
    status: str = "draft"  # draft, sent, accepted, rejected, expired
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.lines is None:
            self.lines = []
        if self.offer_date is None:
            self.offer_date = datetime.utcnow()
        if self.valid_until is None:
            self.valid_until = self.offer_date + timedelta(days=BusinessConstants.DEFAULT_OFFER_VALIDITY_DAYS)


class LemonsoftAPIError(BaseOfferAutomationError):
    """Specific error for Lemonsoft API issues."""
    
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None, **kwargs):
        # Build context with Lemonsoft-specific information
        context = kwargs.pop('context', {})
        context.update({
            'service_name': 'lemonsoft',
            'status_code': status_code,
            'response_data': response_data
        })
        
        # Call BaseOfferAutomationError directly with explicit parameters
        super().__init__(
            message=message,
            error_code="LEMONSOFT_API_ERROR",
            context=context,
            recovery_suggestions=[
                "Check Lemonsoft API connectivity and credentials",
                "Verify API endpoint availability",
                "Try again after a brief delay",
                "Check system logs for more details"
            ],
            **kwargs
        )
        self.status_code = status_code
        self.response_data = response_data or {}


class LemonsoftAPIClient:
    """
    Comprehensive Lemonsoft API client for offer creation and management.
    
    Provides:
    - Authentication and session management
    - Customer CRUD operations
    - Product information retrieval
    - Offer creation and management
    - Price calculation and discounting
    - Document generation triggers
    - Rate limiting and error handling
    """
    
    def __init__(self, credentials: LemonsoftCredentials = None):
        """
        Initialize Lemonsoft API client.
        
        Args:
            credentials: Lemonsoft API credentials, if None will load from settings
        """
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Set up credentials
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = LemonsoftCredentials(
                username=self.settings.lemonsoft_username,
                password=self.settings.lemonsoft_password,
                database=self.settings.lemonsoft_database,
                api_key=self.settings.lemonsoft_api_key,
                base_url=self.settings.lemonsoft_api_url
            )
        
        # HTTP client configuration
        self.client = None
        self.session_token = None
        self.session_expires_at = None
        
        # Rate limiting
        self.request_count = 0
        self.request_window_start = datetime.utcnow()
        self.max_requests_per_minute = TechnicalConstants.DEFAULT_REQUESTS_PER_MINUTE
        
        # Request timeout configuration - match working test settings
        self.timeout = httpx.Timeout(TechnicalConstants.HTTP_TIMEOUT, connect=TechnicalConstants.CONNECT_TIMEOUT)
        
        # SOAP client configuration
        self.soap_client = None  # zeep Client for SOAP
        self.soap_session_id: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def ensure_ready(self):
        """Ensure HTTP client exists and session token is valid (refresh if needed)."""
        # Initialize client if missing
        if self.client is None:
            await self.initialize()
            return
        # Ensure we have a valid/refreshing token
        await self._ensure_authenticated()

    async def initialize(self):
        """Initialize the API client and authenticate."""
        try:
            self.logger.info("Initializing Lemonsoft API client")
            
            # Debug credentials
            self.logger.debug(f"Base URL: {self.credentials.base_url}")
            self.logger.debug(f"Username configured: {bool(self.credentials.username)}")
            self.logger.debug(f"API Key configured: {bool(self.credentials.api_key)}")
            
            # Create HTTP client with exact same configuration as working test
            try:
                self.client = AsyncClient(
                    base_url=self.credentials.base_url,
                    timeout=self.timeout,
                    verify=False,  # Disable SSL verification for internal server
                    headers={
                        'User-Agent': 'OfferAutomation/1.0',
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                )
                self.logger.debug(f"AsyncClient created successfully: {self.client is not None}")
            except Exception as client_error:
                self.logger.error(f"Failed to create AsyncClient: {client_error}")
                raise
            
            # Verify client was created
            if self.client is None:
                raise Exception("AsyncClient creation returned None")
            
            # Authenticate and get session token
            try:
                await self._authenticate()
            except Exception as auth_error:
                self.logger.error(f"Authentication failed: {auth_error}")
                # Clean up client on auth failure
                if self.client:
                    await self.client.aclose()
                    self.client = None
                raise
            
            self.logger.info("Lemonsoft API client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Lemonsoft API client: {e}")
            import traceback
            self.logger.error(f"Initialization traceback: {traceback.format_exc()}")
            raise LemonsoftAPIError(
                f"Initialization failed: {str(e)}",
                response_data={'credentials_configured': bool(self.credentials.api_key)}
            )
    
    async def close(self):
        """Close the API client and clean up resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
        
        # Close database client if exists
        if hasattr(self, '_db_client'):
            self._db_client.close()
            delattr(self, '_db_client')
        
        self.session_token = None
        self.session_expires_at = None
        self.logger.info("Lemonsoft API client closed")
    
    @retry_on_exception(config=EXTERNAL_API_RETRY_CONFIG)
    async def _authenticate(self):
        """Authenticate with Lemonsoft API and obtain session token."""
        try:
            self.logger.debug("Authenticating with Lemonsoft API")
            
            # Check that client is available
            if self.client is None:
                raise Exception("HTTP client is None - cannot authenticate")
            
            # Prepare authentication request using correct Lemonsoft format
            auth_data = {
                'UserName': self.credentials.username,
                'Password': self.credentials.password,
                'Database': self.credentials.database,
                'ApiKey': self.credentials.api_key
            }
            
            self.logger.debug("Making authentication POST request")
            response = await self.client.post(LemonsoftConstants.AUTH_ENDPOINT, json=auth_data)
            
            # Don't raise for status immediately - check the response first
            auth_result = response.json()
            
            # Check if authentication was successful using the exact same logic as working test
            if auth_result.get('code') != LemonsoftConstants.SUCCESS_CODE or auth_result.get('message') != LemonsoftConstants.SUCCESS_MESSAGE:
                raise LemonsoftAPIError(
                    f"Authentication failed: {auth_result.get('message', 'Unknown error')}",
                    status_code=response.status_code,
                    response_data=auth_result
                )
            
            # Extract session information - use get() to handle missing keys
            session_id = auth_result.get('session_id')
            if not session_id:
                raise LemonsoftAPIError(
                    "Authentication response missing session_id",
                    status_code=response.status_code,
                    response_data=auth_result
                )
            
            # Lemonsoft sessions typically last 24 hours
            self.session_expires_at = datetime.utcnow() + timedelta(hours=TechnicalConstants.SESSION_VALIDITY_HOURS)
            
            # Store session token for subsequent requests
            self.session_token = session_id
            
            # Update client headers with session ID (this is the key fix!)
            self.client.headers.update({
                'Session-Id': session_id
            })
            
            self.logger.info(f"Successfully authenticated with Lemonsoft API, session: {session_id[:8]}...")
            
        except HTTPStatusError as e:
            error_msg = f"Authentication HTTP error: {e.response.status_code}"
            self.logger.error(error_msg)
            raise LemonsoftAPIError(error_msg, status_code=e.response.status_code)
        
        except RequestError as e:
            error_msg = f"Authentication request error: {str(e)}"
            self.logger.error(error_msg)
            raise LemonsoftAPIError(message=error_msg)
        
        except Exception as e:
            error_msg = f"Authentication unexpected error: {str(e)}"
            self.logger.error(error_msg)
            raise LemonsoftAPIError(message=error_msg)
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid session token."""
        if not self.session_token:
            await self._authenticate()
            return
        
        # Check if session is about to expire (refresh 5 minutes early)
        if self.session_expires_at and datetime.utcnow() >= (self.session_expires_at - timedelta(minutes=TechnicalConstants.SESSION_REFRESH_BUFFER_MINUTES)):
            self.logger.info("Session token expiring soon, re-authenticating")
            await self._authenticate()
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        current_time = datetime.utcnow()
        
        # Reset counter if window has passed
        if (current_time - self.request_window_start).total_seconds() >= 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check rate limit
        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.request_window_start).total_seconds()
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.request_window_start = datetime.utcnow()
        
        self.request_count += 1
    
    @retry_on_exception(config=EXTERNAL_API_RETRY_CONFIG)
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None,
        params: Dict = None
    ) -> Dict:
        """Make authenticated API request with error handling."""
        await self._ensure_authenticated()
        await self._rate_limit_check()
        
        try:
            self.logger.debug(f"Making {method} request to {endpoint}")
            
            request_kwargs = {
                'method': method,
                'url': endpoint,
                'params': params
            }
            
            if data:
                request_kwargs['json'] = data
            
            response = await self.client.request(**request_kwargs)
            
            # Parse response first, then check for errors
            try:
                result = response.json()
            except Exception:
                # If JSON parsing fails, check HTTP status
                response.raise_for_status()
                # Return empty dict if no JSON content
                return {}
            
            # For non-2xx status codes, still raise an error
            if not (200 <= response.status_code < 300):
                raise LemonsoftAPIError(
                    message=f"HTTP error {response.status_code}: {result.get('message', 'Unknown error')}",
                    status_code=response.status_code,
                    response_data=result
                )
            
            # Check for API-level errors in specific format
            # Some Lemonsoft endpoints use 'success', others use 'code'
            if 'success' in result and not result.get('success', True):
                raise LemonsoftAPIError(
                    message=f"API error: {result.get('message', 'Unknown error')}",
                    status_code=response.status_code,
                    response_data=result
                )
            elif 'code' in result and result.get('code') != 200:
                raise LemonsoftAPIError(
                    message=f"API error: {result.get('message', 'Unknown error')}",
                    status_code=response.status_code,
                    response_data=result
                )
            
            return result
            
        except HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} for {method} {endpoint}"
            self.logger.error(error_msg)
            
            try:
                error_data = e.response.json()
            except:
                error_data = {'text': e.response.text}
            
            raise LemonsoftAPIError(message=error_msg, status_code=e.response.status_code, response_data=error_data)
        
        except RequestError as e:
            error_msg = f"Request error for {method} {endpoint}: {str(e)}"
            self.logger.error(error_msg)
            raise LemonsoftAPIError(message=error_msg)
    
    # HTTP method shortcuts for convenience
    async def get(self, endpoint: str, params: Dict = None) -> 'httpx.Response':
        """Make GET request and return httpx Response object."""
        await self._ensure_authenticated()
        await self._rate_limit_check()
        
        try:
            self.logger.debug(f"Making GET request to {endpoint}")
            response = await self.client.get(endpoint, params=params)
            return response
        except Exception as e:
            self.logger.error(f"GET request failed for {endpoint}: {e}")
            raise
    
    async def post(self, endpoint: str, json: Dict = None, data: Dict = None) -> 'httpx.Response':
        """Make POST request and return httpx Response object."""
        await self._ensure_authenticated()
        await self._rate_limit_check()
        
        try:
            self.logger.debug(f"Making POST request to {endpoint}")
            response = await self.client.post(endpoint, json=json, data=data)
            return response
        except Exception as e:
            self.logger.error(f"POST request failed for {endpoint}: {e}")
            raise
    
    async def put(self, endpoint: str, json: Dict = None, data: Dict = None) -> 'httpx.Response':
        """Make PUT request and return httpx Response object."""
        await self._ensure_authenticated()
        await self._rate_limit_check()
        
        try:
            self.logger.debug(f"Making PUT request to {endpoint}")
            response = await self.client.put(endpoint, json=json, data=data)
            return response
        except Exception as e:
            self.logger.error(f"PUT request failed for {endpoint}: {e}")
            raise
    
    # Customer Management Methods
    
    async def get_customer(self, customer_id: str) -> Optional[LemonsoftCustomer]:
        """
        Retrieve customer information by ID.
        
        Args:
            customer_id: Lemonsoft customer ID
            
        Returns:
            Customer data or None if not found
        """
        try:
            result = await self._make_request('GET', f'/api/customers/{customer_id}')
            
            if result.get('data'):
                customer_data = result['data']
                return self._parse_customer_data(customer_data)
            
            return None
            
        except LemonsoftAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def search_customers(
        self, 
        query: str = None,
        email: str = None,
        customer_number: str = None,
        limit: int = 50
    ) -> List[LemonsoftCustomer]:
        """
        Search for customers using various criteria.
        
        Args:
            query: General search query
            email: Customer email address
            customer_number: Customer number
            limit: Maximum number of results
            
        Returns:
            List of matching customers
        """
        params = {'limit': limit}
        
        if query:
            params['search'] = query
        if email:
            params['email'] = email
        if customer_number:
            params['customerNumber'] = customer_number
        
        result = await self._make_request('GET', '/api/customers', params=params)
        
        customers = []
        for customer_data in result.get('data', []):
            customer = self._parse_customer_data(customer_data)
            customers.append(customer)
        
        return customers
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> LemonsoftCustomer:
        """
        Create a new customer in Lemonsoft.
        
        Args:
            customer_data: Customer information
            
        Returns:
            Created customer data
        """
        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if not customer_data.get(field):
                raise ValidationError(f"Required field '{field}' is missing")
        
        # Prepare API request data
        api_data = {
            'name': customer_data['name'],
            'contactPerson': customer_data.get('contact_person', ''),
            'email': customer_data.get('email', ''),
            'phone': customer_data.get('phone', ''),
            'address': customer_data.get('address', {}),
            'paymentTerms': customer_data.get('payment_terms', 'Net 30'),
            'currency': customer_data.get('currency', 'EUR'),
            'priceListId': customer_data.get('price_list_id', ''),
            'customerGroup': customer_data.get('customer_group', ''),
            'vatNumber': customer_data.get('vat_number', '')
        }
        
        result = await self._make_request('POST', '/api/customers', data=api_data)
        
        self.audit_logger.log_customer_created(
            result['data']['customerId'],
            customer_data['name'],
            {'email': customer_data.get('email', '')}
        )
        
        return self._parse_customer_data(result['data'])
    
    # Product Management Methods
    
    async def get_product(self, product_code: str) -> Optional[LemonsoftProduct]:
        """
        Retrieve product information by code.
        Uses search endpoint since direct lookup requires internal ID.
        
        Args:
            product_code: Product code (SKU)
            
        Returns:
            Product data or None if not found
        """
        try:
            # Use search endpoint to find product by SKU/code
            result = await self._make_request('GET', '/api/products', params={'filter.sku': product_code})
            
            if result.get('results'):
                # When filtering by a specific SKU, we expect one result.
                return self._parse_product_data(result['results'][0])
            
            return None
            
        except LemonsoftAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def search_products(
        self, 
        query: str = None,
        product_group: str = None,
        limit: int = 100
    ) -> List[LemonsoftProduct]:
        """
        Search for products.
        
        Args:
            query: Product search query (SKU)
            product_group: Product group filter
            limit: Maximum results
            
        Returns:
            List of matching products
        """
        params = {'limit': limit}
        
        if query:
            params['filter.sku'] = query
        if product_group:
            params['filter.group_code'] = product_group
        
        result = await self._make_request('GET', '/api/products', params=params)
        
        products = []
        for product_data in result.get('results', []):
            product = self._parse_product_data(product_data)
            products.append(product)
        
        return products
    
    async def get_product_pricing(
        self, 
        product_code: str, 
        customer_id: str = None,
        quantity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Get pricing information for a product.
        
        Args:
            product_code: Product code
            customer_id: Customer ID for customer-specific pricing
            quantity: Quantity for volume pricing
            
        Returns:
            Pricing information
        """
        params = {'quantity': quantity}
        
        if customer_id:
            params['customerId'] = customer_id
        
        result = await self._make_request(
            'GET', 
            f'/api/products/{product_code}/pricing', 
            params=params
        )
        
        return result.get('data', {})
    
    # Offer Management Methods
    
    async def create_offer(self, offer_data: LemonsoftOffer) -> LemonsoftOffer:
        """
        Create a new offer in Lemonsoft.
        
        Args:
            offer_data: Offer information
            
        Returns:
            Created offer with assigned ID and number
        """
        try:
            # Prepare API request data
            api_data = {
                'customerId': offer_data.customer_id,
                'customerName': offer_data.customer_name,
                'contactPerson': offer_data.contact_person,
                'offerDate': offer_data.offer_date.isoformat(),
                'validUntil': offer_data.valid_until.isoformat(),
                'currency': offer_data.currency,
                'paymentTerms': offer_data.payment_terms,
                'deliveryTerms': offer_data.delivery_terms,
                'reference': offer_data.reference,
                'notes': offer_data.notes,
                'lines': [],
                'createdBy': self.credentials.username
            }
            
            # Add offer lines
            for line in offer_data.lines:
                line_data = {
                    'productCode': line.product_code,
                    'productName': line.product_name,
                    'description': line.description,
                    'quantity': line.quantity,
                    'unit': line.unit,
                    'unitPrice': line.unit_price,
                    'discountPercent': line.discount_percent,
                    'discountAmount': line.discount_amount,
                    'vatRate': line.vat_rate,
                    'deliveryTime': line.delivery_time,
                    'notes': line.notes
                }
                api_data['lines'].append(line_data)
            
            result = await self._make_request('POST', '/api/offers', data=api_data)
            
            created_offer = self._parse_offer_data(result['data'])
            
            self.audit_logger.log_offer_created(
                created_offer.offer_id,
                created_offer.customer_id,
                {
                    'offer_number': created_offer.offer_number,
                    'total_amount': created_offer.total_amount,
                    'line_count': len(created_offer.lines)
                }
            )
            
            self.logger.info(f"Created offer {created_offer.offer_number} for customer {created_offer.customer_name}")
            
            return created_offer
            
        except Exception as e:
            self.logger.error(f"Failed to create offer: {e}")
            raise LemonsoftAPIError(message=f"Offer creation failed: {str(e)}")
    
    async def get_offer(self, offer_id: str) -> Optional[LemonsoftOffer]:
        """
        Retrieve offer by ID.
        
        Args:
            offer_id: Offer ID
            
        Returns:
            Offer data or None if not found
        """
        try:
            result = await self._make_request('GET', f'/api/offers/{offer_id}')
            
            if result.get('data'):
                return self._parse_offer_data(result['data'])
            
            return None
            
        except LemonsoftAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def update_offer_status(self, offer_id: str, status: str, notes: str = "") -> bool:
        """
        Update offer status.
        
        Args:
            offer_id: Offer ID
            status: New status (draft, sent, accepted, rejected, expired)
            notes: Optional status change notes
            
        Returns:
            True if successful
        """
        valid_statuses = ['draft', 'sent', 'accepted', 'rejected', 'expired']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")
        
        update_data = {
            'status': status,
            'notes': notes,
            'updatedBy': self.credentials.username
        }
        
        result = await self._make_request('PUT', f'/api/offers/{offer_id}/status', data=update_data)
        
        self.audit_logger.log_offer_status_changed(offer_id, status, {'notes': notes})
        
        return result.get('success', False)
    
    async def send_offer(self, offer_id: str, recipient_email: str, message: str = "") -> bool:
        """
        Send offer to customer via email.
        
        Args:
            offer_id: Offer ID
            recipient_email: Customer email address
            message: Optional email message
            
        Returns:
            True if sent successfully
        """
        send_data = {
            'recipientEmail': recipient_email,
            'message': message,
            'sentBy': self.credentials.username
        }
        
        result = await self._make_request('POST', f'/api/offers/{offer_id}/send', data=send_data)
        
        self.audit_logger.log_offer_sent(offer_id, recipient_email, {'message': message})
        
        return result.get('success', False)
    
    async def generate_offer_pdf(self, offer_id: str) -> Dict[str, Any]:
        """
        Generate PDF document for offer.
        
        Args:
            offer_id: Offer ID
            
        Returns:
            PDF generation result with download URL
        """
        result = await self._make_request('POST', f'/api/offers/{offer_id}/pdf')
        
        return result.get('data', {})
    
    # Utility Methods
    
    def _parse_customer_data(self, data: Dict) -> LemonsoftCustomer:
        """Parse customer data from API response."""
        return LemonsoftCustomer(
            customer_id=data.get('customerId', ''),
            customer_number=data.get('customerNumber', ''),
            name=data.get('name', ''),
            contact_person=data.get('contactPerson', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            address=data.get('address', {}),
            payment_terms=data.get('paymentTerms', 'Net 30'),
            currency=data.get('currency', 'EUR'),
            price_list_id=data.get('priceListId', ''),
            customer_group=data.get('customerGroup', ''),
            vat_number=data.get('vatNumber', ''),
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt'))
        )
    
    def _parse_product_data(self, data: Dict) -> LemonsoftProduct:
        """Parse product data from API response."""
        # Handle Lemonsoft's actual response format
        product_id = str(data.get('id', ''))
        product_code = data.get('sku', data.get('productCode', ''))
        name = data.get('name', '')
        description = data.get('extra_name', data.get('description', ''))
        unit = data.get('stock_unit', data.get('unit', BusinessConstants.DEFAULT_UNIT.lower()))
        
        # Price handling - Lemonsoft has different price fields
        unit_price = float(data.get('sales_price_taxless', data.get('price', data.get('unitPrice', 0.0))))
        if unit_price == 0.0:
            # Fallback to other price fields
            unit_price = float(data.get('sales_price_taxful', 0.0))
        
        # VAT rate from taxrate_code or default
        taxrate_code = data.get('taxrate_code', str(BusinessConstants.DEFAULT_VAT_RATE))
        try:
            vat_rate = float(taxrate_code) if taxrate_code else BusinessConstants.DEFAULT_VAT_RATE
        except (ValueError, TypeError):
            vat_rate = BusinessConstants.DEFAULT_VAT_RATE
        
        # Product group
        product_group = data.get('group_code', data.get('productGroup', ''))
        
        # Stock information
        stocks = data.get('stocks', [])
        stock_balance = 0.0
        reserved_quantity = 0.0
        available_quantity = 0.0
        
        if stocks and isinstance(stocks, list):
            # Sum up stock from all locations
            for stock in stocks:
                if isinstance(stock, dict):
                    stock_balance += float(stock.get('quantity', 0.0))
                    reserved_quantity += float(stock.get('reserved', 0.0))
            available_quantity = stock_balance - reserved_quantity
        
        # Supplier info
        suppliers = data.get('suppliers', [])
        supplier_info = {}
        if suppliers and isinstance(suppliers, list) and suppliers:
            supplier_info = suppliers[0] if isinstance(suppliers[0], dict) else {}
        
        return LemonsoftProduct(
            product_id=product_id,
            product_code=product_code,
            name=name,
            description=description,
            unit=unit,
            unit_price=unit_price,
            vat_rate=vat_rate,
            product_group=product_group,
            stock_balance=stock_balance,
            reserved_quantity=reserved_quantity,
            available_quantity=available_quantity,
            supplier_info=supplier_info
        )
    
    def _parse_offer_data(self, data: Dict) -> LemonsoftOffer:
        """Parse offer data from API response."""
        offer = LemonsoftOffer(
            offer_id=data.get('offerId', ''),
            offer_number=data.get('offerNumber', ''),
            customer_id=data.get('customerId', ''),
            customer_name=data.get('customerName', ''),
            contact_person=data.get('contactPerson', ''),
            offer_date=self._parse_datetime(data.get('offerDate')),
            valid_until=self._parse_datetime(data.get('validUntil')),
            currency=data.get('currency', 'EUR'),
            payment_terms=data.get('paymentTerms', 'Net 30'),
            delivery_terms=data.get('deliveryTerms', ''),
            reference=data.get('reference', ''),
            notes=data.get('notes', ''),
            subtotal=float(data.get('subtotal', 0.0)),
            total_discount=float(data.get('totalDiscount', 0.0)),
            vat_amount=float(data.get('vatAmount', 0.0)),
            total_amount=float(data.get('totalAmount', 0.0)),
            status=data.get('status', 'draft'),
            created_by=data.get('createdBy', ''),
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt'))
        )
        
        # Parse offer lines
        for line_data in data.get('lines', []):
            line = LemonsoftOfferLine(
                line_id=line_data.get('lineId', ''),
                product_code=line_data.get('productCode', ''),
                product_name=line_data.get('productName', ''),
                description=line_data.get('description', ''),
                quantity=float(line_data.get('quantity', 1.0)),
                unit=line_data.get('unit', BusinessConstants.DEFAULT_UNIT.lower()),
                unit_price=float(line_data.get('unitPrice', 0.0)),
                discount_percent=float(line_data.get('discountPercent', 0.0)),
                discount_amount=float(line_data.get('discountAmount', 0.0)),
                line_total=float(line_data.get('lineTotal', 0.0)),
                vat_rate=float(line_data.get('vatRate', BusinessConstants.DEFAULT_VAT_RATE)),
                vat_amount=float(line_data.get('vatAmount', 0.0)),
                delivery_time=line_data.get('deliveryTime', ''),
                notes=line_data.get('notes', '')
            )
            offer.lines.append(line)
        
        return offer
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string from API response."""
        if not date_str:
            return None
        
        try:
            # Handle ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Handle date-only format
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            self.logger.warning(f"Failed to parse datetime: {date_str}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of Lemonsoft API connection.
        
        Returns:
            Health status information
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'api_version': None,
            'authenticated': False,
            'rate_limit_status': {
                'requests_this_minute': self.request_count,
                'max_requests_per_minute': self.max_requests_per_minute
            }
        }
        
        try:
            # Test authentication
            if not self.client:
                await self.initialize()
            
            # Test API connectivity
            result = await self._make_request('GET', '/api/health')
            
            health_status['authenticated'] = True
            health_status['api_version'] = result.get('data', {}).get('version')
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"Health check failed: {e}")
        
        return health_status

    @retry_on_exception(config=EXTERNAL_API_RETRY_CONFIG)
    async def execute_query(self, query: str, params: List = None) -> List[Dict]:
        """
        Execute a direct SQL query against the Lemonsoft database.
        Used for complex pricing and discount queries.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of query result dictionaries
        """
        await self._ensure_authenticated()
        
        # Try direct database connection first (most reliable)
        try:
            if not hasattr(self, '_db_client'):
                from .database_connection import create_database_client
                self._db_client = create_database_client()
            
            self.logger.debug(f"Attempting direct database query: {query[:100]}...")
            results = await self._db_client.execute_query(query, params)
            self.logger.debug("Direct database query succeeded")
            return results
                
        except Exception as e:
            self.logger.debug(f"Direct database query failed: {e}, falling back to SOAP")

        # Direct DB failed – fallback to SOAP ExecuteSQL
        try:
            self.logger.info("Using SOAP ExecuteSQL for query execution")
            # Ensure SOAP client is initialized before running in executor
            await self._ensure_soap_authenticated()
            
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(None, self._soap_execute_sql, query, params)
            return rows
        except Exception as soap_err:
            self.logger.error(f"SOAP ExecuteSQL failed: {soap_err}")
            return []