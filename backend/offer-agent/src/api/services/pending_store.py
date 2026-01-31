"""
In-memory storage with JSON file backup for pending offers.

Provides simple, no-dependency storage that survives container restarts
via JSON file persistence.
"""
import json
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

from src.api.models.responses import PendingOfferResponse, OrderLineResponse
from src.utils.logger import get_logger


class PendingOfferStore:
    """
    In-memory store for pending offers with JSON file backup.

    Features:
    - Thread-safe in-memory dict
    - Auto-save to JSON file on changes
    - Load from file on startup
    - Auto-cleanup of offers older than 7 days
    """

    def __init__(self, backup_path: Optional[str] = None):
        """
        Initialize the store.

        Args:
            backup_path: Path to JSON backup file. Defaults to /app/data/pending_offers.json
        """
        self.logger = get_logger(__name__)
        self._lock = Lock()
        self._offers: Dict[str, PendingOfferResponse] = {}

        # Determine backup path
        if backup_path:
            self._backup_path = Path(backup_path)
        else:
            self._backup_path = Path(
                os.getenv("PENDING_OFFERS_PATH", "/app/data/pending_offers.json")
            )

        # Ensure directory exists
        self._backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Load from file if exists
        self._load_from_file()

        # Cleanup old offers
        self._cleanup_old_offers()

        self.logger.info(f"PendingOfferStore initialized with {len(self._offers)} offers")

    def _load_from_file(self) -> None:
        """Load offers from JSON backup file."""
        if not self._backup_path.exists():
            self.logger.info(f"No backup file found at {self._backup_path}")
            return

        try:
            with open(self._backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            offers_data = data.get("offers", {})
            for offer_id, offer_dict in offers_data.items():
                try:
                    # Parse datetime strings
                    if isinstance(offer_dict.get("created_at"), str):
                        offer_dict["created_at"] = datetime.fromisoformat(
                            offer_dict["created_at"].replace("Z", "+00:00")
                        )

                    # Parse lines
                    lines = [
                        OrderLineResponse(**line) for line in offer_dict.get("lines", [])
                    ]
                    offer_dict["lines"] = lines

                    self._offers[offer_id] = PendingOfferResponse(**offer_dict)
                except Exception as e:
                    self.logger.warning(f"Failed to parse offer {offer_id}: {e}")

            self.logger.info(f"Loaded {len(self._offers)} offers from backup")

        except Exception as e:
            self.logger.error(f"Failed to load backup file: {e}")

    def _save_to_file(self) -> None:
        """Save offers to JSON backup file."""
        try:
            # Convert to serializable format
            offers_data = {}
            for offer_id, offer in self._offers.items():
                offer_dict = offer.model_dump()
                # Convert datetime to ISO string
                if isinstance(offer_dict.get("created_at"), datetime):
                    offer_dict["created_at"] = offer_dict["created_at"].isoformat()
                offers_data[offer_id] = offer_dict

            data = {
                "offers": offers_data,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }

            # Write atomically by writing to temp file first
            temp_path = self._backup_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            # Rename to actual path (atomic on most systems)
            temp_path.rename(self._backup_path)

        except Exception as e:
            self.logger.error(f"Failed to save backup file: {e}")

    def _cleanup_old_offers(self) -> None:
        """Remove offers older than 7 days."""
        cutoff = datetime.utcnow() - timedelta(days=7)

        with self._lock:
            old_count = len(self._offers)
            self._offers = {
                offer_id: offer
                for offer_id, offer in self._offers.items()
                if offer.created_at.replace(tzinfo=None) > cutoff
            }
            removed = old_count - len(self._offers)

            if removed > 0:
                self.logger.info(f"Cleaned up {removed} old offers")
                self._save_to_file()

    async def add(self, offer: PendingOfferResponse) -> None:
        """
        Add a new pending offer.

        Args:
            offer: The offer to add
        """
        with self._lock:
            self._offers[offer.id] = offer
            self._save_to_file()
        self.logger.info(f"Added offer {offer.id} ({offer.offer_number})")

    async def get(self, offer_id: str) -> Optional[PendingOfferResponse]:
        """
        Get an offer by ID.

        Args:
            offer_id: The offer ID

        Returns:
            The offer if found, None otherwise
        """
        with self._lock:
            return self._offers.get(offer_id)

    async def get_all(self) -> List[PendingOfferResponse]:
        """
        Get all pending offers.

        Returns:
            List of all offers sorted by created_at desc
        """
        with self._lock:
            offers = list(self._offers.values())
        return sorted(offers, key=lambda o: o.created_at, reverse=True)

    async def get_pending(self) -> List[PendingOfferResponse]:
        """
        Get only pending offers (not sent/failed).

        Returns:
            List of pending offers sorted by created_at desc
        """
        with self._lock:
            offers = [o for o in self._offers.values() if o.status == "pending"]
        return sorted(offers, key=lambda o: o.created_at, reverse=True)

    async def update(self, offer: PendingOfferResponse) -> bool:
        """
        Update an existing offer.

        Args:
            offer: The updated offer

        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if offer.id not in self._offers:
                return False
            self._offers[offer.id] = offer
            self._save_to_file()
        self.logger.info(f"Updated offer {offer.id}")
        return True

    async def update_status(self, offer_id: str, status: str) -> bool:
        """
        Update the status of an offer.

        Args:
            offer_id: The offer ID
            status: New status (pending, processing, sent, failed)

        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if offer_id not in self._offers:
                return False

            # Create updated offer with new status
            old_offer = self._offers[offer_id]
            updated_offer = PendingOfferResponse(
                id=old_offer.id,
                offer_number=old_offer.offer_number,
                customer_name=old_offer.customer_name,
                customer_email=old_offer.customer_email,
                created_at=old_offer.created_at,
                status=status,
                total_amount=old_offer.total_amount,
                lines=old_offer.lines,
                warnings=old_offer.warnings,
                errors=old_offer.errors,
            )
            self._offers[offer_id] = updated_offer
            self._save_to_file()

        self.logger.info(f"Updated offer {offer_id} status to {status}")
        return True

    async def delete(self, offer_id: str) -> bool:
        """
        Delete an offer.

        Args:
            offer_id: The offer ID

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if offer_id not in self._offers:
                return False
            del self._offers[offer_id]
            self._save_to_file()
        self.logger.info(f"Deleted offer {offer_id}")
        return True

    def count(self) -> int:
        """Get total number of offers."""
        with self._lock:
            return len(self._offers)

    def count_by_status(self) -> Dict[str, int]:
        """Get counts by status."""
        with self._lock:
            counts = {"pending": 0, "processing": 0, "sent": 0, "failed": 0}
            for offer in self._offers.values():
                status = offer.status if offer.status in counts else "pending"
                counts[status] += 1
            return counts


# Global singleton instance
_store_instance: Optional[PendingOfferStore] = None
_store_lock = Lock()


def get_pending_store() -> PendingOfferStore:
    """
    Get the global PendingOfferStore instance.

    Returns:
        The singleton PendingOfferStore instance
    """
    global _store_instance

    with _store_lock:
        if _store_instance is None:
            _store_instance = PendingOfferStore()
        return _store_instance
