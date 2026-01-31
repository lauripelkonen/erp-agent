"""
Application Constants
Centralized configuration for fixed values used throughout the application.
"""

from typing import Dict, Any


class BusinessConstants:
    """Business-related constants and default values."""
    
    # VAT and Taxation
    DEFAULT_VAT_RATE: float = 25.5  # Finnish standard VAT rate
    FALLBACK_VAT_RATE: float = 25.5  # Fallback if VAT rate is missing
    
    # Currency
    DEFAULT_CURRENCY: str = "EUR"
    
    # Product defaults
    DEFAULT_UNIT: str = "KPL"  # Kappale (piece)
    DEFAULT_DELIVERY_TIME: str = ""
    
    # Payment terms
    DEFAULT_PAYMENT_TERMS: str = "Net 30"
    
    # Offer validity
    DEFAULT_OFFER_VALIDITY_DAYS: int = 30
    
    # Pricing defaults
    DEFAULT_PRODUCT_PRICE: float = 0.0
    DEFAULT_DISCOUNT_PERCENT: float = 0.0
    DEFAULT_DISCOUNT_AMOUNT: float = 0.0


class TechnicalConstants:
    """Technical constants for system behavior."""
    
    # Rate limiting
    DEFAULT_REQUESTS_PER_MINUTE: int = 60
    
    # Timeouts (seconds)
    HTTP_TIMEOUT: float = 30.0
    CONNECT_TIMEOUT: float = 10.0
    
    # Session management
    SESSION_VALIDITY_HOURS: int = 24
    SESSION_REFRESH_BUFFER_MINUTES: int = 5
    
    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: float = 1.0
    
    # Database
    DEFAULT_QUERY_LIMIT: int = 100
    MAX_QUERY_LIMIT: int = 1000


class ValidationConstants:
    """Constants for data validation."""
    
    # Field lengths
    MAX_PRODUCT_CODE_LENGTH: int = 50
    MAX_PRODUCT_NAME_LENGTH: int = 200
    MAX_CUSTOMER_NAME_LENGTH: int = 200
    MAX_EMAIL_LENGTH: int = 254
    MAX_PHONE_LENGTH: int = 20
    
    # Required fields
    REQUIRED_CUSTOMER_FIELDS: list = ["name"]
    REQUIRED_PRODUCT_FIELDS: list = ["product_code", "name"]
    REQUIRED_OFFER_FIELDS: list = ["customer_id", "lines"]


class LemonsoftConstants:
    """Lemonsoft API specific constants."""
    
    # API endpoints
    AUTH_ENDPOINT: str = "/api/auth/login"
    CUSTOMERS_ENDPOINT: str = "/api/customers"
    PRODUCTS_ENDPOINT: str = "/api/products"
    OFFERS_ENDPOINT: str = "/api/offers"
    HEALTH_ENDPOINT: str = "/api/health"
    
    # Response codes
    SUCCESS_CODE: int = 200
    SUCCESS_MESSAGE: str = "ok"
    
    # Default field values (using BusinessConstants where applicable)
    DEFAULT_VAT_RATE: float = BusinessConstants.DEFAULT_VAT_RATE
    DEFAULT_UNIT: str = BusinessConstants.DEFAULT_UNIT
    DEFAULT_CURRENCY: str = BusinessConstants.DEFAULT_CURRENCY
    DEFAULT_PAYMENT_TERMS: str = BusinessConstants.DEFAULT_PAYMENT_TERMS
    
    # Offer row defaults
    DEFAULT_ACCOUNT: str = "3000"
    DEFAULT_COST_CENTER: str = "05900"
    DEFAULT_PRODUCT_STOCK: int = 10
    
    # Status values
    VALID_OFFER_STATUSES: list = ["draft", "sent", "accepted", "rejected", "expired"]
    DEFAULT_OFFER_STATUS: str = "draft"


class EmailConstants:
    """Email processing constants."""
    
    # File extensions
    SUPPORTED_ATTACHMENTS: list = [".pdf", ".txt", ".docx", ".xlsx", ".csv"]
    
    # Processing
    MAX_ATTACHMENT_SIZE_MB: int = 10
    MAX_EMAIL_BODY_LENGTH: int = 50000
    
    # Unknown product handling
    UNKNOWN_PRODUCT_CODE: str = "9000"
    UNKNOWN_PRODUCT_NAME: str = "Unknown Product"


# Legacy compatibility - export commonly used constants at module level
DEFAULT_VAT_RATE = BusinessConstants.DEFAULT_VAT_RATE
DEFAULT_CURRENCY = BusinessConstants.DEFAULT_CURRENCY
DEFAULT_UNIT = BusinessConstants.DEFAULT_UNIT
DEFAULT_PAYMENT_TERMS = BusinessConstants.DEFAULT_PAYMENT_TERMS

# For easy access to all constants
ALL_CONSTANTS: Dict[str, Any] = {
    "business": BusinessConstants,
    "technical": TechnicalConstants,
    "validation": ValidationConstants,
    "lemonsoft": LemonsoftConstants,
    "email": EmailConstants,
}
