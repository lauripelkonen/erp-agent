# Purchase Order Automation

This document explains how to use the automated purchase order creation system that generates purchase orders from transfer recommendations.

## Overview

The purchase order automation system:
1. **Analyzes** low stock products using transfer optimization
2. **Generates** purchase order recommendations based on forecasting
3. **Creates** purchase orders automatically using the Lemonsoft API
4. **Maps** delivery information based on target warehouse

## Quick Start

### Run Purchase Order Creation

```bash
# Create purchase orders for warehouse 405 (Suutarila)
python create_purchase_order_for_transfers.py
```

### Programmatic Usage

```python
from src.orders.purchase_order_creator import create_purchase_order_for_warehouse

# Create purchase order for specific warehouse
result = await create_purchase_order_for_warehouse(
    target_warehouse=405,      # Warehouse number
    max_products=15,           # Maximum products to include
    target_days=30,            # Days of stock to target
    min_priority_level="Medium" # Minimum priority level
)

if result:
    print(f"Purchase Order created: {result['id']}")
```

## Key Features

### Automatic Supplier/Delivery Mapping

**Supplier (Always the same):**
- Customer Number: 100001
- Name: ESPOO PÄÄVARASTO, LVI-WaBeK Oy
- Address: Koskelontie 22, 02920 ESPOO
- Contact: TOMI LÄHTEENMÄKI
- Buyer: 212

**Delivery Customers (Mapped by warehouse):**

| Warehouse | Name | Address | Contact |
|-----------|------|---------|---------|
| 402 | WACENTER TURKU | EMMAUKSENKUJA 3, 20380 TURKU | Veli-Pekka Korpi |
| 403 | WACENTER TAMPERE | HIITINTIE 8, 33400 TAMPERE | ARI KAASALAINEN |
| 404 | LVI-Wabek Oy OULU | PORTINKAARRE 5, 90410 OULU | Janne Rajavaara |
| 405 | WACENTER SUUTARILA | SUUTARILANTIE 61, 00750 HELSINKI | Ilpo Paasela |
| 406 | WACENTER LEMPÄÄLÄ | KALLIOKUMMUNTIE 2, 37570 LEMPÄÄLÄ | Jesse Santamaa |
| 407 | WACENTER JYVÄSKYLÄ | VASARAKATU 23B, 40320 JYVÄSKYLÄ | Leo Lahtinen |
| 408 | WACENTER HERTTONIEMI | LINNANRAKENTAJANTIE 4, 00880 HELSINKI | Tomi Koskimaa |
| 409 | MINIWACENTER PARKANO | VARASTOKATU 62, 39700 PARKANO | Juha Kivimäki |

### Product Information Preservation

The system preserves all important product information:
- **Product SKU** - Exact product code
- **Product Name** - Full product name + extra name if available
- **Pricing** - Uses warehouse-specific average purchase price
- **Quantities** - Optimized based on forecasting and packaging
- **Tax Calculation** - Automatic VAT calculation (25.5%)

### Date/Time Formatting

All dates use the required format: `2025-07-01T07:28:53`
- **Order Date**: Current date/time
- **Delivery Date**: Current date/time 
- **Generated automatically** for consistency

## Configuration Options

### Priority Levels

Filter products by minimum priority:
- `"Critical"` - Only critical shortage items
- `"Urgent"` - Urgent and critical items
- `"High"` - High priority and above
- `"Medium"` - Medium priority and above (default)
- `"Low"` - All priority levels

### Target Stock Duration

Configure how many days of stock to target:
- `7` - One week
- `14` - Two weeks  
- `30` - One month (default)
- `60` - Two months

### Maximum Products

Limit the number of products in a single purchase order:
- `10` - Small orders for testing
- `20` - Medium orders (default)
- `50` - Large orders
- `100` - Maximum recommended

## Workflow Example

