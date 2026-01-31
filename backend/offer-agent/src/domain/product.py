"""
Generic Product domain model (ERP-agnostic).

This model represents product catalog data across all ERP systems.
Note: ProductMatch from product_matching/matcher_class.py remains separate
as it represents matching results, not catalog data.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Product:
    """
    Generic product entity (ERP-agnostic).

    Represents a product from the ERP catalog system.
    This is distinct from ProductMatch which represents a product matching result.
    """
    # Core identifiers
    code: str                            # Product code/SKU
    name: str                            # Product name

    # Product details
    description: Optional[str] = None
    extra_name: Optional[str] = None     # Additional name/description (Lisänimi)
    unit: str = "KPL"                    # Unit of measure (KPL, M, KG, etc.)
    product_group: Optional[str] = None

    # Pricing (base price from catalog)
    list_price: float = 0.0              # List/catalog price
    unit_price: float = 0.0              # Current unit price
    price: float = 0.0                   # Alias for unit_price

    # Inventory
    stock_quantity: Optional[float] = None
    stock_location: Optional[str] = None

    # Status
    active: bool = True

    # ERP-specific data
    erp_metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation for logging."""
        return f"Product(code={self.code}, name={self.name}, price=€{self.unit_price:.2f})"
