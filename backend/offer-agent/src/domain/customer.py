"""
Generic Customer domain model (ERP-agnostic).

This model represents a customer entity across all ERP systems.
ERP-specific fields are stored in the erp_metadata dictionary.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Customer:
    """
    Generic customer entity (ERP-agnostic).

    This domain model represents customer data in a normalized format
    that is independent of any specific ERP system. ERP adapters are
    responsible for mapping between ERP-specific formats and this model.
    """
    # Core identifiers
    id: str                              # Generic internal ID
    customer_number: str                  # External customer number (visible to users)
    name: str                            # Company/customer name

    # Address information
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "Finland"

    # Contact information
    contact_person: Optional[str] = None  # General contact (CEO, etc.)
    email: Optional[str] = None
    phone: Optional[str] = None

    # Business terms
    payment_terms: Optional[str] = None
    credit_allowed: bool = True           # Inverted from Lemonsoft's deny_credit

    # Responsible person (salesperson)
    responsible_person_id: Optional[str] = None
    responsible_person_number: Optional[str] = None
    responsible_person_name: Optional[str] = None
    responsible_person_source: Optional[str] = None  # 'email_sender_lookup', 'customer_default', etc.

    # ERP-specific data (stored as dict for flexibility)
    # This allows each ERP adapter to store additional fields without modifying this model
    erp_metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation for logging."""
        return f"Customer(number={self.customer_number}, name={self.name}, id={self.id})"

    @property
    def full_address(self) -> str:
        """Return formatted full address."""
        parts = [
            self.street or "",
            f"{self.postal_code or ''} {self.city or ''}".strip(),
            self.country
        ]
        return ", ".join(filter(None, parts))
