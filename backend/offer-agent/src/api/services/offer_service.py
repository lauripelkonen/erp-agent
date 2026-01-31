"""
Offer service for business logic.

Bridges the API layer with the orchestrator and pending store.
"""
import base64
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from threading import Lock

from src.api.models.requests import CreateOfferRequest, SendToERPRequest
from src.api.models.responses import (
    PendingOfferResponse,
    OrderLineResponse,
    CreateOfferResponse,
    SendOfferResponse,
    DeleteOfferResponse,
)
from src.api.services.pending_store import PendingOfferStore, get_pending_store
from src.core.orchestrator import OfferOrchestrator
from src.core.workflow import WorkflowContext
from src.utils.logger import get_logger


class OfferService:
    """
    Service for managing offer creation, review, and approval flow.

    Handles:
    - Creating offers from form data (processes through orchestrator)
    - Storing pending offers for review
    - Sending approved offers to ERP
    - Deleting rejected offers
    """

    def __init__(
        self,
        store: Optional[PendingOfferStore] = None,
        orchestrator: Optional[OfferOrchestrator] = None
    ):
        """
        Initialize the service.

        Args:
            store: PendingOfferStore instance (defaults to global singleton)
            orchestrator: OfferOrchestrator instance (defaults to new instance)
        """
        self.logger = get_logger(__name__)
        self._store = store or get_pending_store()
        self._orchestrator = orchestrator

        # Store workflow contexts for approved offers (keyed by offer_id)
        self._contexts: Dict[str, WorkflowContext] = {}
        self._context_lock = Lock()

    def _get_orchestrator(self) -> OfferOrchestrator:
        """Get or create orchestrator instance."""
        if self._orchestrator is None:
            self._orchestrator = OfferOrchestrator()
        return self._orchestrator

    async def create_offer(self, request: CreateOfferRequest) -> CreateOfferResponse:
        """
        Create a new offer from form data.

        Processes the request through the orchestrator to extract products,
        match to catalog, calculate pricing, then stores as pending for review.

        Args:
            request: CreateOfferRequest with sender, subject, body, attachments

        Returns:
            CreateOfferResponse with success status and offer ID
        """
        self.logger.info(f"Creating offer from: {request.sender}")

        try:
            # Convert request to email_data format expected by orchestrator
            email_data = self._convert_request_to_email_data(request)

            # Process through orchestrator (stops before ERP creation)
            orchestrator = self._get_orchestrator()
            result = await orchestrator.process_offer_request_for_review(email_data)

            if not result.success:
                return CreateOfferResponse(
                    success=False,
                    message="Failed to process offer request",
                    errors=result.errors,
                    warnings=result.warnings
                )

            # Convert to PendingOfferResponse
            offer_id = str(uuid.uuid4())
            pending_offer = self._workflow_result_to_pending_offer(
                offer_id=offer_id,
                result=result,
                customer_email=request.sender
            )

            # Store the pending offer
            await self._store.add(pending_offer)

            # Store the workflow context for later ERP submission
            with self._context_lock:
                self._contexts[offer_id] = result.context

            self.logger.info(f"Offer created: {offer_id} ({pending_offer.offer_number})")

            return CreateOfferResponse(
                success=True,
                offer_id=offer_id,
                offer_number=pending_offer.offer_number,
                message=f"Offer created and ready for review",
                warnings=result.warnings
            )

        except Exception as e:
            self.logger.error(f"Failed to create offer: {e}", exc_info=True)
            return CreateOfferResponse(
                success=False,
                message=f"Failed to create offer: {str(e)}",
                errors=[str(e)]
            )

    async def get_pending_offers(self) -> List[PendingOfferResponse]:
        """
        Get all pending offers awaiting review.

        Returns:
            List of pending offers
        """
        return await self._store.get_pending()

    async def get_all_offers(self) -> List[PendingOfferResponse]:
        """
        Get all offers regardless of status.

        Returns:
            List of all offers
        """
        return await self._store.get_all()

    async def get_offer(self, offer_id: str) -> Optional[PendingOfferResponse]:
        """
        Get a single offer by ID.

        Args:
            offer_id: The offer ID

        Returns:
            The offer if found, None otherwise
        """
        return await self._store.get(offer_id)

    async def send_to_erp(
        self,
        offer_id: str,
        request: SendToERPRequest
    ) -> SendOfferResponse:
        """
        Approve and send an offer to the ERP system.

        Args:
            offer_id: The offer ID
            request: SendToERPRequest with line_ids to include

        Returns:
            SendOfferResponse with success status
        """
        self.logger.info(f"Sending offer {offer_id} to ERP")

        try:
            # Get the pending offer
            offer = await self._store.get(offer_id)
            if not offer:
                return SendOfferResponse(
                    success=False,
                    message=f"Offer not found: {offer_id}",
                    errors=["Offer not found"]
                )

            # Update status to processing
            await self._store.update_status(offer_id, "processing")

            # Get the workflow context
            with self._context_lock:
                context = self._contexts.get(offer_id)

            if not context:
                self.logger.warning(f"No context found for offer {offer_id}, recreating minimal context")
                # If context is lost (e.g., after restart), we can't send to ERP
                # In production, you might want to re-process or store context in file
                await self._store.update_status(offer_id, "failed")
                return SendOfferResponse(
                    success=False,
                    message="Offer context expired. Please recreate the offer.",
                    errors=["Workflow context not found"]
                )

            # Filter lines if specific line_ids provided
            if request.line_ids and context.offer:
                # Filter offer lines to only include approved ones
                approved_line_ids = set(request.line_ids)
                context.offer.lines = [
                    line for i, line in enumerate(context.offer.lines)
                    if f"line-{i}" in approved_line_ids or str(i) in approved_line_ids
                ]

                # Recalculate totals
                context.offer.calculate_totals()

            # Send to ERP
            orchestrator = self._get_orchestrator()
            result = await orchestrator.send_offer_to_erp(context)

            if result.success:
                # Update status to sent
                await self._store.update_status(offer_id, "sent")

                # Clean up context
                with self._context_lock:
                    self._contexts.pop(offer_id, None)

                return SendOfferResponse(
                    success=True,
                    offer_number=result.offer_number,
                    erp_reference=result.offer_number,
                    message=f"Offer sent to ERP: {result.offer_number}"
                )
            else:
                await self._store.update_status(offer_id, "failed")
                return SendOfferResponse(
                    success=False,
                    message="Failed to send offer to ERP",
                    errors=result.errors
                )

        except Exception as e:
            self.logger.error(f"Failed to send offer to ERP: {e}", exc_info=True)
            await self._store.update_status(offer_id, "failed")
            return SendOfferResponse(
                success=False,
                message=f"Failed to send offer to ERP: {str(e)}",
                errors=[str(e)]
            )

    async def delete_offer(self, offer_id: str) -> DeleteOfferResponse:
        """
        Delete/reject an offer.

        Args:
            offer_id: The offer ID

        Returns:
            DeleteOfferResponse with success status
        """
        self.logger.info(f"Deleting offer {offer_id}")

        try:
            # Delete from store
            deleted = await self._store.delete(offer_id)

            if not deleted:
                return DeleteOfferResponse(
                    success=False,
                    message=f"Offer not found: {offer_id}"
                )

            # Clean up context
            with self._context_lock:
                self._contexts.pop(offer_id, None)

            return DeleteOfferResponse(
                success=True,
                message=f"Offer deleted successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to delete offer: {e}", exc_info=True)
            return DeleteOfferResponse(
                success=False,
                message=f"Failed to delete offer: {str(e)}"
            )

    def _convert_request_to_email_data(self, request: CreateOfferRequest) -> Dict[str, Any]:
        """
        Convert API request to email_data format for orchestrator.

        Args:
            request: CreateOfferRequest

        Returns:
            Dict in email_data format
        """
        # Convert attachments from base64
        attachments = []
        for att in request.attachments:
            try:
                decoded_data = base64.b64decode(att.data)
                attachments.append({
                    "filename": att.filename,
                    "data": decoded_data,
                    "mime_type": att.mime_type or "application/octet-stream",
                    "source": "api"
                })
            except Exception as e:
                self.logger.warning(f"Failed to decode attachment {att.filename}: {e}")

        return {
            "sender": request.sender,
            "subject": request.subject,
            "body": request.body,
            "attachments": attachments,
            "date": datetime.now().isoformat()
        }

    def _workflow_result_to_pending_offer(
        self,
        offer_id: str,
        result: Any,  # WorkflowResult
        customer_email: str
    ) -> PendingOfferResponse:
        """
        Convert WorkflowResult to PendingOfferResponse.

        Args:
            offer_id: Generated offer ID
            result: WorkflowResult from orchestrator
            customer_email: Customer email address

        Returns:
            PendingOfferResponse
        """
        context = result.context
        lines = []

        if context and context.offer:
            for i, line in enumerate(context.offer.lines):
                # Get original customer term from matched products
                original_term = ""
                if context.matched_products and i < len(context.matched_products):
                    match_details = context.matched_products[i].match_details or {}
                    original_term = match_details.get(
                        "original_term",
                        match_details.get("product_name", line.product_name)
                    )

                lines.append(OrderLineResponse(
                    id=f"line-{i}",
                    product_code=line.product_code,
                    product_name=line.product_name,
                    description=line.description,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    total_price=line.line_total,
                    ai_confidence=min(100, max(0, line.ai_confidence * 100)) if line.ai_confidence <= 1 else line.ai_confidence,
                    ai_reasoning=None,  # Could be populated from match_details
                    original_customer_term=original_term or line.product_name
                ))

        return PendingOfferResponse(
            id=offer_id,
            offer_number=result.offer_number or f"PENDING-{offer_id[:8]}",
            customer_name=result.customer_name or "Unknown",
            customer_email=customer_email,
            created_at=datetime.utcnow(),
            status="pending",
            total_amount=result.total_amount or 0.0,
            lines=lines,
            warnings=result.warnings or [],
            errors=result.errors or []
        )


# Global singleton instance
_service_instance: Optional[OfferService] = None
_service_lock = Lock()


def get_offer_service() -> OfferService:
    """
    Get the global OfferService instance.

    Returns:
        The singleton OfferService instance
    """
    global _service_instance

    with _service_lock:
        if _service_instance is None:
            _service_instance = OfferService()
        return _service_instance
