"""
Lemonsoft Offer Adapter

Implements the OfferRepository interface for Lemonsoft ERP.
Handles the complex 3-step offer creation process specific to Lemonsoft.
"""
from typing import Optional, Dict, Any
from datetime import datetime

from src.erp.base.offer_repository import OfferRepository
from src.domain.offer import Offer, OfferLine
from src.erp.lemonsoft.field_mapper import LemonsoftFieldMapper
from src.lemonsoft.api_client import LemonsoftAPIClient
from src.config.constants import LemonsoftConstants
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError, BaseOfferAutomationError


class LemonsoftOfferAdapter(OfferRepository):
    """
    Lemonsoft implementation of the OfferRepository interface.

    This adapter handles the complex Lemonsoft offer creation process:
    1. POST /api/offers/6 - Create minimal offer (just customer_id)
    2. GET /api/offers/{number} - Retrieve created offer
    3. PUT /api/offers - Update with complete data
    4. POST /api/offers/{number}/offerrows - Add each product line

    This 3-step process is specific to Lemonsoft's API requirements.
    """

    def __init__(self):
        """Initialize the Lemonsoft offer adapter."""
        self.logger = get_logger(__name__)
        self.client = LemonsoftAPIClient()
        self.mapper = LemonsoftFieldMapper()

    async def create(self, offer: Offer) -> str:
        """
        Create a new offer in Lemonsoft using the 3-step process.

        Args:
            offer: Offer object to create

        Returns:
            Offer number/ID assigned by Lemonsoft

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
            ValidationError: If offer data is invalid
        """
        try:
            self.logger.info(f"Creating offer for customer {offer.customer_id}")

            async with self.client as client:
                await client.ensure_ready()

                # ===== STEP 1: Create minimal offer =====
                self.logger.info("Step 1: Creating minimal offer")
                minimal_offer_data = {
                    "customer_id": offer.erp_metadata.get('customer_internal_id', offer.customer_id)
                }

                offer_response = await client.post('/api/offers/6', json=minimal_offer_data)

                if offer_response.status_code not in [200, 201]:
                    raise ExternalServiceError(
                        f"Failed to create offer: {offer_response.status_code}"
                    )

                offer_result = offer_response.json()
                offer_number = offer_result.get('offer_number') or offer_result.get('number')
                offer_id = offer_result.get('offer_id') or offer_result.get('id')

                self.logger.info(f"Created minimal offer: {offer_number} (ID: {offer_id})")

                # ===== STEP 2: Get the created offer =====
                self.logger.info(f"Step 2: Retrieving offer {offer_number}")
                await client.ensure_ready()
                get_response = await client.get(f'/api/offers/{offer_number}')

                if get_response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to retrieve created offer: {get_response.status_code}"
                    )

                complete_offer = get_response.json()

                # ===== STEP 3: Update with complete data =====
                self.logger.info("Step 3: Updating offer with complete data")

                # Get invoicing details from erp_metadata if available
                invoicing_details = offer.erp_metadata.get('invoicing_details', {})

                # Map generic Offer to Lemonsoft format
                lemonsoft_offer_data = self.mapper.from_offer(offer, invoicing_details)

                # Merge with existing offer data
                complete_offer.update(lemonsoft_offer_data)

                # Update the offer
                await client.ensure_ready()
                update_response = await client.put('/api/offers', json=complete_offer)

                if update_response.status_code not in [200, 201, 204]:
                    self.logger.warning(
                        f"Failed to update offer with complete data: {update_response.status_code}"
                    )
                    try:
                        error_data = update_response.json()
                        self.logger.warning(f"Update error response: {error_data}")
                    except:
                        self.logger.warning(f"Update error response text: {update_response.text}")
                else:
                    self.logger.info(f"✅ Updated offer {offer_number} with complete data")

                # ===== STEP 4: Add product lines =====
                if offer.lines:
                    self.logger.info(f"Step 4: Adding {len(offer.lines)} product lines")
                    await self._add_all_lines(client, offer_number, offer.lines)

                self.logger.info(f"✅ Successfully created offer {offer_number}")
                return offer_number

        except Exception as e:
            self.logger.error(f"Error creating offer: {e}")
            raise ExternalServiceError(f"Failed to create offer: {e}")

    async def add_line(self, offer_id: str, line: OfferLine) -> bool:
        """
        Add a product line to an existing offer.

        Args:
            offer_id: Offer number/ID
            line: OfferLine object to add

        Returns:
            True if line was added successfully

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
            ValidationError: If line data is invalid
        """
        try:
            self.logger.info(f"Adding product line {line.product_code} to offer {offer_id}")

            async with self.client as client:
                await client.ensure_ready()

                # Map generic OfferLine to Lemonsoft row format
                row_data = self.mapper.from_offer_line(line)

                # Add additional Lemonsoft-specific fields
                row_data.update({
                    "number": line.position,
                    "unit_price": line.unit_price,
                    "unit_net_price": f"{line.net_price:.2f}",
                    "discount": f"{line.discount_percent:.2f}",
                    "total": f"{line.line_total + line.vat_amount:.2f}",
                    "tax_rate": f"{line.vat_rate:.2f}",
                    "tax_amount": f"{line.vat_amount:.2f}",
                    "net_price": f"{line.net_price:.2f}",
                    "type": 0,
                })

                # Add the row
                success = await self._add_single_row(client, offer_id, line.position, row_data)

                if success:
                    self.logger.info(
                        f"✅ Added line: {line.product_name} x {line.quantity} "
                        f"@ €{line.unit_price:.2f} = €{line.line_total:.2f}"
                    )
                return success

        except Exception as e:
            self.logger.error(f"Error adding line to offer: {e}")
            raise ExternalServiceError(f"Failed to add line: {e}")

    async def get(self, offer_id: str) -> Optional[Offer]:
        """
        Retrieve an offer by ID/number.

        Args:
            offer_id: Offer number/ID

        Returns:
            Offer object if found, None otherwise

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Retrieving offer {offer_id}")

            async with self.client as client:
                await client.ensure_ready()

                response = await client.get(f'/api/offers/{offer_id}')

                if response.status_code == 404:
                    self.logger.info(f"Offer not found: {offer_id}")
                    return None

                if response.status_code != 200:
                    raise ExternalServiceError(f"Failed to retrieve offer: {response.status_code}")

                offer_data = response.json()

                # Map Lemonsoft data to generic Offer
                offer = self.mapper.to_offer(offer_data)

                self.logger.info(f"Retrieved offer: {offer.offer_number}")
                return offer

        except Exception as e:
            self.logger.error(f"Error retrieving offer: {e}")
            raise ExternalServiceError(f"Failed to retrieve offer: {e}")

    async def update(self, offer_id: str, offer: Offer) -> bool:
        """
        Update an existing offer.

        Args:
            offer_id: Offer number/ID to update
            offer: Offer object with updated data

        Returns:
            True if offer was updated successfully

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Updating offer {offer_id}")

            async with self.client as client:
                await client.ensure_ready()

                # Get current offer
                get_response = await client.get(f'/api/offers/{offer_id}')
                if get_response.status_code != 200:
                    raise ExternalServiceError(f"Failed to retrieve offer for update")

                current_offer = get_response.json()

                # Get invoicing details from erp_metadata if available
                invoicing_details = offer.erp_metadata.get('invoicing_details', {})

                # Map generic Offer to Lemonsoft format
                lemonsoft_offer_data = self.mapper.from_offer(offer, invoicing_details)

                # Merge with current offer data
                current_offer.update(lemonsoft_offer_data)

                # Update the offer
                await client.ensure_ready()
                update_response = await client.put('/api/offers', json=current_offer)

                if update_response.status_code not in [200, 201, 204]:
                    self.logger.warning(f"Failed to update offer: {update_response.status_code}")
                    return False

                self.logger.info(f"✅ Updated offer {offer_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error updating offer: {e}")
            raise ExternalServiceError(f"Failed to update offer: {e}")

    async def verify(self, offer_id: str) -> Dict[str, Any]:
        """
        Verify that an offer was created correctly in Lemonsoft.

        Args:
            offer_id: Offer number/ID to verify

        Returns:
            Dict containing verification results and offer status

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Verifying offer {offer_id}")

            # Get the offer
            offer = await self.get(offer_id)

            if not offer:
                return {
                    'verified': False,
                    'error': f'Offer {offer_id} not found'
                }

            # Check that offer has lines
            has_lines = len(offer.lines) > 0 if offer.lines else False

            # Check that totals are calculated
            has_totals = offer.total_amount > 0

            verified = has_lines and has_totals

            verification = {
                'verified': verified,
                'offer_number': offer.offer_number,
                'customer_id': offer.customer_id,
                'lines_count': len(offer.lines) if offer.lines else 0,
                'total_amount': offer.total_amount,
                'has_lines': has_lines,
                'has_totals': has_totals
            }

            if verified:
                self.logger.info(f"✅ Offer {offer_id} verified successfully")
            else:
                self.logger.warning(f"⚠️ Offer {offer_id} verification failed: {verification}")

            return verification

        except Exception as e:
            self.logger.error(f"Error verifying offer: {e}")
            return {
                'verified': False,
                'error': str(e)
            }

    async def delete(self, offer_id: str) -> bool:
        """
        Delete an offer from Lemonsoft.

        Args:
            offer_id: Offer number/ID to delete

        Returns:
            True if offer was deleted successfully

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Deleting offer {offer_id}")

            async with self.client as client:
                await client.ensure_ready()

                response = await client._make_request('DELETE', f'/api/offers/{offer_id}')

                self.logger.info(f"✅ Deleted offer {offer_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error deleting offer: {e}")
            raise ExternalServiceError(f"Failed to delete offer: {e}")

    # ==================== HELPER METHODS ====================

    async def _add_all_lines(self, client, offer_number: str, lines: list) -> int:
        """
        Add all product lines to an offer.

        Args:
            client: LemonsoftAPIClient instance
            offer_number: Offer number
            lines: List of OfferLine objects

        Returns:
            Number of successfully added lines
        """
        successful_additions = 0
        errors = []

        # Check if offer already has rows (avoid duplicates)
        get_response = await client.get(f'/api/offers/{offer_number}')
        if get_response.status_code == 200:
            current_offer = get_response.json()
            existing_rows = current_offer.get('offer_rows', [])

            if existing_rows:
                self.logger.warning(
                    f"Offer {offer_number} already has {len(existing_rows)} rows - "
                    f"counting existing rows"
                )
                return len(existing_rows)

        # Add each line
        for i, line in enumerate(lines, 1):
            try:
                # Map to Lemonsoft format
                row_data = self.mapper.from_offer_line(line)
                row_data.update({
                    "number": i,
                    "position": str(i),
                    "unit_price": line.unit_price,
                    "unit_net_price": f"{line.net_price:.2f}",
                    "discount": f"{line.discount_percent:.2f}",
                    "total": f"{line.line_total + line.vat_amount:.2f}",
                    "tax_rate": f"{line.vat_rate:.2f}",
                    "tax_amount": f"{line.vat_amount:.2f}",
                    "net_price": f"{line.net_price:.2f}",
                    "type": 0,
                })

                success = await self._add_single_row(client, offer_number, i, row_data)
                if success:
                    successful_additions += 1

            except Exception as e:
                error_msg = f"Failed to add row {i} (product {line.product_code}): {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        self.logger.info(
            f"Row addition summary: {successful_additions} successful, {len(errors)} failed"
        )

        # Check if we have enough valid rows
        if successful_additions < 1:
            # Try to delete the empty offer
            try:
                await client._make_request('DELETE', f'/api/offers/{offer_number}')
                self.logger.info(f"Deleted empty offer {offer_number}")
            except Exception as delete_e:
                self.logger.warning(f"Could not delete empty offer {offer_number}: {delete_e}")

            raise BaseOfferAutomationError(
                f"Offer creation failed: Only {successful_additions} out of {len(lines)} "
                f"products could be added to the offer"
            )

        return successful_additions

    async def _add_single_row(
        self,
        client,
        offer_number: str,
        position: int,
        row_data: dict
    ) -> bool:
        """
        Add a single product row to an offer with retry logic for duplicate positions.

        Args:
            client: LemonsoftAPIClient instance
            offer_number: Offer number
            position: Row position
            row_data: Row data in Lemonsoft format

        Returns:
            True if row was added successfully
        """
        try:
            await client._make_request('POST', f'/api/offers/{offer_number}/offerrows', data=row_data)
            return True

        except Exception as e:
            error_str = str(e).lower()

            # Handle duplicate position errors (race condition)
            if "duplicate key" in error_str and "index2" in error_str:
                self.logger.warning(
                    f"Duplicate position {position} for offer {offer_number} - "
                    f"retrying with different position"
                )

                # Try positions 11-50 higher
                for retry_position in range(position + 10, position + 50):
                    try:
                        retry_row_data = row_data.copy()
                        retry_row_data["number"] = retry_position
                        retry_row_data["position"] = str(retry_position)

                        await client._make_request(
                            'POST',
                            f'/api/offers/{offer_number}/offerrows',
                            data=retry_row_data
                        )

                        self.logger.info(f"✅ Added row with retry position {retry_position}")
                        return True

                    except Exception as retry_e:
                        if "duplicate key" not in str(retry_e).lower():
                            # Different error, stop retrying
                            break
                        continue

                # All retries failed
                self.logger.warning(
                    f"Could not add product row due to position conflicts - "
                    f"continuing with other products"
                )
                return False
            else:
                # Non-duplicate error, re-raise
                raise

        return False
