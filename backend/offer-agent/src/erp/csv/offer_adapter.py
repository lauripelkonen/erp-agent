"""
CSV Offer Adapter

Implements the OfferRepository interface for CSV-based offer data.
Writes created offers to CSV files in the results folder.
"""
from typing import Optional, List
import pandas as pd
from pathlib import Path
from datetime import datetime

from src.erp.base.offer_repository import OfferRepository
from src.domain.offer import Offer, OfferLine
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class CSVOfferAdapter(OfferRepository):
    """CSV implementation of the OfferRepository interface."""

    def __init__(self, results_folder: Optional[str] = None):
        """Initialize the CSV offer adapter."""
        self.logger = get_logger(__name__)

        if results_folder is None:
            current_dir = Path(__file__).parent
            results_folder = current_dir / 'results'

        self.results_folder = Path(results_folder)
        self.results_folder.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"CSV Offer Adapter initialized - results will be saved to: {self.results_folder}")

    async def create(self, offer: Offer) -> Offer:
        """Create a new offer and save to CSV."""
        try:
            # Generate offer number if not present
            if not offer.offer_number:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                offer.offer_number = f"OFFER-{timestamp}"

            self.logger.info(f"Creating offer: {offer.offer_number}")

            # Save offer to CSV
            await self._save_offer_to_csv(offer)

            self.logger.info(f"✅ Offer {offer.offer_number} saved to CSV")
            return offer

        except Exception as e:
            self.logger.error(f"Error creating offer: {e}")
            raise ExternalServiceError(f"Failed to create offer: {e}")

    async def _save_offer_to_csv(self, offer: Offer):
        """Save offer to CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save offer header
        offer_file = self.results_folder / f"offer_{offer.offer_number}_{timestamp}.csv"
        offer_data = {
            'offer_number': [offer.offer_number],
            'customer_id': [offer.customer_id],
            'customer_name': [offer.customer_name],
            'offer_date': [offer.offer_date.isoformat() if offer.offer_date else ''],
            'valid_until': [offer.valid_until.isoformat() if offer.valid_until else ''],
            'our_reference': [offer.our_reference or ''],
            'customer_reference': [offer.customer_reference or ''],
            'delivery_contact': [offer.delivery_contact or ''],
            'notes': [offer.notes or ''],
            'total_value': [sum(line.quantity * line.unit_price * (1 - line.discount_percent / 100)
                               for line in offer.lines)],
        }

        df_offer = pd.DataFrame(offer_data)
        df_offer.to_csv(offer_file, sep=';', index=False)
        self.logger.info(f"  📄 Saved offer header to: {offer_file.name}")

        # Save offer lines (products)
        if offer.lines:
            lines_file = self.results_folder / f"offer_{offer.offer_number}_{timestamp}_lines.csv"
            lines_data = []

            for idx, line in enumerate(offer.lines, 1):
                line_total = line.quantity * line.unit_price * (1 - line.discount_percent / 100)
                lines_data.append({
                    'offer_number': offer.offer_number,
                    'line_number': idx,
                    'product_code': line.product_code,
                    'product_name': line.product_name,
                    'description': line.description or '',
                    'quantity': line.quantity,
                    'unit': line.unit,
                    'unit_price': line.unit_price,
                    'discount_percent': line.discount_percent,
                    'line_total': round(line_total, 2),
                })

            df_lines = pd.DataFrame(lines_data)
            df_lines.to_csv(lines_file, sep=';', index=False)
            self.logger.info(f"  📦 Saved {len(offer.lines)} product lines to: {lines_file.name}")

            # Also save a summary
            summary_file = self.results_folder / f"offer_{offer.offer_number}_{timestamp}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"OFFER: {offer.offer_number}\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Customer: {offer.customer_name} ({offer.customer_id})\n")
                f.write(f"Date: {offer.offer_date.strftime('%Y-%m-%d') if offer.offer_date else 'N/A'}\n")
                f.write(f"Valid Until: {offer.valid_until.strftime('%Y-%m-%d') if offer.valid_until else 'N/A'}\n")
                f.write(f"Our Reference: {offer.our_reference or 'N/A'}\n")
                f.write(f"Customer Reference: {offer.customer_reference or 'N/A'}\n\n")

                f.write("-" * 80 + "\n")
                f.write("PRODUCTS:\n")
                f.write("-" * 80 + "\n\n")

                total = 0
                for idx, line in enumerate(offer.lines, 1):
                    line_total = line.quantity * line.unit_price * (1 - line.discount_percent / 100)
                    total += line_total

                    f.write(f"{idx}. {line.product_code} - {line.product_name}\n")
                    f.write(f"   Quantity: {line.quantity} {line.unit}\n")
                    f.write(f"   Unit Price: €{line.unit_price:.2f}\n")
                    if line.discount_percent > 0:
                        f.write(f"   Discount: {line.discount_percent}%\n")
                    f.write(f"   Line Total: €{line_total:.2f}\n")
                    if line.description:
                        f.write(f"   Description: {line.description}\n")
                    f.write("\n")

                f.write("-" * 80 + "\n")
                f.write(f"TOTAL: €{total:.2f}\n")
                f.write("=" * 80 + "\n")

            self.logger.info(f"  📝 Saved summary to: {summary_file.name}")

    async def add_line(self, offer_id: str, line: OfferLine) -> bool:
        """Add a single line to an existing offer (not supported in demo mode)."""
        self.logger.warning("Adding single line to offers not supported in CSV demo mode")
        return True

    async def get(self, offer_id: str) -> Optional[Offer]:
        """Retrieve an offer by ID (not supported in demo mode)."""
        self.logger.warning("Getting offers not supported in CSV demo mode")
        return None

    async def verify(self, offer_id: str) -> dict:
        """Verify that an offer was created correctly."""
        # In CSV demo mode, we just check if the file exists
        results_folder = Path(self.results_folder)
        offer_files = list(results_folder.glob(f"offer_{offer_id}*"))
        return {
            'verified': len(offer_files) > 0,
            'offer_id': offer_id,
            'files_created': len(offer_files),
        }

    async def add_lines(self, offer_number: str, lines: List[OfferLine]) -> Offer:
        """Add lines to an existing offer (not supported in demo mode)."""
        self.logger.warning("Adding lines to existing offers not supported in CSV demo mode")
        # Return a dummy offer
        return Offer(
            customer_id="DEMO",
            customer_name="Demo Customer",
            offer_number=offer_number,
            lines=lines
        )

    async def get_by_number(self, offer_number: str) -> Optional[Offer]:
        """Get offer by number (not supported in demo mode)."""
        self.logger.warning("Getting offers not supported in CSV demo mode")
        return None

    async def update(self, offer: Offer) -> Offer:
        """Update an offer (not supported in demo mode)."""
        self.logger.warning("Updating offers not supported in CSV demo mode")
        return offer

    async def delete(self, offer_number: str) -> bool:
        """Delete an offer (not supported in demo mode)."""
        self.logger.warning("Deleting offers not supported in CSV demo mode")
        return False

    async def list_by_customer(self, customer_id: str) -> List[Offer]:
        """List offers for a customer (not supported in demo mode)."""
        self.logger.warning("Listing offers not supported in CSV demo mode")
        return []
