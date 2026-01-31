"""
Abstract base interface for pricing service operations.

Defines the contract that all ERP-specific pricing adapters must implement.
Supports both API-only and database-optimized pricing strategies.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.pricing.net_price import OfferPricing, LineItemPricing
from src.product_matching.matcher_class import ProductMatch


class PricingService(ABC):
    """
    Abstract interface for pricing calculations across all ERP systems.

    Each ERP adapter must implement this interface to provide pricing calculations
    including discounts, customer-specific pricing, and product group discounts.

    Implementation Strategy:
    - ERPs with database access (like Lemonsoft) can use direct SQL queries for
      complex discount lookups (faster).
    - ERPs without database access can use API calls only (slower but universal).
    """

    @abstractmethod
    async def calculate_pricing(
        self,
        customer_id: str,
        matched_products: List[ProductMatch],
        **kwargs
    ) -> OfferPricing:
        """
        Calculate complete pricing for an offer including all discounts.

        Args:
            customer_id: Customer number/ID
            matched_products: List of ProductMatch objects with quantities
            **kwargs: Additional ERP-specific parameters

        Returns:
            OfferPricing object with complete pricing breakdown

        Raises:
            ExternalServiceError: If ERP service is unavailable
            ValidationError: If pricing data is invalid
        """
        pass

    @abstractmethod
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
            customer_id: Customer number/ID
            product_code: Product code
            quantity: Quantity requested
            **kwargs: Additional ERP-specific parameters

        Returns:
            LineItemPricing object with pricing details

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def get_customer_discount(
        self,
        customer_id: str,
        product_code: str
    ) -> float:
        """
        Get customer-specific discount for a product.

        Args:
            customer_id: Customer number/ID
            product_code: Product code

        Returns:
            Discount percentage (0-100)

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def get_customer_group_discount(
        self,
        customer_id: str,
        product_group: str
    ) -> float:
        """
        Get customer discount for a product group.

        Args:
            customer_id: Customer number/ID
            product_group: Product group code

        Returns:
            Discount percentage (0-100)

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
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
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def get_historical_price(
        self,
        customer_id: str,
        product_name: str
    ) -> Optional[float]:
        """
        Get historical price for a product from past orders.

        Useful for products not in catalog (like product code "9000" in Lemonsoft).

        Args:
            customer_id: Customer number/ID
            product_name: Product name/description

        Returns:
            Historical price if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @property
    @abstractmethod
    def supports_database_optimization(self) -> bool:
        """
        Indicate whether this pricing service supports direct database access.

        Returns:
            True if database optimization is available, False for API-only
        """
        pass
