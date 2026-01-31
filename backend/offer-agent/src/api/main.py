"""
FastAPI application for ERP-Agent REST API.

Provides REST endpoints for creating, reviewing, and approving offers
before sending to ERP.
"""
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import offers_router, health_router
from src.api.services.pending_store import get_pending_store
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_allowed_origins() -> list:
    """
    Get allowed CORS origins.

    Returns:
        List of allowed origin patterns
    """
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Add Vercel frontend URL if configured
    vercel_url = os.getenv("VERCEL_FRONTEND_URL", "")
    if vercel_url:
        origins.append(vercel_url)

    # Add common Vercel patterns
    origins.extend([
        "https://*.vercel.app",
    ])

    return origins


def origin_matches_pattern(origin: str, patterns: list) -> bool:
    """
    Check if origin matches any allowed pattern.

    Supports wildcard patterns like https://*.vercel.app

    Args:
        origin: The origin to check
        patterns: List of allowed patterns

    Returns:
        True if origin matches any pattern
    """
    for pattern in patterns:
        if "*" in pattern:
            # Convert wildcard pattern to regex
            regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
            if re.match(f"^{regex_pattern}$", origin):
                return True
        elif origin == pattern:
            return True
    return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Initializes services on startup and cleans up on shutdown.
    """
    logger.info("=" * 60)
    logger.info("Starting ERP-Agent REST API")
    logger.info("=" * 60)

    # Initialize the pending store (loads from file backup)
    store = get_pending_store()
    logger.info(f"Loaded {store.count()} pending offers from backup")

    erp_type = os.getenv("ERP_TYPE", "csv")
    logger.info(f"ERP Type: {erp_type}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down ERP-Agent REST API")


# Create FastAPI app
app = FastAPI(
    title="ERP-Agent REST API",
    description="REST API for creating, reviewing, and approving offers before sending to ERP",
    version="1.0.0",
    lifespan=lifespan
)


# Custom CORS middleware to handle wildcard patterns
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    """
    Custom CORS middleware with wildcard pattern support.
    """
    origin = request.headers.get("origin", "")
    allowed_origins = get_allowed_origins()

    # Check if this is a preflight request
    if request.method == "OPTIONS":
        if origin and origin_matches_pattern(origin, allowed_origins):
            return JSONResponse(
                content={},
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "86400",
                }
            )

    # Process the request
    response = await call_next(request)

    # Add CORS headers if origin is allowed
    if origin and origin_matches_pattern(origin, allowed_origins):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


# API prefix for namespacing under the main domain
API_PREFIX = "/offer-agent"

# Include routers with prefix
app.include_router(health_router, prefix=API_PREFIX)
app.include_router(offers_router, prefix=API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ERP-Agent REST API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
        "offers": f"{API_PREFIX}/api/offers"
    }


@app.get(f"{API_PREFIX}")
async def offer_agent_root():
    """Offer agent root endpoint."""
    return {
        "name": "Offer Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": f"{API_PREFIX}/health",
            "create_offer": f"{API_PREFIX}/api/offers/create",
            "pending_offers": f"{API_PREFIX}/api/offers/pending",
            "offer_status": f"{API_PREFIX}/api/offers/status"
        }
    }


# Exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "errors": [str(exc)]
        }
    )
