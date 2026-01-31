"""
Generic Offer domain model (ERP-agnostic).

This model represents an offer/quote entity across all ERP systems.
Pricing details are handled by LineItemPricing and OfferPricing from pricing module.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


@dataclass
class OfferLine:
    """
    Generic offer line item (ERP-agnostic).

    Represents a single product line in an offer.
    """
    # Product information
    product_code: str
    product_name: str
    description: Optional[str] = None

    # Quantity and unit
    quantity: float = 1.0
    unit: str = "KPL"

    # Pricing
    unit_price: float = 0.0
    list_price: float = 0.0
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    net_price: float = 0.0
    line_total: float = 0.0

    # Tax
    vat_rate: float = 25.5
    vat_amount: float = 0.0

    # Positioning
    position: int = 0                    # Line order in offer
    ai_confidence: float = 0.0

    # ERP-specific data (e.g., account, cost_center, stock for Lemonsoft)
    erp_metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation for logging."""
        return f"OfferLine(product={self.product_code}, qty={self.quantity}, total=€{self.line_total:.2f})"


@dataclass
class Offer:
    """
    Generic offer/quote entity (ERP-agnostic).

    Represents a complete offer with customer, lines, and pricing information.
    ERP adapters map between this model and ERP-specific formats.
    """
    # Customer information
    customer_id: str                     # Customer number/ID
    customer_name: str

    # Offer lines
    lines: List[OfferLine] = field(default_factory=list)

    # Dates
    offer_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    # References
    our_reference: str = ""              # Our reference (e.g., AUTO-202501141230)
    customer_reference: str = ""         # Customer's reference/PO number

    # Contacts
    delivery_contact: str = ""           # Delivery contact person
    offer_contact: Optional[str] = None  # General offer contact

    # Delivery and payment
    payment_term: Optional[int] = None   # Payment term code
    delivery_method: Optional[int] = None # Delivery method code
    delivery_term: Optional[int] = None  # Delivery term code

    # Pricing totals (can be calculated from lines or provided separately)
    subtotal: float = 0.0
    total_discount_amount: float = 0.0
    net_total: float = 0.0
    vat_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "EUR"

    # Person responsible (salesperson)
    responsible_person_id: Optional[str] = None
    responsible_person_number: Optional[str] = None

    # Status and metadata
    offer_number: Optional[str] = None   # ERP-assigned offer number (after creation)
    status: str = "draft"                # draft, sent, accepted, rejected
    notes: str = ""

    # Additional fields
    language_code: str = "FIN"           # Language for offer document
    company_location_id: Optional[int] = None

    # ERP-specific data (stores fields like Sales_phase_collection, offer_type, etc.)
    erp_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default dates if not provided."""
        if self.offer_date is None:
            self.offer_date = datetime.now()
        if self.valid_until is None:
            # Default validity: 30 days from offer date
            self.valid_until = self.offer_date + timedelta(days=30)
        # Generate our_reference if not provided
        if not self.our_reference:
            self.our_reference = f"AUTO-{self.offer_date.strftime('%Y%m%d%H%M')}"

    def add_line(self, line: OfferLine) -> None:
        """Add a line to the offer and update position."""
        line.position = len(self.lines) + 1
        self.lines.append(line)

    def calculate_totals(self) -> None:
        """Calculate offer totals from line items."""
        self.subtotal = sum(line.line_total for line in self.lines)
        self.total_discount_amount = sum(
            (line.discount_amount * line.quantity) for line in self.lines
        )
        self.vat_amount = sum(line.vat_amount for line in self.lines)
        self.net_total = self.subtotal
        self.total_amount = self.net_total + self.vat_amount

    def __repr__(self) -> str:
        """String representation for logging."""
        return (
            f"Offer(customer={self.customer_id}, "
            f"lines={len(self.lines)}, "
            f"total=€{self.total_amount:.2f}, "
            f"number={self.offer_number or 'draft'})"
        )
