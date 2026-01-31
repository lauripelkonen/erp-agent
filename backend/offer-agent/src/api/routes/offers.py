"""
Offer CRUD endpoints for the REST API.
"""
from fastapi import APIRouter, HTTPException, Depends

from src.api.models.requests import CreateOfferRequest, SendToERPRequest
from src.api.models.responses import (
    PendingOfferResponse,
    OffersListResponse,
    OfferStatusResponse,
    CreateOfferResponse,
    SendOfferResponse,
    DeleteOfferResponse,
)
from src.api.services.offer_service import OfferService, get_offer_service

router = APIRouter(prefix="/api/offers", tags=["offers"])


def get_service() -> OfferService:
    """Dependency to get offer service."""
    return get_offer_service()


@router.post("/create", response_model=CreateOfferResponse)
async def create_offer(
    request: CreateOfferRequest,
    service: OfferService = Depends(get_service)
) -> CreateOfferResponse:
    """
    Create a new offer from form data.

    Processes the request through AI to extract products, match to catalog,
    and calculate pricing. The offer is queued for review before sending to ERP.

    Args:
        request: CreateOfferRequest with sender, subject, body, attachments

    Returns:
        CreateOfferResponse with offer ID if successful
    """
    return await service.create_offer(request)


@router.get("/pending", response_model=OffersListResponse)
async def list_pending_offers(
    service: OfferService = Depends(get_service)
) -> OffersListResponse:
    """
    List all offers awaiting review.

    Returns only offers with status "pending".

    Returns:
        OffersListResponse with list of pending offers
    """
    offers = await service.get_pending_offers()
    return OffersListResponse(
        offers=offers,
        total_count=len(offers)
    )


@router.get("/status", response_model=OfferStatusResponse)
async def get_offers_status(
    service: OfferService = Depends(get_service)
) -> OfferStatusResponse:
    """
    Get all offers with their status.

    Returns all offers regardless of status with counts by status.

    Returns:
        OfferStatusResponse with offers and status counts
    """
    offers = await service.get_all_offers()

    # Count by status
    pending = sum(1 for o in offers if o.status == "pending")
    processing = sum(1 for o in offers if o.status == "processing")
    sent = sum(1 for o in offers if o.status == "sent")
    failed = sum(1 for o in offers if o.status == "failed")

    return OfferStatusResponse(
        offers=offers,
        total_count=len(offers),
        pending_count=pending,
        processing_count=processing,
        sent_count=sent,
        failed_count=failed
    )


@router.get("/{offer_id}", response_model=PendingOfferResponse)
async def get_offer(
    offer_id: str,
    service: OfferService = Depends(get_service)
) -> PendingOfferResponse:
    """
    Get a single offer by ID.

    Args:
        offer_id: The offer ID

    Returns:
        PendingOfferResponse with offer details

    Raises:
        HTTPException 404 if offer not found
    """
    offer = await service.get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.post("/{offer_id}/send", response_model=SendOfferResponse)
async def send_offer_to_erp(
    offer_id: str,
    request: SendToERPRequest,
    service: OfferService = Depends(get_service)
) -> SendOfferResponse:
    """
    Approve and send an offer to the ERP system.

    Args:
        offer_id: The offer ID
        request: SendToERPRequest with line_ids to include

    Returns:
        SendOfferResponse with ERP reference if successful

    Raises:
        HTTPException 404 if offer not found
    """
    result = await service.send_to_erp(offer_id, request)

    if not result.success and "not found" in result.message.lower():
        raise HTTPException(status_code=404, detail=result.message)

    return result


@router.delete("/{offer_id}", response_model=DeleteOfferResponse)
async def delete_offer(
    offer_id: str,
    service: OfferService = Depends(get_service)
) -> DeleteOfferResponse:
    """
    Delete/reject an offer.

    Removes the offer from the pending queue.

    Args:
        offer_id: The offer ID

    Returns:
        DeleteOfferResponse with success status

    Raises:
        HTTPException 404 if offer not found
    """
    result = await service.delete_offer(offer_id)

    if not result.success and "not found" in result.message.lower():
        raise HTTPException(status_code=404, detail=result.message)

    return result
