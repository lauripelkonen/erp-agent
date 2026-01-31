"""
Customer Invoicing Details Fetcher
Fetches invoicing details for customers from Lemonsoft API.
"""

import logging
from typing import Optional, Dict, Any

from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class InvoicingDetailsFetcher:
    """Handles fetching invoicing details for customers from Lemonsoft API."""

    def __init__(self):
        """Initialize invoicing details fetcher."""
        self.logger = get_logger(__name__)

    async def get_customer_invoicing_details(self, client, customer_number: str) -> Dict[str, str]:
        """
        Fetch invoicing details for a customer.

        Args:
            client: LemonsoftAPIClient instance
            customer_number: Customer number to look up

        Returns:
            Dictionary with invoicing details for offer_customer fields
        """
        try:
            self.logger.info(f"Fetching invoicing details for customer {customer_number}")

            # Ensure client is ready
            await client.ensure_ready()

            # Make API request to get customer data with filter
            params = {
                'filter.customer_number': customer_number
            }

            response = await client.get('/api/customers', params=params)

            if response.status_code != 200:
                self.logger.warning(
                    f"Failed to fetch customer data: status {response.status_code}"
                )
                return self._get_default_invoicing_details(customer_number)

            # Parse response
            data = response.json()

            # Handle both single customer and list response formats
            customers = []
            if isinstance(data, dict):
                # Single customer response
                if 'customer_number' in data:
                    customers = [data]
                # Results field (most common format from API)
                elif 'results' in data:
                    customers = data['results']
                # List wrapped in response object
                elif 'customers' in data:
                    customers = data['customers']
                elif 'data' in data:
                    customers = data['data']
            elif isinstance(data, list):
                # Direct list of customers
                customers = data

            # Find the matching customer
            for customer in customers:
                # Check both 'customer_number' and 'number' fields
                cust_num = customer.get('customer_number') or customer.get('number')
                if str(cust_num) == str(customer_number):
                    # Extract invoicing details
                    invoicing_details = {
                        'offer_customer_number': str(customer_number),
                        'offer_customer_name1': customer.get('invoicing_name', customer.get('name', '')),
                        'offer_customer_name2': customer.get('invoicing_name2', ''),
                        'offer_customer_address1': customer.get('invoicing_address', customer.get('street', '')),
                        'offer_customer_address2': '',  # Always empty as specified
                        'offer_customer_address3': customer.get('invoicing_postaladdress', ''),
                    }

                    # Log what was found
                    self.logger.info(
                        f"Found invoicing details for customer {customer_number}: "
                        f"name={invoicing_details['offer_customer_name1']}, "
                        f"address={invoicing_details['offer_customer_address1']}"
                    )

                    # If invoicing_postaladdress is empty, construct from postal_code and city
                    if not invoicing_details['offer_customer_address3']:
                        postal_code = customer.get('invoicing_postal_code', customer.get('postal_code', ''))
                        city = customer.get('invoicing_city', customer.get('city', ''))
                        if postal_code or city:
                            invoicing_details['offer_customer_address3'] = f"{postal_code} {city}".strip()

                    return invoicing_details

            self.logger.warning(f"Customer {customer_number} not found in response")
            return self._get_default_invoicing_details(customer_number)

        except Exception as e:
            self.logger.error(
                f"Error fetching invoicing details for customer {customer_number}: {e}"
            )
            return self._get_default_invoicing_details(customer_number)

    def _get_default_invoicing_details(self, customer_number: str) -> Dict[str, str]:
        """
        Return default invoicing details structure.

        Args:
            customer_number: Customer number

        Returns:
            Dictionary with default/empty invoicing details
        """
        return {
            'offer_customer_number': str(customer_number),
            'offer_customer_name1': '',
            'offer_customer_name2': '',
            'offer_customer_address1': '',
            'offer_customer_address2': '',
            'offer_customer_address3': '',
        }


async def fetch_customer_invoicing_details(client, customer_number: str) -> Dict[str, str]:
    """
    Convenience function to fetch invoicing details for a customer.

    Args:
        client: LemonsoftAPIClient instance
        customer_number: Customer number to look up

    Returns:
        Dictionary with invoicing details for offer_customer fields
    """
    fetcher = InvoicingDetailsFetcher()
    return await fetcher.get_customer_invoicing_details(client, customer_number)