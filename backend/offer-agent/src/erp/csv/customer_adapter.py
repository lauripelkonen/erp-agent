"""
CSV Customer Adapter

Implements the CustomerRepository interface for CSV-based customer data.
"""
from typing import Optional, List
import pandas as pd
from pathlib import Path

from src.erp.base.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class CSVCustomerAdapter(CustomerRepository):
    """CSV implementation of the CustomerRepository interface."""

    def __init__(self, csv_file_path: Optional[str] = None):
        """Initialize the CSV customer adapter."""
        self.logger = get_logger(__name__)

        if csv_file_path is None:
            current_dir = Path(__file__).parent
            csv_file_path = current_dir / 'data' / 'customers.csv'

        self.csv_file_path = str(csv_file_path)
        self._customers_df: Optional[pd.DataFrame] = None

        self.logger.info(f"CSV Customer Adapter initialized with file: {self.csv_file_path}")

    def _load_customers(self) -> pd.DataFrame:
        """Load customers from CSV file."""
        if self._customers_df is not None:
            return self._customers_df

        try:
            self._customers_df = pd.read_csv(
                self.csv_file_path,
                sep=';',
                dtype=str,
                keep_default_na=False
            )
            self.logger.info(f"Loaded {len(self._customers_df)} customers from CSV")
            return self._customers_df
        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")
            raise ExternalServiceError(f"Failed to load customer data from CSV: {e}")

    async def find_by_name(self, name: str) -> Optional[Customer]:
        """Find customer by company name."""
        customers = await self.search_by_name(name, limit=1)
        return customers[0] if customers else None

    async def find_by_number(self, customer_number: str) -> Optional[Customer]:
        """Find customer by customer number (alias for get_by_number)."""
        return await self.get_by_number(customer_number)

    async def search(self, query: str, limit: int = 10) -> List[Customer]:
        """Search for customers by query string."""
        return await self.search_by_name(query, limit)

    async def get_payment_terms(self, customer_id: str) -> dict:
        """Get payment terms for a customer."""
        customer = await self.get_by_number(customer_id)
        if not customer:
            return {}
        return {
            'payment_term': '14',  # Default: 14 days
            'delivery_method': 6 if customer.credit_allowed else 33,  # 6=invoice, 33=prepayment
        }

    async def validate_customer(self, customer: Customer) -> bool:
        """Validate customer data."""
        # Simple validation for demo mode
        return bool(customer.customer_number and customer.name)

    async def get_by_number(self, customer_number: str) -> Optional[Customer]:
        """Get customer by customer number."""
        try:
            df = self._load_customers()
            matches = df[df['customer_number'].str.strip() == str(customer_number).strip()]

            if matches.empty:
                return None

            row = matches.iloc[0]
            return Customer(
                id=row['customer_number'],
                customer_number=row['customer_number'],
                name=row['name'],
                street=row.get('street', ''),
                postal_code=row.get('postal_code', ''),
                city=row.get('city', ''),
                country=row.get('country', 'Finland'),
                contact_person=row.get('contact_person', ''),
                email=row.get('email', ''),
                phone=row.get('phone', ''),
                credit_allowed=row.get('credit_allowed', 'true').lower() == 'true',
                responsible_person_number=row.get('responsible_person_number'),
                responsible_person_name=row.get('responsible_person_name'),
            )
        except Exception as e:
            self.logger.error(f"Error getting customer by number: {e}")
            raise ExternalServiceError(f"Failed to get customer: {e}")

    async def search_by_name(self, name: str, limit: int = 10) -> List[Customer]:
        """Search customers by name."""
        try:
            df = self._load_customers()
            name_lower = name.lower()

            matches = df[df['name'].str.lower().str.contains(name_lower, na=False)]
            matches = matches.head(limit)

            customers = []
            for _, row in matches.iterrows():
                customers.append(Customer(
                    id=row['customer_number'],
                    customer_number=row['customer_number'],
                    name=row['name'],
                    street=row.get('street', ''),
                    postal_code=row.get('postal_code', ''),
                    city=row.get('city', ''),
                    country=row.get('country', 'Finland'),
                    contact_person=row.get('contact_person', ''),
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    credit_allowed=row.get('credit_allowed', 'true').lower() == 'true',
                ))

            return customers
        except Exception as e:
            self.logger.error(f"Error searching customers: {e}")
            raise ExternalServiceError(f"Failed to search customers: {e}")

    async def create(self, customer: Customer) -> Customer:
        """Create a new customer (not supported in demo CSV mode)."""
        self.logger.warning("Customer creation not supported in CSV demo mode")
        return customer

    async def update(self, customer: Customer) -> Customer:
        """Update a customer (not supported in demo CSV mode)."""
        self.logger.warning("Customer update not supported in CSV demo mode")
        return customer

    async def get_invoicing_details(self, customer_number: str) -> dict:
        """Get customer invoicing details."""
        customer = await self.get_by_number(customer_number)
        if not customer:
            return {}

        return {
            'offer_customer_number': customer.customer_number,
            'offer_customer_name1': customer.name,
            'offer_customer_name2': '',
            'offer_customer_address1': customer.street,
            'offer_customer_address2': '',
            'offer_customer_address3': f"{customer.postal_code} {customer.city}",
        }
