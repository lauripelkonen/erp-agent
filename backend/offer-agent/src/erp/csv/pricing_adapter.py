"""
CSV Pricing Adapter

Implements the PricingService interface for CSV-based pricing.
Uses simple pricing rules for demo purposes.
"""
from typing import List, Optional
from decimal import Decimal

from src.erp.base.pricing_service import PricingService
from src.domain.offer import Offer, OfferLine
from src.pricing.net_price import OfferPricing, LineItemPricing
from src.product_matching.matcher_class import ProductMatch
from src.utils.logger import get_logger


class CSVPricingAdapter(PricingService):
    """CSV implementation of the PricingService interface."""

    def __init__(self):
        """Initialize the CSV pricing adapter."""
        self.logger = get_logger(__name__)
        self.logger.info("CSV Pricing Adapter initialized - using simple demo pricing")

    @property
    def supports_database_optimization(self) -> bool:
        """CSV mode does not support database optimization."""
        return False

    async def calculate_offer_pricing(self, offer: Offer, discount_percent: float = 0.0) -> OfferPricing:
        """Calculate pricing for an offer."""
        try:
            line_items = []
            subtotal = Decimal('0')

            for line in offer.lines:
                # Simple pricing: use unit price from product
                unit_price = Decimal(str(line.unit_price))
                list_price = unit_price  # Same as unit price in demo
                quantity = Decimal(str(line.quantity))
                line_discount = Decimal(str(line.discount_percent)) / 100

                # Calculate line total
                line_subtotal = unit_price * quantity
                line_discount_amount = line_subtotal * line_discount
                line_net_price = unit_price * (1 - line_discount)
                line_total = line_subtotal - line_discount_amount
                line_vat = line_total * Decimal('0.24')

                line_pricing = LineItemPricing(
                    product_code=line.product_code,
                    product_name=line.product_name,
                    quantity=float(quantity),
                    unit_price=float(unit_price),
                    list_price=float(list_price),
                    discount_percent=float(line_discount * 100),
                    discount_amount=float(line_discount_amount),
                    net_price=float(line_net_price),
                    line_total=float(line_total),
                    vat_rate=24.0,
                    vat_amount=float(line_vat),
                )

                line_items.append(line_pricing)
                subtotal += line_total

            # Apply offer-level discount if any
            offer_discount_decimal = Decimal(str(discount_percent)) / 100
            offer_discount_amount = subtotal * offer_discount_decimal
            net_total = subtotal - offer_discount_amount

            # Calculate VAT
            vat_amount = net_total * Decimal('0.24')
            total_amount = net_total + vat_amount

            return OfferPricing(
                line_items=line_items,
                subtotal=float(subtotal),
                total_discount_percent=discount_percent,
                total_discount_amount=float(offer_discount_amount),
                net_total=float(net_total),
                vat_amount=float(vat_amount),
                total_amount=float(total_amount),
                currency='EUR',
            )

        except Exception as e:
            self.logger.error(f"Error calculating pricing: {e}")
            import traceback
            traceback.print_exc()
            # Return zero pricing on error
            return OfferPricing(
                line_items=[],
                subtotal=0.0,
                total_discount_percent=0.0,
                total_discount_amount=0.0,
                net_total=0.0,
                vat_amount=0.0,
                total_amount=0.0,
                currency='EUR',
            )

    async def calculate_pricing(
        self,
        customer_id: str,
        matched_products: List[ProductMatch],
        **kwargs
    ) -> OfferPricing:
        """Calculate complete pricing for an offer."""
        try:
            line_items = []
            subtotal = Decimal('0')

            for match in matched_products:
                # Get unit price from the matched product
                unit_price = Decimal(str(match.unit_price)) if match.unit_price else Decimal('0')
                list_price = unit_price
                quantity = Decimal(str(match.quantity))

                # Simple discount logic
                discount_percent = await self.get_customer_discount(customer_id, match.product_code)
                line_discount = Decimal(str(discount_percent)) / 100

                # Calculate line total
                line_subtotal = unit_price * quantity
                line_discount_amount = line_subtotal * line_discount
                line_net_price = unit_price * (1 - line_discount)
                line_total = line_subtotal - line_discount_amount
                line_vat = line_total * Decimal('0.24')

                line_pricing = LineItemPricing(
                    product_code=match.product_code,
                    product_name=match.product_name or "",
                    quantity=float(quantity),
                    unit_price=float(unit_price),
                    list_price=float(list_price),
                    discount_percent=discount_percent,
                    discount_amount=float(line_discount_amount),
                    net_price=float(line_net_price),
                    line_total=float(line_total),
                    vat_rate=24.0,
                    vat_amount=float(line_vat),
                )

                line_items.append(line_pricing)
                subtotal += line_total

            # Calculate VAT
            vat_amount = subtotal * Decimal('0.24')
            total_amount = subtotal + vat_amount

            return OfferPricing(
                line_items=line_items,
                subtotal=float(subtotal),
                total_discount_percent=0.0,
                total_discount_amount=0.0,
                net_total=float(subtotal),
                vat_amount=float(vat_amount),
                total_amount=float(total_amount),
                currency='EUR',
            )

        except Exception as e:
            self.logger.error(f"Error calculating pricing: {e}")
            return OfferPricing(
                line_items=[],
                subtotal=0.0,
                total_discount_percent=0.0,
                total_discount_amount=0.0,
                net_total=0.0,
                vat_amount=0.0,
                total_amount=0.0,
                currency='EUR',
            )

    async def calculate_line_pricing(
        self,
        customer_id: str,
        product_code: str,
        quantity: float,
        **kwargs
    ) -> LineItemPricing:
        """Calculate pricing for a single product line."""
        # Get product price (in demo, use a default price)
        unit_price = kwargs.get('unit_price', 10.0)
        list_price = unit_price
        product_name = kwargs.get('product_name', '')

        # Get discount
        discount_percent = await self.get_customer_discount(customer_id, product_code)

        # Calculate
        subtotal = unit_price * quantity
        discount_amount = subtotal * (discount_percent / 100)
        net_price = unit_price * (1 - discount_percent / 100)
        line_total = subtotal - discount_amount
        vat_amount = line_total * 0.24

        return LineItemPricing(
            product_code=product_code,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            list_price=list_price,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            net_price=net_price,
            line_total=line_total,
            vat_rate=24.0,
            vat_amount=vat_amount,
        )

    async def get_customer_discount(self, customer_id: str, product_code: str) -> float:
        """Get customer-specific discount (simple demo: no special discounts)."""
        return 0.0

    async def get_customer_group_discount(self, customer_id: str, product_group: str) -> float:
        """Get customer discount for a product group (simple demo: no discounts)."""
        return 0.0

    async def get_product_group_discount(self, product_group: str) -> float:
        """Get general discount for a product group (simple demo: no discounts)."""
        return 0.0

    async def get_historical_price(self, customer_id: str, product_name: str) -> Optional[float]:
        """Get historical price for a product (not supported in CSV demo mode)."""
        return None

    async def get_volume_discount(self, product_code: str, quantity: float) -> float:
        """Get volume-based discount (simple demo: 5% for qty > 10)."""
        if quantity > 10:
            return 5.0
        return 0.0

    async def calculate_delivery_cost(self, offer: Offer) -> float:
        """Calculate delivery cost (simple demo: free delivery)."""
        return 0.0
