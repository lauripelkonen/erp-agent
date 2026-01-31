"""
Response models for the API endpoints.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OrderLineResponse(BaseModel):
    """Single order line in a pending offer."""
    id: str
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity: float
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    ai_confidence: float = Field(ge=0, le=100, description="AI match confidence 0-100")
    ai_reasoning: Optional[str] = None
    original_customer_term: str = Field(
        ...,
        description="Original product term from customer request"
    )


class PendingOfferResponse(BaseModel):
    """Pending offer awaiting review."""
    id: str
    offer_number: str
    customer_name: str
    customer_email: str
    created_at: datetime
    status: str = Field(default="pending", description="pending, processing, sent, failed")
    total_amount: float
    lines: List[OrderLineResponse]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class OffersListResponse(BaseModel):
    """List of pending offers."""
    offers: List[PendingOfferResponse]
    total_count: int


class OfferStatusResponse(BaseModel):
    """All offers with their status."""
    offers: List[PendingOfferResponse]
    total_count: int
    pending_count: int
    processing_count: int
    sent_count: int
    failed_count: int


class CreateOfferResponse(BaseModel):
    """Response after creating a new offer."""
    success: bool
    offer_id: Optional[str] = None
    offer_number: Optional[str] = None
    message: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SendOfferResponse(BaseModel):
    """Response after sending offer to ERP."""
    success: bool
    offer_number: Optional[str] = None
    erp_reference: Optional[str] = None
    message: str
    errors: List[str] = Field(default_factory=list)


class DeleteOfferResponse(BaseModel):
    """Response after deleting an offer."""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    erp_type: str
    pending_offers_count: int
