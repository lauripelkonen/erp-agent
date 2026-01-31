"""
Customer Payment Term Fetcher
Fetches payment term number for customers from Lemonsoft API.
"""

import logging
from typing import Optional, Dict, Any

from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class PaymentTermFetcher:
    """Handles fetching payment terms for customers from Lemonsoft API."""

    def __init__(self):
        """Initialize payment term fetcher."""
        self.logger = get_logger(__name__)

    async def get_customer_payment_term(self, client, customer_number: str) -> Optional[int]:
        """
        Fetch payment term number for a customer.

        Args:
            client: LemonsoftAPIClient instance
            customer_number: Customer number to look up

        Returns:
            Payment term number if found, None otherwise
        """
        try:
            self.logger.info(f"Fetching payment term for customer {customer_number}")

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
                return None

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
                    payment_term = customer.get('payment_term_number')

                    if payment_term is not None:
                        self.logger.info(
                            f"Found payment term {payment_term} for customer {customer_number}"
                        )
                        return int(payment_term)
                    else:
                        self.logger.warning(
                            f"Customer {customer_number} has no payment_term_number field"
                        )
                        return None

            self.logger.warning(f"Customer {customer_number} not found in response")
            return None

        except Exception as e:
            self.logger.error(
                f"Error fetching payment term for customer {customer_number}: {e}"
            )
            return None


async def fetch_customer_payment_term(client, customer_number: str) -> Optional[int]:
    """
    Convenience function to fetch payment term for a customer.

    Args:
        client: LemonsoftAPIClient instance
        customer_number: Customer number to look up

    Returns:
        Payment term number if found, None otherwise
    """
    fetcher = PaymentTermFetcher()
    return await fetcher.get_customer_payment_term(client, customer_number)