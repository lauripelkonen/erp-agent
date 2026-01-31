"""
ERP Factory

Factory pattern for creating ERP-specific implementations.
Selects the correct ERP adapter based on configuration.
"""
import os
from typing import Optional

from src.erp.base.customer_repository import CustomerRepository
from src.erp.base.person_repository import PersonRepository
from src.erp.base.offer_repository import OfferRepository
from src.erp.base.product_repository import ProductRepository
from src.erp.base.pricing_service import PricingService
from src.utils.logger import get_logger
from src.config.settings import get_settings


class ERPFactory:
    """
    Factory for creating ERP-specific implementations.

    This factory provides a single point for instantiating the correct
    ERP adapters based on configuration, enabling multi-ERP support.

    Usage:
        factory = ERPFactory(erp_type="lemonsoft")
        customer_repo = factory.create_customer_repository()
        offer_repo = factory.create_offer_repository()
    """

    # Supported ERP systems
    SUPPORTED_ERPS = ["lemonsoft", "jeeves", "oscar", "csv"]

    def __init__(self, erp_type: Optional[str] = None):
        """
        Initialize the ERP factory.

        Args:
            erp_type: ERP system type ("lemonsoft", "jeeves", "oscar", etc.)
                     If None, reads from environment variable ERP_TYPE or defaults to "lemonsoft"
        """
        self.logger = get_logger(__name__)

        # Determine ERP type from parameter, environment, or default
        if erp_type is None:
            erp_type = os.getenv('ERP_TYPE', 'lemonsoft').lower()

        self.erp_type = erp_type.lower()

        # Validate ERP type
        if self.erp_type not in self.SUPPORTED_ERPS:
            self.logger.warning(
                f"ERP type '{self.erp_type}' not in supported list {self.SUPPORTED_ERPS}. "
                f"This may indicate a new ERP adapter that hasn't been added to SUPPORTED_ERPS yet. "
                f"Proceeding anyway..."
            )

        self.logger.info(f"ERP Factory initialized for: {self.erp_type}")

    def create_customer_repository(self) -> CustomerRepository:
        """
        Create customer repository for configured ERP.

        Returns:
            CustomerRepository implementation for the selected ERP

        Raises:
            ValueError: If ERP type is not supported
        """
        if self.erp_type == "lemonsoft":
            from src.erp.lemonsoft.customer_adapter import LemonsoftCustomerAdapter
            return LemonsoftCustomerAdapter()

        elif self.erp_type == "csv":
            # Use CSV customer adapter for demo mode
            from src.erp.csv.customer_adapter import CSVCustomerAdapter
            return CSVCustomerAdapter()

        elif self.erp_type == "jeeves":
            # TODO: Implement when Jeeves support is added
            raise NotImplementedError(
                f"Jeeves customer repository not yet implemented. "
                f"Create src/erp/jeeves/customer_adapter.py"
            )

        elif self.erp_type == "oscar":
            # TODO: Implement when Oscar support is added
            raise NotImplementedError(
                f"Oscar customer repository not yet implemented. "
                f"Create src/erp/oscar/customer_adapter.py"
            )

        else:
            raise ValueError(
                f"Unknown ERP type: {self.erp_type}. "
                f"Supported ERPs: {', '.join(self.SUPPORTED_ERPS)}"
            )

    def create_person_repository(self) -> PersonRepository:
        """
        Create person repository for configured ERP.

        Returns:
            PersonRepository implementation for the selected ERP

        Raises:
            ValueError: If ERP type is not supported
        """
        if self.erp_type == "lemonsoft":
            from src.erp.lemonsoft.person_adapter import LemonsoftPersonAdapter
            return LemonsoftPersonAdapter()

        elif self.erp_type == "csv":
            # Use CSV person adapter for demo mode
            from src.erp.csv.person_adapter import CSVPersonAdapter
            return CSVPersonAdapter()

        elif self.erp_type == "jeeves":
            raise NotImplementedError(
                f"Jeeves person repository not yet implemented. "
                f"Create src/erp/jeeves/person_adapter.py"
            )

        elif self.erp_type == "oscar":
            raise NotImplementedError(
                f"Oscar person repository not yet implemented. "
                f"Create src/erp/oscar/person_adapter.py"
            )

        else:
            raise ValueError(f"Unknown ERP type: {self.erp_type}")

    def create_offer_repository(self) -> OfferRepository:
        """
        Create offer repository for configured ERP.

        Returns:
            OfferRepository implementation for the selected ERP

        Raises:
            ValueError: If ERP type is not supported
        """
        if self.erp_type == "lemonsoft":
            from src.erp.lemonsoft.offer_adapter import LemonsoftOfferAdapter
            return LemonsoftOfferAdapter()

        elif self.erp_type == "csv":
            # Use CSV offer adapter for demo mode (saves to results folder)
            from src.erp.csv.offer_adapter import CSVOfferAdapter
            return CSVOfferAdapter()

        elif self.erp_type == "jeeves":
            raise NotImplementedError(
                f"Jeeves offer repository not yet implemented. "
                f"Create src/erp/jeeves/offer_adapter.py"
            )

        elif self.erp_type == "oscar":
            raise NotImplementedError(
                f"Oscar offer repository not yet implemented. "
                f"Create src/erp/oscar/offer_adapter.py"
            )

        else:
            raise ValueError(f"Unknown ERP type: {self.erp_type}")

    def create_product_repository(self) -> ProductRepository:
        """
        Create product repository for configured ERP.

        Returns:
            ProductRepository implementation for the selected ERP

        Raises:
            ValueError: If ERP type is not supported
        """
        if self.erp_type == "lemonsoft":
            from src.erp.lemonsoft.product_adapter import LemonsoftProductAdapter
            return LemonsoftProductAdapter()

        elif self.erp_type == "csv":
            from src.erp.csv.csv_adapter import CSVProductAdapter
            return CSVProductAdapter()

        elif self.erp_type == "jeeves":
            raise NotImplementedError(
                f"Jeeves product repository not yet implemented. "
                f"Create src/erp/jeeves/product_adapter.py"
            )

        elif self.erp_type == "oscar":
            raise NotImplementedError(
                f"Oscar product repository not yet implemented. "
                f"Create src/erp/oscar/product_adapter.py"
            )

        else:
            raise ValueError(f"Unknown ERP type: {self.erp_type}")

    def create_pricing_service(self) -> PricingService:
        """
        Create pricing service for configured ERP.

        Returns:
            PricingService implementation for the selected ERP

        Raises:
            ValueError: If ERP type is not supported
        """
        if self.erp_type == "lemonsoft":
            from src.erp.lemonsoft.pricing_adapter import LemonsoftPricingAdapter
            return LemonsoftPricingAdapter()

        elif self.erp_type == "csv":
            # Use CSV pricing adapter for demo mode (simple pricing rules)
            from src.erp.csv.pricing_adapter import CSVPricingAdapter
            return CSVPricingAdapter()

        elif self.erp_type == "jeeves":
            raise NotImplementedError(
                f"Jeeves pricing service not yet implemented. "
                f"Create src/erp/jeeves/pricing_adapter.py"
            )

        elif self.erp_type == "oscar":
            raise NotImplementedError(
                f"Oscar pricing service not yet implemented. "
                f"Create src/erp/oscar/pricing_adapter.py"
            )

        else:
            raise ValueError(f"Unknown ERP type: {self.erp_type}")

    def create_all(self) -> dict:
        """
        Create all ERP repositories and services at once.

        Returns:
            Dict with all repositories and services:
                - customer_repo: CustomerRepository
                - person_repo: PersonRepository
                - offer_repo: OfferRepository
                - product_repo: ProductRepository
                - pricing_service: PricingService

        Raises:
            ValueError: If ERP type is not supported
        """
        self.logger.info(f"Creating all ERP adapters for {self.erp_type}")

        return {
            'customer_repo': self.create_customer_repository(),
            'person_repo': self.create_person_repository(),
            'offer_repo': self.create_offer_repository(),
            'product_repo': self.create_product_repository(),
            'pricing_service': self.create_pricing_service(),
        }

    @property
    def erp_name(self) -> str:
        """Get the display name of the current ERP."""
        erp_names = {
            'lemonsoft': 'Lemonsoft',
            'jeeves': 'Jeeves',
            'oscar': 'Oscar',
            'csv': 'CSV',
        }
        return erp_names.get(self.erp_type, self.erp_type.title())

    @property
    def is_lemonsoft(self) -> bool:
        """Check if current ERP is Lemonsoft."""
        return self.erp_type == 'lemonsoft'

    @property
    def is_jeeves(self) -> bool:
        """Check if current ERP is Jeeves."""
        return self.erp_type == 'jeeves'

    @property
    def is_oscar(self) -> bool:
        """Check if current ERP is Oscar."""
        return self.erp_type == 'oscar'

    @property
    def is_csv(self) -> bool:
        """Check if current ERP is CSV."""
        return self.erp_type == 'csv'


# Convenience function for quick access
def get_erp_factory(erp_type: Optional[str] = None) -> ERPFactory:
    """
    Get an ERP factory instance.

    Args:
        erp_type: Optional ERP type. If None, reads from environment.

    Returns:
        ERPFactory instance

    Example:
        factory = get_erp_factory()
        customer_repo = factory.create_customer_repository()
    """
    return ERPFactory(erp_type=erp_type)