```python
#!/usr/bin/env python3
import asyncio
from src.orders.purchase_order_creator import PurchaseOrderCreator
from src.products.transfer_optimizer_integration import TransferOptimizerIntegration

async def custom_purchase_order_workflow():
    # Step 1: Get transfer recommendations
    integration = TransferOptimizerIntegration()
    await integration.api_client.initialize()
    
    recommendations = await integration.analyze_low_stock_transfers(
        target_warehouse=405,
        max_products=20,
        target_days=30
    )
    
    await integration.api_client.close()
    
    # Step 2: Filter recommendations (optional)
    urgent_items = [
        rec for rec in recommendations 
        if rec.priority in ['Critical', 'Urgent'] and 
           rec.is_feasible and 
           rec.recommended_quantity > 0
    ]
    
    if urgent_items:
        # Step 3: Create purchase order
        creator = PurchaseOrderCreator()
        result = await creator.create_purchase_order(urgent_items, 405)
        
        if result:
            print(f"Emergency purchase order created: {result['id']}")
            return result
    
    return None

# Run the workflow
asyncio.run(custom_purchase_order_workflow())
```

## API Integration

### Purchase Order Structure

The system creates purchase orders following the Lemonsoft API specification:

```json
{
  "currency_code": "EUR",
  "delivery_date": "2025-07-08T14:30:00",
  "language_code": "FIN",
  "order_number": 20250708,
  "purchase_order_date": "2025-07-08T14:30:00",
  
  "customer_number": 100001,
  "customer_name1": "ESPOO PÄÄVARASTO, LVI-WaBeK Oy",
  
  "delivery_customer_number": 100005,
  "delivery_customer_name1": "WACENTER SUUTARILA",
  
  "rows": [
    {
      "product_code": "12345",
      "product_name": "PRODUCT NAME - EXTRA NAME",
      "quantity": 10,
      "unit_price": 25.50,
      "total": 255.00,
      "tax_rate": 25.5,
      "tax_amount": 65.03
    }
  ],
  
  "totalsum": 320.03
}
```

### Error Handling

The system includes comprehensive error handling:
- **API connection errors** - Automatic retry and fallback
- **Invalid warehouse numbers** - Clear error messages
- **No feasible recommendations** - Graceful handling
- **Missing product data** - Skip and continue processing

## Testing and Validation

### Test with Small Orders

```bash
# Test with 5 products only
python -c "
import asyncio
from src.orders.purchase_order_creator import create_purchase_order_for_warehouse

async def test():
    result = await create_purchase_order_for_warehouse(
        target_warehouse=405,
        max_products=5,
        min_priority_level='High'
    )
    print('Test result:', result is not None)

asyncio.run(test())
"
```

### Verify Purchase Order

After creation, verify in Lemonsoft:
1. Check order exists with returned ID
2. Verify supplier and delivery information
3. Confirm product details and quantities
4. Review total amounts and tax calculations

## Integration with Existing Systems

### With Transfer Analysis

The purchase order creator integrates seamlessly with existing transfer analysis:

```python
# Combined workflow
from src.orders.purchase_order_creator import create_purchase_order_for_warehouse

# This function does everything:
# 1. Runs transfer analysis
# 2. Filters recommendations
# 3. Creates purchase order
# 4. Returns result
result = await create_purchase_order_for_warehouse(405)
```

### With Manual Recommendations

You can also create purchase orders from manual recommendations:

```python
from src.orders.purchase_order_creator import PurchaseOrderCreator

creator = PurchaseOrderCreator()

# Create purchase order from existing recommendations
result = await creator.create_purchase_order(
    recommendations=your_recommendations,
    target_warehouse=405
)
```

## Troubleshooting

### Common Issues

**No purchase order created:**
- Check if products meet minimum priority criteria
- Verify warehouse number is supported (402-409)
- Ensure API credentials are configured

**API errors:**
- Verify Lemonsoft API access
- Check network connectivity
- Confirm API endpoints are available

**Incorrect delivery information:**
- Verify warehouse number mapping
- Check delivery customer data in WAREHOUSE_DELIVERY_INFO

### Logging

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger('src.orders.purchase_order_creator').setLevel(logging.DEBUG)
logging.getLogger('src.lemonsoft.api_client').setLevel(logging.DEBUG)
```

## Next Steps

1. **Test the system** with a small warehouse first
2. **Review created orders** in Lemonsoft before approval
3. **Monitor performance** and adjust parameters as needed
4. **Integrate with scheduling** for automated regular orders
5. **Extend functionality** for additional warehouses or suppliers 