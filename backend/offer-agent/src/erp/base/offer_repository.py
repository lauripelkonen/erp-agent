"""
Abstract base interface for offer repository operations.

Defines the contract that all ERP-specific offer adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.domain.offer import Offer, OfferLine


class OfferRepository(ABC):
    """
    Abstract interface for offer operations across all ERP systems.

    Each ERP adapter must implement this interface to provide offer creation,
    retrieval, and management functionality.
    """

    @abstractmethod
    async def create(self, offer: Offer) -> str:
        """
        Create a new offer in the ERP system.

        Args:
            offer: Offer object to create

        Returns:
            Offer number/ID assigned by the ERP system

        Raises:
            ExternalServiceError: If ERP service is unavailable
            ValidationError: If offer data is invalid
        """
        pass

    @abstractmethod
    async def add_line(self, offer_id: str, line: OfferLine) -> bool:
        """
        Add a product line to an existing offer.

        Args:
            offer_id: Offer number/ID
            line: OfferLine object to add

        Returns:
            True if line was added successfully

        Raises:
            ExternalServiceError: If ERP service is unavailable
            ValidationError: If line data is invalid
        """
        pass

    @abstractmethod
    async def get(self, offer_id: str) -> Optional[Offer]:
        """
        Retrieve an offer by ID/number.

        Args:
            offer_id: Offer number/ID

        Returns:
            Offer object if found, None otherwise

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def update(self, offer_id: str, offer: Offer) -> bool:
        """
        Update an existing offer.

        Args:
            offer_id: Offer number/ID to update
            offer: Offer object with updated data

        Returns:
            True if offer was updated successfully

        Raises:
            ExternalServiceError: If ERP service is unavailable
            ValidationError: If offer data is invalid
        """
        pass

    @abstractmethod
    async def verify(self, offer_id: str) -> Dict[str, Any]:
        """
        Verify that an offer was created correctly in the ERP system.

        Args:
            offer_id: Offer number/ID to verify

        Returns:
            Dict containing verification results and offer status

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass

    @abstractmethod
    async def delete(self, offer_id: str) -> bool:
        """
        Delete an offer from the ERP system.

        Args:
            offer_id: Offer number/ID to delete

        Returns:
            True if offer was deleted successfully

        Raises:
            ExternalServiceError: If ERP service is unavailable
        """
        pass
