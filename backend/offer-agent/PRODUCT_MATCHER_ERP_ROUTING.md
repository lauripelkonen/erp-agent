# 🔀 Product Matcher ERP Routing - Complete

**Date:** November 14, 2025
**Status:** Implemented
**Feature:** ProductMatcher now routes through ERP adapters instead of direct SQL

---

## 📋 Overview

The `ProductMatcher` has been refactored to support **multiple ERP systems** through the adapter pattern. Instead of hardcoded Lemonsoft SQL queries, it now routes product searches through the `ProductRepository` interface.

### What Changed:

**Before (Lemonsoft-only):**
```python
# ProductMatcher hardcoded to Lemonsoft SQL
matcher = ProductMatcher()
# Executes Lemonsoft-specific SQL queries directly
```

**After (ERP-agnostic):**
```python
# ProductMatcher works with ANY ERP via repository
from src.erp.factory import ERPFactory

factory = ERPFactory(erp_type="lemonsoft")  # or "jeeves", "oscar"
product_repo = factory.create_product_repository()

matcher = ProductMatcher(product_repository=product_repo)
# Routes through repository → works with any ERP!
```

---

## 🔧 Changes Made

### 1. **ProductRepository Interface Extended**

**File:** `src/erp/base/product_repository.py`

Added two new abstract methods:

```python
class ProductRepository(ABC):
    # ... existing methods ...

    @abstractmethod
    async def wildcard_search(self, pattern: str) -> Optional[pd.DataFrame]:
        """
        Perform wildcard search on products using a search pattern.

        Used by ProductMatcher to find products that match unclear terms
        from emails (e.g., "heat pump" might match product codes or
        descriptions containing those words).

        Returns:
            DataFrame with product search results or None
        """
        pass

    @abstractmethod
    async def search_by_product_codes(self, product_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        Search for products by exact product codes (batch lookup).

        Used by ProductMatcher when it has identified exact product codes
        from the email and needs to fetch their details.

        Returns:
            DataFrame with product search results or None
        """
        pass
```

### 2. **Lemonsoft ProductAdapter Implementation**

**File:** `src/erp/lemonsoft/product_adapter.py`

Implemented both methods with Lemonsoft-specific SQL logic:

```python
class LemonsoftProductAdapter(ProductRepository):
    async def wildcard_search(self, pattern: str) -> Optional[pd.DataFrame]:
        """Lemonsoft-specific wildcard search using SQL."""
        # Complex SQL query with:
        # - yearly_sales CTE
        # - total_stock CTE
        # - Joins on products, product_dimensions, product_texts, product_stocks
        # - Filters: active products, product groups, no special attributes
        # Returns DataFrame with 12 columns
        pass

    async def search_by_product_codes(self, product_codes: List[str]) -> Optional[pd.DataFrame]:
        """Lemonsoft-specific batch product lookup using SQL."""
        # Same complex query but with IN clause for product codes
        # Returns same DataFrame format
        pass

    # Helper methods:
    async def _execute_sql_query(self, query: str) -> List[Any]:
        """Execute SQL using create_database_client()"""

    def _classify_product_priority(self, group_code: int) -> str:
        """Lemonsoft-specific: group_code < 1000 = priority"""
```

**SQL Query Features:**
- Fetches yearly sales data (last 12 months)
- Fetches current stock levels
- Joins product dimensions and texts
- Filters inactive/non-stock products
- Excludes products with attribute_code = 30
- Returns rich product data for matching

### 3. **ProductMatcher Refactored**

**File:** `src/product_matching/product_matcher.py`

Updated to accept optional `product_repository`:

```python
class ProductMatcher:
    def __init__(
        self,
        products_csv_path: Optional[str] = None,
        max_iterations: int = 5,
        product_repository=None  # NEW PARAMETER
    ):
        self.product_repository = product_repository

        if self.product_repository:
            # Use repository (ERP-agnostic mode)
            self.logger.info(f"Using repository: {type(product_repository).__name__}")
        else:
            # Legacy mode (backward compatibility)
            self.lemonsoft_client = LemonsoftAPIClient()
```

**Search Methods Updated:**

```python
async def _local_wildcard_search(self, pattern: str):
    """Routes to repository if available, otherwise legacy SQL."""
    if self.product_repository:
        # ERP-agnostic: use repository
        return await self.product_repository.wildcard_search(pattern)
    else:
        # Legacy: direct Lemonsoft SQL
        return await self._legacy_local_wildcard_search(pattern)

async def _search_by_product_codes(self, product_codes: list):
    """Routes to repository if available, otherwise legacy SQL."""
    if self.product_repository:
        # ERP-agnostic: use repository
        return await self.product_repository.search_by_product_codes(product_codes)
    else:
        # Legacy: direct Lemonsoft SQL
        return await self._legacy_search_by_product_codes(product_codes)
```

