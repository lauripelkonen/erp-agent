"""
Lemonsoft Field Mapper

Maps between generic domain models and Lemonsoft-specific API formats.
This centralized mapping layer makes it easy to understand and maintain
all Lemonsoft-specific field transformations.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from src.domain.customer import Customer
from src.domain.offer import Offer, OfferLine
from src.domain.product import Product
from src.domain.person import Person


class LemonsoftFieldMapper:
    """
    Maps between generic domain models and Lemonsoft API formats.

    This class centralizes all knowledge about Lemonsoft's field names,
    data structures, and conventions, making it easier to:
    - Understand Lemonsoft-specific requirements
    - Maintain field mappings in one place
    - Add new fields without changing business logic
    - Support API changes by updating only this mapper
    """

    # ==================== CUSTOMER MAPPING ====================

    def to_customer(self, lemonsoft_data: Dict[str, Any]) -> Customer:
        """
        Convert Lemonsoft customer API response to generic Customer model.

        Args:
            lemonsoft_data: Raw customer data from Lemonsoft API

        Returns:
            Generic Customer domain model
        """
        return Customer(
            id=str(lemonsoft_data.get('id', '')),
            customer_number=str(lemonsoft_data.get('number', '')),
            name=lemonsoft_data.get('name', ''),
            street=lemonsoft_data.get('street', ''),
            postal_code=lemonsoft_data.get('postal_code', ''),
            city=lemonsoft_data.get('city', ''),
            country=lemonsoft_data.get('country', 'Finland'),
            contact_person=lemonsoft_data.get('ceo_contact', ''),
            email=lemonsoft_data.get('email', ''),
            phone=lemonsoft_data.get('phone', ''),
            # Lemonsoft uses 'deny_credit', we use 'credit_allowed' (inverted)
            credit_allowed=not lemonsoft_data.get('deny_credit', False),
            # Salesperson/responsible person info
            responsible_person_number=lemonsoft_data.get('person_responsible_number'),
            responsible_person_name=lemonsoft_data.get('person_responsible_name'),
            # Store original Lemonsoft data for reference
            erp_metadata=lemonsoft_data
        )

    def from_customer(self, customer: Customer) -> Dict[str, Any]:
        """
        Convert generic Customer model to Lemonsoft API format.

        Args:
            customer: Generic Customer domain model

        Returns:
            Dict in Lemonsoft API format
        """
        return {
            "id": customer.id,
            "number": customer.customer_number,
            "name": customer.name,
            "street": customer.street,
            "postal_code": customer.postal_code,
            "city": customer.city,
            "country": customer.country,
            "ceo_contact": customer.contact_person,
            "email": customer.email,
            "phone": customer.phone,
            # Invert credit_allowed back to deny_credit
            "deny_credit": not customer.credit_allowed,
            "person_responsible_number": customer.responsible_person_number,
        }

    # ==================== PERSON MAPPING ====================

    def to_person(self, lemonsoft_data: Dict[str, Any]) -> Person:
        """
        Convert Lemonsoft person API response to generic Person model.

        Args:
            lemonsoft_data: Raw person data from Lemonsoft API

        Returns:
            Generic Person domain model
        """
        return Person(
            id=str(lemonsoft_data.get('id', '')),
            number=str(lemonsoft_data.get('number', '')),
            name=lemonsoft_data.get('name', ''),
            email=lemonsoft_data.get('email', ''),
            phone=lemonsoft_data.get('phone', ''),
            role=lemonsoft_data.get('role', ''),
            active=lemonsoft_data.get('active', True),
            erp_metadata=lemonsoft_data
        )

    # ==================== PRODUCT MAPPING ====================

    def to_product(self, lemonsoft_data: Dict[str, Any]) -> Product:
        """
        Convert Lemonsoft product API response to generic Product model.

        Args:
            lemonsoft_data: Raw product data from Lemonsoft API

        Returns:
            Generic Product domain model
        """
        return Product(
            code=lemonsoft_data.get('product_code', lemonsoft_data.get('code', '')),
            name=lemonsoft_data.get('product_name', lemonsoft_data.get('name', '')),
            description=lemonsoft_data.get('description', ''),
            unit=lemonsoft_data.get('unit', 'KPL'),
            product_group=lemonsoft_data.get('product_group', ''),
            # Lemonsoft uses 'product_exp_price' for list price
            list_price=float(lemonsoft_data.get('product_exp_price', 0.0)),
            unit_price=float(lemonsoft_data.get('unit_price', lemonsoft_data.get('product_exp_price', 0.0))),
            stock_quantity=lemonsoft_data.get('stock_quantity'),
            stock_location=lemonsoft_data.get('stock_location'),
            active=lemonsoft_data.get('active', True),
            erp_metadata=lemonsoft_data
        )

    # ==================== OFFER MAPPING ====================

    def from_offer(self, offer: Offer, invoicing_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert generic Offer model to Lemonsoft API format.

        This is the most complex mapping as Lemonsoft has 20+ specific fields
        for offers with unique naming conventions and required structures.

        Args:
            offer: Generic Offer domain model
            invoicing_details: Optional invoicing details from customer lookup

        Returns:
            Dict in Lemonsoft API format for PUT /api/offers
        """
        invoicing_details = invoicing_details or {}

        # Map delivery method based on credit_allowed
        # Lemonsoft uses code 33 for prepayment, 6 for invoice
        delivery_method = offer.delivery_method
        if delivery_method is None:
            # Default based on typical credit logic (if we had customer info)
            delivery_method = 6  # Default to invoice delivery

        lemonsoft_offer = {
            # === Date fields ===
            "offer_date": offer.offer_date.isoformat() if offer.offer_date else datetime.now().isoformat(),
            "offer_valid_date": offer.valid_until.isoformat() if offer.valid_until else None,

            # === Reference fields ===
            "offer_our_reference": offer.our_reference,
            "offer_customer_reference": offer.customer_reference,

            # === Customer fields (offer customer = invoicing address) ===
            "offer_customer_number": invoicing_details.get('offer_customer_number', offer.customer_id),
            "offer_customer_name1": invoicing_details.get('offer_customer_name1', offer.customer_name),
            "offer_customer_name2": invoicing_details.get('offer_customer_name2', ''),
            "offer_customer_address1": invoicing_details.get('offer_customer_address1', ''),
            "offer_customer_address2": invoicing_details.get('offer_customer_address2', ''),
            "offer_customer_address3": invoicing_details.get('offer_customer_address3', ''),
            "offer_customer_contact": offer.offer_contact or '',
            "offer_customer_country": "FINLAND",

            # === Delivery customer fields (delivery address) ===
            "delivery_customer_number": offer.customer_id,
            "delivery_customer_name1": offer.customer_name,
            "delivery_customer_address1": "",
            "delivery_customer_address2": "",
            "delivery_customer_address3": "",
            "delivery_customer_contact": offer.delivery_contact,

            # === Payment and delivery terms ===
            "payment_term": offer.payment_term,
            "delivery_method": delivery_method,
            "offer_delivery_code": "",
            "offer_delivery_term": offer.delivery_term or 1,

            # === Offer metadata ===
            "offer_note": offer.notes or "Automated offer from email",
            "offer_type": 6,  # Lemonsoft offer type
            "company_location_id": offer.company_location_id or 1,
            "language_code": offer.language_code or "FIN",

            # === Sales phase (Lemonsoft specific) ===
            "Sales_phase_collection": 1,
            "Offer_current_sales_phase": 1,
        }

        # === Responsible person fields (only if set) ===
        if offer.responsible_person_number:
            lemonsoft_offer.update({
                "person_invoice_res_person": offer.responsible_person_number,
                "person_seller_number": offer.responsible_person_number,
            })

        # === Merge any ERP-specific metadata ===
        if offer.erp_metadata:
            lemonsoft_offer.update(offer.erp_metadata)

        return lemonsoft_offer

    def from_offer_line(self, line: OfferLine) -> Dict[str, Any]:
        """
        Convert generic OfferLine to Lemonsoft offer row format.

        Args:
            line: Generic OfferLine domain model

        Returns:
            Dict in Lemonsoft API format for POST /api/offers/{number}/offerrows
        """
        # Lemonsoft-specific defaults from analysis
        DEFAULT_ACCOUNT = "3000"
        DEFAULT_COST_CENTER = "05900"
        DEFAULT_PRODUCT_STOCK = "10"

        lemonsoft_row = {
            "product_code": line.product_code,
            "quantity": line.quantity,
            "unit": line.unit,
            "unit_price": line.unit_price,
            "discount_percent": line.discount_percent,
            "position": line.position,
            "description": line.description or line.product_name,

            # Lemonsoft-specific fields
            "account": line.erp_metadata.get('account', DEFAULT_ACCOUNT),
            "cost_center": line.erp_metadata.get('cost_center', DEFAULT_COST_CENTER),
            "product_stock": line.erp_metadata.get('product_stock', DEFAULT_PRODUCT_STOCK),
        }

        # Merge any additional ERP-specific metadata
        if line.erp_metadata:
            lemonsoft_row.update(line.erp_metadata)

        return lemonsoft_row

    def to_offer(self, lemonsoft_data: Dict[str, Any]) -> Offer:
        """
        Convert Lemonsoft offer API response to generic Offer model.

        Args:
            lemonsoft_data: Raw offer data from Lemonsoft API

        Returns:
            Generic Offer domain model
        """
        # Parse dates
        offer_date = None
        valid_until = None
        if lemonsoft_data.get('offer_date'):
            try:
                offer_date = datetime.fromisoformat(lemonsoft_data['offer_date'])
            except:
                pass
        if lemonsoft_data.get('offer_valid_date'):
            try:
                valid_until = datetime.fromisoformat(lemonsoft_data['offer_valid_date'])
            except:
                pass

        return Offer(
            customer_id=lemonsoft_data.get('offer_customer_number', ''),
            customer_name=lemonsoft_data.get('offer_customer_name1', ''),
            offer_number=lemonsoft_data.get('offer_number', lemonsoft_data.get('number')),
            offer_date=offer_date,
            valid_until=valid_until,
            our_reference=lemonsoft_data.get('offer_our_reference', ''),
            customer_reference=lemonsoft_data.get('offer_customer_reference', ''),
            delivery_contact=lemonsoft_data.get('delivery_customer_contact', ''),
            offer_contact=lemonsoft_data.get('offer_customer_contact'),
            payment_term=lemonsoft_data.get('payment_term'),
            delivery_method=lemonsoft_data.get('delivery_method'),
            delivery_term=lemonsoft_data.get('offer_delivery_term'),
            responsible_person_number=lemonsoft_data.get('person_seller_number'),
            language_code=lemonsoft_data.get('language_code', 'FIN'),
            company_location_id=lemonsoft_data.get('company_location_id'),
            notes=lemonsoft_data.get('offer_note', ''),
            erp_metadata=lemonsoft_data
        )

    # ==================== HELPER METHODS ====================

    def map_delivery_method(self, credit_allowed: bool) -> int:
        """
        Map credit status to Lemonsoft delivery method code.

        Args:
            credit_allowed: Whether customer allows credit

        Returns:
            Lemonsoft delivery method code (33 = prepayment, 6 = invoice)
        """
        return 6 if credit_allowed else 33

    def map_vat_code(self, vat_rate: float) -> str:
        """
        Map VAT rate to Lemonsoft VAT code.

        Args:
            vat_rate: VAT rate percentage

        Returns:
            Lemonsoft VAT code
        """
        # Lemonsoft VAT code mapping (extend as needed)
        vat_mapping = {
            25.5: "FI25",
            24.0: "FI24",
            14.0: "FI14",
            10.0: "FI10",
            0.0: "FI0",
        }
        return vat_mapping.get(vat_rate, "FI25")
