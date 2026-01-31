"""
Abstract base interface for customer repository operations.

Defines the contract that all ERP-specific customer adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from src.domain.customer import Customer


class CustomerRepository(ABC):
    """
    Abstract interface for customer operations across all ERP systems.

    Each ERP adapter (Lemonsoft, Jeeves, Oscar, etc.) must implement this interface
    to provide customer lookup, search, and data retrieval functionality.
    """

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Customer]:
        """
        Find customer by company name.

        Args:
            name: Company name to search for

        Returns:
            Customer object if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def find_by_number(self, customer_number: str) -> Optional[Customer]:
        """
        Find customer by customer number.

        Args:
            customer_number: Customer number/ID to search for

        Returns:
            Customer object if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Customer]:
        """
        Search for customers by query string.

        Args:
            query: Search query (can be name, number, email, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching Customer objects

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def get_payment_terms(self, customer_id: str) -> Dict[str, Any]:
        """
        Get payment terms for a customer.

        Args:
            customer_id: Customer ID or number

        Returns:
            Dict containing payment terms information

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def get_invoicing_details(self, customer_id: str) -> Dict[str, Any]:
        """
        Get invoicing details for a customer.

        Args:
            customer_id: Customer ID or number

        Returns:
            Dict containing invoicing details (address, contact, etc.)

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def validate_customer(self, customer: Customer) -> bool:
        """
        Validate customer data against ERP system rules.

        Args:
            customer: Customer object to validate

        Returns:
            True if customer is valid, False otherwise
        """
        pass
