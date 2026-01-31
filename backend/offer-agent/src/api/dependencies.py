"""
FastAPI dependency injection helpers.
"""
from src.api.services.offer_service import OfferService, get_offer_service
from src.api.services.pending_store import PendingOfferStore, get_pending_store


def get_service() -> OfferService:
    """
    Dependency to get the offer service singleton.

    Returns:
        The global OfferService instance
    """
    return get_offer_service()


def get_store() -> PendingOfferStore:
    """
    Dependency to get the pending store singleton.

    Returns:
        The global PendingOfferStore instance
    """
    return get_pending_store()
