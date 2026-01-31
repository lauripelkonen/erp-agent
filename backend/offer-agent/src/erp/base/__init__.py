"""
Abstract base interfaces for ERP operations.

These interfaces define the contract that all ERP adapters must implement,
enabling the application to work with multiple ERP systems through a
unified interface.
"""

from src.erp.base.customer_repository import CustomerRepository
from src.erp.base.person_repository import PersonRepository
from src.erp.base.offer_repository import OfferRepository
from src.erp.base.product_repository import ProductRepository
from src.erp.base.pricing_service import PricingService

__all__ = [
    "CustomerRepository",
    "PersonRepository",
    "OfferRepository",
    "ProductRepository",
    "PricingService",
]
