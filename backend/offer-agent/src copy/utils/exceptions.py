"""
Custom exception classes for the Offer Automation System.
Provides structured error handling with context and recovery suggestions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class BaseOfferAutomationError(Exception):
    """Base exception class for all offer automation errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        context: Dict[str, Any] = None,
        recovery_suggestions: List[str] = None,
        request_id: str = None
    ):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for categorization
            context: Additional context information about the error
            recovery_suggestions: List of suggestions for fixing the error
            request_id: Request ID for tracking the error in logs
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.request_id = request_id
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses."""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'recovery_suggestions': self.recovery_suggestions,
            'request_id': self.request_id,
            'timestamp': self.timestamp
        }
    
    def __str__(self) -> str:
        """String representation with context."""
        base = f"{self.error_code}: {self.message}"
        if self.request_id:
            base += f" [Request: {self.request_id}]"
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            base += f" [Context: {context_str}]"
        return base


# Email Processing Exceptions
class EmailProcessingError(BaseOfferAutomationError):
    """Base exception for email processing errors."""
    pass


class EmailParsingError(EmailProcessingError):
    """Error parsing email content or attachments."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="EMAIL_PARSING_ERROR",
            recovery_suggestions=[
                "Check email format and encoding",
                "Verify attachment file formats are supported",
                "Check for corrupted attachments"
            ],
            **kwargs
        )


class AttachmentProcessingError(EmailProcessingError):
    """Error processing email attachments."""
    
    def __init__(self, message: str, attachment_name: str = None, **kwargs):
        context = kwargs.pop('context', {})
        if attachment_name:
            context['attachment_name'] = attachment_name
        
        super().__init__(
            message=message,
            error_code="ATTACHMENT_PROCESSING_ERROR",
            context=context,
            recovery_suggestions=[
                "Verify attachment file format is Excel (.xlsx, .xls)",
                "Check if attachment is corrupted",
                "Ensure attachment contains product data in expected format"
            ],
            **kwargs
        )


# Customer Identification Exceptions
class CustomerIdentificationError(BaseOfferAutomationError):
    """Base exception for customer identification errors."""
    pass


