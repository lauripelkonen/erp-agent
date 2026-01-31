"""
Workflow Definition

Defines the sequential steps for offer creation workflow.
Each step is ERP-agnostic and uses the repository interfaces.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

from src.domain.customer import Customer
from src.domain.person import Person
from src.domain.offer import Offer, OfferLine
from src.product_matching.matcher_class import ProductMatch


class WorkflowStep(Enum):
    """Enumeration of workflow steps."""
    PARSE_EMAIL = "parse_email"
    EXTRACT_COMPANY = "extract_company"
    FIND_CUSTOMER = "find_customer"
    FIND_SALESPERSON = "find_salesperson"
    EXTRACT_PRODUCTS = "extract_products"
    MATCH_PRODUCTS = "match_products"
    CALCULATE_PRICING = "calculate_pricing"
    BUILD_OFFER = "build_offer"
    CREATE_OFFER = "create_offer"
    VERIFY_OFFER = "verify_offer"
    SEND_CONFIRMATION = "send_confirmation"
    COMPLETE = "complete"


@dataclass
class WorkflowContext:
    """
    Context object that carries state through the workflow.

    This replaces the large number of variables in the old main.py.
    Each workflow step reads from and writes to this context.
    """
    # Input
    email_data: Dict[str, Any] = field(default_factory=dict)

    # Email parsing results
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None

    # Company extraction results
    company_name: Optional[str] = None
    customer_number: Optional[str] = None
    delivery_contact: Optional[str] = None
    customer_reference: Optional[str] = None
    extraction_confidence: float = 0.0

    # ERP lookups
    customer: Optional[Customer] = None
    salesperson: Optional[Person] = None

    # Product extraction and matching
    extracted_products: List[Dict[str, Any]] = field(default_factory=list)
    matched_products: List[ProductMatch] = field(default_factory=list)

    # Pricing
    pricing_result: Optional[Dict[str, Any]] = None

    # Offer
    offer: Optional[Offer] = None
    offer_number: Optional[str] = None

    # Verification
    verification_result: Optional[Dict[str, Any]] = None

    # Workflow state
    current_step: WorkflowStep = WorkflowStep.PARSE_EMAIL
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message to the context."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the context."""
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution."""
        return {
            'current_step': self.current_step.value,
            'company_name': self.company_name,
            'customer_number': self.customer_number,
            'offer_number': self.offer_number,
            'products_count': len(self.matched_products),
            'has_errors': self.has_errors(),
            'errors': self.errors,
            'warnings': self.warnings,
        }


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.

    Provides a clean interface for the caller to understand what happened.
    """
    success: bool
    offer_number: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    context: Optional[WorkflowContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for API responses."""
        return {
            'success': self.success,
            'offer_number': self.offer_number,
            'customer_name': self.customer_name,
            'total_amount': self.total_amount,
            'errors': self.errors,
            'warnings': self.warnings,
        }


class WorkflowDefinition:
    """
    Defines the sequence of steps for offer creation.

    This is a pure definition class - it doesn't execute anything.
    The Orchestrator will execute these steps.
    """

    # Define the workflow sequence
    WORKFLOW_STEPS = [
        WorkflowStep.PARSE_EMAIL,
        WorkflowStep.EXTRACT_COMPANY,
        WorkflowStep.FIND_CUSTOMER,
        WorkflowStep.FIND_SALESPERSON,
        WorkflowStep.EXTRACT_PRODUCTS,
        WorkflowStep.MATCH_PRODUCTS,
        WorkflowStep.CALCULATE_PRICING,
        WorkflowStep.BUILD_OFFER,
        WorkflowStep.CREATE_OFFER,
        WorkflowStep.VERIFY_OFFER,
        WorkflowStep.SEND_CONFIRMATION,
        WorkflowStep.COMPLETE,
    ]

    # Define which steps are critical (workflow fails if they fail)
    CRITICAL_STEPS = {
        WorkflowStep.PARSE_EMAIL,
        WorkflowStep.EXTRACT_COMPANY,
        WorkflowStep.FIND_CUSTOMER,
        WorkflowStep.MATCH_PRODUCTS,
        WorkflowStep.CALCULATE_PRICING,
        WorkflowStep.CREATE_OFFER,
    }

    # Define which steps can be retried
    RETRIABLE_STEPS = {
        WorkflowStep.FIND_CUSTOMER,
        WorkflowStep.FIND_SALESPERSON,
        WorkflowStep.MATCH_PRODUCTS,
        WorkflowStep.CREATE_OFFER,
    }

    @classmethod
    def get_next_step(cls, current_step: WorkflowStep) -> Optional[WorkflowStep]:
        """Get the next step in the workflow."""
        try:
            current_index = cls.WORKFLOW_STEPS.index(current_step)
            if current_index < len(cls.WORKFLOW_STEPS) - 1:
                return cls.WORKFLOW_STEPS[current_index + 1]
            return None
        except ValueError:
            return None

    @classmethod
    def is_critical_step(cls, step: WorkflowStep) -> bool:
        """Check if a step is critical (workflow fails if it fails)."""
        return step in cls.CRITICAL_STEPS

    @classmethod
    def is_retriable_step(cls, step: WorkflowStep) -> bool:
        """Check if a step can be retried."""
        return step in cls.RETRIABLE_STEPS

    @classmethod
    def get_workflow_description(cls) -> str:
        """Get a human-readable description of the workflow."""
        return """
        Offer Creation Workflow:

        1. PARSE_EMAIL - Extract sender, subject, body from email
        2. EXTRACT_COMPANY - Use AI to extract company name, contact, reference
        3. FIND_CUSTOMER - Look up customer in ERP system
        4. FIND_SALESPERSON - Look up responsible salesperson
        5. EXTRACT_PRODUCTS - Use AI to extract products from email
        6. MATCH_PRODUCTS - Match extracted products to ERP catalog
        7. CALCULATE_PRICING - Calculate discounts and pricing
        8. BUILD_OFFER - Construct offer object with all data
        9. CREATE_OFFER - Create offer in ERP system
        10. VERIFY_OFFER - Verify offer was created correctly
        11. SEND_CONFIRMATION - Send confirmation email
        12. COMPLETE - Workflow finished
        """
