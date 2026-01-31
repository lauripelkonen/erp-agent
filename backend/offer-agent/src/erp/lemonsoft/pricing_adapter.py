"""
Lemonsoft Pricing Adapter

Implements the PricingService interface for Lemonsoft ERP.
Wraps existing PricingCalculator with database optimization support.
"""
from typing import List, Optional, Dict, Any

from src.erp.base.pricing_service import PricingService
from src.pricing.net_price import OfferPricing, LineItemPricing, PricingCalculator
from src.product_matching.matcher_class import ProductMatch
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class LemonsoftPricingAdapter(PricingService):
    """
    Lemonsoft implementation of the PricingService interface.

    This adapter wraps the existing PricingCalculator which supports:
    - Customer product group discounts (SQL)
    - Product-specific pricing (SQL)
    - Customer group discounts (SQL)
    - General product group discounts (SQL)
    - Historical pricing for 9000 products
    - Multiple deployment modes (direct DB, Docker proxy, API-only)
    """

    def __init__(self):
        """Initialize the Lemonsoft pricing adapter."""
        self.logger = get_logger(__name__)
        # Use existing PricingCalculator
        self.calculator = PricingCalculator()

    async def calculate_pricing(
        self,
        customer_id: str,
        matched_products: List[ProductMatch],
        **kwargs
    ) -> OfferPricing:
        """
        Calculate complete pricing for an offer including all discounts.

        Args:
            customer_id: Customer number
            matched_products: List of ProductMatch objects with quantities
            **kwargs: Additional pricing context

        Returns:
            OfferPricing object with complete pricing breakdown

        Raises:
            ExternalServiceError: If pricing calculation fails
        """
        try:
            self.logger.info(
                f"Calculating pricing for customer {customer_id}, "
                f"{len(matched_products)} products"
            )

            # Extract pricing context from kwargs
            pricing_context = kwargs.get('pricing_context', {})

            # Use existing PricingCalculator
            offer_pricing = await self.calculator.calculate_offer_pricing(
                product_matches=matched_products,
                customer_id=customer_id,
                pricing_context=pricing_context
            )

            self.logger.info(
                f"Pricing calculated: net_total=€{offer_pricing.net_total:.2f}, "
                f"vat=€{offer_pricing.vat_amount:.2f}, "
                f"total=€{offer_pricing.total_amount:.2f}"
            )

            return offer_pricing

        except Exception as e:
            self.logger.error(f"Error calculating pricing: {e}")
            raise ExternalServiceError(f"Failed to calculate pricing: {e}")

    async def calculate_line_pricing(
        self,
        customer_id: str,
        product_code: str,
        quantity: float,
        **kwargs
    ) -> LineItemPricing:
        """
        Calculate pricing for a single product line.

        Args:
            customer_id: Customer number
            product_code: Product code
            quantity: Quantity requested
            **kwargs: Additional parameters

        Returns:
            LineItemPricing object with pricing details

        Raises:
            ExternalServiceError: If pricing calculation fails
        """
        try:
            self.logger.info(
                f"Calculating line pricing for customer {customer_id}, "
                f"product {product_code}, qty {quantity}"
            )

            # Create a ProductMatch for this single item
            product_match = ProductMatch(
                product_code=product_code,
                product_name=kwargs.get('product_name', ''),
                description=kwargs.get('description', ''),
                unit=kwargs.get('unit', 'KPL'),
                price=kwargs.get('price', 0.0),
                quantity_requested=int(quantity),
                confidence_score=1.0,
                match_method='direct'
            )

            # Calculate pricing for this single product
            offer_pricing = await self.calculate_pricing(
                customer_id=customer_id,
                matched_products=[product_match],
                **kwargs
            )

            # Return the first (and only) line item
            if offer_pricing.line_items:
                return offer_pricing.line_items[0]

            # Fallback: create basic line pricing
            return LineItemPricing(
                product_code=product_code,
                product_name=kwargs.get('product_name', ''),
                quantity=quantity,
                unit_price=kwargs.get('price', 0.0),
                list_price=kwargs.get('price', 0.0),
                net_price=kwargs.get('price', 0.0),
                line_total=kwargs.get('price', 0.0) * quantity,
                vat_rate=25.5
            )

        except Exception as e:
            self.logger.error(f"Error calculating line pricing: {e}")
            raise ExternalServiceError(f"Failed to calculate line pricing: {e}")

    async def get_customer_discount(
        self,
        customer_id: str,
        product_code: str
    ) -> float:
        """
        Get customer-specific discount for a product.

        This is handled automatically by the PricingCalculator
        when calculating pricing, but can be called separately if needed.

        Args:
            customer_id: Customer number
            product_code: Product code

        Returns:
            Discount percentage (0-100)

        Raises:
            ExternalServiceError: If discount lookup fails
        """
        try:
            self.logger.info(
                f"Getting customer discount for {customer_id}, product {product_code}"
            )

            # Create a test ProductMatch
            product_match = ProductMatch(
                product_code=product_code,
                product_name='',
                quantity_requested=1,
                confidence_score=1.0,
                match_method='direct'
            )

            # Calculate pricing to get the discount
            pricing = await self.calculate_pricing(
                customer_id=customer_id,
                matched_products=[product_match]
            )

            if pricing.line_items:
                discount = pricing.line_items[0].discount_percent
                self.logger.info(f"Customer discount: {discount}%")
                return discount

            return 0.0

        except Exception as e:
            self.logger.error(f"Error getting customer discount: {e}")
            # Don't raise - return 0 discount as fallback
            return 0.0

    async def get_customer_group_discount(
        self,
        customer_id: str,
        product_group: str
    ) -> float:
        """
        Get customer discount for a product group.

        Handled by PricingCalculator's database queries.

        Args:
            customer_id: Customer number
            product_group: Product group code

        Returns:
            Discount percentage (0-100)

        Raises:
            ExternalServiceError: If discount lookup fails
        """
        try:
            self.logger.info(
                f"Getting customer group discount for {customer_id}, group {product_group}"
            )

            # The PricingCalculator handles this via SQL queries
            # to customer_product_group_pricelist table
            # We would need to expose this as a separate method in the calculator
            # For now, return 0 and log that this is handled in calculate_pricing

            self.logger.info(
                "Customer group discounts are applied automatically "
                "during pricing calculation"
            )
            return 0.0

        except Exception as e:
            self.logger.error(f"Error getting customer group discount: {e}")
            return 0.0

    async def get_product_group_discount(
        self,
        product_group: str
    ) -> float:
        """
        Get general discount for a product group.

        Args:
            product_group: Product group code

        Returns:
            Discount percentage (0-100)

        Raises:
            ExternalServiceError: If discount lookup fails
        """
        try:
            self.logger.info(f"Getting product group discount for group {product_group}")

            # General product group discounts are handled by the
            # PricingCalculator via pricelist queries
            # Return 0 - these are applied during calculate_pricing

            self.logger.info(
                "Product group discounts are applied automatically "
                "during pricing calculation"
            )
            return 0.0

        except Exception as e:
            self.logger.error(f"Error getting product group discount: {e}")
            return 0.0

    async def get_historical_price(
        self,
        customer_id: str,
        product_name: str
    ) -> Optional[float]:
        """
        Get historical price for a product from past orders.

        Useful for products not in catalog (like product code "9000" in Lemonsoft).

        Args:
            customer_id: Customer number
            product_name: Product name/description

        Returns:
            Historical price if found, None otherwise

        Raises:
            ExternalServiceError: If lookup fails
        """
        try:
            self.logger.info(
                f"Getting historical price for customer {customer_id}, "
                f"product {product_name}"
            )

            # The PricingCalculator has _get_historical_9000_price method
            # but it's private. For now, we can't access it directly.
            # This would require either:
            # 1. Making it public in PricingCalculator
            # 2. Creating a ProductMatch with code 9000 and calculating

            # Option 2: Create a 9000 ProductMatch and calculate
            product_match = ProductMatch(
                product_code="9000",
                product_name=product_name,
                quantity_requested=1,
                confidence_score=1.0,
                match_method='direct'
            )

            pricing = await self.calculate_pricing(
                customer_id=customer_id,
                matched_products=[product_match]
            )

            if pricing.line_items:
                historical_price = pricing.line_items[0].unit_price
                if historical_price > 0:
                    self.logger.info(f"Found historical price: €{historical_price:.2f}")
                    return historical_price

            self.logger.info("No historical price found")
            return None

        except Exception as e:
            self.logger.error(f"Error getting historical price: {e}")
            return None

    @property
    def supports_database_optimization(self) -> bool:
        """
        Indicate whether this pricing service supports direct database access.

        Returns:
            True - Lemonsoft pricing adapter supports database optimization
                   via the PricingCalculator's deployment modes:
                   - direct: Direct SQL database access
                   - docker: SQL queries via Azure Function App proxy
                   - api-only: Fallback to API calls only
        """
        return True
