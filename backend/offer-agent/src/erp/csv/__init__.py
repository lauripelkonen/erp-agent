"""
CSV ERP Adapter
Complete implementation of ERP interfaces for CSV-based demo/testing.
Provides a self-contained adapter that works without external ERP systems.
"""

from src.erp.csv.field_mapper import CSVFieldMapper
from src.erp.csv.customer_adapter import CSVCustomerAdapter
from src.erp.csv.person_adapter import CSVPersonAdapter
from src.erp.csv.csv_adapter import CSVProductAdapter
from src.erp.csv.offer_adapter import CSVOfferAdapter
from src.erp.csv.pricing_adapter import CSVPricingAdapter

__all__ = [
    "CSVFieldMapper",
    "CSVCustomerAdapter",
    "CSVPersonAdapter",
    "CSVProductAdapter",
    "CSVOfferAdapter",
    "CSVPricingAdapter",

]