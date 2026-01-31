"""
Abstract base interface for person/salesperson repository operations.

Defines the contract that all ERP-specific person adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.person import Person


class PersonRepository(ABC):
    """
    Abstract interface for person/salesperson operations across all ERP systems.

    Each ERP adapter must implement this interface to provide person lookup functionality.
    """

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Person]:
        """
        Find person/salesperson by email address.

        Args:
            email: Email address to search for

        Returns:
            Person object if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def find_by_number(self, person_number: str) -> Optional[Person]:
        """
        Find person by person number.

        Args:
            person_number: Person number/ID to search for

        Returns:
            Person object if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Person]:
        """
        Search for persons by query string.

        Args:
            query: Search query (can be name, email, number, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching Person objects

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass
