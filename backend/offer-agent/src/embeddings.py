"""
Embeddings stub for CSV demo mode.

This is a minimal stub to allow CSV demo mode to work without full AI dependencies.
"""
from typing import List, Dict, Any
from src.utils.logger import get_logger


class ProductEmbeddingService:
    """Stub product embedding service for demo mode."""

    def __init__(self):
        """Initialize the stub embedding service."""
        self.logger = get_logger(__name__)
        self.logger.info("ProductEmbeddingService initialized (stub for demo mode)")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a stub embedding."""
        # Return a dummy embedding
        return [0.0] * 768

    async def find_similar_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar products (stub implementation)."""
        return []