---

## 🎯 Usage Examples

### Example 1: Use with Lemonsoft (ERP-agnostic way)

```python
from src.erp.factory import ERPFactory
from src.product_matching.product_matcher import ProductMatcher

# Create Lemonsoft product repository
factory = ERPFactory(erp_type="lemonsoft")
product_repo = factory.create_product_repository()

# Create matcher with repository
matcher = ProductMatcher(product_repository=product_repo)

# Use matcher (routes through repository)
unclear_terms = ["heat pump", "air conditioner"]
matches = await matcher.match_products(unclear_terms)

# Works exactly the same, but ERP-agnostic!
```

### Example 2: Use with Jeeves (future)

```python
from src.erp.factory import ERPFactory
from src.product_matching.product_matcher import ProductMatcher

# Create Jeeves product repository
factory = ERPFactory(erp_type="jeeves")
product_repo = factory.create_product_repository()

# Create matcher with repository
matcher = ProductMatcher(product_repository=product_repo)

# Same code, different ERP!
matches = await matcher.match_products(unclear_terms)
```

### Example 3: Legacy Mode (backward compatibility)

```python
from src.product_matching.product_matcher import ProductMatcher

# No repository provided = legacy Lemonsoft mode
matcher = ProductMatcher()

# Works exactly as before (direct SQL)
matches = await matcher.match_products(unclear_terms)
```

---

## 🔀 How It Routes

```
┌─────────────────────────────────────────────────────────────┐
│                  ProductMatcher                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  _local_wildcard_search(pattern)                      │  │
│  │  _search_by_product_codes(codes)                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
│              ┌────────────┴─────────────┐                   │
│              │                          │                   │
│         Has Repository?             No Repository?          │
│              │                          │                   │
└──────────────┼──────────────────────────┼───────────────────┘
               │                          │
               │                          │
┌──────────────▼──────────────┐  ┌────────▼──────────────────┐
│  ProductRepository          │  │  Legacy Lemonsoft SQL     │
│  (ERP-agnostic)             │  │  (backward compatible)    │
│                             │  │                           │
│  wildcard_search()          │  │  _legacy_local_wildcard_  │
│  search_by_product_codes()  │  │  search()                 │
│                             │  │                           │
│  Routes to ERP adapter:     │  │  Direct SQL queries       │
│  - Lemonsoft                │  │  (old code)               │
│  - Jeeves                   │  │                           │
│  - Oscar                    │  │                           │
└─────────────────────────────┘  └───────────────────────────┘
```

---

## 📊 DataFrame Format

Both methods return a pandas DataFrame with these columns:

| Column | Type | Description |
|--------|------|-------------|
| id | str | Product ID in ERP |
| sku | str | Product code/SKU |
| name | str | Product name/description |
| extra_name | str | Additional description |
| price | float | Product list price |
| product_searchcode | str | Search code |
| description | str | Long description/notes |
| group_code | int | Product group code |
| priority | str | 'priority' or 'non_priority' |
| total_stock | float | Available stock quantity |
| yearly_sales_qty | float | Sales quantity (last 12 months) |
| data_source | str | 'SQL_DATABASE' or 'PRODUCT_CODE_SEARCH' |

This format is **ERP-agnostic** - each ERP adapter must return this same structure.

---

## 🚀 How to Add Support for Jeeves ERP

### Step 1: Implement JeevesProductAdapter

Create `src/erp/jeeves/product_adapter.py`:

```python
from src.erp.base.product_repository import ProductRepository
import pandas as pd

class JeevesProductAdapter(ProductRepository):
    async def wildcard_search(self, pattern: str) -> Optional[pd.DataFrame]:
        """Jeeves-specific wildcard search."""
        # Option 1: Use Jeeves API
        results = await self.jeeves_client.search_products(pattern)

        # Option 2: Use Jeeves SQL database
        query = f"SELECT ... FROM jeeves_products WHERE ..."
        results = await self._execute_jeeves_query(query)

        # Convert to DataFrame format (same columns as above)
        df = pd.DataFrame([
            {
                'id': product['id'],
                'sku': product['code'],
                'name': product['name'],
                'extra_name': product['description'],
                'price': product['price'],
                # ... map all 12 columns ...
                'priority': self._classify_priority(product),
                'data_source': 'JEEVES_API'
            }
            for product in results
        ])

        return df if not df.empty else None

    async def search_by_product_codes(self, product_codes: List[str]) -> Optional[pd.DataFrame]:
        """Jeeves-specific batch lookup."""
        # Same approach, but filter by exact codes
        results = await self.jeeves_client.get_products_by_codes(product_codes)

        # Convert to same DataFrame format
        df = pd.DataFrame(...)
        return df if not df.empty else None

    def _classify_priority(self, product):
        """Jeeves-specific priority logic."""
        # Jeeves might use different criteria
        return 'priority' if product['category'] == 'A' else 'non_priority'
```

