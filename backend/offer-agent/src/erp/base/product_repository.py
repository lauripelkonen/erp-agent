"""
Abstract base interface for product repository operations.

Defines the contract that all ERP-specific product adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd
from src.domain.product import Product


class ProductRepository(ABC):
    """
    Abstract interface for product catalog operations across all ERP systems.

    Each ERP adapter must implement this interface to provide product search
    and retrieval functionality from the ERP's product catalog.
    """

    @abstractmethod
    async def get_by_code(self, product_code: str) -> Optional[Product]:
        """
        Get product by product code/SKU.

        Args:
            product_code: Product code to search for

        Returns:
            Product object if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Product]:
        """
        Search for products by query string.

        Args:
            query: Search query (can be code, name, description, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching Product objects

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def get_product_group_products(self, product_group: str) -> List[Product]:
        """
        Get all products in a product group.

        Args:
            product_group: Product group identifier

        Returns:
            List of Product objects in the group

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def check_availability(self, product_code: str, quantity: float) -> bool:
        """
        Check if product is available in requested quantity.

        Args:
            product_code: Product code to check
            quantity: Requested quantity

        Returns:
            True if product is available in requested quantity

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def wildcard_search(self, pattern: str) -> Optional[pd.DataFrame]:
        """
        Perform wildcard search on products using a search pattern.

        This is used by the product matcher to find products that match
        unclear terms from emails (e.g., "heat pump" might match product
        codes or descriptions containing those words).

        Args:
            pattern: Search pattern (can include wildcards, spaces, etc.)

        Returns:
            DataFrame with product search results in format expected by ProductMatcher:
                - id: Product ID
                - sku: Product code/SKU
                - name: Product name/description
                - extra_name: Additional product description
                - price: Product price
                - product_searchcode: Search code
                - description: Long description
                - group_code: Product group code
                - priority: Priority level ('priority' or 'non_priority')
                - total_stock: Available stock
                - yearly_sales_qty: Sales quantity in last year
                - data_source: Where the data came from
            Returns None if no matches found.

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def search_by_product_codes(self, product_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        Search for products by exact product codes (batch lookup).

        This is used by the product matcher when it has identified exact
        product codes from the email and needs to fetch their details.

        Args:
            product_codes: List of product codes to search for

        Returns:
            DataFrame with product search results in same format as wildcard_search().
            Returns None if no matches found.

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass
