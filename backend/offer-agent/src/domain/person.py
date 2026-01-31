"""
Generic Person domain model (ERP-agnostic).

Represents salesperson/responsible person across all ERP systems.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Person:
    """
    Generic person/salesperson entity (ERP-agnostic).

    Represents a person (salesperson, account manager, etc.) in the ERP system.
    """
    # Core identifiers
    id: str                              # Internal ID
    number: Optional[str] = None         # Person number (external reference)

    # Personal information
    name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None

    # Role/status
    role: Optional[str] = None           # Role/title
    active: bool = True

    # ERP-specific data
    erp_metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation for logging."""
        return f"Person(number={self.number}, name={self.name}, email={self.email})"
