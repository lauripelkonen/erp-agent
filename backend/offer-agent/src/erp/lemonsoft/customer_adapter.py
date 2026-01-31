"""
Lemonsoft Customer Adapter

Implements the CustomerRepository interface for Lemonsoft ERP.
Wraps existing Lemonsoft customer lookup logic and maps to generic domain models.
"""
from typing import Optional, List, Dict, Any

from src.erp.base.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.erp.lemonsoft.field_mapper import LemonsoftFieldMapper
from src.lemonsoft.api_client import LemonsoftAPIClient
from src.customer.enhanced_lookup import EnhancedCustomerLookup
from src.customer.payment_term import PaymentTermFetcher
from src.customer.invoicing_details import InvoicingDetailsFetcher
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class LemonsoftCustomerAdapter(CustomerRepository):
    """
    Lemonsoft implementation of the CustomerRepository interface.

    This adapter wraps the existing Lemonsoft customer lookup functionality
    and maps between Lemonsoft API format and generic Customer domain models.
    """

    def __init__(self):
        """Initialize the Lemonsoft customer adapter."""
        self.logger = get_logger(__name__)
        self.client = LemonsoftAPIClient()
        self.mapper = LemonsoftFieldMapper()
        self.enhanced_lookup = EnhancedCustomerLookup()
        self.payment_term_fetcher = PaymentTermFetcher()
        self.invoicing_fetcher = InvoicingDetailsFetcher()

    async def find_by_name(self, name: str) -> Optional[Customer]:
        """
        Find customer by company name using enhanced lookup.

        Args:
            name: Company name to search for

        Returns:
            Customer object if found, None otherwise

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Looking up customer by name: {name}")

            # Use enhanced lookup (handles multiple search strategies)
            result = await self.enhanced_lookup.find_customer(
                company_name=name,
                customer_number=None
            )

            if not result.get('success', False):
                self.logger.info(f"Customer not found: {name}")
                return None

            # Extract customer data from result
            customer_data = result.get('customer', {})

            # Map Lemonsoft data to generic Customer model
            customer = self.mapper.to_customer(customer_data)

            self.logger.info(f"Found customer: {customer.name} (ID: {customer.id})")
            return customer

        except Exception as e:
            self.logger.error(f"Error finding customer by name '{name}': {e}")
            raise ExternalServiceError(f"Failed to find customer: {e}")

    async def find_by_number(self, customer_number: str) -> Optional[Customer]:
        """
        Find customer by customer number.

        Args:
            customer_number: Customer number to search for

        Returns:
            Customer object if found, None otherwise

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Looking up customer by number: {customer_number}")

            # Use enhanced lookup with customer number
            result = await self.enhanced_lookup.find_customer(
                company_name='null',  # Placeholder when searching by number
                customer_number=customer_number
            )

            if not result.get('success', False):
                self.logger.info(f"Customer not found: {customer_number}")
                return None

            # Extract customer data from result
            customer_data = result.get('customer', {})

            # Map Lemonsoft data to generic Customer model
            customer = self.mapper.to_customer(customer_data)

            self.logger.info(f"Found customer: {customer.name} (number: {customer.customer_number})")
            return customer

        except Exception as e:
            self.logger.error(f"Error finding customer by number '{customer_number}': {e}")
            raise ExternalServiceError(f"Failed to find customer: {e}")

    async def search(self, query: str, limit: int = 10) -> List[Customer]:
        """
        Search for customers by query string.

        Args:
            query: Search query (can be name, number, email, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching Customer objects

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Searching customers with query: {query}, limit: {limit}")

            customers = []

            # Use Lemonsoft API to search
            async with self.client as client:
                await client.ensure_ready()

                response = await client.get(
                    '/api/customers',
                    params={'filter.search': query}
                )

                if response.status_code != 200:
                    self.logger.warning(f"Customer search failed: {response.status_code}")
                    return []

                data = response.json()

                # Extract customers from response
                customer_list = self._extract_customers_from_response(data)

                # Map to generic Customer models
                for customer_data in customer_list[:limit]:
                    customer = self.mapper.to_customer(customer_data)
                    customers.append(customer)

            self.logger.info(f"Found {len(customers)} customers matching '{query}'")
            return customers

        except Exception as e:
            self.logger.error(f"Error searching customers with query '{query}': {e}")
            raise ExternalServiceError(f"Failed to search customers: {e}")

    async def get_payment_terms(self, customer_id: str) -> Dict[str, Any]:
        """
        Get payment terms for a customer.

        Args:
            customer_id: Customer number (in Lemonsoft, this is the customer_number)

        Returns:
            Dict containing payment terms information

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Fetching payment terms for customer: {customer_id}")

            async with self.client as client:
                await client.ensure_ready()

                # Use payment term fetcher
                payment_term = await self.payment_term_fetcher.get_customer_payment_term(
                    client,
                    customer_id
                )

                return {
                    'payment_term': payment_term,
                    'payment_term_number': payment_term
                }

        except Exception as e:
            self.logger.error(f"Error fetching payment terms for customer '{customer_id}': {e}")
            raise ExternalServiceError(f"Failed to get payment terms: {e}")

    async def get_invoicing_details(self, customer_id: str) -> Dict[str, Any]:
        """
        Get invoicing details for a customer.

        Args:
            customer_id: Customer number (in Lemonsoft, this is the customer_number)

        Returns:
            Dict containing invoicing details (Lemonsoft-specific format)

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Fetching invoicing details for customer: {customer_id}")

            async with self.client as client:
                await client.ensure_ready()

                # Use invoicing details fetcher
                invoicing_details = await self.invoicing_fetcher.get_customer_invoicing_details(
                    client,
                    customer_id
                )

                return invoicing_details

        except Exception as e:
            self.logger.error(f"Error fetching invoicing details for customer '{customer_id}': {e}")
            raise ExternalServiceError(f"Failed to get invoicing details: {e}")

    async def validate_customer(self, customer: Customer) -> bool:
        """
        Validate customer data against Lemonsoft rules.

        Args:
            customer: Customer object to validate

        Returns:
            True if customer is valid, False otherwise
        """
        # Basic validation
        if not customer.customer_number:
            self.logger.warning("Customer validation failed: missing customer_number")
            return False

        if not customer.name:
            self.logger.warning("Customer validation failed: missing name")
            return False

        # Check if customer exists in Lemonsoft
        try:
            existing_customer = await self.find_by_number(customer.customer_number)
            if not existing_customer:
                self.logger.warning(f"Customer {customer.customer_number} not found in Lemonsoft")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating customer: {e}")
            return False

    # ==================== HELPER METHODS ====================

    def _extract_customers_from_response(self, data: Any) -> List[Dict]:
        """
        Extract customer list from Lemonsoft API response.

        Handles various response formats from Lemonsoft API.

        Args:
            data: API response data

        Returns:
            List of customer dictionaries
        """
        customers = []

        if isinstance(data, list):
            customers = data
        elif isinstance(data, dict):
            # Try various possible keys
            customers = data.get('results', data.get('data', data.get('customers', [])))

            # If still not a list, check if it's a single customer
            if not isinstance(customers, list):
                if 'customer_number' in data or 'number' in data:
                    customers = [data]
                else:
                    customers = []

        return customers