### Step 2: Update ERPFactory

In `src/erp/factory.py`:

```python
def create_product_repository(self) -> ProductRepository:
    if self.erp_type == "lemonsoft":
        from src.erp.lemonsoft.product_adapter import LemonsoftProductAdapter
        return LemonsoftProductAdapter()

    elif self.erp_type == "jeeves":
        from src.erp.jeeves.product_adapter import JeevesProductAdapter
        return JeevesProductAdapter()  # NEW!

    # ...
```

### Step 3: Use It!

```python
factory = ERPFactory(erp_type="jeeves")
product_repo = factory.create_product_repository()
matcher = ProductMatcher(product_repository=product_repo)

# ProductMatcher now works with Jeeves!
matches = await matcher.match_products(["unclear term"])
```

**That's it!** ProductMatcher doesn't need any changes.

---

## 💡 Key Benefits

### 1. **ERP Independence**
- ProductMatcher no longer tied to Lemonsoft
- Works with any ERP via repository interface
- Easy to add new ERPs

### 2. **Backward Compatibility**
- Existing code continues to work (legacy mode)
- No breaking changes
- Gradual migration path

### 3. **Clean Separation**
- Product search logic separated from matching logic
- ERP-specific code isolated in adapters
- Easier to test and maintain

### 4. **Flexibility**
- Each ERP can implement search differently:
  - SQL queries (Lemonsoft)
  - REST API calls (Jeeves)
  - GraphQL (Oscar)
  - Mix of approaches

---

## 📁 Files Changed

1. **`src/erp/base/product_repository.py`** (+54 lines)
   - Added `wildcard_search()` method
   - Added `search_by_product_codes()` method

2. **`src/erp/lemonsoft/product_adapter.py`** (+353 lines)
   - Implemented `wildcard_search()` (180 lines)
   - Implemented `search_by_product_codes()` (158 lines)
   - Added `_execute_sql_query()` helper
   - Added `_classify_product_priority()` helper

3. **`src/product_matching/product_matcher.py`** (+27 lines)
   - Added `product_repository` parameter to `__init__`
   - Updated `_local_wildcard_search()` to route through repository
   - Updated `_search_by_product_codes()` to route through repository
   - Renamed old methods to `_legacy_*` for backward compatibility

**Total:** ~434 lines added, 0 lines deleted (100% backward compatible)

---

## ✅ Testing

### Test with Lemonsoft (ERP-agnostic mode):

```python
import asyncio
from src.erp.factory import ERPFactory
from src.product_matching.product_matcher import ProductMatcher

async def test_lemonsoft_via_repository():
    factory = ERPFactory(erp_type="lemonsoft")
    product_repo = factory.create_product_repository()

    matcher = ProductMatcher(product_repository=product_repo)

    # Test wildcard search
    df = await matcher._local_wildcard_search("heat pump")
    assert df is not None
    assert 'sku' in df.columns
    assert 'data_source' in df.columns

    # Test product code search
    df = await matcher._search_by_product_codes(['12345', '67890'])
    assert df is not None

    print("✅ Lemonsoft via repository works!")

asyncio.run(test_lemonsoft_via_repository())
```

### Test Legacy Mode (backward compatibility):

```python
async def test_legacy_mode():
    # No repository = legacy mode
    matcher = ProductMatcher()

    # Should still work with direct SQL
    df = await matcher._local_wildcard_search("heat pump")
    assert df is not None

    print("✅ Legacy mode still works!")

asyncio.run(test_legacy_mode())
```

---

## 🎉 Summary

**What we achieved:**
- ✅ ProductMatcher now supports multiple ERPs
- ✅ Clean routing through ProductRepository interface
- ✅ Lemonsoft implementation complete
- ✅ 100% backward compatible
- ✅ Ready for Jeeves/Oscar implementation
- ✅ Zero changes to matching logic

**Next ERPs:**
- Jeeves: Implement JeevesProductAdapter (2-3 days)
- Oscar: Implement OscarProductAdapter (2-3 days)

**Impact:**
- ProductMatcher can now work with ANY ERP
- Adding new ERP = implement 2 methods in adapter
- No changes to product matching logic required

**The ProductMatcher is now ERP-agnostic!** 🚀
