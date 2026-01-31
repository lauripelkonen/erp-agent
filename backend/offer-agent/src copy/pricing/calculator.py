"""
Pricing Calculator
Calculates pricing for offers using Lemonsoft database queries for customer-specific 
discounts, product group pricing, and sophisticated pricelist integration.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import math

from src.config.settings import get_settings
from src.config.constants import BusinessConstants, TechnicalConstants
from src.utils.logger import get_logger
from src.utils.exceptions import ValidationError
from src.product_matching.matcher_class import ProductMatch
from src.lemonsoft.api_client import LemonsoftAPIClient
from src.lemonsoft.database_connection import LemonsoftDatabaseClient
import os
import httpx
import json


@dataclass
class PricingRule:
    """Pricing rule definition."""
    rule_type: str  # volume, customer_group, product_group, total_value
    condition: Dict[str, Any]
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    priority: int = 0
    description: str = ""


@dataclass
class LineItemPricing:
    """Pricing information for a single line item."""
    product_code: str
    quantity: float
    unit_price: float
    list_price: float
    product_name: str = ""
    extra_name: str = ""
    unit: str = BusinessConstants.DEFAULT_UNIT
    discount_percent: float = BusinessConstants.DEFAULT_DISCOUNT_PERCENT
    discount_amount: float = BusinessConstants.DEFAULT_DISCOUNT_AMOUNT
    net_price: float = BusinessConstants.DEFAULT_PRODUCT_PRICE
    line_total: float = 0.0
    vat_rate: float = BusinessConstants.DEFAULT_VAT_RATE
    vat_amount: float = 0.0
    applied_rules: List[str] = None
    
    def __post_init__(self):
        if self.applied_rules is None:
            self.applied_rules = []


@dataclass
class OfferPricing:
    """Complete pricing information for an offer."""
    line_items: List[LineItemPricing]
    subtotal: float = 0.0
    total_discount_amount: float = 0.0
    total_discount_percent: float = 0.0
    net_total: float = 0.0
    vat_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = BusinessConstants.DEFAULT_CURRENCY
    pricing_date: datetime = None
    applied_global_rules: List[str] = None
    
    def __post_init__(self):
        if self.pricing_date is None:
            self.pricing_date = datetime.utcnow()
        if self.applied_global_rules is None:
            self.applied_global_rules = []


class PricingCalculator:
    """
    Advanced pricing calculator with Lemonsoft integration for:
    - PRIMARY Customer Product Group Discounts (customer_product_group_pricelist)
    - Product-specific pricing (pricelist_products)
    - SOPHISTICATED Customer Group Discounts (pricelist integration)
    - HYBRID General Product Group Discounts (cross-pricelist validation)
    - OVH list pricing (fallback)
    
    Modes:
    - Direct database mode: Uses LemonsoftDatabaseClient for SQL queries
    - Docker/Function App mode: Routes SQL queries through Azure Function App proxy
    - API-only mode: Uses only lemonsoft_client.get_product (fallback)
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Check deployment mode
        self.deployment_mode = os.getenv('DEPLOYMENT_MODE', 'direct').lower()
        self.logger.info(f"Pricing calculator deployment mode: {self.deployment_mode}")
        
        # SQL proxy configuration for Docker mode
        if self.deployment_mode == 'docker':
            self.sql_proxy_url = os.getenv('SQL_PROXY_URL', 'https://xxxx.azurewebsites.net')
            self.sql_proxy_api_key = os.getenv('SQL_PROXY_API_KEY', '')
            self.azure_function_key = os.getenv('AZURE_FUNCTION_KEY', '')
            self.logger.info(f"SQL proxy configured: {self.sql_proxy_url}")
        
        # Default pricing rules
        self.pricing_rules = self._initialize_default_pricing_rules()
        
        # Lemonsoft client for pricing data
        self.lemonsoft_client: Optional[LemonsoftAPIClient] = None
        
        # Direct database client for SQL queries (only in direct mode)
        self.database_client = None
        
        # HTTP client for Function App proxy (only in docker mode)
        self.http_client = None
    
    def _initialize_default_pricing_rules(self) -> List[PricingRule]:
        """Initialize default pricing rules."""
        return []
    
    async def initialize(self):
        """Initialize the pricing calculator with appropriate connection mode."""
        if self.lemonsoft_client is None:
            self.lemonsoft_client = LemonsoftAPIClient()
        
        # Try to initialize the API client, but continue if it fails (fallback to API-only mode)
        try:
            await self.lemonsoft_client.initialize()
            print(f"DEBUG: After initialization - lemonsoft_client: {self.lemonsoft_client is not None}")
            if self.lemonsoft_client:
                print(f"DEBUG: After initialization - HTTP client: {self.lemonsoft_client.client is not None}")
                if self.lemonsoft_client.client:
                    print(f"DEBUG: After initialization - HTTP client type: {type(self.lemonsoft_client.client)}")
                else:
                    print("WARNING: HTTP client is None after initialization - will use fallback pricing")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Lemonsoft API client: {e}")
            print(f"WARNING: Lemonsoft client initialization failed: {e}")
            self.logger.info("Will continue with fallback pricing modes only")
            # Don't raise - continue with API-only mode
        
        if self.deployment_mode == 'docker':
            # Initialize HTTP client for Function App proxy
            try:
                if self.http_client is None:
                    self.http_client = httpx.AsyncClient(timeout=30.0)
                
                # Test Function App connection
                await self._test_function_app_connection()
                connection_type = "API + Function App Proxy"
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize Function App proxy: {e}")
                self.logger.info("Will use API-only pricing (product info from lemonsoft_client)")
                connection_type = "API-only (Function App failed)"
                
        else:
            # Direct database mode
            try:
                if self.database_client is None:
                    self.database_client = LemonsoftDatabaseClient()
                
                # Test database connection
                test_result = await self.database_client.test_connection()
                if test_result.get('status') != 'success':
                    self.logger.warning(f"Database connection test failed: {test_result.get('error')}")
                    self.database_client = None
                else:
                    self.logger.info("Database client initialized and tested successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize database client: {e}")
                self.logger.info("Will use API-only pricing (product info from lemonsoft_client)")
                self.database_client = None
            
            connection_type = "API + Database" if self.database_client else "API-only"
        
        self.logger.info(f"Pricing calculator initialized with {connection_type} clients")
    
    async def _test_function_app_connection(self):
        """Test connection to the Function App SQL proxy."""
        try:
            headers = {
                'x-functions-key': self.azure_function_key,  # Azure Function authentication
                'Content-Type': 'application/json'
            }
            
            # Get database name from environment variable for health check
            database_name = os.getenv('DATABASE_NAME', 'LemonDB1')
            
            response = await self.http_client.get(
                f"{self.sql_proxy_url}/api/health?database={database_name}",
                headers=headers
            )
            
            if response.status_code == 200:
                self.logger.info("Function App SQL proxy connection successful")
            else:
                raise Exception(f"Function App health check failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Function App connection test failed: {e}")
            raise
    
    async def _execute_sql_query(self, query: str, params: list = None) -> list:
        """
        Execute SQL query using the appropriate method based on deployment mode.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        if self.deployment_mode == 'docker' and self.http_client:
            return await self._execute_sql_via_function_app(query, params)
        elif self.database_client:
            # execute_query is synchronous, use execute_query_async for async operation
            return await self.database_client.execute_query_async(query, params)
        else:
            raise Exception("No SQL execution method available")
    
    async def _execute_sql_via_function_app(self, query: str, params: list = None) -> list:
        """Execute SQL query via Azure Function App proxy."""
        try:
            headers = {
                'x-functions-key': self.azure_function_key,  # Azure Function authentication
                'X-API-Key': self.sql_proxy_api_key,  # Our custom API key for query validation
                'Content-Type': 'application/json'
            }
            
            # Get database name from environment variable
            database_name = os.getenv('DATABASE_NAME', 'LemonDB1')
            
            payload = {
                'query': query,
                'params': params or [],
                'database': database_name
            }
            
            self.logger.debug(f"Executing SQL via Function App: {query[:100]}...")
            
            # Debug: Print request details
            url = f"{self.sql_proxy_url}/api/query"
            print(f"DEBUG HTTP Request:")
            print(f"  URL: {url}")
            print(f"  Headers: {headers}")
            print(f"  Payload: {payload}")
            
            response = await self.http_client.post(url, headers=headers, json=payload)
            
            # Debug: Log response
            print(f"DEBUG Function App Response:")
            print(f"  Status: {response.status_code}")
            print(f"  Body: {response.text[:500] if response.text else 'No body'}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', [])
                    self.logger.debug(f"Function App query successful: {result.get('row_count', 0)} rows")
                    print(f"  Rows returned: {len(data)}")
                    if data:
                        print(f"  First row: {data[0]}")
                    return data
                else:
                    raise Exception(f"Function App query failed: {result.get('error')}")
            else:
                error_text = response.text if response.text else f"HTTP {response.status_code}"
                raise Exception(f"Function App request failed: {error_text}")
                
        except Exception as e:
            self.logger.error(f"SQL query via Function App failed: {e}")
            raise
    
    async def calculate_offer_pricing(
        self,
        product_matches: List[ProductMatch],
        customer_id: str = None,
        pricing_context: Dict[str, Any] = None
    ) -> OfferPricing:
        """
        Calculate complete pricing for an offer.
        
        Args:
            product_matches: List of matched products
            customer_id: Customer ID for customer-specific pricing
            pricing_context: Additional context for pricing rules
            
        Returns:
            Complete offer pricing information
        """
        await self.initialize()
        
        if pricing_context is None:
            pricing_context = {}
        
        try:
            self.logger.info(f"Calculating pricing for {len(product_matches)} products")
            
            # Get customer information for pricing
            customer_data = None
            if customer_id:
                customer_data = await self.lemonsoft_client.get_customer(customer_id)
            
            # Calculate line item pricing
            line_items = []
            for match in product_matches:
                if match.product_code == "9000":  # Handle unknown products with historical pricing
                    # Check if this product has been matched before in the 9000 filtered products
                    historical_price = await self._get_historical_9000_price(match.product_name)
                    
                    if historical_price is not None:
                        # Use historical price from previous matches
                        line_pricing = LineItemPricing(
                            product_code=match.product_code,
                            product_name=match.product_name,
                            extra_name="",  # 9000 products don't have extra_name
                            unit=BusinessConstants.DEFAULT_UNIT,  # Default unit for 9000 products
                            quantity=match.quantity_requested,
                            list_price=historical_price,
                            unit_price=historical_price,
                            net_price=historical_price,
                            discount_percent=0.0,
                            discount_amount=0.0,
                            line_total=historical_price * match.quantity_requested,
                            vat_rate=BusinessConstants.DEFAULT_VAT_RATE,  # Standard VAT rate
                            vat_amount=(historical_price * match.quantity_requested) * 0.255,
                            applied_rules=[f"Historical price from previous 9000 matches (€{historical_price:.2f})"]
                        )
                        self.logger.info(f"💰 Using historical price €{historical_price:.2f} for 9000 product: {match.product_name}")
                    else:
                        # No historical price found - use 0€ for manual pricing
                        line_pricing = LineItemPricing(
                            product_code=match.product_code,
                            product_name=match.product_name,
                            extra_name="",  # 9000 products don't have extra_name
                            unit=BusinessConstants.DEFAULT_UNIT,  # Default unit for 9000 products
                            quantity=match.quantity_requested,
                            list_price=0.0,
                            unit_price=0.0,
                            net_price=0.0,
                            discount_percent=0.0,
                            discount_amount=0.0,
                            line_total=0.0,
                            vat_rate=BusinessConstants.DEFAULT_VAT_RATE,  # Standard VAT rate
                            vat_amount=0.0,
                            applied_rules=["Manual pricing required - new product code 9000"]
                        )
                        self.logger.info(f"🆕 New 9000 product - using €0.00 for manual pricing: {match.product_name}")
                    
                    line_items.append(line_pricing)
                else:
                    line_pricing = await self._calculate_line_pricing(
                        match, customer_id, customer_data, pricing_context
                    )
                    line_items.append(line_pricing)
            
            # Calculate offer totals
            offer_pricing = self._calculate_offer_totals(line_items, customer_data, pricing_context)
            
            # Apply global pricing rules
            offer_pricing = await self._apply_global_pricing_rules(
                offer_pricing, customer_data, pricing_context
            )
            
            self.logger.info(
                f"Pricing calculated: €{offer_pricing.total_amount:.2f} "
                f"({offer_pricing.total_discount_percent:.1f}% discount)"
            )
            
            return offer_pricing
            
        except Exception as e:
            self.logger.error(f"Pricing calculation failed: {e}")
            raise ValidationError(f"Failed to calculate pricing: {str(e)}")
    
    async def _calculate_line_pricing(
        self,
        match: ProductMatch,
        customer_id: str,
        customer_data: Any,
        pricing_context: Dict[str, Any]
    ) -> LineItemPricing:
        """
        Calculate pricing for a single line item using Lemonsoft pricing hierarchy.
        
        Falls back to API-only pricing (product info from lemonsoft_client.get_product)
        when database connectivity is not available.
        """
        
        # Get pricing using Lemonsoft hierarchy
        try:
            pricing_info = await self._get_lemonsoft_pricing(
                match.product_code,
                customer_id,
                match.quantity_requested,
                customer_data
            )
            
            # Get product info for VAT rate and other details
            product_info = await self.lemonsoft_client.get_product(match.product_code)
            
            list_price = pricing_info.get('list_price', match.price)
            unit_price = pricing_info.get('unit_price', match.price)
            vat_rate = product_info.vat_rate if product_info else BusinessConstants.DEFAULT_VAT_RATE
            
            # Extract Lemonsoft discount information
            lemonsoft_discount_percent = pricing_info.get('discount_percent', 0.0)
            lemonsoft_applied_rule = pricing_info.get('applied_rule', '')
            
            self.logger.info(
                f"Lemonsoft pricing for {match.product_code}: "
                f"List: €{list_price:.2f}, Unit: €{unit_price:.2f}, "
                f"Discount: {lemonsoft_discount_percent:.1f}% ({lemonsoft_applied_rule})"
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to get Lemonsoft pricing for {match.product_code}: {e}")
            # Fallback to match pricing
            list_price = match.price
            unit_price = match.price
            vat_rate = BusinessConstants.DEFAULT_VAT_RATE
            lemonsoft_discount_percent = BusinessConstants.DEFAULT_DISCOUNT_PERCENT
            lemonsoft_applied_rule = "Fallback pricing"
        
        # Extract net price from pricing info if available
        net_price_from_db = pricing_info.get('net_price', None)
        
        # Get product extra_name and default_unit from database
        extra_name = await self._get_product_extra_name(match.product_code)
        default_unit = await self._get_product_default_unit(match.product_code)
        
        # Create initial line pricing with correct structure
        line_pricing = LineItemPricing(
            product_code=match.product_code,
            product_name=getattr(match, 'product_name', ''),  # Get product name from match
            extra_name=extra_name,  # Extra name from product_description2
            unit=default_unit,  # Default unit from product_units
            quantity=match.quantity_requested,
            unit_price=list_price,  # OVH list price
            list_price=list_price,  # OVH list price
            net_price=net_price_from_db if net_price_from_db is not None else list_price,  # From product_exp_price
            vat_rate=vat_rate,
            discount_percent=lemonsoft_discount_percent,  # Customer discount percentage
            applied_rules=[lemonsoft_applied_rule] if lemonsoft_applied_rule else []
        )
        
        # Calculate line total: unit_price with customer discount applied × quantity
        discounted_unit_price = line_pricing.unit_price * (1 - line_pricing.discount_percent / 100)
        line_pricing.line_total = discounted_unit_price * line_pricing.quantity
        line_pricing.vat_amount = line_pricing.line_total * (line_pricing.vat_rate / 100)
        
        return line_pricing
    

    

    
    def _calculate_offer_totals(
        self,
        line_items: List[LineItemPricing],
        customer_data: Any,
        pricing_context: Dict[str, Any]
    ) -> OfferPricing:
        """Calculate offer-level totals."""
        
        subtotal = sum(item.line_total for item in line_items)
        total_discount_amount = sum(
            item.unit_price * item.quantity * (item.discount_percent / 100) + item.discount_amount * item.quantity
            for item in line_items
        )
        vat_amount = sum(item.vat_amount for item in line_items)
        
        total_discount_percent = (total_discount_amount / (subtotal + total_discount_amount)) * 100 if (subtotal + total_discount_amount) > 0 else 0
        
        return OfferPricing(
            line_items=line_items,
            subtotal=subtotal,
            total_discount_amount=total_discount_amount,
            total_discount_percent=total_discount_percent,
            net_total=subtotal,
            vat_amount=vat_amount,
            total_amount=subtotal + vat_amount,
            currency=pricing_context.get("currency", BusinessConstants.DEFAULT_CURRENCY)
        )
    
    async def _apply_global_pricing_rules(
        self,
        offer_pricing: OfferPricing,
        customer_data: Any,
        pricing_context: Dict[str, Any]
    ) -> OfferPricing:
        """Apply global (offer-level) pricing rules."""
        
        # All pricing comes from Lemonsoft database queries
        # No global discount rules needed - individual product discounts are already optimal
        offer_pricing.applied_global_rules = []
        
        return offer_pricing
    
    def add_pricing_rule(self, rule: PricingRule):
        """Add a custom pricing rule."""
        self.pricing_rules.append(rule)
        self.logger.info(f"Added pricing rule: {rule.description}")
    
    def remove_pricing_rule(self, rule_description: str):
        """Remove a pricing rule by description."""
        self.pricing_rules = [r for r in self.pricing_rules if r.description != rule_description]
        self.logger.info(f"Removed pricing rule: {rule_description}")
    
    async def get_price_estimate(
        self,
        product_code: str,
        quantity: float,
        customer_id: str = None
    ) -> Dict[str, Any]:
        """Get a quick price estimate for a single product using Lemonsoft hierarchy."""
        await self.initialize()
        
        try:
            # Get Lemonsoft pricing using the full hierarchy
            pricing_info = await self._get_lemonsoft_pricing(
                product_code, customer_id, quantity
            )
            
            unit_price = pricing_info.get('unit_price', 0.0)
            list_price = pricing_info.get('list_price', 0.0)
            discount_percent = pricing_info.get('discount_percent', 0.0)
            applied_rule = pricing_info.get('applied_rule', 'List price')
            
            line_total = unit_price * quantity
            
            return {
                'product_code': product_code,
                'quantity': quantity,
                'unit_price': unit_price,
                'list_price': list_price,
                'discount_percent': discount_percent,
                'line_total': line_total,
                'applied_rule': applied_rule,
                'currency': 'EUR'
            }
            
        except Exception as e:
            self.logger.error(f"Price estimate failed for {product_code}: {e}")
            return {
                'product_code': product_code,
                'error': str(e)
            }
    
    async def close(self):
        """Close the pricing calculator."""
        if self.lemonsoft_client:
            await self.lemonsoft_client.close()
        if self.http_client:
            await self.http_client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for pricing calculator."""
        
        # Test SQL connection based on deployment mode
        sql_status = 'not_configured'
        sql_error = None
        
        if self.deployment_mode == 'docker' and self.http_client:
            try:
                await self._test_function_app_connection()
                sql_status = 'success'
            except Exception as e:
                sql_status = 'failed'
                sql_error = str(e)
        elif self.database_client:
            try:
                db_test = await self.database_client.test_connection()
                sql_status = db_test.get('status', 'unknown')
                if sql_status != 'success':
                    sql_error = db_test.get('error')
            except Exception as e:
                sql_status = 'failed'
                sql_error = str(e)
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'deployment_mode': self.deployment_mode,
            'pricing_rules_count': len(self.pricing_rules),
            'lemonsoft_api_connected': self.lemonsoft_client is not None,
            'sql_available': self.database_client is not None or (self.deployment_mode == 'docker' and self.http_client is not None),
            'sql_status': sql_status,
            'sql_error': sql_error,
            'sql_proxy_url': self.sql_proxy_url if self.deployment_mode == 'docker' else None,
            'pricing_mode': 'full' if (self.database_client or (self.deployment_mode == 'docker' and self.http_client)) else 'api_only'
        }
    
    async def _get_lemonsoft_pricing(
        self,
        product_code: str,
        customer_id: str,
        quantity: float,
        customer_data: Any = None
    ) -> Dict[str, Any]:
        """
        Get Lemonsoft pricing following the hierarchy:
        0. Customer Product Group Discount (customer_product_group_pricelist) - MOST POWERFUL
        1. Product-specific pricing (v_pricelist_products)
        2. Customer-specific product group pricing (customer_product_group_pricelist) - LEGACY
        3. General product group pricing (v_pricelist_productgroups)
        4. Use OVH (list price)
        
        If database client is not available, falls back to API-only pricing (product info only).
        """
        self.logger.info(f"Getting Lemonsoft pricing for product {product_code}, customer {customer_id}")
        
        # Ensure the lemonsoft client is properly initialized
        if not self.lemonsoft_client or not self.lemonsoft_client.client:
            self.logger.warning(f"Lemonsoft client not properly initialized, attempting to initialize...")
            try:
                await self.initialize()
                if not self.lemonsoft_client or not self.lemonsoft_client.client:
                    raise Exception("Failed to initialize lemonsoft client properly")
            except Exception as e:
                self.logger.error(f"Failed to initialize lemonsoft client: {e}")
                # Return fallback pricing
                return {
                    "unit_price": 0.0,
                    "list_price": 0.0,
                    "discount_type": "fallback",
                    "net_price": 0.0,
                    "discount_percent": 0.0,
                    "applied_rule": "Fallback pricing (client initialization failed)"
                }
        
        try:
            # Get product information first (for product group and OVH price)
            product_info = await self.lemonsoft_client.get_product(product_code)
            if not product_info:
                self.logger.warning(f"Product {product_code} not found in Lemonsoft")
                return {"unit_price": 0.0, "list_price": 0.0, "discount_type": "none", "net_price": 0.0}

            ovh_price = getattr(product_info, 'list_price', 0.0)
            product_group = getattr(product_info, 'product_group', None)

            self.logger.info(f"Product {product_code}: OVH price €{ovh_price}, product group {product_group}")

            # If no SQL execution method is available, use API-only pricing (net resolved at end)
            sql_available = (self.database_client is not None) or (self.deployment_mode == 'docker' and self.http_client is not None)

            # Prepare base response and decide pricing path without returning yet
            pricing_decision: Dict[str, Any] = {
                "unit_price": ovh_price,
                "list_price": ovh_price,
                "discount_type": "api_only" if not sql_available else "none",
                "discount_percent": 0.0,
                "applied_rule": "API-only pricing (List price from product info)" if not sql_available else "List price (OVH)"
            }

            if sql_available:
                # Get customer information for proper customer number lookup
                customer_info = await self._get_customer_info(customer_id)
                customer_number = None

                if customer_info:
                    customer_number = customer_info.get('customer_number') or customer_info.get('number')
                    self.logger.info(f"Customer {customer_id} resolved to customer number: {customer_number}")
                else:
                    self.logger.warning(f"Could not resolve customer {customer_id} to customer number")

                # 1. Check product-specific pricing (v_pricelist_products)
                if customer_number:
                    self.logger.info(f"Checking product-specific pricing for {product_code}")
                    product_specific_price = await self._get_product_specific_pricing(
                        product_code, customer_id, customer_number
                    )
                    if product_specific_price:
                        self.logger.info(f"Found product-specific pricing for {product_code}: {product_specific_price}")
                        pricing_decision = {
                            "unit_price": product_specific_price.get("unit_price", ovh_price),
                            "list_price": product_specific_price.get("list_price", ovh_price),
                            "discount_type": product_specific_price.get("discount_type", "product_specific"),
                            "discount_percent": product_specific_price.get("discount_percent", 0.0),
                            "applied_rule": product_specific_price.get("applied_rule", "Product-specific pricing")
                        }
                    else:
                        self.logger.info(f"No product-specific pricing found for {product_code}")

                # 2. Check customer-specific product group pricing (PRIMARY)
                if customer_info and product_group and pricing_decision.get("discount_type") in ("none", "api_only"):
                    internal_customer_id = customer_info.get('id')
                    if internal_customer_id:
                        self.logger.info(f"Checking PRIMARY customer product group discount for customer ID {internal_customer_id} (number: {customer_number}), group {product_group}")
                        primary_customer_group_discount = await self._get_primary_customer_product_group_discount(
                            internal_customer_id, product_group
                        )
                        if primary_customer_group_discount:
                            discount_percent = float(primary_customer_group_discount['discount_percent'])
                            self.logger.info(
                                f"Found PRIMARY customer product group discount for {product_code}: "
                                f"{discount_percent}% discount on OVH €{ovh_price:.2f}"
                            )
                            pricing_decision = {
                                "unit_price": ovh_price,
                                "list_price": ovh_price,
                                "discount_type": "primary_customer_product_group",
                                "discount_percent": discount_percent,
                                "applied_rule": f"PRIMARY Customer Product Group Discount {discount_percent}% for group {product_group}"
                            }
                        else:
                            self.logger.info(f"No PRIMARY customer product group discount found for customer {internal_customer_id}, group {product_group}")

                # 3. Check general product group pricing
                if customer_id and product_group and pricing_decision.get("discount_type") in ("none", "api_only"):
                    self.logger.info(f"Checking general group discount for group {product_group}")
                    general_group_discount = await self._get_general_product_group_discount(
                        customer_id, product_group
                    )
                    if general_group_discount:
                        general_discount_percent = float(general_group_discount['discount_percent'])
                        discounted_price = ovh_price * (1 - general_discount_percent / 100)
                        self.logger.info(
                            f"Found general group discount for {product_code}: "
                            f"{general_discount_percent}% = €{discounted_price}"
                        )
                        pricing_decision = {
                            "unit_price": discounted_price,
                            "list_price": ovh_price,
                            "discount_type": "general_group",
                            "discount_percent": general_discount_percent,
                            "applied_rule": f"General group discount for group {product_group}"
                        }
                    else:
                        self.logger.info(f"No general group discount found for group {product_group}")

            # Resolve net price exactly once at the end
            try:
                product_exp_price = await self._get_product_exp_price(product_code)
            except Exception as e:
                self.logger.warning(f"_get_product_exp_price failed for {product_code}: {e}")
                product_exp_price = None

            if product_exp_price is None:
                # Fallback to product.product_price, then OVH if missing
                fallback_net = getattr(product_info, 'product_price', None)
                if fallback_net is None:
                    fallback_net = ovh_price
                product_exp_price = fallback_net

            pricing_decision["net_price"] = product_exp_price

            return pricing_decision
        
        except Exception as e:
            self.logger.error(f"Failed to get Lemonsoft pricing for {product_code}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Don't try to use lemonsoft client again if it failed - just return fallback
            self.logger.info(f"Using fallback pricing due to lemonsoft client error")
            return {
                "unit_price": 0.0,
                "list_price": 0.0,
                "discount_type": "error_fallback",
                "discount_percent": 0.0,
                "applied_rule": f"Error fallback pricing (Lemonsoft client error: {str(e)})",
                "error": str(e)
            }
        
    async def _get_customer_pricelist_ids(self, customer_number, product_group=None):
        """
        Get all pricelist IDs that apply to a customer using SQL queries as requested by boss.
        Returns both customer-specific product group pricelists and tick pricelists
        Primary method: Customer's own product group pricelists
        Fallback method: Tick pricelists (täppähinnastot)
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping customer pricelist lookup")
            return []
        
        try:
            self.logger.info(f"Getting pricelists for customer number {customer_number} using SQL queries")
            
            # Query 1: Customer's own product group pricelists (PRIMARY)
            query1 = """
            SELECT DISTINCT pc.pricelist_id, p.pricelist_description, p.pricelist_type
            FROM [dbo].[pricelist_products] as pp 
            JOIN [dbo].[pricelist_customers] as pc ON (pp.pricelist_id = pc.pricelist_id) 
            JOIN [dbo].[customers] as c ON (pc.pricelist_customer_number = c.customer_number)  
            JOIN [dbo].[pricelists] as p ON p.pricelist_id = pc.pricelist_id
            WHERE pp.pricelist_product_group = 1 
            AND c.customer_number = ?
            AND EXISTS (
                SELECT 1
                FROM [dbo].[customer_product_group_pricelist] as cpgp 
                WHERE pp.pricelist_product_code = CAST(cpgp.group_id as varchar(50)) 
                AND cpgp.customer_id = c.customer_id
            )
            """
            
            self.logger.debug(f"Executing SQL query 1 for customer {customer_number}")
            result1 = await self._execute_sql_query(query1, [customer_number])
            
            if result1:
                pricelist_ids = [row['pricelist_id'] for row in result1]
                self.logger.info(
                    f"Found {len(pricelist_ids)} customer-specific product group pricelists for {customer_number}: {pricelist_ids}"
                )
                return pricelist_ids
            
            # Query 2: Tick pricelists (täppähinnastot) - FALLBACK
            self.logger.info(f"No customer-specific pricelists found for {customer_number}, trying tick pricelists")
            
            query2 = """
            SELECT DISTINCT pc.pricelist_id, p.pricelist_description, p.pricelist_type
            FROM [dbo].[pricelist_products] as pp 
            JOIN [dbo].[pricelist_customers] as pc ON (pp.pricelist_id = pc.pricelist_id) 
            JOIN [dbo].[customers] as c ON (pc.pricelist_customer_number = c.customer_number)  
            JOIN [dbo].[pricelists] as p ON p.pricelist_id = pc.pricelist_id
            WHERE pp.pricelist_product_group = 1 
            AND c.customer_number = ?
            AND EXISTS (
                SELECT pp2.pricelist_product_code  
                FROM [dbo].[pricelist_products] as pp2 
                JOIN [dbo].[pricelist_customers] as pc2 ON (pp2.pricelist_id = pc2.pricelist_id) 
                WHERE pp2.pricelist_product_code = pp.pricelist_product_code 
                AND pp.pricelist_id <> pp2.pricelist_id 
                AND pc2.pricelist_customer_number = c.customer_number
                AND pp2.pricelist_product_group = 1 
            )
            """
            
            self.logger.debug(f"Executing SQL query 2 for customer {customer_number}")
            result2 = await self._execute_sql_query(query2, [customer_number])
            
            if result2:
                pricelist_ids = [row['pricelist_id'] for row in result2]
                self.logger.info(
                    f"Found {len(pricelist_ids)} tick pricelists for {customer_number}: {pricelist_ids}"
                )
                return pricelist_ids
            
            self.logger.warning(f"No pricelists found for customer {customer_number}")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get customer pricelist IDs for {customer_number}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    async def _get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer information using the correct API approach from integration test.
        This method accepts either customer ID or customer number and finds the customer.
        Returns customer data including both id and number fields.
        """
        # Debug: Check client state at start of method
        print(f"DEBUG: _get_customer_info - lemonsoft_client: {self.lemonsoft_client is not None}")
        if self.lemonsoft_client:
            print(f"DEBUG: _get_customer_info - HTTP client: {self.lemonsoft_client.client is not None}")
        else:
            print("DEBUG: _get_customer_info - lemonsoft_client is None!")
        
        if not self.lemonsoft_client or not self.lemonsoft_client.client:
            print(f"DEBUG: _get_customer_info - Cannot proceed: client={self.lemonsoft_client is not None}, http_client={self.lemonsoft_client.client is not None if self.lemonsoft_client else 'N/A'}")
            return None
        
        try:
            self.logger.info(f"Looking up customer info for: {customer_id}")
            
            # Use the correct filter parameter for customer number search
            search_methods = [
                # Primary method: filter by customer number
                {'name': 'filter.customer_number', 'params': {'filter.customer_number': customer_id, 'limit': 10}},
                # Fallback method: generic search
                {'name': 'search', 'params': {'search': customer_id, 'limit': 10}},
            ]
            
            for method in search_methods:
                try:
                    self.logger.debug(f"Trying customer lookup {method['name']}: {method['params']}")
                    
                    # Use the client directly without context manager to avoid closing it
                    response = await self.lemonsoft_client.get('/api/customers', params=method['params'])
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats from integration test
                        if isinstance(data, list):
                            customers = data
                        elif isinstance(data, dict):
                            customers = data.get('results', data.get('data', data.get('customers', [])))
                        else:
                            customers = []
                        
                        if customers:
                            # First try exact matches by ID or number
                            for customer in customers:
                                if str(customer.get('id')) == str(customer_id) or str(customer.get('number')) == str(customer_id):
                                    self.logger.info(
                                        f"Found exact match: "
                                        f"{customer.get('name')} (ID: {customer.get('id')}, Number: {customer.get('number')})"
                                    )
                                    return customer
                            
                            # If no exact match but we have results, use the first one
                            # (search by customer number "101" should return LVI-NORDIC OY as first result)
                            customer = customers[0]
                            self.logger.info(
                                f"Found customer via search: "
                                f"{customer.get('name')} (ID: {customer.get('id')}, Number: {customer.get('number')})"
                            )
                            return customer
                                
                except Exception as e:
                    self.logger.debug(f"Customer lookup {method['name']} failed: {e}")
                    continue
            
            # Try direct customer lookup by ID as final fallback
            try:
                self.logger.debug(f"Trying direct customer lookup: /api/customers/{customer_id}")
                response = await self.lemonsoft_client.client.get(f'/api/customers/{customer_id}')
                
                if response.status_code == 200:
                    customer = response.json()
                    self.logger.info(
                        f"Found customer via direct lookup: "
                        f"{customer.get('name')} (ID: {customer.get('id')}, Number: {customer.get('number')})"
                    )
                    return customer
                    
            except Exception as e:
                self.logger.debug(f"Direct customer lookup failed: {e}")
            
            self.logger.warning(f"Customer {customer_id} not found with any method")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get customer info for {customer_id}: {e}")
            return None
    
    async def _get_product_specific_pricing(
        self,
        product_code: str,
        customer_id: str,
        customer_number: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get product-specific pricing from v_pricelist_products using customer's pricelist IDs.
        Returns discount or fixed price based on the pricelist.
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping product-specific pricing")
            return None
        
        try:
            self.logger.info(f"Getting product-specific pricing for {product_code}, customer {customer_id}")
            
            # Use provided customer_number or try to get it from customer_id
            if not customer_number:
                customer_info = await self._get_customer_info(customer_id)
                if not customer_info:
                    self.logger.warning(f"Customer {customer_id} not found")
                    return None
                customer_number = customer_info.get('customer_number') or customer_info.get('number')
            
            if not customer_number:
                self.logger.warning(f"Could not determine customer number for customer {customer_id}")
                return None
            
            self.logger.info(f"Using customer number {customer_number} for pricelist lookup")
            
            # Get customer's pricelist IDs
            pricelist_ids = await self._get_customer_pricelist_ids(customer_number)
            
            if not pricelist_ids:
                self.logger.info(f"No pricelists found for customer {customer_number}")
                return None
            
            # Query v_pricelist_products using customer's pricelist IDs with SQL
            placeholders = ','.join(['?'] * len(pricelist_ids))
            query = f"""
            SELECT 
                vpp.pricelist_id,
                p.product_id,
                p.product_code,
                CASE WHEN vpp.pricelist_product_discount > 0 THEN 'percent' ELSE 'fixedprice' END as discount_type,
                CAST((CASE WHEN vpp.pricelist_product_discount > 0 THEN vpp.pricelist_product_discount ELSE vpp.pricelist_product_price END) AS DECIMAL(12,4)) as discount_value
            FROM v_pricelist_products as vpp
            JOIN products as p ON p.product_code = vpp.pricelist_product_code
            WHERE vpp.pricelist_id IN ({placeholders})
            AND p.product_code = ?
            AND vpp.pricelist_product_group = 0
            ORDER BY vpp.pricelist_id DESC
            """
            
            params = pricelist_ids + [product_code]
            self.logger.debug(f"Executing SQL query for product pricing: {product_code} in pricelists {pricelist_ids}")
            result = await self._execute_sql_query(query, params)
            
            if result:
                pricing_data = result[0]
                self.logger.info(
                    f"Found product-specific pricing for {product_code} in pricelist {pricing_data['pricelist_id']}: "
                    f"{pricing_data['discount_type']} = {pricing_data['discount_value']}"
                )
                
                # Get product OVH price and net price from product_pricing
                product_info = await self.lemonsoft_client.get_product(product_code)
                ovh_price = getattr(product_info, 'list_price', 0.0)
                
                # Get net price from product_pricing table
                product_exp_price = await self._get_product_exp_price(product_code)
                if product_exp_price is None:
                    # Fallback to product.product_price
                    product_exp_price = getattr(product_info, 'product_price', 0.0) if product_info else 0.0
                
                if pricing_data['discount_type'] == 'percent':
                    return {
                        "unit_price": ovh_price,  # OVH list price
                        "list_price": ovh_price,
                        "net_price": product_exp_price,  # From product_pricing.product_exp_price
                        "discount_type": "product_specific_percent",
                        "discount_percent": pricing_data['discount_value'],
                        "applied_rule": f"Product-specific discount {pricing_data['discount_value']}% (Pricelist {pricing_data['pricelist_id']})"
                    }
                else:
                    # Fixed price
                    return {
                        "unit_price": ovh_price,  # OVH list price
                        "list_price": ovh_price,
                        "net_price": product_exp_price,  # From product_pricing.product_exp_price
                        "discount_type": "product_specific_fixed",
                        "discount_percent": 0.0,
                        "applied_rule": f"Product-specific fixed price €{pricing_data['discount_value']} (Pricelist {pricing_data['pricelist_id']})"
                    }
            
            self.logger.info(f"No product-specific pricing found for {product_code} in customer pricelists {pricelist_ids}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get product-specific pricing for {product_code}: {e}")
            return None
    
    async def _get_customer_product_group_discount(
        self,
        customer_id: str,
        product_group: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get customer-specific product group discount using sophisticated pricelist-customer integration.
        This query combines customer_product_group_pricelist with pricelist_products for rich context.
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping customer product group discount")
            return None
        
        try:
            # Get customer information to get customer_number
            customer_info = await self._get_customer_info(customer_id)
            if not customer_info:
                self.logger.warning(f"Could not get customer info for {customer_id}")
                return None
            
            customer_number = customer_info.get('customer_number') or customer_info.get('number')
            if not customer_number:
                self.logger.warning(f"Could not determine customer number for customer {customer_id}")
                return None
            
            self.logger.info(f"Checking sophisticated customer product group discount for customer {customer_number}, group {product_group}")
            
            # Sophisticated query that links customer_product_group_pricelist with pricelist system
            query = """
            SELECT 
                pp.pricelist_product_code as tuoteryhma, 
                c.customer_number as asiakasnro, 
                c.customer_name1 as nimi, 
                p.pricelist_description as hinnasto, 
                CAST(pp.pricelist_product_discount AS DECIMAL(12,4)) as alepros, 
                CAST(pp.pricelist_product_discount2 AS DECIMAL(12,4)) as alepros2
            FROM [dbo].[pricelist_products] as pp 
            JOIN [dbo].[pricelist_customers] as pc ON (pp.pricelist_id = pc.pricelist_id) 
            JOIN [dbo].[customers] as c ON (pc.pricelist_customer_number = c.customer_number)  
            JOIN [dbo].[pricelists] p ON p.pricelist_id = pc.pricelist_id
            WHERE pp.pricelist_product_group = 1 
            AND c.customer_number = ?
            AND pp.pricelist_product_code = ?
            AND EXISTS (
                SELECT CAST(cpgp.group_id as varchar) as tuoteryhma
                FROM [dbo].[customer_product_group_pricelist] as cpgp 
                WHERE pp.pricelist_product_code = CAST(cpgp.group_id as varchar) 
                AND cpgp.customer_id = c.customer_id
            )
            ORDER BY pp.pricelist_product_discount DESC
            """
            
            self.logger.debug(f"Executing sophisticated customer group discount query: customer {customer_number}, group {product_group}")
            # Ensure product_group is clean integer string without spaces
            clean_product_group = str(product_group).replace(' ', '').strip()
            result = await self._execute_sql_query(query, [customer_number, clean_product_group])
            
            if result:
                discount_data = result[0]
                primary_discount = float(discount_data['alepros'])
                secondary_discount = float(discount_data['alepros2']) if discount_data['alepros2'] else 0.0
                
                self.logger.info(f"✅ SOPHISTICATED customer group discount: {primary_discount}% (secondary: {secondary_discount}%)")
                self.logger.info(f"  Customer: {discount_data['asiakasnro']} ({discount_data['nimi']})")
                self.logger.info(f"  Pricelist: {discount_data['hinnasto']}")
                self.logger.info(f"  Product Group: {discount_data['tuoteryhma']}")
                
                return {
                    "discount_percent": primary_discount,
                    "secondary_discount_percent": secondary_discount,
                    "group_id": discount_data['tuoteryhma'],
                    "customer_number": discount_data['asiakasnro'],
                    "customer_name": discount_data['nimi'],
                    "pricelist_description": discount_data['hinnasto'],
                    "query_type": "sophisticated_customer_group"
                }
            
            self.logger.info(f"No sophisticated customer group discount found for customer {customer_number}, group {product_group}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get sophisticated customer group discount for customer {customer_id}, group {product_group}: {e}")
            return None
    
    async def _get_general_product_group_discount(
        self,
        customer_id: str,
        product_group: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get general product group discount using hybrid approach:
        1. First try sophisticated query (cross-pricelist validation)
        2. Fall back to simple query if no sophisticated results
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping general product group discount")
            return None
        
        try:
            # Get customer information to get customer_number
            customer_info = await self._get_customer_info(customer_id)
            if not customer_info:
                self.logger.warning(f"Could not get customer info for {customer_id}")
                return None
            
            customer_number = customer_info.get('customer_number') or customer_info.get('number')
            if not customer_number:
                self.logger.warning(f"Could not determine customer number for customer {customer_id}")
                return None
            
            self.logger.info(f"Checking general product group discount for customer {customer_number}, group {product_group}")
            
            # STEP 1: Try sophisticated query with cross-pricelist validation
            # Use TRY_CAST to handle malformed data gracefully
            sophisticated_query = """
            SELECT 
                pp.pricelist_product_code as tuoteryhma, 
                c.customer_number as asiakasnro, 
                c.customer_name1 as nimi, 
                p.pricelist_description as hinnasto, 
                CAST(pp.pricelist_product_discount AS DECIMAL(12,4)) as alepros, 
                CAST(pp.pricelist_product_discount2 AS DECIMAL(12,4)) as alepros2,
                'sophisticated' as query_type
            FROM [dbo].[pricelist_products] as pp 
            JOIN [dbo].[pricelist_customers] as pc ON (pp.pricelist_id = pc.pricelist_id) 
            JOIN [dbo].[customers] as c ON (pc.pricelist_customer_number = c.customer_number)  
            JOIN [dbo].[pricelists] p ON p.pricelist_id = pc.pricelist_id
            WHERE pp.pricelist_product_group = 1 
            AND c.customer_number = ?
            AND pp.pricelist_product_code = ?
            AND pp.pricelist_product_discount > 0
            AND EXISTS (
                SELECT pp2.pricelist_product_code  
                FROM [dbo].[pricelist_products] as pp2 
                JOIN [dbo].[pricelist_customers] as pc2 ON (pp2.pricelist_id = pc2.pricelist_id) 
                WHERE pp2.pricelist_product_code = pp.pricelist_product_code 
                AND pp.pricelist_id <> pp2.pricelist_id 
                AND pc2.pricelist_customer_number = c.customer_number
                AND pp2.pricelist_product_group = 1 
                AND ISNUMERIC(REPLACE(pp2.pricelist_product_code, ' ', '')) = 1
                AND LEN(REPLACE(pp2.pricelist_product_code, ' ', '')) > 0
            )
            ORDER BY pp.pricelist_product_discount DESC
            """
            
            self.logger.debug(f"Trying sophisticated general group discount query for customer {customer_number}, product_group {product_group}")
            # Ensure product_group is clean integer string without spaces
            clean_product_group = str(product_group).replace(' ', '').strip()
            result = await self._execute_sql_query(sophisticated_query, [customer_number, clean_product_group])
            
            if result:
                discount_data = result[0]
                primary_discount = float(discount_data['alepros'])
                secondary_discount = float(discount_data['alepros2']) if discount_data['alepros2'] else 0.0
                
                self.logger.info(f"✅ SOPHISTICATED general group discount: {primary_discount}% (secondary: {secondary_discount}%)")
                self.logger.info(f"  Customer: {discount_data['asiakasnro']} ({discount_data['nimi']})")
                self.logger.info(f"  Pricelist: {discount_data['hinnasto']}")
                self.logger.info(f"  Cross-pricelist validated product group: {discount_data['tuoteryhma']}")
                
                return {
                    "discount_percent": primary_discount,
                    "secondary_discount_percent": secondary_discount,
                    "group_id": discount_data['tuoteryhma'],
                    "customer_number": discount_data['asiakasnro'],
                    "customer_name": discount_data['nimi'],
                    "pricelist_description": discount_data['hinnasto'],
                    "query_type": "sophisticated"
                }
            
            # STEP 2: Fall back to simple query without cross-pricelist validation
            self.logger.info(f"No sophisticated discount found, trying simple general discount query")
            
            # Ensure product_group is clean integer string without spaces (same as above)
            clean_product_group = str(product_group).replace(' ', '').strip()
            
            simple_query = """
            SELECT TOP 1
                pp.pricelist_product_code as tuoteryhma, 
                c.customer_number as asiakasnro, 
                c.customer_name1 as nimi, 
                p.pricelist_description as hinnasto, 
                CAST(pp.pricelist_product_discount AS DECIMAL(12,4)) as alepros, 
                CAST(pp.pricelist_product_discount2 AS DECIMAL(12,4)) as alepros2,
                'simple' as query_type
            FROM [dbo].[pricelist_products] as pp 
            JOIN [dbo].[pricelist_customers] as pc ON (pp.pricelist_id = pc.pricelist_id) 
            JOIN [dbo].[customers] as c ON (pc.pricelist_customer_number = c.customer_number)  
            JOIN [dbo].[pricelists] p ON p.pricelist_id = pc.pricelist_id
            WHERE pp.pricelist_product_group = 1 
            AND c.customer_number = ?
            AND pp.pricelist_product_code = ?
            AND pp.pricelist_product_discount > 0
            ORDER BY pp.pricelist_product_discount DESC
            """
            
            simple_result = await self._execute_sql_query(simple_query, [customer_number, clean_product_group])
            
            if simple_result:
                discount_data = simple_result[0]
                primary_discount = float(discount_data['alepros'])
                secondary_discount = float(discount_data['alepros2']) if discount_data['alepros2'] else 0.0
                
                self.logger.info(f"✅ SIMPLE general group discount: {primary_discount}% (secondary: {secondary_discount}%)")
                self.logger.info(f"  Customer: {discount_data['asiakasnro']} ({discount_data['nimi']})")
                self.logger.info(f"  Pricelist: {discount_data['hinnasto']}")
                self.logger.info(f"  Product Group: {discount_data['tuoteryhma']}")
                
                return {
                    "discount_percent": primary_discount,
                    "secondary_discount_percent": secondary_discount,
                    "group_id": discount_data['tuoteryhma'],
                    "customer_number": discount_data['asiakasnro'],
                    "customer_name": discount_data['nimi'],
                    "pricelist_description": discount_data['hinnasto'],
                    "query_type": "simple"
                }
            
            self.logger.info(f"No general group discount found for customer {customer_number}, group {product_group}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get general group discount for customer {customer_id}, group {product_group}: {e}")
            return None
    
    async def _get_primary_customer_product_group_discount(
        self,
        customer_id: str,
        product_group: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get PRIMARY customer product group discount from customer_product_group_pricelist.
        This is the MOST POWERFUL/PRIMARY discount option.
        
        Uses the SQL query provided by the user:
        select CAST(cpgp.group_id as varchar) as tuoteryhma, c.customer_number as asiakasnro, 
               c.customer_name1 as nimi, cpgp.discount_percent as alepros
        from [dbo].[customer_product_group_pricelist] as cpgp 
        join [dbo].[customers] as c on (cpgp.customer_id = c.customer_id)
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping PRIMARY customer product group discount")
            return None
        
        try:
            # Clean customer_id - remove spaces and convert to int
            clean_customer_id = str(customer_id).replace(' ', '').strip()
            try:
                customer_id_int = int(clean_customer_id)
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid customer_id format: {customer_id}")
                return None
                
            self.logger.info(f"Checking PRIMARY customer product group discount for customer {customer_id_int}, group {product_group}")
            
            query = """
            SELECT 
                CAST(cpgp.group_id as varchar) as tuoteryhma,
                c.customer_number as asiakasnro,
                c.customer_name1 as nimi,
                CAST(cpgp.discount_percent AS DECIMAL(12,4)) as alepros
            FROM [dbo].[customer_product_group_pricelist] as cpgp 
            JOIN [dbo].[customers] as c ON (cpgp.customer_id = c.customer_id)
            WHERE cpgp.customer_id = ?
            AND cpgp.group_id = CAST(? AS INT)
            AND cpgp.discount_percent > 0
            """

            
            
            self.logger.debug(f"Executing PRIMARY customer product group discount query: customer {customer_id_int}, group {product_group}")
            # Ensure product_group is clean integer
            clean_product_group = str(product_group).replace(' ', '').strip()
            result = await self._execute_sql_query(query, [customer_id_int, int(clean_product_group)])
            
            if result:
                discount_data = result[0]
                self.logger.info(
                    f"Found PRIMARY customer product group discount: {discount_data['alepros']}% "
                    f"for customer {discount_data['asiakasnro']} ({discount_data['nimi']}) "
                    f"in product group {discount_data['tuoteryhma']}"
                )
                return {
                    "discount_percent": discount_data['alepros'],
                    "customer_number": discount_data['asiakasnro'],
                    "customer_name": discount_data['nimi'],
                    "product_group": discount_data['tuoteryhma']
                }
            
            self.logger.info(f"No PRIMARY customer product group discount found for customer {customer_id}, group {product_group}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get PRIMARY customer product group discount for customer {customer_id}, group {product_group}: {e}")
            return None

    async def _get_product_exp_price(self, product_code: str) -> Optional[float]:
        """
        Get net price from product_pricing.product_exp_price table.
        
        Args:
            product_code: Product code to lookup
            
        Returns:
            Net price from product_exp_price column or None if not found
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping product_exp_price lookup")
            return None
        
        try:
            self.logger.info(f"Looking up product_exp_price for product {product_code}")
            
            query = """
            SELECT pp.product_exp_price as net_price
            FROM product_pricing pp
            JOIN products p ON pp.product_id = p.product_id
            WHERE p.product_code = ?
            """
            
            result = await self._execute_sql_query(query, [product_code])
            
            if result and len(result) > 0:
                net_price = float(result[0]['net_price'])
                self.logger.info(f"Found product_exp_price for {product_code}: €{net_price:.4f}")
                return net_price
            else:
                self.logger.info(f"No product_exp_price found for {product_code}")
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to get product_exp_price for {product_code}: {e}")
            return None

    async def _get_product_extra_name(self, product_code: str) -> str:
        """
        Get extra name from products.product_description2 column.
        
        Args:
            product_code: Product code to lookup
            
        Returns:
            Extra name from product_description2 column or empty string if not found
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping product extra_name lookup")
            return ""
        
        try:
            self.logger.debug(f"Looking up product extra_name for product {product_code}")
            
            query = """
            SELECT p.product_description2 as extra_name
            FROM products p
            WHERE p.product_code = ?
            """
            
            result = await self._execute_sql_query(query, [product_code])
            
            if result and len(result) > 0:
                extra_name = str(result[0]['extra_name'] or "")
                self.logger.debug(f"Found product extra_name for {product_code}: '{extra_name}'")
                return extra_name
            else:
                self.logger.debug(f"No product extra_name found for {product_code}")
                return ""
                
        except Exception as e:
            self.logger.warning(f"Failed to get product extra_name for {product_code}: {e}")
            return ""

    async def _get_product_default_unit(self, product_code: str) -> str:
        """
        Get default purchase unit from product_units table using same priority logic as transfer_stock_query.
        Priority: KPL -> M -> 1 -> others, only units where product_unit_use_purchase_bit = 1.
        
        Args:
            product_code: Product code to lookup
            
        Returns:
            Default unit from product_units or DEFAULT_UNIT if not found
        """
        if not (self.database_client or (self.deployment_mode == 'docker' and self.http_client)):
            self.logger.debug(f"No SQL execution method available - skipping product default_unit lookup")
            return BusinessConstants.DEFAULT_UNIT
        
        try:
            self.logger.debug(f"Looking up product default_unit for product {product_code}")
            
            query = """
            SELECT TOP 1 pu.product_unit as default_unit
            FROM products p
            LEFT JOIN (
                SELECT 
                    product_id,
                    product_unit,
                    ROW_NUMBER() OVER (
                        PARTITION BY product_id 
                        ORDER BY 
                            CASE 
                                WHEN product_unit = 'KPL' THEN 1
                                WHEN product_unit = 'M' THEN 2
                                WHEN product_unit = '1' THEN 3
                                ELSE 4
                            END,
                            product_unit
                    ) as priority_rank
                FROM [product_units]
                WHERE product_unit_use_purchase_bit = 1
                    AND product_unit NOT LIKE 'BOX%'
            ) pu ON p.[product_id] = pu.[product_id] AND pu.priority_rank = 1
            WHERE p.product_code = ?
            """
            
            result = await self._execute_sql_query(query, [product_code])
            
            if result and len(result) > 0 and result[0]['default_unit']:
                default_unit = str(result[0]['default_unit'])
                self.logger.debug(f"Found product default_unit for {product_code}: '{default_unit}'")
                return default_unit
            else:
                self.logger.debug(f"No product default_unit found for {product_code}, using '{BusinessConstants.DEFAULT_UNIT}'")
                return BusinessConstants.DEFAULT_UNIT
                
        except Exception as e:
            self.logger.warning(f"Failed to get product default_unit for {product_code}: {e}")
            return BusinessConstants.DEFAULT_UNIT

    async def _get_historical_9000_price(self, product_name: str) -> Optional[float]:
        """Look up historical price for a 9000 product from the filtered products CSV."""
        import pandas as pd
        import os
        
        try:
            filtered_products_path = "emails/products_9000_filtered.csv"
            
            # Check if the filtered products file exists
            if not os.path.exists(filtered_products_path):
                self.logger.debug(f"📂 Filtered products file not found: {filtered_products_path}")
                return None
            
            # Load the filtered products CSV
            df = pd.read_csv(filtered_products_path, encoding="utf-8")
            
            # Clean product name for matching
            clean_product_name = str(product_name).strip()
            
            # Find matching products by name (case-insensitive)
            matches = df[df['product_name'].str.strip().str.lower() == clean_product_name.lower()]
            
            if matches.empty:
                self.logger.debug(f"📊 No historical price found for 9000 product: '{product_name}'")
                return None
            
            # Sort by date (newest first) and get the most recent price
            if 'date' in matches.columns:
                try:
                    matches['date_parsed'] = pd.to_datetime(matches['date'])
                    matches = matches.sort_values('date_parsed', ascending=False)
                except Exception as e:
                    self.logger.debug(f"Date parsing error, using first match: {e}")
            
            # Get the most recent match
            latest_match = matches.iloc[0]
            
            # Try to get the best available price (sales_price > unit_price > total_price)
            price = None
            price_source = ""
            
            if 'sales_price' in latest_match and pd.notna(latest_match['sales_price']) and latest_match['sales_price'] > 0:
                price = float(latest_match['sales_price'])
                price_source = "sales_price"
            elif 'unit_price' in latest_match and pd.notna(latest_match['unit_price']) and latest_match['unit_price'] > 0:
                price = float(latest_match['unit_price'])
                price_source = "unit_price"
            elif 'total_price' in latest_match and pd.notna(latest_match['total_price']) and latest_match['total_price'] > 0:
                price = float(latest_match['total_price'])
                price_source = "total_price"
            
            if price is not None and price > 0:
                latest_date = latest_match.get('date', 'unknown')
                self.logger.info(f"📈 Found historical price €{price:.2f} ({price_source}) for '{product_name}' from {latest_date}")
                return price
            else:
                self.logger.debug(f"📊 Historical match found but no valid price for '{product_name}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Error loading historical 9000 prices: {e}")
            return None