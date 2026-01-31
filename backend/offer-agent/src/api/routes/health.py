"""
Health check endpoint for Fargate and load balancer.
"""
import os
from datetime import datetime
from fastapi import APIRouter

from src.api.models.responses import HealthResponse
from src.api.services.pending_store import get_pending_store

router = APIRouter(tags=["health"])

VERSION = "1.0.0"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status for Fargate health checks and load balancer.
    """
    store = get_pending_store()

    return HealthResponse(
        status="healthy",
        version=VERSION,
        timestamp=datetime.utcnow(),
        erp_type=os.getenv("ERP_TYPE", "csv"),
        pending_offers_count=store.count()
    )
