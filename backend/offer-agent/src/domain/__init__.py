"""
Domain models for offer automation (ERP-agnostic).

These models represent business entities independent of any specific ERP system.
ERP adapters are responsible for mapping between these models and ERP-specific formats.
"""

from src.domain.customer import Customer
from src.domain.product import Product
from src.domain.person import Person
from src.domain.offer import Offer, OfferLine

__all__ = [
    "Customer",
    "Product",
    "Person",
    "Offer",
    "OfferLine",
]