class CustomerNotFoundError(CustomerIdentificationError):
    """Customer could not be identified from email content."""
    
    def __init__(self, message: str, search_terms: List[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if search_terms:
            context['search_terms'] = search_terms
        
        super().__init__(
            message=message,
            error_code="CUSTOMER_NOT_FOUND",
            context=context,
            recovery_suggestions=[
                "Include customer name or company in email content",
                "Add customer identification information to email signature",
                "Use registered customer email addresses",
                "Include customer ID or reference number in email"
            ],
            **kwargs
        )


class MultipleCustomersFoundError(CustomerIdentificationError):
    """Multiple potential customers found, cannot determine correct one."""
    
    def __init__(self, message: str, candidates: List[dict] = None, **kwargs):
        context = kwargs.pop('context', {})
        if candidates:
            context['customer_candidates'] = candidates
            context['candidate_count'] = len(candidates)
        
        super().__init__(
            message=message,
            error_code="MULTIPLE_CUSTOMERS_FOUND",
            context=context,
            recovery_suggestions=[
                "Include more specific customer identification in email",
                "Use unique customer identifiers (customer ID, VAT number)",
                "Send email from registered customer contact"
            ],
            **kwargs
        )


# Product Identification Exceptions
class ProductIdentificationError(BaseOfferAutomationError):
    """Base exception for product identification errors."""
    pass


class ProductNotFoundError(ProductIdentificationError):
    """Product could not be identified from description."""
    
    def __init__(self, message: str, product_description: str = None, **kwargs):
        context = kwargs.get('context', {})
        if product_description:
            context['product_description'] = product_description
        
        super().__init__(
            message=message,
            error_code="PRODUCT_NOT_FOUND",
            context=context,
            recovery_suggestions=[
                "Use exact product names or codes from catalog",
                "Include product category or specifications",
                "Check spelling and terminology",
                "Attach Excel file with product codes if available"
            ],
            **kwargs
        )


class InvalidProductDataError(ProductIdentificationError):
    """Product data format is invalid or incomplete."""
    
    def __init__(self, message: str, data_source: str = None, **kwargs):
        context = kwargs.get('context', {})
        if data_source:
            context['data_source'] = data_source
        
        super().__init__(
            message=message,
            error_code="INVALID_PRODUCT_DATA",
            context=context,
            recovery_suggestions=[
                "Check Excel attachment format matches expected schema",
                "Ensure product codes are valid",
                "Verify quantity fields contain numeric values",
                "Include all required columns (product code, quantity)"
            ],
            **kwargs
        )


# Lemonsoft API Exceptions
class LemonsoftAPIError(BaseOfferAutomationError):
    """Base exception for Lemonsoft API errors."""
    pass


class LemonsoftAuthenticationError(LemonsoftAPIError):
    """Authentication failed with Lemonsoft API."""
    
    def __init__(self, message: str = "Authentication failed with Lemonsoft API", **kwargs):
        super().__init__(
            message=message,
            error_code="LEMONSOFT_AUTH_ERROR",
            recovery_suggestions=[
                "Check API credentials configuration",
                "Verify API key is valid and not expired",
                "Ensure proper authentication headers are set",
                "Contact Lemonsoft support if credentials are correct"
            ],
            **kwargs
        )


class LemonsoftAPIConnectionError(LemonsoftAPIError):
    """Connection error with Lemonsoft API."""
    
    def __init__(self, message: str, status_code: int = None, **kwargs):
        context = kwargs.get('context', {})
        if status_code:
            context['status_code'] = status_code
        
        super().__init__(
            message=message,
            error_code="LEMONSOFT_CONNECTION_ERROR",
            context=context,
            recovery_suggestions=[
                "Check network connectivity",
                "Verify Lemonsoft API endpoint URL",
                "Check if Lemonsoft service is available",
                "Retry the operation after a delay"
            ],
            **kwargs
        )


class LemonsoftDataValidationError(LemonsoftAPIError):
    """Data validation error when creating offer in Lemonsoft."""
    
    def __init__(self, message: str, validation_errors: List[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if validation_errors:
            context['validation_errors'] = validation_errors
        
        super().__init__(
            message=message,
            error_code="LEMONSOFT_VALIDATION_ERROR",
            context=context,
            recovery_suggestions=[
                "Check offer data format and required fields",
                "Verify customer ID exists in Lemonsoft",
                "Ensure product codes are valid",
                "Check price and quantity values are within allowed ranges"
            ],
            **kwargs
        )


# Pricing and Discount Exceptions
class PricingCalculationError(BaseOfferAutomationError):
    """Base exception for pricing calculation errors."""
    pass


class DiscountCalculationError(PricingCalculationError):
    """Error calculating discounts for offer."""
    
    def __init__(self, message: str, customer_id: str = None, **kwargs):
        context = kwargs.get('context', {})
        if customer_id:
            context['customer_id'] = customer_id
        
        super().__init__(
            message=message,
            error_code="DISCOUNT_CALCULATION_ERROR",
            context=context,
            recovery_suggestions=[
                "Check customer discount rules configuration",
                "Verify product pricing data is available",
                "Ensure customer category is properly set",
                "Check if special pricing periods are active"
            ],
            **kwargs
        )


class PriceDataMissingError(PricingCalculationError):
    """Required price data is missing for products."""
    
    def __init__(self, message: str, missing_products: List[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if missing_products:
            context['missing_products'] = missing_products
        
        super().__init__(
            message=message,
            error_code="PRICE_DATA_MISSING",
            context=context,
            recovery_suggestions=[
                "Update product catalog with missing price information",
                "Check if products are active and available for sale",
                "Verify product codes are correct",
                "Contact product management for pricing information"
            ],
            **kwargs
        )


# Document Generation Exceptions
class DocumentGenerationError(BaseOfferAutomationError):
    """Base exception for document generation errors."""
    pass


class PDFGenerationError(DocumentGenerationError):
    """Error generating PDF document."""
    
    def __init__(self, message: str = "Failed to generate PDF document", **kwargs):
        super().__init__(
            message=message,
            error_code="PDF_GENERATION_ERROR",
            recovery_suggestions=[
                "Check PDF template configuration",
                "Verify all required data is available",
                "Check file system permissions for output directory",
                "Ensure PDF library dependencies are installed"
            ],
            **kwargs
        )


class EmailNotificationError(BaseOfferAutomationError):
    """Error sending email notification."""
    
    def __init__(self, message: str, recipient: str = None, **kwargs):
        context = kwargs.get('context', {})
        if recipient:
            context['recipient'] = recipient
        
        # Prepare kwargs without duplicates
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['error_code', 'context', 'recovery_suggestions']}
        
        super().__init__(
            message=message,
            error_code="EMAIL_NOTIFICATION_ERROR",
            context=context,
            recovery_suggestions=[
                "Check SMTP server configuration",
                "Verify email credentials",
                "Check recipient email address format",
                "Ensure network connectivity to email server"
            ],
            **filtered_kwargs
        )


class EmailSenderError(EmailNotificationError):
    """Error in email sending operations via Gmail API or OAuth2."""
    
    def __init__(self, message: str, **kwargs):
        # Set custom recovery suggestions for Gmail/OAuth errors
        kwargs['recovery_suggestions'] = [
            "Check Gmail API authentication",
            "Verify OAuth2 credentials are valid",
            "Check Gmail API quotas and limits",
            "Ensure proper email permissions are granted",
            "Re-authorize OAuth2 if credentials expired"
        ]
        
        # Filter out parameters that will be overridden
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['error_code']}
        
        super().__init__(message=message, **filtered_kwargs)
        
        # Override the error code after initialization
        self.error_code = "EMAIL_SENDER_ERROR"


# Configuration and System Exceptions
class ConfigurationError(BaseOfferAutomationError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context,
            recovery_suggestions=[
                "Check environment variables configuration",
                "Verify configuration file format",
                "Ensure all required settings are provided",
                "Check configuration validation rules"
            ],
            **kwargs
        )


class ExternalServiceError(BaseOfferAutomationError):
    """Error with external service (OpenAI, web search, etc.)."""
    
    def __init__(self, message: str, service_name: str = None, **kwargs):
        context = kwargs.get('context', {})
        if service_name:
            context['service_name'] = service_name
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            context=context,
            recovery_suggestions=[
                "Check service availability and status",
                "Verify API credentials and quotas",
                "Check network connectivity",
                "Try again later if service is temporarily unavailable"
            ],
            **kwargs
        )


class ValidationError(BaseOfferAutomationError):
    """Data validation error."""
    
    def __init__(self, message: str, field_name: str = None, **kwargs):
        context = kwargs.get('context', {})
        if field_name:
            context['field_name'] = field_name
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context,
            recovery_suggestions=[
                "Check input data format and values",
                "Verify required fields are provided",
                "Ensure data types match expected formats",
                "Check value ranges and constraints"
            ],
            **kwargs
        )


def handle_exception(
    exception: Exception, 
    request_id: str = None, 
    context: Dict[str, Any] = None
) -> BaseOfferAutomationError:
    """
    Convert any exception to a structured offer automation error.
    
    Args:
        exception: The original exception
        request_id: Request ID for tracking
        context: Additional context information
    
    Returns:
        BaseOfferAutomationError: Structured error with context
    """
    if isinstance(exception, BaseOfferAutomationError):
        # Already a structured error, just update request_id if needed
        if request_id and not exception.request_id:
            exception.request_id = request_id
        return exception
    
    # Convert generic exception to structured error
    error_context = context or {}
    error_context['original_exception'] = str(exception)
    error_context['exception_type'] = type(exception).__name__
    
    return BaseOfferAutomationError(
        message=f"Unexpected error: {str(exception)}",
        error_code="UNEXPECTED_ERROR",
        context=error_context,
        request_id=request_id,
        recovery_suggestions=[
            "Check application logs for detailed error information",
            "Verify system resources and dependencies",
            "Try the operation again",
            "Contact system administrator if error persists"
        ]
    ) 